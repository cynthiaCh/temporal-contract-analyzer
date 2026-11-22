"""Authorized eight-worker queue, durable progress and automatic result archiving."""
import datetime,json,shutil,subprocess,sys,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent/'temporal-contract-analyzer';sys.path.insert(0,str(REPO))
from temporal_contract_analyzer import archive
from temporal_contract_analyzer.core import sha
TARGET=REPO/'experiments/testing-runs'/ROOT.name

def read(p):return json.loads(p.read_text())
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def snapshot():
    cases=[]
    for row in read(ROOT/'batch/progress.json'):
        t=Path(row['root'])/'trajectory';s=read(t/'state.json');stages=s['stages'];gold=s.get('gold_result') or {}
        assert s.get('contract') is None and all(x['kind'] in ('action','gold') for x in stages)
        cases.append(dict(case_id=row['case_id'],rank=row['rank'],status=s['status'],passed=gold.get('passed') if gold.get('valid') else None,requests=sum(x.get('requests') or 0 for x in stages),error=s.get('error'),stage_kinds=[x['kind'] for x in stages],active=next((x['key'] for x in stages if x['status']=='started'),None)))
    status=dict(at_utc=now(),total=30,passed=sum(x['passed'] is True for x in cases),failed=sum(x['passed'] is False for x in cases),execution_invalid=sum(x['status']=='execution_invalid' for x in cases),started=sum(bool(x['stage_kinds']) for x in cases),active=sum(bool(x['active']) for x in cases),finished=(ROOT/'completion.json').exists(),experience_updates=False,cases=cases)
    archive.atomic_json(ROOT/'monitor-status.json',status);archive.atomic_json(TARGET/'monitor-status.json',status)
    return status

assert read(ROOT/'preflight.json')['valid'] is True
review=read(ROOT/'independent-validation.json');assert review['ready'] is True
assert not (ROOT/'queue-events.jsonl').exists() and not (ROOT/'completion.json').exists()
TARGET.mkdir(parents=True,exist_ok=True)
stop=threading.Event()
def monitor():
    while not stop.is_set():
        try:snapshot()
        except Exception as error:archive.atomic_json(ROOT/'monitor-error.json',dict(at_utc=now(),error=repr(error)))
        stop.wait(10)
thread=threading.Thread(target=monitor,daemon=True);thread.start()
args=[sys.executable,'-B',str(REPO/'tools/tempoevo-docker/run_testing.py'),'--root',str(ROOT),'--workers','8','--execute']
with (ROOT/'testing.log').open('a') as log:result=subprocess.run(args,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
stop.set();thread.join();status=snapshot()
archive.atomic_json(ROOT/'run-exit.json',dict(exit_code=result.returncode,finished_at_utc=now()))
for name in ('completion.json','testing-progress.json','queue-events.jsonl','run-exit.json','monitor-status.json','launch-verification.json'):
    if (ROOT/name).exists():shutil.copyfile(ROOT/name,TARGET/name)
if (ROOT/'completion.json').exists():
    summary=read(ROOT/'completion.json');valid=summary['passed']+summary['failed']
    (TARGET/'RESULT.md').write_text('# GPT-6.1-sol medium: Latent + experience only\n\n'+str(summary['passed'])+' passed; '+str(summary['failed'])+' failed; '+str(summary['unscored'])+' unscored. Valid pass rate: '+(str(round(summary['passed']/valid*100,1))+'%' if valid else 'not available')+'.\n\nAll 30 fixed cases, eight workers, one Action, frozen historical 61-entry bank; no Contract or experience updates. Historical selector costs are separate. Runtime drift is documented in README.md.\n')
    pairs=[];new={r['case_id']:r for r in summary['cases']}
    for old in read(ROOT/'parent-results.json'):
        r=new[old['case_id']];pairs.append(dict(case_id=old['case_id'],historical_auto_contract_experience=old['gold_passed'],latent_experience=r['gold_passed']))
    archive.atomic_json(TARGET/'paired-results.json',pairs)
    subprocess.run(['git','add','--',str(TARGET)],cwd=REPO,check=True)
    check=subprocess.run(['git','diff','--cached','--quiet','--',str(TARGET)],cwd=REPO)
    if check.returncode:
        subprocess.run(['git','commit','--only','-m','Archive GPT-6.1 latent plus experience test30 results','--',str(TARGET)],cwd=REPO,check=True)
print(json.dumps({k:v for k,v in status.items() if k!='cases'}),flush=True)
sys.exit(result.returncode)
