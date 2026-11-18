"""Authorized fresh rerun of exactly five unscored training evaluations."""
import argparse,fcntl,hashlib,importlib.util,json,shutil,subprocess,sys,threading
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=Path('/home/sribd/Downloads/wangshu/temporal-contract-analyzer')
sys.path.insert(0,str(REPO))
from temporal_contract_analyzer import archive,experience_approval as approval
from temporal_contract_analyzer.candidate_files import capture,inventory
from temporal_contract_analyzer.evaluation_split import enforce
from temporal_contract_analyzer.tempoevo_v4 import Trajectory
SPEC=importlib.util.spec_from_file_location('replay',REPO/'tools/tempoevo-docker/run_training_replay.py');replay=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(replay)
def read(p):return json.loads(Path(p).read_text())
def save(p,x):archive.atomic_json(Path(p),x)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def verify_inputs():
    plan=read(ROOT/'plan.json');jobs=read(ROOT/'jobs.json');assert len(jobs)==5
    for n,v in read(ROOT/'frozen-files.json').items():assert sha(ROOT/n)==v,('Frozen retry inputs changed',n)
    for n,v in read(ROOT/'env-spec.json')['runtime_files'].items():assert sha(REPO/n)==v,('Runtime changed',n)
    original=read(Path(plan['parent'])/'completion.json')['arms']['with_experience']['cases'];bad={x['case_id'] for x in original if x['final_passed'] is None}
    assert {j['case_id'] for j in jobs}==bad and all(x['actions']==0 for x in original if x['case_id'] in bad)
    bank=approval.validate_snapshot(ROOT/'experience-library',read(ROOT/'memory-snapshot.json'));assert len(bank['entries'])==61
    records=[]
    source=Path(plan['original']);alloriginal=read(source/'jobs.json')
    for j in jobs:
        cfg=read(j['config']);assert enforce(cfg)['role']=='training';assert sha(j['binary'])==j['binary_sha256']
        assert inventory(capture(Path(cfg['candidate']))[0])==j['original_inventory']
        receiptpath=source/'calibration'/j['case_id']/'receipt.json';receipt=read(receiptpath);assert receipt['valid']
        auto=next(x for x in alloriginal if x['arm']=='auto_contract' and x['case_id']==j['case_id']);assert receipt['config_sha256']==sha(auto['config'])
        for x in receipt['raw_results']:
            assert sha(x['path'])==x['sha256'];raw=read(x['path']);assert raw['valid']
            if x['kind']=='gold':assert raw['passed']==(x['control']=='reference')
        records.append(dict(case_id=j['case_id'],receipt=str(receiptpath),sha256=sha(receiptpath)))
    return plan,jobs,records

def prepare():
    plan,jobs,controls=verify_inputs();spec=read(ROOT/'env-spec.json');hashes=read(ROOT/'benchmark-file-hashes.json')
    code="import sys,json,hashlib;from pathlib import Path;d=json.load(sys.stdin);bad=[k for k,v in d.items() if not (Path('/opt/swe-tempoc')/k).is_file() or hashlib.sha256((Path('/opt/swe-tempoc')/k).read_bytes()).hexdigest()!=v];print(json.dumps(dict(files_checked=len(d),mismatches=bad)))"
    out=subprocess.run(['docker','run','--rm','-i','--pull=never','--network','none','--read-only','--entrypoint','python3',spec['grader_image'],'-B','-c',code],input=json.dumps(hashes),text=True,capture_output=True,check=True)
    imagecheck=json.loads(out.stdout);assert not imagecheck['mismatches'];save(ROOT/'selected-case-image-verification.json',imagecheck)
    bindings=[]
    allowed={str(REPO/'temporal_contract_analyzer/_session_runtime/read_policy.py'),str(REPO/'experiments/evaluation-splits.json')}
    for j in jobs:
        p=replay.prepare_job(j);old=read(Path(j['original_trajectory'])/'protocol.json');t=Path(j['trajectory']);s=read(t/'state.json');assert not s['stages'] and s['status']=='prepared'
        for k in ['task','original_inventory','public_case_record','model_settings','backend','limits','max_attempts','memory_snapshot','training_recipe','retrieval_profile','learning_policy','training_feedback']:assert p.get(k)==old.get(k),(j['case_id'],k)
        assert p['binary']==old['binary'] and p['total_request_cap']==old['total_request_cap']==132
        for k in ['training_evaluator','visible_evaluator']:
            assert all(p[k][a]==old[k][a] for a in ['image','command','seconds'])
            assert {v:sha(k) for k,v in p[k]['inputs'].items()}=={v:sha(k) for k,v in old[k]['inputs'].items()}
        newbinding=read(t/'binding.json');oldbinding=read(Path(j['original_trajectory'])/'binding.json')
        delta={k for k,v in oldbinding['runtime'].items() if newbinding['runtime'].get(k)!=v};assert delta<=allowed and str(REPO/'temporal_contract_analyzer/_session_runtime/read_policy.py') in delta
        bindings.append(dict(case_id=j['case_id'],protocol_sha256=sha(t/'protocol.json'),binding_sha256=sha(t/'binding.json'),runtime_delta=sorted(delta)))
    save(ROOT/'preflight.json',dict(valid=True,cases=5,bindings=bindings,controls_reused=30,control_receipts=controls,imagecheck=imagecheck,new_model_calls=0,new_gold_calls=0,other65scores_unchanged=True))
    print(json.dumps(dict(valid=True,cases=5,controls_reused=30,new_model_calls=0,new_gold_calls=0)),flush=True)

def execute():
    assert read(ROOT/'agent-follows-doc.json')['status']=='READY';plan,jobs,_=verify_inputs();assert read(ROOT/'preflight.json')['valid']
    assert not (ROOT/'completion.json').exists();target=REPO/'experiments/training-replays'/ROOT.name;target.mkdir(parents=True,exist_ok=True)
    lock=threading.Lock();results=[]
    def event(x):
        with lock:
            with (ROOT/'queue-events.jsonl').open('a') as f:f.write(json.dumps(dict(at_utc=now(),**x))+'\n')
    def one(j):
        t=Trajectory(j['trajectory']);t.verify();assert not t.state()['stages'],'Never silently replay started attempts'
        event(dict(event='job_started',case_id=j['case_id'],arm='with_experience'))
        with (t.root.parent/'training.log').open('a') as log:
            proc=subprocess.Popen([sys.executable,'-B','-m','temporal_contract_analyzer','tempoevo','run','--root',str(t.root),'--execute'],cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
            event(dict(event='model_cli_started',case_id=j['case_id'],pid=proc.pid));rc=proc.wait()
        row=dict(case_id=j['case_id'],arm='with_experience',rank=j['rank'],trajectory=str(t.root),queue_exit_code=rc,retry_of=j['original_trajectory'],**replay.score_state(t.state()))
        event(dict(event='job_finished',**row));return row
    with ThreadPoolExecutor(max_workers=min(8,len(jobs))) as pool:
        futures={pool.submit(one,j):j for j in jobs}
        for future in as_completed(futures):
            j=futures[future]
            try:row=future.result()
            except Exception as error:row=dict(case_id=j['case_id'],arm='with_experience',rank=j['rank'],trajectory=j['trajectory'],final_passed=None,first_passed=None,actions=0,status='queue_error',extraction_error=False,error=repr(error))
            results.append(row);save(ROOT/'retry-progress.json',dict(workers=8,actual_max_active_jobs=5,expected_cases=5,recorded_cases=len(results),summary=replay.summarize(results,5)))
            print(json.dumps(row),flush=True)
    parent=read(Path(plan['parent'])/'completion.json');mapping={x['case_id']:x for x in results};original=parent['arms']['with_experience']['cases']
    combined=[mapping.get(x['case_id'],x) for x in original];assert len(combined)==70 and len({x['case_id'] for x in combined})==70
    for x in original:
        if x['case_id'] not in mapping:assert combined[original.index(x)]==x
    arms=dict(parent['arms']);arms['with_experience']=replay.summarize(combined,70)
    completion=dict(expected_jobs=140,recorded_jobs=140,remaining_jobs=0,workers=8,finished_at_utc=now(),arms=arms,parent=str(plan['parent']),retry_cases=results,retained_with_experience_valid_scores=65,auto_contract_unchanged=True,memory_publications=0,protocol_note='Only5 previously unscored executions replaced after read-policy fix; all other65 training-with-memory scores and70auto-contract scores retained. Fixed61 bank, same original task/source/model/CLI/Gold/budgets. Earlier execution records retained separately.')
    save(ROOT/'completion.json',completion)
    for row in results:
        t=Path(row['trajectory']);d=target/'cases'/row['case_id'];d.mkdir(parents=True,exist_ok=True)
        for n in ['protocol.json','state.json','summary.json']:shutil.copyfile(t/n,d/n)
        if (t/'candidate-pool').exists():shutil.copytree(t/'candidate-pool',d/'candidate-pool',dirs_exist_ok=True)
    table=(Path(plan['parent'])/'BIG_TABLE.md').read_text();a=arms['with_experience'];cell=f"**{100*a['pass_rate']:.1f}%（{a['passed']}/{a['valid']}）**，{a['unscored']}例执行异常，最多3轮"
    lines=[]
    for line in table.splitlines():
        if line.startswith('| 训练集 | GPT-5.6-sol medium |') or line.startswith('| 训练集复测 | GPT-5.6-sol medium |'):
            line=f"| 训练集复测 | GPT-5.6-sol medium | 70 / 24 | **31.9%（22/69）**，覆盖69/70 | **38.6%（27/70）**，最多3轮 | {cell} |"
        lines.append(line)
    (ROOT/'BIG_TABLE.md').write_text('\n'.join(lines)+'\n\n本次只补跑5例执行异常，保留另外65例带经验评分；修复只读sort与换行命令误拒绝，网络异常从原始源码重新运行。固定61条经验、不在线更新。原5例异常及旧版本评分记录保留。\n')
    for n in ['completion.json','retry-progress.json','queue-events.jsonl','BIG_TABLE.md']:shutil.copyfile(ROOT/n,target/n)
    subprocess.run(['git','add','--',str(target.relative_to(REPO))],cwd=REPO,check=True)
    subprocess.run(['git','commit','--quiet','--only','-m','Archive5 execution-error reruns and updated train70 results','--',str(target.relative_to(REPO))],cwd=REPO,check=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--prepare-only',action='store_true');g.add_argument('--execute',action='store_true');args=p.parse_args()
    with (ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);(prepare if args.prepare_only else execute)()
