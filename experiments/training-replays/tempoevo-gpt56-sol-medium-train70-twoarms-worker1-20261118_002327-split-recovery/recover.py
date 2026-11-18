"""Recover only never-started tasks blocked by omitted explicit cohort split."""
import argparse,fcntl,hashlib,importlib.util,json,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=Path('/home/sribd/Downloads/wangshu/temporal-contract-analyzer')
sys.path.insert(0,str(REPO))
from temporal_contract_analyzer import archive
from temporal_contract_analyzer.candidate_files import capture,inventory
from temporal_contract_analyzer.evaluation_split import enforce
from temporal_contract_analyzer.tempoevo_v4 import Trajectory
SPEC=importlib.util.spec_from_file_location('replay',REPO/'tools/tempoevo-docker/run_training_replay.py')
replay=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(replay)
def read(p):return json.loads(Path(p).read_text())
def save(p,x):archive.atomic_json(Path(p),x)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def verify():
    plan=read(ROOT/'plan.json');parent=Path(plan['parent']);jobs=read(ROOT/'jobs.json');assert len(jobs)==24
    for name,digest in read(ROOT/'frozen-files.json').items():assert sha(ROOT/name)==digest,('Changed recovery input',name)
    for name,digest in plan['runtime_files'].items():assert sha(REPO/name)==digest,('Changed parent runtime',name)
    pp=read(parent/'plan.json');receipts=[]
    for j in jobs:
        old=Path(j['parent_config']);assert sha(old)==pp['frozen_files'][str(old.relative_to(parent))]
        before=read(old);after=read(j['config']);assert set(after)==set(before)|{'evaluation_split_file'}
        assert all(after[k]==v for k,v in before.items())
        assert enforce(after)['role']=='training'
        assert inventory(capture(Path(after['candidate']))[0])==j['inventory']
        oldtrajectory=Path(j['parent_trajectory']);assert not (oldtrajectory/'state.json').exists(),'Never replay a started model task'
        receiptpath=parent/'calibration'/j['case_id']/'receipt.json';receipt=read(receiptpath)
        auto=next(x for x in read(parent/'jobs.json') if x['case_id']==j['case_id'] and x['arm']=='auto_contract')
        assert receipt['valid'] and receipt['config_sha256']==sha(auto['config'])
        for raw in receipt['raw_results']:assert sha(raw['path'])==raw['sha256']
        receipts.append(dict(case_id=j['case_id'],path=str(receiptpath),sha256=sha(receiptpath)))
    return parent,jobs,receipts

def prepare():
    parent,jobs,receipts=verify();bindings=[]
    for j in jobs:
        p=replay.prepare_job(j);state=Trajectory(j['trajectory']).state();assert not state['stages'] and state['status']=='prepared'
        assert p['evaluation_split']['role']=='training' and p['max_attempts']==3
        assert p['model_settings']['model']=='gpt-5.6-sol' and p['model_settings']['reasoning_effort']=='medium'
        bindings.append(dict(case_id=j['case_id'],arm=j['arm'],protocol_sha256=sha(Path(j['trajectory'])/'protocol.json')))
    save(ROOT/'preflight.json',dict(valid=True,jobs=24,unique_cases=12,models_called=0,new_gold_calls=0,bindings=bindings,reused_controls=receipts))
    print(json.dumps(dict(valid=True,jobs=24,unique_cases=12,models_called=0,new_gold_calls=0)),flush=True)

def execute():
    assert read(ROOT/'agent-follows-doc.json')['status']=='READY';parent,jobs,_=verify()
    target=REPO/'experiments/training-replays'/ROOT.name;target.mkdir(parents=True,exist_ok=True)
    save(ROOT/'waiting.json',dict(status='waiting_for_parent_queue_lock',parent=str(parent),workers=1,at_utc=now()))
    # Parent holds this exact lock until all140 original jobs finish. No overlap.
    with (parent/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        previous=read(parent/'completion.json');results=[]
        old={(arm,x['case_id']):x for arm,v in previous['arms'].items() for x in v['cases']}
        for j in jobs:
            prior=old[j['arm'],j['case_id']]
            assert prior['final_passed'] is None and prior['actions']==0 and 'Reserved testing case' in prior.get('error','')
            t=Trajectory(j['trajectory']);t.verify();assert not t.state()['stages']
            with (ROOT/'queue-events.jsonl').open('a') as f:f.write(json.dumps(dict(event='job_started',arm=j['arm'],case_id=j['case_id'],at_utc=now()))+'\n')
            with (t.root.parent/'training.log').open('a') as log:rc=subprocess.run([sys.executable,'-B','-m','temporal_contract_analyzer','tempoevo','run','--root',str(t.root),'--execute'],cwd=REPO,stdout=log,stderr=subprocess.STDOUT).returncode
            row=dict(case_id=j['case_id'],arm=j['arm'],rank=j['rank'],trajectory=str(t.root),queue_exit_code=rc,**replay.score_state(t.state()))
            results.append(row);save(ROOT/'recovery-progress.json',dict(expected_jobs=24,recorded_jobs=len(results),workers=1,cases=results))
            d=target/'cases'/j['arm']/j['case_id'];d.mkdir(parents=True,exist_ok=True)
            for name in ('protocol.json','state.json','summary.json'):shutil.copyfile(t.root/name,d/name)
            if (t.root/'candidate-pool').exists():shutil.copytree(t.root/'candidate-pool',d/'candidate-pool',dirs_exist_ok=True)
            with (ROOT/'queue-events.jsonl').open('a') as f:f.write(json.dumps(dict(event='job_finished',at_utc=now(),**row))+'\n')
            print(json.dumps(row),flush=True)
        replacements={(x['arm'],x['case_id']):x for x in results}
        arms={arm:replay.summarize([replacements.get((arm,x['case_id']),x) for x in v['cases']],70) for arm,v in previous['arms'].items()}
        merged=dict(expected_jobs=140,recorded_jobs=140,workers=1,arms=arms,parent=str(parent),recovery=str(ROOT),replaced_never_started_setup_errors=24,finished_at_utc=now(),original_results_preserved=True,experience_publications=0)
        save(ROOT/'completion.json',merged);save(ROOT/'recovery-progress.json',dict(expected_jobs=24,recorded_jobs=24,workers=1,cases=results))
        def cell(arm):
            a=arms[arm];return f"**{100*a['pass_rate']:.1f}%（{a['passed']}/{a['valid']}）**，{a['unscored']}例执行异常，最多3轮" if a['pass_rate'] is not None else '无有效评分'
        if (parent/'BIG_TABLE.md').exists():
            text=(parent/'BIG_TABLE.md').read_text();lines=text.splitlines()
            lines=[f"| 训练集 | GPT-5.6-sol medium | 70 / 24 | **31.9%（22/69）**，覆盖69/70 | {cell('auto_contract')} | {cell('with_experience')} |" if line.startswith('| 训练集 | GPT-5.6-sol medium |') else line for line in lines]
            text='\n'.join(lines)+'\n\n已用原最终70/30划分显式绑定，补跑因旧默认划分误拦截而未调用模型的24个任务；原始评分和原始错误记录保留。全程1并发。\n'
            (ROOT/'BIG_TABLE.md').write_text(text);shutil.copyfile(ROOT/'BIG_TABLE.md',target/'BIG_TABLE.md')
        for name in ('completion.json','recovery-progress.json','queue-events.jsonl'):shutil.copyfile(ROOT/name,target/name)
    subprocess.run(['git','add','--',str(target.relative_to(REPO))],cwd=REPO,check=True)
    subprocess.run(['git','commit','--only','-m','Complete train70 replay with explicit final split recovery','--',str(target.relative_to(REPO))],cwd=REPO,check=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--prepare-only',action='store_true');g.add_argument('--execute',action='store_true');args=p.parse_args()
    (prepare if args.prepare_only else execute)()
