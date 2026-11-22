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
 for p in ROOT.iterdir():
  if p.is_file() and p.suffix in ('.json','.py','.md','.csv'):shutil.copyfile(p,TARGET/p.name)
 for p in (ROOT/'calibration').glob('*/[orn]*/result.json'):
  q=TARGET/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)

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
 assert read(ROOT/'independent-validation.json')['ready'] and read(ROOT/'preflight.json')['valid']
 assert not (ROOT/'selection-events.jsonl').exists() and not (ROOT/'queue-events.jsonl').exists()
 spec=importlib.util.spec_from_file_location('training_cohort_queue',REPO/'tools/tempoevo-docker/run_testing.py');queue=importlib.util.module_from_spec(spec);spec.loader.exec_module(queue)
 rows=read(ROOT/'selection-seeds-v2/progress.json');jobs=[dict(case_id=r['case_id'],rank=r['rank'],trajectory=str(Path(r['root'])/'trajectory')) for r in rows]
 lock=threading.Lock()
 def event(v):
  with lock:
   with (ROOT/'selection-events.jsonl').open('a') as f:f.write(json.dumps(dict(at_utc=now(),**v))+'\n')
 def execute(job):
  event(dict(event='selection_started',case_id=job['case_id']));r=select_job(job);event(dict(event='selection_finished',case_id=job['case_id'],nonempty=r['nonempty'],requests=r['requests']));return r
 def progress(results):
  write(ROOT/'selection-progress.json',results);status('selecting_experience',completed=len(results),nonempty=sum(r.get('nonempty',False) for r in results),selection_requests=sum(r.get('requests') or 0 for r in results),selection_known_tokens=sum(r.get('known_tokens',0) for r in results),selection_usage_incomplete=any(r.get('usage_incomplete',True) for r in results))
 status('selecting_experience',completed=0)
 selected=queue.schedule(jobs,8,execute,progress,event=event)
 assert len(selected)==70 and all(r['status']=='selection_frozen' for r in selected),'Selection infrastructure errors: inspect selection-progress.json; no repair scores produced'
 write(ROOT/'frozen-selections.json',{r['case_id']:r['frozen'] for r in selected})
 write(ROOT/'retrieval-provenance.json',dict(policy='fresh public-source business selection then freeze, no scoring feedback',cases=70,nonempty=sum(r['nonempty'] for r in selected),selection_requests=sum(r['requests'] for r in selected),selection_known_tokens=sum(r['known_tokens'] for r in selected),selection_usage_incomplete=any(r['usage_incomplete'] for r in selected),experience_updates=False))
 status('preparing_frozen_actions',completed=70)
 args=read(ROOT/'seed-command.json');args[args.index('--root')+1]=str(ROOT/'batch');args[args.index('--condition')+1]='latent_experience';args+=['--frozen-selections',str(ROOT/'frozen-selections.json')]
 write(ROOT/'action-prepare-command.json',args)
 with (ROOT/'prepare-actions.log').open('w') as log:subprocess.run(args,cwd=REPO,stdout=log,stderr=subprocess.STDOUT,check=True)
 batch=read(ROOT/'batch/progress.json');assert len(batch)==70
 for r in batch:
  assert r['status']=='prepared';t=Path(r['root'])/'trajectory';p=read(t/'protocol.json');seed=Path(next(x['root'] for x in rows if x['case_id']==r['case_id']))/'trajectory';old=read(seed/'protocol.json')
  assert p['frozen_experience_delivery']==read(seed/'delivery.json') and p['condition']=='latent_experience' and p['total_request_cap']==24
  assert p['evaluation_purpose']=='training_replay' and p['evaluation_split']['role']=='training'
  for k in ('task','original_inventory','memory_snapshot','model_settings','binary','backend','gold_evaluator','evaluation_budget','max_attempts'):assert p[k]==old[k],(r['case_id'],k)
 write(ROOT/'action-preflight.json',dict(valid=True,cases=70,nonempty_experience_cases=sum(x['nonempty'] for x in selected),action_attempts=1,contract=False,total_action_request_cap=24,selection_usage_separate=True))
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
 for r in rows:
  t=Path(r['root'])/'trajectory';out=TARGET/'selector-evidence'/r['case_id'];out.mkdir(parents=True,exist_ok=True)
  for name in ('protocol.json','state.json','delivery.json'):shutil.copyfile(t/name,out/name)
  for p in t.glob('stages/*/result.json'):
   q=out/p.relative_to(t);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
 valid=summary['passed']+summary['failed'];(TARGET/'RESULT.md').write_text(f"# GPT-6.1-sol medium training70 Latent+Experience evaluation\n\n{summary['passed']} passed; {summary['failed']} failed; {summary['unscored']} unscored. Valid pass rate {100*summary['passed']/valid if valid else 0:.1f}%.\n\nFrozen61bank, original70training IDs,8workers,oneAction24requests600seconds, noContract or experience updates. Selection requests reported separately. Training-cohort replay, not independent holdout; historical training allowed3Actions and evolved memory, so its65/70 is a different protocol.\n")
 subprocess.run(['git','add','--',str(TARGET)],cwd=REPO,check=True);subprocess.run(['git','commit','--only','-m','Archive GPT-6.1 latent experience train70 evaluation','--',str(TARGET)],cwd=REPO,check=True)
 return code
try:sys.exit(main())
except Exception as e:
 status('pipeline_error',error=repr(e));raise
