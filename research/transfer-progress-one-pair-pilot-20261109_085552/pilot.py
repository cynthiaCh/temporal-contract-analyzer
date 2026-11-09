"""Bounded new one-pair experiment with explicit stages and no hidden retries."""
import json,sys,time,subprocess,tempfile,shutil,unittest
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A))
import runner
from archive import save,sha,inventory,digest
from toolflow import (canonical,public_material,maintenance_prompt,validate_analysis,
                     semantic_gate,route,freeze_entry,PREDICATES)
from feedback import feedback
from handoff import (make_schema,assemble_payload,verify_ledger,rebuild_feedback,
                     validate_candidate,render,numbered_rules,object_digest,
                     semantic_gate as candidate_gate)

def read(p,default=None):return json.loads(Path(p).read_text()) if Path(p).exists() else default
def cases():return {c['alias']:c for c in read(A/'cases.json')}
def sources(alias):
 root=A/'materials'/alias/'candidate'
 out={str(p.relative_to(root)):p.read_text() for p in root.rglob('*') if p.is_file() and p.suffix in ['.md','.js','.py']}
 out['TASK']=(A/'materials'/alias/'task.md').read_text();return out
def journal():return read(A/'actual-schedule.json',[])
def stop(reason,kind):
 save(A/'stop.json',{'time':time.time(),'reason':reason,'kind':kind,'no_retry':True,'no_more_model_calls':True})
 raise RuntimeError(reason)
def check():
 assert not (A/'stop.json').exists(),'Stopped, no retry'
 runner.verify(read(A/'initial-freeze.json')['files'])
 for f in ['reflection-freeze.json','library-freeze.json','test-freeze.json']:
  if (A/f).exists():runner.verify(read(A/f)['files'])
def approved(alias):
 analysis=read(A/'derived'/alias/'analysis.json');review=read(A/'derived'/alias/'semantic-review.json')
 assert analysis is not None and review is not None,'Source-bound AI review required'
 issue=semantic_gate((A/'materials'/alias/'task.md').read_text(),sources(alias),analysis,review)
 if issue:stop('Core analysis conflict: '+str(issue),'semantic')
 return analysis

def scorer(alias):
 def score(final,out):
  c=cases()[alias];cmd=[c['node'],str(Path(c['source_case'])/'oracle/probe.cjs'),str(final),'ungranted']
  with (out/'stdout.json').open('wb') as o,(out/'stderr.txt').open('wb') as e:z=subprocess.run(cmd,stdout=o,stderr=e,timeout=120)
  s=read(out/'stdout.json');rules=read(A/'materials'/alias/'evaluation/effects.json')['variants']['ungranted'];eff=s['observed_effects']
  assert z.returncode in [0,1] and s['case_id']==c['case']
  assert set(eff)==set(read(A/'calibration'/alias/'original/stdout.json')['observed_effects'])
  missing=[k for k in rules['required'] if eff.get(k) is not True];forbidden=[k for k in rules['forbidden'] if eff.get(k) is True]
  expected='UNDERREACH_AND_OVERREACH' if missing and forbidden else 'UNDERREACH' if missing else 'OVERREACH' if forbidden else 'PASS'
  assert expected==s['verdict'] and missing==s['missing_required_effects'] and forbidden==s['observed_forbidden_effects']
  assert not any(v.get('runtimeError') for v in s['schedules'].values())
  save(out/'receipt.json',{'command':cmd,'exit_code':z.returncode,'oracle_files':c['oracle_files'],'candidate_digest':digest(inventory(final)),'single_scoring_invocation':True})
  return {'verdict':expected,'effects':eff,'missing':missing,'forbidden':forbidden,'score_valid':True}
 return score

def execute(name,phase,alias,prompt,condition,*,candidate=None,task=None):
 check();rows=journal();assert len(rows)<11 and not any(r['name']==name for r in rows)
 assert sum(r['phase']==phase for r in rows)<{'extract':2,'reflect':1,'repair':8}[phase]
 slot={'slot':f'session-{len(rows)+1:02d}','name':name,'phase':phase,'alias':alias,'condition':condition}
 save(A/'actual-schedule.json',rows+[{**slot,'status':'DISPATCHING','dispatched_at':time.time()}])
 c=dict(cases()[alias])
 if phase=='reflect':c.pop('candidate_files');c.pop('task_sha256')
 try:
  rec=runner.session(slot,prompt,case=c,candidate=candidate or A/'materials'/alias/'candidate',task=task or A/'materials'/alias/'task.md',
    config={'seconds_per_session':600,'stdout_bytes':16777216,'frozen_files':read(A/'initial-freeze.json')['files']},
    run_dir=A/'runs'/slot['slot'],score_fn=scorer(alias) if phase=='repair' else None,allow_model_execution=True)
 except Exception as exc:rec={**slot,'status':'INVALID','catastrophic_runner_exception':repr(exc)}
 save(A/'actual-schedule.json',rows+[rec])
 print(json.dumps({'name':name,'slot':slot['slot'],'status':rec.get('status'),'requests':rec.get('native',{}).get('started'),
  'seconds':rec.get('seconds'),'score':rec.get('score_result',{}).get('verdict'),'missing':rec.get('score_result',{}).get('missing')},ensure_ascii=False),flush=True)
 if rec.get('catastrophic_runner_exception'):stop(rec['catastrophic_runner_exception'],'runner')
 root=A/'runs'/rec['slot']/'archive';meter=read(root/'meter/ledger.json',{});native=rec.get('native',{})
 if rec.get('archive_failure_requires_stop'):stop('Archival error (service outcome retained separately)','archive')
 if read(root/'guard-collector-status.json',{}).get('errors'):stop('Collector error','meter')
 if meter.get('started')!=native.get('started') or meter.get('completed')!=native.get('completed'):stop('Meter counter drift','meter')
 if sum(r.get('native',{}).get('started',0) for r in journal())>228:stop('Batch request cap exceeded','meter')
 if not rec.get('infrastructure_valid') or not rec.get('candidate_complete'):stop('Infrastructure/incomplete output: '+name,'infrastructure_or_output')
 if phase=='extract' and not rec.get('preanalysis_valid'):stop('Invalid preanalysis: '+name,'analysis')
 if phase=='repair' and (rec.get('scoring_status')!='COLLECTED' or not rec.get('scored_candidate_unchanged')):stop('Candidate not validly scored','score')
 check();return rec

def extract(alias):
 assert not (A/'derived'/alias/'analysis.json').exists()
 if alias=='T':assert (A/'library-freeze.json').exists()
 r=execute(alias+'-analysis','extract',alias,(A/'materials'/alias/'preanalysis-prompt.md').read_text(),'COMMON')
 root=A/'runs'/r['slot']/'archive';analysis=read(root/'analysis.json')
 save(A/'derived'/alias/'analysis.json',analysis);(A/'derived'/alias/'automatic-contract.md').write_text(analysis['contract'])
 save(A/'derived'/alias/'provenance.json',{'source':str(root/'raw-answer.txt'),'raw_sha256':sha(root/'raw-answer.txt'),'unmodified_automatic_output':True})

def baselines():
 assert not (A/'development/baselines.json').exists();analysis=approved('D')
 prompt=maintenance_prompt((A/'materials/D/task.md').read_text(),analysis['contract'])
 (A/'development').mkdir(exist_ok=True);(A/'development/AUTO-prompt.md').write_text(prompt)
 records=[execute('AUTO-'+str(n),'repair','D',prompt,'AUTO') for n in (1,2)]
 save(A/'development/baselines.json',records)
 if all(r['score_result']['verdict']=='PASS' for r in records):
  save(A/'development/no-experience.json',{'reason':'Both AUTO pass; no observed failure to learn; no harder case or old experience substituted.'})
  stop('Both training AUTO pass; no new experience generated','training_all_pass')

def build_reflection():
 approved('D');assert not (A/'reflection-freeze.json').exists()
 from training_ledger import build,REFLECTION_INSTRUCTIONS
 build()
 ledger=read(A/'training/evidence-ledger.json');fb=read(A/'training/feedback.json')
 verify_ledger(A/'training',ledger);payload=assemble_payload(A/'training',ledger,fb)
 payload['mechanism_predicates']=PREDICATES
 payload['output_protocol']={'mandatory_counterevidence':ledger['mandatory_counterevidence'],'preservation_constraints':[r['id'] for r in ledger['constraints']]}
 save(A/'training/reflection-input.json',payload)
 save(A/'reflection.schema.json',make_schema(ledger,PREDICATES))
 prompt=REFLECTION_INSTRUCTIONS+'\n'+json.dumps(payload,ensure_ascii=False)
 (A/'training/reflection-prompt.md').write_text(prompt);(A/'training/reflection-task.md').write_text('Learn one new bounded experience from this batch training only, no tools or prior experience seed.\n')
 (A/'training/model-workspace').mkdir();save(A/'training/model-workspace/payload.json',payload)
 files={str(p):sha(p) for p in (A/'training').rglob('*') if p.is_file()};files[str(A/'reflection.schema.json')]=sha(A/'reflection.schema.json')
 save(A/'reflection-freeze.json',{'time':time.time(),'files':files,'single_candidate_only':True})

def reflect():
 assert not (A/'development/experience-object.json').exists();check()
 r=execute('reflection','reflect','D',(A/'training/reflection-prompt.md').read_text(),'LEARN',candidate=A/'training/model-workspace',task=A/'training/reflection-task.md')
 root=A/'runs'/r['slot']/'archive';raw=(root/'raw-answer.txt').read_bytes();(A/'development/reflection-raw.txt').write_bytes(raw)
 candidate=json.loads(raw);save(A/'development/experience-object.json',candidate)
 try:
  result=validate_candidate(candidate,read(A/'training/evidence-ledger.json'),PREDICATES)
  text=render(candidate);(A/'development/experience.md').write_text(text)
  if any(c['case'] in text for c in cases().values()) or any(s['effect'] in text for s in read(A/'materials/D/standards.json')) or '```' in text or 'src/' in text:raise ValueError('Prohibited case/grading/path/patch in experience body')
  save(A/'development/rule-evidence.json',{'rules':numbered_rules(candidate),'applicability':candidate['applicability'],'unresolved':candidate['unresolved']})
  save(A/'development/structural-review.json',result)
  save(A/'development/derivation.json',{'origin':'program-derived numbering and exact model body concatenation','raw_object_sha256':object_digest(candidate),'text_sha256':sha(A/'development/experience.md'),'no_business_rewriting':True})
 except Exception as exc:
  save(A/'development/rejection.json',{'reason':repr(exc),'raw_candidate_unmodified':True});stop('Invalid experience: '+repr(exc),'candidate')

def develop():
 assert not (A/'development/experience-freeze.json').exists();check()
 candidate=read(A/'development/experience-object.json');review=read(A/'development/semantic-review.json')
 decision=candidate_gate(candidate,read(A/'training/evidence-ledger.json'),PREDICATES,review)
 save(A/'development/content-review.json',decision)
 if not decision['development_eligible']:stop('Unsupported candidate in AI-assisted review','candidate')
 text=render(candidate);assert sha(A/'development/experience.md')==runner.backend.sha(text)
 prompt=(A/'development/AUTO-prompt.md').read_text()+'\n\n以下为冻结经验，按当前证据核查适用性：\n'+text
 (A/'development/revalidation-prompt.md').write_text(prompt)
 files={str(A/'development'/n):sha(A/'development'/n) for n in ['experience-object.json','experience.md','semantic-review.json','rule-evidence.json','derivation.json','revalidation-prompt.md']}
 save(A/'development/experience-freeze.json',{'files':files,'time':time.time()})
 records=[]
 for n in (1,2):
  runner.verify(files);records.append(execute('development-'+str(n),'repair','D',prompt,'AUTO_NEW_EXPERIENCE'))
 save(A/'development/revalidations.json',records)
 standards=read(A/'materials/D/standards.json');base=read(A/'development/baselines.json');comparison=[]
 for r in records:
  score=read(A/'runs'/r['slot']/'archive/score/stdout.json')
  comparison.append({'slot':r['slot'],'vs_each_AUTO':[feedback(read(A/'runs'/b['slot']/'archive/score/stdout.json'),[score],standards)['runs'][0] for b in base]})
 save(A/'development/comparisons.json',comparison)
 qualifies=any(row['improvements'] for c in comparison for row in c['vs_each_AUTO'])
 save(A/'development/admission.json',{'eligible':qualifies,'AI_assisted':True,'no_confirmed_unsupported_policy':True,
  'regressions_fully_recorded':True,'both_full_passes_required':False,'production_admitted':False})
 if not qualifies:stop('No evidenced target/overall improvement in two fixed development trials','no_development_improvement')

def freeze_library():
 check();assert not (A/'library-freeze.json').exists();assert read(A/'development/admission.json')['eligible']
 candidate=read(A/'development/experience-object.json');text=(A/'development/experience.md').read_text()
 entry=freeze_entry({'text':text,'requires':candidate['requires'],'excludes':candidate['excludes']},approved('D')['primary_class'])
 entry['version']='new-transfer-pair-v1';entry['sha256']=runner.backend.sha(canonical({k:v for k,v in entry.items() if k!='sha256'}))
 save(A/'frozen-library.json',[entry])
 files={str(p):sha(p) for p in (A/'development').rglob('*') if p.is_file()};files[str(A/'frozen-library.json')]=sha(A/'frozen-library.json')
 save(A/'library-freeze.json',{'time':time.time(),'files':files,'entries':1,'no_learning_after_this_point':True})

def test():
 check();assert not (A/'test-freeze.json').exists();analysis=approved('T');task=(A/'materials/T/task.md').read_text()
 decision=route(analysis,sources('T'),read(A/'frozen-library.json'),task=task,review=read(A/'derived/T/semantic-review.json'))
 save(A/'testing/route.json',decision)
 selected=read(A/'frozen-library.json')[0]['text'] if decision['selected'] else None
 aa=maintenance_prompt(task,analysis['contract']);bb=maintenance_prompt(task,analysis['contract'],selected)
 (A/'testing/A.md').write_text(aa);(A/'testing/B.md').write_text(bb)
 save(A/'testing/prompt-comparison.json',{'A_sha256':runner.backend.sha(aa),'B_sha256':runner.backend.sha(bb),'identical':aa==bb,'selected':decision['selected']})
 files={str(p):sha(p) for p in (A/'testing').rglob('*') if p.is_file()}
 files.update({str(p):sha(p) for p in (A/'derived/T').rglob('*') if p.is_file()})
 save(A/'test-freeze.json',{'time':time.time(),'files':files,'order':['B1','A1','A2','B2'],'controls_sampling':False})
 for arm,repeat in [('B',1),('A',1),('A',2),('B',2)]:
  execute('test-'+arm+str(repeat),'repair','T',(A/'testing'/(arm+'.md')).read_text(),'AUTO' if arm=='A' else 'ROUTED')
 save(A/'completion.json',{'time':time.time(),'test_slots':4,'no_next_batch':True})

def preflight():
 assert not (A/'initial-freeze.json').exists()
 import test_toolflow,test_runtime_v2
 suite=unittest.TestLoader().loadTestsFromModule(test_toolflow)
 for n in unittest.TestLoader().getTestCaseNames(test_runtime_v2.RuntimeV2):
  if n!='test_real_v1_failure_replay':suite.addTest(test_runtime_v2.RuntimeV2(n))
 with (A/'offline-tests.log').open('w') as log:r=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
 assert r.wasSuccessful()
 for alias,c in cases().items():
  with tempfile.TemporaryDirectory(prefix='pair-offline-') as td:
   runtime=Path(td);folder=runtime/'fixture';folder.mkdir();(folder/'archive').mkdir();shutil.copytree(A/'materials'/alias/'candidate',folder/'workspace')
   socket=runtime/'control';socket.mkdir()
   cmd=runner.command('offline',folder,'repair',c,runtime=runtime,socket_dir=socket,copy_auth=False);prefix=cmd[:cmd.index('/opt/codex')]
   target='src/workspace.js' if alias=='D' else 'src/workflow.py'
   z=subprocess.run(prefix+['/bin/sh','-c','set -eu\ncat /workspace/'+target+'\ntest ! -e /home/sribd\n/runtime/node --version'],capture_output=True,timeout=30)
   assert z.returncode==0 and (A/'materials'/alias/'candidate'/target).read_bytes() in z.stdout
 protected={str(p):sha(p) for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 for c in cases().values():
  for folder in ['base','oracle']:
   for p in (Path(c['source_case'])/folder).rglob('*'):
    if p.is_file():protected[str(p)]=sha(p)
 protected[str(Path.home()/'.codex/config.toml')]=sha(Path.home()/'.codex/config.toml')
 save(A/'initial-freeze.json',{'time':time.time(),'files':protected,'offline_tests':r.testsRun,'model_calls':0})
 print('OFFLINE PASS',r.testsRun,'checks, source isolation and pinned scoring calibrated',flush=True)

if __name__=='__main__':
 try:
  stage=sys.argv[1]
  if stage=='extract':extract(sys.argv[2])
  else:{'preflight':preflight,'baselines':baselines,'build-reflection':build_reflection,'reflect':reflect,'develop':develop,'freeze-library':freeze_library,'test':test}[stage]()
 except Exception as exc:
  if not (A/'stop.json').exists():save(A/'stop.json',{'time':time.time(),'reason':repr(exc),'kind':'stage_exception','no_more_model_calls':True,'no_retry':True})
  print('STOP',repr(exc),flush=True);raise
