"""Frozen six-slot follow-up only; never extracts, reflects, retries or resumes."""
import sys,json,time,subprocess
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A))
import runner as r
from archive import save,sha,inventory,digest
C=json.loads((A/'cohort.json').read_text());CID=C['case']
def read(p):return json.loads(Path(p).read_text())
def check():
 assert sha(A/'protocol.json')==(A/'protocol.sha256').read_text().strip()
 r.verify(read(A/'protocol.json')['files']);r.verify(read(A/'protected-files.json'))
def stop(reason,rows):
 done={x['slot'] for x in rows};save(A/'stop.json',{'reason':reason,'time':time.time(),'unstarted':[s for s in read(A/'schedule.json')['slots'] if s['slot'] not in done],'no_retry':True});print('STOP: '+reason,flush=True)
def score(final,out):
 cmd=[C['node'],str(Path(C['source_case'])/'oracle/probe.cjs'),str(final),'ungranted']
 with (out/'stdout.json').open('wb') as stdout,(out/'stderr.txt').open('wb') as stderr:
  z=subprocess.run(cmd,stdout=stdout,stderr=stderr,timeout=90)
 s=read(out/'stdout.json');assert z.returncode in [0,1] and s['case_id']==CID
 assert set(s['observed_effects'])==set(C['calibration'][0]['effects'])
 rules=read(A/'materials/evaluation/effects.json')['variants']['ungranted'];missing=[k for k in rules['required'] if not s['observed_effects'].get(k)];forbidden=[k for k in rules['forbidden'] if s['observed_effects'].get(k)]
 assert missing==s['missing_required_effects'] and forbidden==s['observed_forbidden_effects']
 expected='UNDERREACH' if missing else ('OVERREACH' if forbidden else 'PASS');assert expected==s['verdict']
 save(out/'receipt.json',{'command':cmd,'exit_code':z.returncode,'case':CID,'source_oracle_sha256':C['oracle_files'],'candidate_digest':digest(inventory(final))})
 return {'verdict':s['verdict'],'effects':s['observed_effects'],'missing':missing,'forbidden':forbidden,'runtime_errors':{k:v['runtimeError'] for k,v in s['schedules'].items() if v.get('runtimeError')},'score_valid':True}

def critical(rec):
 # A service/CLI outage is infrastructure; evidence of distorted input/isolation/meter is an immediate stop.
 if rec.get('archive_failure_requires_stop'):return 'archive integrity failure; no model archival repair'
 if rec.get('scoring_status')!='COLLECTED' or not rec.get('scored_candidate_unchanged'):return 'scoring handoff/version or final-candidate integrity failure'
 d=A/'runs'/rec['slot']/'archive';ledger=read(d/'meter/ledger.json') if (d/'meter/ledger.json').exists() else {}
 events=[x['event'] for x in ledger.get('events',[])];pre=[e for e in events if e.get('hook_event_name')=='PreModelRequest'];post=[e for e in events if e.get('hook_event_name')=='PostModelRequest'];n=rec.get('native',{})
 allowed=[e for e in pre if not e.get('blocked')]
 # Guard entries use top-level allowed; use native ledger totals as the primary immutable counters.
 if any(e.get('model')!='gpt-5.6-terra' for e in pre+post):return 'model identity distortion'
 if ledger and (ledger.get('started')!=n.get('started',0) or ledger.get('completed')!=n.get('completed',0)):return 'meter counter distortion'
 if n.get('blocked_tools'):return 'isolation/tool-policy failure'
 if n.get('started',0)>24 or rec['seconds']>605:return 'session resource accounting violation'
 if post and len(post)!=n.get('completed',0):return 'meter event/counter distortion'
 if rec.get('infrastructure_valid') and n.get('started',0)-n.get('completed',0) not in [0,1]:return 'unaccounted model requests'
 return None

def main():
 assert len(sys.argv)==1,'No phase/resume arguments supported'
 assert not (A/'actual-schedule.json').exists() and not (A/'runs').exists(),'New batch only; no resume or retry'
 assert read(A/'offline-validation.json')['status']=='PASS'
 check();rows=[];consecutive=0;slots=read(A/'schedule.json')['slots'];assert len(slots)==6
 for s in slots:
  try:check()
  except Exception as e:stop('frozen input/configuration drift: '+repr(e),rows);return
  assert s['phase']=='repair' and s['condition'] in ['AUTO','AUTO_EXP']
  save(A/'launch-state.json',{'next_slot':s,'prior_started':len(rows),'time':time.time()})
  prompt=(A/'prompts'/f"{s['condition']}.md").read_text()
  try:
   rec=r.session(s,prompt,case=C,candidate=A/'materials/candidate',task=A/'materials/task.md',config={'seconds_per_session':600,'stdout_bytes':16777216,'frozen_files':read(A/'protocol.json')['files']},run_dir=A/'runs'/s['slot'],score_fn=score,allow_model_execution=True)
  except Exception as e:
   # Preserve every attempted slot; never retry a possibly launched session.
   rec={**s,'status':'INVALID','infrastructure_valid':False,'exception':repr(e),'seconds':None,'native':{},'catastrophic_runner_exception':True}
   rows.append(rec);save(A/'actual-schedule.json',rows);stop('session evidence incomplete after runner exception: '+repr(e),rows);return
  rows.append(rec);save(A/'actual-schedule.json',rows)
  print(json.dumps({'slot':s['slot'],'completed_slots':len(rows),'status':rec['status'],'requests':rec['native'].get('started',0),'seconds':round(rec['seconds'],2),'archive':rec['archive_status']['status']},ensure_ascii=False),flush=True)
  try:check()
  except Exception as e:stop('frozen input/configuration drift: '+repr(e),rows);return
  issue=critical(rec)
  if issue:stop(issue,rows);return
  if sum(x['native'].get('started',0) for x in rows)>144 or sum(x['seconds'] for x in rows)>3600:stop('cumulative budget violation',rows);return
  consecutive=0 if rec['infrastructure_valid'] else consecutive+1
  if consecutive>=2:stop('two consecutive infrastructure anomalies',rows);return
 save(A/'completion.json',{'six_slots_ended':True,'time':time.time(),'no_more_calls':True,'extraction_calls':0,'reflection_calls':0,'gepa_calls':0,'retries':0,'all_results_await_unified_analysis':True})
if __name__=='__main__':main()
