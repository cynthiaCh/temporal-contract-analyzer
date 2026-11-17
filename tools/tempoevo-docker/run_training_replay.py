"""Frozen two-arm training replay: one global worker, no memory publication.

Prepare verifies all frozen inputs and calibrates/prepares the first paired case.
Execution calibrates remaining cases just in time, then runs every trajectory via
its public CLI. Calibration and model execution never overlap between cases.
"""
import argparse
import csv
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from temporal_contract_analyzer import archive, experience_approval as approval
from temporal_contract_analyzer.candidate_files import capture, inventory
from temporal_contract_analyzer.tempoevo_v4 import Trajectory
from temporal_contract_analyzer.tempoevo_backend import NativeV4Backend


def read(p): return json.loads(Path(p).read_text())
def save(p, data): archive.atomic_json(Path(p), data)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()


def score_state(state):
    """Repair acceptance survives a subsequent experience-extraction failure."""
    accepted = state.get('training_accepted')
    final = state.get('final_acceptance') or {}
    valid = type(accepted) is bool and final.get('valid') is True
    attempts = state.get('attempts', [])
    first = attempts[0].get('acceptance_passed') if attempts else None
    return dict(final_passed=accepted if valid else None,
                first_passed=first if type(first) is bool else None,
                actions=len(attempts), status=state['status'],
                extraction_error=valid and state['status']=='execution_invalid',
                error=state.get('error'))


def summarize(rows, expected):
    passed=sum(x['final_passed'] is True for x in rows)
    failed=sum(x['final_passed'] is False for x in rows)
    first_valid=sum(type(x['first_passed']) is bool for x in rows)
    return dict(expected_cases=expected,recorded_cases=len(rows),passed=passed,failed=failed,
                unscored=sum(x['final_passed'] is None for x in rows),
                valid=passed+failed,pass_rate=passed/(passed+failed) if passed+failed else None,
                first_passed=sum(x['first_passed'] is True for x in rows),first_valid=first_valid,
                extraction_errors=sum(x['extraction_error'] for x in rows),
                execution_errors_count_as_failure=False,cases=rows)


def verify_inputs(root):
    plan=read(root/'plan.json')
    assert plan['workers']==1 and plan['cases_per_arm']==70
    for name,digest in plan['frozen_files'].items():
        assert sha(root/name)==digest,('Frozen input changed',name)
    spec=read(root/'env-spec.json')
    for name,digest in spec['runtime_files'].items():
        assert sha(REPO/name)==digest,('Runtime changed',name)
    jobs=read(root/'jobs.json');assert len(jobs)==140
    ids={j['case_id'] for j in jobs};assert len(ids)==70
    for arm in ('auto_contract','with_experience'):
        bank=approval.validate_snapshot(root/arm/'experience-library',read(root/arm/'memory-snapshot.json'))
        assert len(bank['entries'])==(0 if arm=='auto_contract' else 61)
        selected=[j for j in jobs if j['arm']==arm]
        assert len(selected)==70 and {j['case_id'] for j in selected}==ids
    for job in jobs:
        config=read(job['config']);p=Path(config['candidate'])
        assert inventory(capture(p)[0])==job['inventory'],('Public source changed',job['case_id'])
        assert config['max_attempts']==3 and config['mode']=='learning' and config['learning_policy']=='frozen'
        assert config['training_recipe']=='v8-compatible-v1' and config['retrieval_profile']=='source-bound-v8'
    return jobs


def calibrate(root, job):
    cid=job['case_id'];base=root/'calibration'/cid;receipt=base/'receipt.json'
    if receipt.exists():
        result=read(receipt)
        assert result['valid'] and result['config_sha256']==sha(job['config'])
        for item in result['raw_results']:assert sha(Path(item['path']))==item['sha256']
        return result
    config=read(job['config']);record=read(root/'case-inputs.json')[cid]
    base.mkdir(parents=True,exist_ok=True);results=[]
    for name,overlay in [('original',None),('reference',record['reference']),('negative',record['negative'])]:
        subject=base/'subjects'/name
        shutil.copytree(config['candidate'],subject)
        if overlay:shutil.copytree(overlay,subject,dirs_exist_ok=True)
        for kind,key in [('visible','visible_evaluator'),('gold','training_evaluator')]:
            output=base/'checks'/name/kind;output.mkdir(parents=True)
            raw=NativeV4Backend({}).evaluate(kind,dict(candidate=str(subject),evaluator=config[key]),output)
            save(output/'result.json',raw)
            assert raw.get('valid') is True,(cid,name,kind,raw.get('error'))
            if kind=='gold':assert raw['passed']==(name=='reference'),(cid,name,kind,'Unexpected control verdict')
            if kind=='visible' and name=='reference':assert raw['passed'] is True,(cid,'Reference fails public syntax')
            results.append(dict(control=name,kind=kind,path=str(output/'result.json'),sha256=sha(output/'result.json'),passed=raw['passed']))
    result=dict(valid=True,case_id=cid,config_sha256=sha(job['config']),raw_results=results,models_called=0)
    save(receipt,result);return result


def prepare_job(job):
    t=Trajectory(job['trajectory'])
    if not (t.root/'protocol.json').exists():t.prepare(read(job['config']))
    p=t.verify()
    assert p['model_settings']['model']=='gpt-5.6-sol' and p['model_settings']['reasoning_effort']=='medium'
    assert p['mode']=='learning' and p['max_attempts']==3 and p['learning_policy']=='frozen'
    assert p['condition']==('contract' if job['arm']=='auto_contract' else 'structured')
    assert len(p['memory_snapshot']['entries'])==(0 if job['arm']=='auto_contract' else 61)
    return p


def prepare(root):
    jobs=verify_inputs(root)
    spec=read(root/'env-spec.json');benchmark=Path(spec['benchmark'])
    code="import sys,json,hashlib;from pathlib import Path;d=json.load(sys.stdin);bad=[k for k,v in d.items() if not (Path('/opt/swe-tempoc')/k).is_file() or hashlib.sha256((Path('/opt/swe-tempoc')/k).read_bytes()).hexdigest()!=v];print(json.dumps(dict(files_checked=len(d),mismatches=bad)))"
    hashes=read(root/'benchmark-file-hashes.json')
    assert all(sha(benchmark/name)==digest for name,digest in hashes.items())
    out=subprocess.run(['docker','run','--rm','-i','--pull=never','--network','none','--read-only','--entrypoint','python3',spec['grader_image'],'-B','-c',code],input=json.dumps(hashes),capture_output=True,text=True,check=True)
    check=json.loads(out.stdout);assert not check['mismatches'];save(root/'selected-case-image-verification.json',check)
    first=jobs[0];calibrate(root,first)
    paired=[j for j in jobs if j['case_id']==first['case_id']]
    for job in paired:prepare_job(job)
    save(root/'preflight.json',dict(valid=True,configs_verified=140,unique_cases=70,prepared_first_pair=[j['trajectory'] for j in paired],remaining_prepared_just_in_time=True,controls_per_case=6,controls_shared_across_arms=True,models_called=0,image_check=check))
    print(json.dumps(read(root/'preflight.json')),flush=True)


def execute(root):
    assert read(root/'agent-follows-doc.json')['status']=='READY'
    assert read(root/'preflight.json')['valid']
    if (root/'completion.json').exists():raise ValueError('Completed replay is read-only')
    jobs=verify_inputs(root);results=[]
    target=REPO/'experiments/training-replays'/root.name;target.mkdir(parents=True,exist_ok=True)
    def persist():
        progress=dict(workers=1,expected_jobs=140,recorded_jobs=len(results),arms={arm:summarize([x for x in results if x['arm']==arm],70) for arm in ('auto_contract','with_experience')})
        save(root/'training-progress.json',progress);shutil.copyfile(root/'training-progress.json',target/'training-progress.json')
    for job in jobs:
        t=Trajectory(job['trajectory']);event=dict(at_utc=now(),event='job_started',case_id=job['case_id'],arm=job['arm'])
        with (root/'queue-events.jsonl').open('a') as f:f.write(json.dumps(event)+'\n')
        # One shared calibration per case, always derived from Auto-Contract config.
        control=next(j for j in jobs if j['case_id']==job['case_id'] and j['arm']=='auto_contract')
        try:
            calibrate(root,control);prepare_job(job);state=t.state()
            if not state.get('finalized') and state['status'] not in ('execution_invalid','cancelled'):
                assert not any(s['status']=='started' for s in state['stages']),'Never silently replay an interrupted stage'
                with (t.root.parent/'training.log').open('a') as log:
                    proc=subprocess.run([sys.executable,'-B','-m','temporal_contract_analyzer','tempoevo','run','--root',str(t.root),'--execute'],cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
                code=proc.returncode
            else:code=None
            row=dict(case_id=job['case_id'],arm=job['arm'],rank=job['rank'],trajectory=str(t.root),queue_exit_code=code,**score_state(t.state()))
        except Exception as error:
            row=dict(case_id=job['case_id'],arm=job['arm'],rank=job['rank'],trajectory=str(t.root),status='queue_error',final_passed=None,first_passed=None,actions=0,extraction_error=False,error=repr(error))
        results.append(row);persist()
        if (t.root/'candidate-pool').exists():shutil.copytree(t.root/'candidate-pool',target/'candidate-pools'/job['arm']/job['case_id'],dirs_exist_ok=True)
        case_archive=target/'cases'/job['arm']/job['case_id'];case_archive.mkdir(parents=True,exist_ok=True)
        for name in ('protocol.json','state.json','summary.json'):
            if (t.root/name).exists():shutil.copyfile(t.root/name,case_archive/name)
        with (root/'queue-events.jsonl').open('a') as f:f.write(json.dumps(dict(at_utc=now(),event='job_finished',**row))+'\n')
        print(json.dumps(row),flush=True)
    complete=read(root/'training-progress.json');complete.update(finished_at_utc=now(),memory_publications=0,bank_frozen=True)
    save(root/'completion.json',complete);shutil.copyfile(root/'completion.json',target/'completion.json');shutil.copyfile(root/'queue-events.jsonl',target/'queue-events.jsonl')
    subprocess.run(['git','add','--',str(target.relative_to(REPO))],cwd=REPO,check=True)
    subprocess.run(['git','commit','--only','-m','Archive GPT5.6 medium train70 two-arm replay results','--',str(target.relative_to(REPO))],cwd=REPO,check=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True)
    g=parser.add_mutually_exclusive_group(required=True);g.add_argument('--prepare-only',action='store_true');g.add_argument('--execute',action='store_true');args=parser.parse_args();root=args.root.resolve()
    with (root/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        (prepare if args.prepare_only else execute)(root)

if __name__=='__main__':main()
