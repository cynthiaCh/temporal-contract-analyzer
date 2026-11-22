"""Eight-worker selection phase followed by frozen one-Action training-set evaluation."""
import csv,datetime,importlib.util,json,shutil,subprocess,sys,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent/'temporal-contract-analyzer';sys.path.insert(0,str(REPO))
from temporal_contract_analyzer import archive,business_retrieval as retrieval
from temporal_contract_analyzer.core import canonical,sha
from temporal_contract_analyzer.tempoevo_v4 import Trajectory
from temporal_contract_analyzer.tempoevo_backend import NativeV4Backend
TARGET=REPO/'experiments/testing-runs'/ROOT.name
read=lambda p:json.loads(p.read_text())
def write(p,x):archive.atomic_json(p,x)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def status(phase,**fields):
 d=dict(at_utc=now(),phase=phase,total=70,workers=8,cohort='training70',experience_updates=False,**fields);write(ROOT/'pipeline-status.json',d);write(TARGET/'pipeline-status.json',d)
def evidence():
 TARGET.mkdir(parents=True,exist_ok=True)
 for name in ('plan.json','README.md','training_70_cases.csv','pipeline-status.json','retrieval-provenance.json','testing-progress.json','completion.json','run-exit.json'):
  if (ROOT/name).exists():shutil.copyfile(ROOT/name,TARGET/name)

def select_job(job):
 t=Trajectory(job['trajectory']);p=read(t.root/'protocol.json');s=t.state();assert not s['stages'] and s['contract'] is None
 delivery=t.retrieve(p,NativeV4Backend(p));s=t.state();assert s['contract'] is None and all(x['kind']=='selection' for x in s['stages'])
 assert s['status']!='execution_invalid',s.get('error')
 stages=[x for x in s['stages'] if x['kind']=='selection']
 output=read(t.root/'stages'/stages[-1]['key']/'result.json').get('output') if delivery['reason']=='public_business_applicability_and_coverage' else None
 frozen=dict(output=output,delivery_sha256=sha(canonical(delivery).encode()))
 sources={f.relative_to(t.root/'original').as_posix():f.read_text() for f in (t.root/'original').rglob('*') if f.is_file()}
 assert retrieval.replay(frozen,p['task'],sources,[e['bundle'] for e in p['memory_snapshot']['entries']])==delivery
 return dict(case_id=job['case_id'],rank=job['rank'],frozen=frozen,nonempty=bool(delivery['experience_text']),requests=sum(x.get('requests') or 0 for x in stages),known_tokens=sum((x.get('tokens') or x.get('observed_tokens') or {}).get('total_tokens',0) for x in stages),gold_passed=None,usage_incomplete=any(x.get('usage_incomplete',False) or type(x.get('requests')) is not int for x in stages),status='selection_frozen')

def main():
 assert not (ROOT/'queue-events.jsonl').exists() and not (ROOT/'completion.json').exists()
 rows=read(ROOT/'selection-seeds-v2/progress.json');selected=read(ROOT/'selection-progress.json');batch=read(ROOT/'batch/progress.json')
 assert len(selected)==len(batch)==70 and all(x['status']=='selection_frozen' for x in selected)
 for r in batch:
  assert r['status']=='prepared';t=Path(r['root'])/'trajectory';p=read(t/'protocol.json');seed=Path(next(x['root'] for x in rows if x['case_id']==r['case_id']))/'trajectory';old=read(seed/'protocol.json')
  assert p['frozen_experience_delivery']==read(seed/'delivery.json') and p['condition']=='latent_experience' and p['total_request_cap']==24
  assert p['evaluation_purpose']=='training_replay' and p['evaluation_split']['role']=='training'
  ga=p['gold_evaluator'];gb=old['gold_evaluator']
  assert {k:v for k,v in ga.items() if k!='inputs'}=={k:v for k,v in gb.items() if k!='inputs'}
  assert {v:Path(k).read_bytes() for k,v in ga['inputs'].items()}=={v:Path(k).read_bytes() for k,v in gb['inputs'].items()}
  for k in ('task','original_inventory','memory_snapshot','model_settings','binary','backend','evaluation_budget','max_attempts'):assert p[k]==old[k],(r['case_id'],k)
 evidence();status('repairing',completed=0)
 stop=threading.Event()
 def monitor():
  while not stop.wait(10):
   try:
    progress=read(ROOT/'testing-progress.json') if (ROOT/'testing-progress.json').exists() else {}
    active=0;started=0
    for row in batch:
     s=read(Path(row['root'])/'trajectory/state.json');assert s['contract'] is None and all(x['kind'] in ('action','gold') for x in s['stages']);started+=bool(s['stages']);active+=any(x['status']=='started' for x in s['stages'])
    status('repairing',completed=progress.get('recorded_cases',0),passed=progress.get('passed',0),failed=progress.get('failed',0),unscored=progress.get('unscored',0),active=active,started=started)
   except Exception as e:write(ROOT/'monitor-error.json',dict(error=repr(e),at_utc=now()))
 thread=threading.Thread(target=monitor,daemon=True);thread.start()
 with (ROOT/'testing.log').open('w') as log:code=subprocess.run([sys.executable,'-B',str(REPO/'tools/tempoevo-docker/run_testing.py'),'--root',str(ROOT),'--workers','8','--execute'],cwd=REPO,stdout=log,stderr=subprocess.STDOUT).returncode
 stop.set();thread.join();summary=read(ROOT/'completion.json');status('finished',completed=summary['recorded_cases'],passed=summary['passed'],failed=summary['failed'],unscored=summary['unscored']);write(ROOT/'run-exit.json',dict(exit_code=code,finished_at_utc=now()));evidence()
 valid=summary['passed']+summary['failed'];(TARGET/'RESULT.md').write_text(f"# GPT-6.1-sol medium training70 Latent+Experience evaluation\n\n{summary['passed']} passed; {summary['failed']} failed; {summary['unscored']} unscored. Valid pass rate {100*summary['passed']/valid if valid else 0:.1f}%.\n\nFrozen61bank, original70training IDs,8workers,oneAction24requests600seconds, noContract or experience updates. Selection requests reported separately. Training-cohort replay, not independent holdout; historical training allowed3Actions and evolved memory, so its65/70 is a different protocol.\n")
 subprocess.run(['git','add','--',str(TARGET)],cwd=REPO,check=True);subprocess.run(['git','commit','--only','-m','Archive GPT-6.1 latent experience train70 evaluation','--',str(TARGET)],cwd=REPO,check=True)
 return code
try:sys.exit(main())
except Exception as e:
 status('pipeline_error',error=repr(e));raise
