"""Bounded8-worker handoff; first slot observes the already-running CLI."""
import argparse,fcntl,hashlib,importlib.util,json,os,shutil,subprocess,sys,threading,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=Path('/home/sribd/Downloads/wangshu/temporal-contract-analyzer')
sys.path.insert(0,str(REPO))
from temporal_contract_analyzer import archive
from temporal_contract_analyzer.candidate_files import capture,inventory
from temporal_contract_analyzer.tempoevo_v4 import Trajectory
from temporal_contract_analyzer.evaluation_split import enforce
SPEC=importlib.util.spec_from_file_location('replay',REPO/'tools/tempoevo-docker/run_training_replay.py');replay=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(replay)
def read(p):return json.loads(Path(p).read_text())
def save(p,x):archive.atomic_json(Path(p),x)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def alive(pid):
    try:return Path('/proc',str(pid),'stat').read_text().split(') ',1)[1].split()[0]!='Z'
    except FileNotFoundError:return False

def verify():
    plan=read(ROOT/'plan.json');parent=Path(plan['parent']);jobs=read(ROOT/'jobs.json');retained=read(ROOT/'retained-results.json')
    assert plan['workers']==8 and len(jobs)==32 and len(retained)==108
    assert jobs[0]['execution_kind']=='observe_existing' and sum(j['execution_kind']=='observe_existing' for j in jobs)==1
    for name,digest in read(ROOT/'frozen-files.json').items():assert sha(ROOT/name)==digest,('Frozen handoff changed',name)
    for name,digest in plan['runtime_files'].items():assert sha(REPO/name)==digest,('Runtime changed',name)
    original=read(parent/'jobs.json');allkeys={(j['arm'],j['case_id']) for j in original};keys=[(j['arm'],j['case_id']) for j in jobs+retained]
    assert len(set(keys))==len(keys)==140 and set(keys)==allkeys
    prior={(arm,x['case_id']):x for arm,v in read(parent/'training-progress.json')['arms'].items() for x in v['cases']}
    for row in retained:assert prior[row['arm'],row['case_id']]==row
    for job in jobs:
        cfg=read(job['config']);assert inventory(capture(Path(cfg['candidate']))[0])==job['inventory']
        originaljob=next(x for x in original if x['arm']==job['arm'] and x['case_id']==job['case_id']);before=read(originaljob['config'])
        assert all(cfg[k]==v for k,v in before.items())
        if job['execution_kind']=='new':assert enforce(cfg)['role']=='training'
        receipt=read(parent/'calibration'/job['case_id']/'receipt.json');assert receipt['valid']
        auto=next(x for x in original if x['arm']=='auto_contract' and x['case_id']==job['case_id']);assert receipt['config_sha256']==sha(auto['config'])
        for item in receipt['raw_results']:assert sha(item['path'])==item['sha256']
    return plan,jobs,retained

def prepare():
    plan,jobs,retained=verify();bindings=[]
    for job in jobs:
        if job['execution_kind']=='new':
            p=replay.prepare_job(job);s=Trajectory(job['trajectory']).state();assert not s['stages'] and s['status']=='prepared'
        else:p=Trajectory(job['trajectory']).verify()
        bindings.append(dict(arm=job['arm'],case_id=job['case_id'],kind=job['execution_kind'],protocol_sha256=sha(Path(job['trajectory'])/'protocol.json')))
    save(ROOT/'preflight.json',dict(valid=True,retained_jobs=len(retained),retained_valid_scores=plan['retained_valid_scores'],new_fresh_bindings=31,existing_cli_observed=1,total_remaining=32,workers=8,bindings=bindings,new_gold_calls=0,new_model_calls=0))
    print(json.dumps(read(ROOT/'preflight.json'))[:400],flush=True)

def execute():
    assert read(ROOT/'agent-follows-doc.json')['status']=='READY'
    plan,jobs,retained=verify();parent=Path(plan['parent']);assert read(ROOT/'preflight.json')['valid']
    # Verify stopped scheduler cannot dispatch; replacement waiter was stopped too.
    state=Path('/proc',str(plan['old_scheduler_pid']),'stat').read_text().split(') ',1)[1].split()[0];assert state=='T'
    assert not alive(plan['old_recovery_waiter_pid'])
    assert not (ROOT/'completion.json').exists()
    target=REPO/'experiments/training-replays'/ROOT.name;target.mkdir(parents=True,exist_ok=True)
    lock=threading.Lock();results=list(retained)
    def event(e):
        with lock:
            with (ROOT/'queue-events.jsonl').open('a') as f:f.write(json.dumps(dict(at_utc=now(),**e))+'\n')
    def run(job):
        t=Trajectory(job['trajectory']);event(dict(event='job_started',arm=job['arm'],case_id=job['case_id'],kind=job['execution_kind']))
        if job['execution_kind']=='observe_existing':
            while alive(job['observe_pid']):time.sleep(2)
            rc=None
        else:
            p=t.verify();state=t.state();assert not state['stages'],'Never replay a previously started model task'
            with (t.root.parent/'training.log').open('a') as log:
                proc=subprocess.Popen([sys.executable,'-B','-m','temporal_contract_analyzer','tempoevo','run','--root',str(t.root),'--execute'],cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
                event(dict(event='model_cli_started',arm=job['arm'],case_id=job['case_id'],pid=proc.pid));rc=proc.wait()
        row=dict(case_id=job['case_id'],arm=job['arm'],rank=job['rank'],trajectory=str(t.root),queue_exit_code=rc,handoff_origin=job['origin'],**replay.score_state(t.state()))
        event(dict(event='job_finished',**row));return row
    def persist():
        d=dict(workers=8,expected_jobs=140,retained_jobs=108,recorded_jobs=len(results),new_jobs_finished=len(results)-108,remaining_jobs=140-len(results),arms={a:replay.summarize([x for x in results if x['arm']==a],70) for a in ['auto_contract','with_experience']})
        save(ROOT/'training-progress.json',d);shutil.copyfile(ROOT/'training-progress.json',target/'training-progress.json')
    persist()
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures={pool.submit(run,j):j for j in jobs}
        for future in as_completed(futures):
            j=futures[future]
            try:row=future.result()
            except Exception as error:row=dict(arm=j['arm'],case_id=j['case_id'],rank=j['rank'],trajectory=j['trajectory'],final_passed=None,first_passed=None,actions=0,status='queue_error',error=repr(error),extraction_error=False)
            results.append(row);persist();print(json.dumps(row),flush=True)
    d=read(ROOT/'training-progress.json');d.update(finished_at_utc=now(),parent=str(parent),split_recovery=plan['split_recovery'],original_valid_scores_preserved=105,memory_publications=0,worker_change='initial1worker;remaining32jobs use8slots including observer of existing CLI')
    save(ROOT/'completion.json',d)
    # Collect both inherited and new receipts/drafts, without publishing guidance.
    for row in results:
        t=Path(row['trajectory']);dest=target/'cases'/row['arm']/row['case_id'];dest.mkdir(parents=True,exist_ok=True)
        for name in ['protocol.json','state.json','summary.json']:
            if (t/name).exists():shutil.copyfile(t/name,dest/name)
        if (t/'candidate-pool').exists():shutil.copytree(t/'candidate-pool',dest/'candidate-pool',dirs_exist_ok=True)
    for name in ['completion.json','training-progress.json','queue-events.jsonl']:shutil.copyfile(ROOT/name,target/name)
    def cell(arm):
        a=d['arms'][arm];return f"**{100*a['pass_rate']:.1f}%（{a['passed']}/{a['valid']}）**，{a['unscored']}例执行异常，最多3轮" if a['pass_rate'] is not None else '无有效评分'
    table="""| 集合 | 执行模型 | case / cluster数 | Latent通过率 | 仅Auto-Contract（无经验） | 带经验最终通过率 |
|---|---|---:|---|---|---|
| 训练集 | GPT-6.1-sol medium | 70 / 24 | **51.2%**，覆盖70/70 | **82.6%（19/23）**，仅覆盖23/70，最多3轮 | **92.9%（65/70）**，最多3轮 |
| 训练集 | GPT-5.6-sol medium | 70 / 24 | **31.9%（22/69）**，覆盖69/70 | AUTO_CELL | MEMORY_CELL |
| 测试集 | GPT-5.6-sol medium | 30 / 14 | **16.7%（5/30）** | **34.5%（10/29）**，1例执行异常 | **82.1%（23/28）**，2例执行异常 |
| 测试集 | GPT-6.1-sol medium | 30 / 14 | **72.4%（21/29）**，1例评分异常 | **53.3%（16/30）** | **90.0%（27/30）** |

执行/评分异常排除分母。GPT5.6训练集是固定0/61经验库、最多3轮的训练集复测，经验包含本训练集历史来源，不是独立泛化测试或历史在线训练重建。保留原105个有效评分和3个执行异常；余下32个任务含原正在运行任务，按用户要求切至8并发，补齐24个因漏传最终划分而未启动的任务，未修改全局划分和训练/测试成员。候选经验只归档，不发布、不在线复用。
""".replace('AUTO_CELL',cell('auto_contract')).replace('MEMORY_CELL',cell('with_experience'))
    (ROOT/'BIG_TABLE.md').write_text(table);shutil.copyfile(ROOT/'BIG_TABLE.md',target/'BIG_TABLE.md')
    # The old coordinator was paused before scheduling any more work. Retire it
    # only after its preserved child has finished; never signal the child/group.
    if alive(plan['old_scheduler_pid']):
        import signal
        os.kill(plan['old_scheduler_pid'],signal.SIGTERM);os.kill(plan['old_scheduler_pid'],signal.SIGCONT)
    subprocess.run(['git','add','--',str(target.relative_to(REPO))],cwd=REPO,check=True)
    subprocess.run(['git','commit','--quiet','--only','-m','Complete8worker GPT5.6 train70 replay preserving prior scores','--',str(target.relative_to(REPO))],cwd=REPO,check=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--prepare-only',action='store_true');g.add_argument('--execute',action='store_true');a=p.parse_args()
    with (ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        (prepare if a.prepare_only else execute)()
