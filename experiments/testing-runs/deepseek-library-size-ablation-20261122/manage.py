"""Frozen nested size ablation; prepare without model calls, then controller queue."""
import copy, datetime, hashlib, json, os, random, subprocess, sys, time, urllib.request
from pathlib import Path
REPO=Path(__file__).resolve().parents[3]
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(REPO))
from temporal_contract_analyzer import experience_approval as approval
from temporal_contract_analyzer.experience_memory import canonical
from temporal_contract_analyzer.tempoevo_v4 import Trajectory
PARENT=REPO/'.tempoevo/runs/run-20261121-093940-7eca6f'
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def api(path,body=None):
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    if body is None:return json.load(opener.open('http://127.0.0.1:8765'+path,timeout=60))
    token=api('/api/bootstrap')['token']
    req=urllib.request.Request('http://127.0.0.1:8765'+path,data=json.dumps(body).encode(),headers={'Content-Type':'application/json','Origin':'http://127.0.0.1:8765','X-TempoEvo-Token':token})
    return json.load(opener.open(req,timeout=120))
def prepare():
    assert not (ROOT/'plan.json').exists(), 'Never overwrite a frozen plan'
    assert not any(r['status'] in ('running','preparing','stopping') for r in api('/api/runs'))
    bank=read(PARENT/'batch/memory-snapshot.json')
    approval.validate_snapshot(REPO/'experience-memory/library',bank)
    entries=sorted(bank['entries'],key=lambda e:e['bundle']['sha256'])
    random.Random(20261118).shuffle(entries)
    plan=dict(created_at=now(),model='DeepSeek-Flash',reasoning_effort='low',backend='Qoder Credits',workers=8,global_max_workers=8,selection='Sort original58 by bundle sha256, shuffle with Python random.Random(20261118), use nested prefixes20/40. No outcomes used.',seed=20261118,source_bank_sha256=bank['sha256'],source_size=58,case_selection='cases/test30.csv',testing_policy='One Action; frozen memory; candidate crashes count as failure; infrastructure errors separately identified.',arms=[])
    for n in (20,40):
        subset={k:copy.deepcopy(bank[k]) for k in ('schema_version','scope')};subset['entries']=entries[:n];subset['sha256']=hashlib.sha256(canonical(subset).encode()).hexdigest()
        approval.validate_snapshot(REPO/'experience-memory/library',subset)
        snapshot=ROOT/f'memory{n}-snapshot.json';write(snapshot,subset)
        ident='run-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S')+f'-memory{n}'
        target=REPO/'.tempoevo/runs'/ident;target.mkdir()
        old=read(PARENT/'lab.json');command=old['prepare_command'][:];command[command.index('--root')+1]=str(target/'batch');command+=['--memory-snapshot',str(snapshot)]
        config=copy.deepcopy(old['config']);config['workers']=8
        meta=dict(id=ident,title=f'DeepSeek Flash low · {n} experiences · fixed30 · workers8',status='preparing',created_at=now(),config=config,model=old['model'],prepare_command=command,ablation=dict(size=n,plan=str(ROOT/'plan.json'),parent=str(PARENT),snapshot_sha256=subset['sha256']))
        write(target/'lab.json',meta)
        arm=dict(size=n,id=ident,root=str(target),snapshot=str(snapshot),snapshot_sha256=subset['sha256'],selected_ids=[e['bundle']['id'] for e in entries[:n]])
        plan['arms'].append(arm)
    write(ROOT/'plan.json',plan)
    for arm in plan['arms']:
        target=Path(arm['root']);meta=read(target/'lab.json')
        with (target/'prepare.log').open('w') as log:
            result=subprocess.run(meta['prepare_command'],cwd=REPO,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,TCA_BENCH_ROOT=meta['config']['benchmark']))
        assert result.returncode==0,(arm['id'],'prepare failed')
        rows=read(target/'batch/progress.json');oldrows=read(PARENT/'batch/progress.json')
        assert len(rows)==30 and [r['case_id'] for r in rows]==[r['case_id'] for r in oldrows]
        bindings=[]
        for row in rows:
            current=Path(row['root'])/'trajectory';p=Trajectory(current).verify();previous=read(PARENT/'batch'/row['case_id']/'trajectory/protocol.json')
            for key in ('task','original_inventory','public_case_record','binary','model_settings','backend','limits','total_request_cap','max_attempts','mode','learning_policy','retrieval_profile'):
                assert p[key]==previous[key],(row['case_id'],key)
            assert p['condition']=='structured' and p['mode']=='testing' and p['max_attempts']==1
            assert len(p['memory_snapshot']['entries'])==arm['size'] and p['memory_snapshot']['sha256']==arm['snapshot_sha256']
            assert p['gold_evaluator']['image']==previous['gold_evaluator']['image'] and p['gold_evaluator']['command']==previous['gold_evaluator']['command']
            assert p['evaluation_split']['role']=='testing'
            bindings.append(dict(case_id=row['case_id'],protocol_sha256=hashlib.sha256((current/'protocol.json').read_bytes()).hexdigest()))
        write(target/'paired-input-validation.json',dict(valid=True,cases=30,size=arm['size'],model_calls=0,bindings=bindings,notes='Same original tasks, sources, model, images, stage/total budgets, one Action and final scorer. Runtime includes already-committed adapter fixes since original58 run; no new adapter edits for ablation.'))
        meta.update(status='prepared',prepared_cases=30,updated_at=now());write(target/'lab.json',meta)
        with (target/'events.jsonl').open('a') as log:log.write(json.dumps(dict(at=now(),kind='READY',message=f'30 cases validated; frozen {arm["size"]}-entry subset; no models launched by preparation.'))+'\n')
        print('READY',arm['size'],arm['id'],flush=True)
def run():
    plan=read(ROOT/'plan.json')
    for arm in plan['arms']:
        target=Path(arm['root']);status=read(target/'lab.json')['status']
        while status=='preparing':
            time.sleep(15);status=read(target/'lab.json')['status']
        if status=='prepared':
            print('START',arm['size'],api('/api/start',dict(id=arm['id'])),flush=True)
        while read(target/'lab.json')['status']=='running':time.sleep(15)
        status=read(target/'lab.json')['status'];print('ENDED',arm['size'],status,flush=True)
        assert status=='finished', 'Queue interrupted; do not automatically continue'
        time.sleep(2)
    write(ROOT/'queue-complete.json',dict(at=now(),arms=plan['arms']))
if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='run':run()
