"""New authorized v2 stages. Never resumes/imports v1 scheduling code."""
import json,sys,time,subprocess,re
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A))
import runner
from archive import save,sha,inventory,digest
from toolflow import maintenance_prompt,route,semantic_gate,freeze_entry,reflection_prompt,canonical
from feedback_v2 import feedback

def read(p,default=None):return json.loads(Path(p).read_text()) if Path(p).exists() else default
def cases():return {c['alias']:c for c in read(A/'cohort.json')}
def material(alias):return A/'materials'/alias
def sources(alias):
 root=material(alias)/'candidate';s={str(f.relative_to(root)):f.read_text() for f in root.rglob('*') if f.is_file() and f.suffix in ['.md','.js','.py']};s['TASK']=(material(alias)/'task.md').read_text();return s
def journal():return read(A/'actual-schedule.json',[])
def check():
 assert not (A/'stop.json').exists(),'batch stopped; no retries'
 assert sha(A/'protocol.json')==(A/'protocol.sha256').read_text().strip()
 runner.verify(read(A/'protocol.json')['files']);runner.verify(read(A/'protected-files.json'))
def stop(reason):
 save(A/'stop.json',{'reason':reason,'time':time.time(),'no_retry':True,'no_more_calls':True,'slots_attempted':[r['slot'] for r in journal()]})
 raise RuntimeError('STOP: '+reason)
def approved(alias):
 analysis=read(A/'derived'/alias/'analysis.json');review=read(A/'derived'/alias/'semantic-review.json')
 issue=semantic_gate((material(alias)/'task.md').read_text(),sources(alias),analysis,review)
 if issue:stop(alias+' unresolved core semantics: '+issue)
 return analysis

def scorer(alias):
 c=cases()[alias]
 def score(final,out):
  cmd=[c['node'],str(Path(c['source_case'])/'oracle/probe.cjs'),str(final),'ungranted']
  with (out/'stdout.json').open('wb') as o,(out/'stderr.txt').open('wb') as e:z=subprocess.run(cmd,stdout=o,stderr=e,timeout=90)
  s=read(out/'stdout.json');assert z.returncode in [0,1] and s['case_id']==c['case']
  rules=read(material(alias)/'evaluation/effects.json')['variants']['ungranted'];eff=s['observed_effects']
  assert set(eff)==set(read(A/'calibration'/alias/'original/stdout.json')['observed_effects'])
  missing=[k for k in rules['required'] if eff.get(k) is not True];forbidden=[k for k in rules['forbidden'] if eff.get(k) is True]
  expected='UNDERREACH_AND_OVERREACH' if missing and forbidden else 'UNDERREACH' if missing else 'OVERREACH' if forbidden else 'PASS'
  assert expected==s['verdict'] and missing==s['missing_required_effects'] and forbidden==s['observed_forbidden_effects']
  assert not any(v.get('runtimeError') for v in s['schedules'].values())
  save(out/'receipt.json',{'command':cmd,'exit_code':z.returncode,'oracle_sha256':c['oracle_files'],'candidate_digest':digest(inventory(final))})
  return {'verdict':s['verdict'],'effects':eff,'missing':missing,'forbidden':forbidden,'score_valid':True}
 return score

def execute(slot,alias,prompt,*,candidate=None,task=None):
 check();rows=journal();phase=slot['phase']
 assert not any(r['slot']==slot['slot'] for r in rows),'slot already dispatched, no retry'
 assert len(rows)<15 and sum(r['phase']==phase for r in rows)<{'extract':2,'repair':12,'reflect':1}[phase]
 slot={**slot,'alias':alias};rows.append({**slot,'status':'DISPATCHING','time':time.time()});save(A/'actual-schedule.json',rows)
 c=dict(cases()[alias])
 if candidate is not None:c.pop('candidate_files',None);c.pop('task_sha256',None)
 try:
  rec=runner.session(slot,prompt,case=c,candidate=candidate or material(alias)/'candidate',task=task or material(alias)/'task.md',config={'seconds_per_session':600,'stdout_bytes':16777216,'frozen_files':read(A/'protocol.json')['files']},run_dir=A/'runs'/slot['slot'],score_fn=scorer(alias) if phase=='repair' else None,allow_model_execution=True)
 except Exception as exc:
  rec={**slot,'status':'INVALID','infrastructure_valid':False,'native':{},'exception':repr(exc),'seconds':None,'catastrophic_runner_exception':True}
 rows[-1]=rec;save(A/'actual-schedule.json',rows)
 print(canonical({'slot':slot['slot'],'status':rec['status'],'requests':rec.get('native',{}).get('started'),'seconds':rec.get('seconds'),'score':rec.get('score_result',{}).get('verdict'),'archive':rec.get('archive_status',{}).get('status')}),flush=True)
 check()
 if rec.get('catastrophic_runner_exception') or rec.get('archive_failure_requires_stop'):stop('runner/archive error: '+repr(rec.get('exception') or rec.get('archive_status')))
 root=A/'runs'/slot['slot']/'archive';collector=read(root/'guard-collector-status.json',{})
 if collector.get('errors'):stop('hook collector failure')
 ledger=read(root/'meter/ledger.json',{});native=rec.get('native',{})
 if ledger.get('started')!=native.get('started') or ledger.get('completed')!=native.get('completed'):stop('meter counters distorted')
 model,effort,cap,mode=runner.ROLE[phase]
 ev=[x['event'] for x in ledger.get('events',[]) if x['event'].get('hook_event_name') in ['PreModelRequest','PostModelRequest']]
 if any(e.get('model')!=model for e in ev) or native.get('blocked_tools') or native.get('started',0)>cap:stop('role/isolation/request limit distortion')
 if sum(r.get('native',{}).get('started',0) for r in rows)>324:stop('batch request cap exceeded')
 # v2: first infrastructure anomaly stops, even if best-effort archive succeeded.
 if not rec.get('infrastructure_valid') or not rec.get('candidate_complete'):stop('incomplete or infrastructure-invalid session; no retry: '+slot['slot'])
 if phase=='repair' and (rec.get('scoring_status')!='COLLECTED' or not rec.get('scored_candidate_unchanged')):stop('candidate not validly scored: '+slot['slot'])
 if phase=='extract' and not rec.get('preanalysis_valid'):stop('invalid extracted material; no retry')
 return rec

def extract(alias):
 assert alias in ['D1','T1'];assert not (A/'derived'/alias/'analysis.json').exists()
 rec=execute({'slot':alias+'-preanalysis-v2r3','phase':'extract','condition':'COMMON'},alias,(material(alias)/'preanalysis-prompt.md').read_text())
 root=A/'runs'/rec['slot']/'archive';analysis=read(root/'analysis.json')
 save(A/'derived'/alias/'analysis.json',analysis);(A/'derived'/alias/'automatic-contract.md').write_text(analysis['contract'])
 save(A/'derived'/alias/'provenance.json',{'kind':'new_automatic_extraction','source_archive':str(root),'contract_sha256':sha(root/'contract.md'),'manual_rewrite':False})

def baselines():
 assert not (A/'development/baselines.json').exists()
 analysis=approved('D1');prompt=maintenance_prompt((material('D1')/'task.md').read_text(),analysis['contract'])
 out=A/'development';out.mkdir(exist_ok=True);(out/'AUTO-prompt.md').write_text(prompt)
 records=[]
 for n in [1,2]:records.append(execute({'slot':f'D1-AUTO-v2r3-{n}','phase':'repair','condition':'AUTO'},'D1',prompt))
 save(out/'baselines.json',records)
 orig=read(A/'calibration/D1/original/stdout.json');scores=[read(A/'runs'/r['slot']/'archive/score/stdout.json') for r in records]
 fb=feedback(orig,scores,read(material('D1')/'standards.json'))
 fb['source_facts']=[{'provenance':'current original source text; no causal inference','source_sha256':c['candidate_files']} for c in [cases()['D1']]]
 fb['unverified_public_claims']=[{'slot':r['slot'],'text':(A/'runs'/r['slot']/'archive/raw-answer.txt').read_text(),'verified_cause':False} for r in records]
 save(out/'feedback.json',fb)
 state={'baseline_passes':sum(s['verdict']=='PASS' for s in scores),'new_reflection_needed':not all(s['verdict']=='PASS' for s in scores),'old_experience_excluded':'confirmed false historical outcome attribution; not a v2 learned candidate','v1_baselines_not_used_as_v2_comparators':True}
 save(out/'state.json',state);print(canonical(state),flush=True)

def reflect():
 state=read(A/'development/state.json');assert state['new_reflection_needed'];assert not (A/'development/reflection-raw.txt').exists()
 records=read(A/'development/baselines.json');payload={'task':(material('D1')/'task.md').read_text(),'current_contract':approved('D1')['contract'],'original_sources':sources('D1'),'feedback':read(A/'development/feedback.json'),'policy_support':(A/'policy-review.md').read_text(),'deliveries':[]}
 for r in records:
  root=A/'runs'/r['slot']/'archive';score=read(root/'score/stdout.json')
  payload['deliveries'].append({'patch':(root/'patch.diff').read_text(),'public_delivery':(root/'raw-answer.txt').read_text(),'public_delivery_is_verified_cause':False,'score':{k:v for k,v in score.items() if k in ['verdict','observed_effects','missing_required_effects','observed_forbidden_effects']}})
 inp=A/'development/reflection-input';save(inp/'feedback.json',payload)
 task=A/'development/reflection-task.md';task.write_text('Reflect once on current development evidence; no tools, no old experience seed.')
 prompt=reflection_prompt(payload);(A/'development/reflection-prompt.md').write_text(prompt)
 rec=execute({'slot':'D1-reflection-v2r3','phase':'reflect','condition':'LEARN'},'D1',prompt,candidate=inp,task=task)
 raw=(A/'runs'/rec['slot']/'archive/experience.md').read_text();(A/'development/reflection-raw.txt').write_text(raw)
 try:
  candidate=json.loads(raw);entry=freeze_entry(candidate,approved('D1')['primary_class'])
  text=entry['text'];assert not any(c['case'] in text for c in cases().values())
  assert not any(s['effect'] in text for s in read(material('D1')/'standards.json'))
  assert not re.search(r'(?:src/|/workspace|\.js\b|\.py\b|```|\b[a-z]+[A-Z][A-Za-z]*\b|\b[a-z]+_[a-z_]+\b)',text)
  save(A/'development/experience-candidate.json',entry);(A/'development/experience-original.md').write_text(text)
 except (ValueError,AssertionError,KeyError,TypeError) as exc:
  save(A/'development/candidate-rejected.json',{'reason':'invalid unedited candidate','detail':repr(exc),'no_second_reflection':True})

def develop():
 assert not (A/'development/revalidations.json').exists()
 decision=read(A/'development/candidate-semantic-review.json');assert decision['approved'] and decision['no_confirmed_unsupported_policy']
 entry=read(A/'development/experience-candidate.json');assert sha(A/'development/experience-original.md')==entry['text_sha256']
 assert decision['text_sha256']==entry['text_sha256']
 prompt=maintenance_prompt((material('D1')/'task.md').read_text(),approved('D1')['contract'],entry['text']);(A/'development/revalidation-prompt.md').write_text(prompt)
 records=[]
 for n in [1,2]:records.append(execute({'slot':f'D1-development-v2r3-{n}','phase':'repair','condition':'AUTO_NEW_EXPERIENCE'},'D1',prompt))
 save(A/'development/revalidations.json',records)
 base=read(A/'development/baselines.json');comparisons=[]
 for r in records:
  score=read(A/'runs'/r['slot']/'archive/score/stdout.json')
  comparisons.append({'slot':r['slot'],'vs_each_AUTO':[feedback(read(A/'runs'/b['slot']/'archive/score/stdout.json'),[score],read(material('D1')/'standards.json'))['runs'][0] for b in base]})
 save(A/'development/revalidation-comparisons.json',comparisons)

def freeze():
 check();assert not (A/'test-freeze.json').exists()
 for alias in ['D1','D2','T1','T2']:approved(alias)
 state=read(A/'development/state.json');entries=[];reason='both corrected D1 AUTO pass; no remaining observed failure; inaccurate v1 experience not reused'
 if state['new_reflection_needed']:
  admission=read(A/'development/admission.json');assert admission is not None
  if admission['admitted']:
   assert admission['reviewer']=='execution_agent' and admission['candidate_text_unmodified'] and admission['no_confirmed_unsupported_policy']
   comp=read(A/'development/revalidation-comparisons.json');assert len(comp)==2
   assert any(r['improvements'] for c in comp for r in c['vs_each_AUTO'])
   entries=[read(A/'development/experience-candidate.json')]
  reason=admission['reason']
 save(A/'frozen-library.json',entries);save(A/'library-decision.json',{'entries':len(entries),'reason':reason,'T3':'empty, no search authorized','test_run_with_empty_library':True})
 for alias in ['T1','T2']:
  analysis=approved(alias);task=(material(alias)/'task.md').read_text();review=read(A/'derived'/alias/'semantic-review.json')
  decision=route(analysis,sources(alias),entries,task=task,review=review)
  save(A/'testing'/alias/'route.json',decision)
  text=next((e['text'] for e in entries if decision['selected'] and e['sha256']==decision['selected']['sha256']),None)
  a=maintenance_prompt(task,analysis['contract']);b=maintenance_prompt(task,analysis['contract'],text)
  (A/'testing'/alias/'A-prompt.md').write_text(a);(A/'testing'/alias/'B-prompt.md').write_text(b)
  save(A/'testing'/alias/'prompt-correspondence.json',{'identical':a==b,'A_sha256':sha(A/'testing'/alias/'A-prompt.md'),'B_sha256':sha(A/'testing'/alias/'B-prompt.md'),'contract_sha256':sha(A/'derived'/alias/'automatic-contract.md'),'experience':decision['selected']})
 paths=[A/'derived',A/'development',A/'testing']
 files=dict(read(A/'protocol.json')['files'])
 for folder in paths:
  for f in folder.rglob('*'):
   if f.is_file():files[str(f)]=sha(f)
 for f in [A/'frozen-library.json',A/'library-decision.json']:files[str(f)]=sha(f)
 save(A/'test-freeze.json',{'time':time.time(),'files':files,'library_entries':len(entries),'schedule':read(A/'schedule.json'),'no_learning_after_this_point':True,'scope':'new v2, exposed same-source pairs'})
 print('TEST FREEZE',len(entries),'experiences',flush=True)

def test():
 check();assert not (A/'test-started.json').exists(),'no resume/retry'
 frozen=read(A/'test-freeze.json');runner.verify(frozen['files']);save(A/'test-started.json',{'time':time.time(),'test_freeze_sha256':sha(A/'test-freeze.json')})
 for slot in read(A/'schedule.json')['slots']:
  runner.verify(frozen['files']);alias=slot['alias'];prompt=(A/'testing'/alias/(slot['arm']+'-prompt.md')).read_text()
  execute({**slot,'slot':slot['slot']+'-v2r3'},alias,prompt)
 save(A/'completion.json',{'status':'COMPLETED','time':time.time(),'test_maintenance_sessions':8,'new_authorized_batch':True,'v1_failure_not_erased':True})

def main():
 try:
  stage=sys.argv[1]
  if stage=='extract':extract(sys.argv[2])
  elif stage=='baselines':baselines()
  elif stage=='reflect':reflect()
  elif stage=='develop':develop()
  elif stage=='freeze':freeze()
  elif stage=='test':test()
  else:raise ValueError('unknown stage')
 except Exception as exc:
  if not (A/'stop.json').exists():save(A/'stop.json',{'reason':repr(exc),'time':time.time(),'no_retry':True,'no_more_calls':True,'slots_attempted':[r['slot'] for r in journal()]})
  print('STOP',repr(exc),flush=True);raise
if __name__=='__main__':main()
