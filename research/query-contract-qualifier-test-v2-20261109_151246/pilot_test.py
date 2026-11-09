"""Fixed one-case test: extract once, freeze routing, B1/A1/A2/B2, no learning."""
import json,shutil,subprocess,sys,tempfile,time,unittest
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A))
import runner
from archive import save,sha,inventory,digest
from citations import verify_catalog,fingerprint
from toolflow import (PREDICATES,canonical,freeze_entry,route,maintenance_prompt,
                      semantic_gate,validate_analysis)
P=A.parent/'query-headroom-reuse-pilot-20261109_141850'
D=P
ORDER=['T-analysis','B1','A1','A2','B2']
def read(p,default=None):return json.loads(Path(p).read_text()) if Path(p).exists() else default
def sources():
 root=A/'materials/T/candidate'
 out={str(f.relative_to(root)):f.read_text() for f in root.rglob('*') if f.is_file() and f.suffix in ['.md','.py']}
 out['TASK']=(A/'materials/T/task.md').read_text();return out
def frozen_input_files(root):
 return {str(p):sha(p) for p in Path(root).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['initial-freeze.json','actual-schedule.json','stop.json'] and p.suffix!='.log'}
def stop(kind,reason):
 save(A/'stop.json',{'kind':kind,'reason':reason,'time':time.time(),'no_retry':True,'no_more_model_calls':True});raise RuntimeError(reason)
def check():
 assert not (A/'stop.json').exists(),'Batch stopped'
 runner.verify(read(A/'initial-freeze.json')['files'])
 if (A/'test-freeze.json').exists():runner.verify(read(A/'test-freeze.json')['files'])

def prepare():
 assert not (A/'initial-freeze.json').exists()
 runner.verify(read(A/'initial-state.json')['predecessor_files'])
 c=read(A/'case.json');case=Path(c['source_case'])
 assert runner.backend.hashes(A/'materials/T/candidate')==c['candidate_files']==runner.backend.hashes(case/'base')
 assert sha(A/'materials/T/task.md')==c['task_sha256']
 assert read(A/'materials/T/manifest.json')==read(case/'case.json')
 for name,h in c['oracle_files'].items():assert sha(case/'oracle'/name)==h
 verify_catalog(read(A/'materials/T/source-catalog.json'),sources())
 assert fingerprint(read(A/'materials/T/source-catalog.json'))==c['source_catalog_sha256']
 prompt=(A/'materials/T/preanalysis-prompt.md').read_text()
 assert c['case'] not in prompt and c['independent_unit_id'] not in prompt and c['source_case'] not in prompt
 # Verify existing calibration input versions only; never execute historical
 # candidates, load reference bodies into actors, or alter the original scorer.
 calibrations=[]
 for folder in sorted((A/'calibration/T').iterdir()):
  rec=read(folder/'receipt.json');score=read(folder/'stdout.json')
  assert rec['oracle_files']==c['oracle_files'] and rec['score_valid'] and rec['verdict']==score['verdict']
  assert runner.backend.hashes(Path(rec['command'][2]))==rec['candidate_before']
  assert not any(x.get('runtimeError') for x in score['schedules'].values())
  if folder.name in ['reference-bounded','reference-alternative']:assert score['verdict']=='PASS'
  elif folder.name=='reference-expanded':assert score['verdict']=='OVERREACH'
  else:assert score['verdict']!='PASS'
  calibrations.append({'variant':folder.name,'verdict':score['verdict'],'receipt_sha256':sha(folder/'receipt.json'),'same_inputs_and_scorer':True,'rerun':False})
 save(A/'calibration-reuse.json',calibrations)
 obj=read(A/'experience/experience-object.json');text=(A/'experience/experience.md').read_text()
 assert read(D/'development-admission.json')['eligible_for_later_frozen_research']
 assert read(A/'experience/semantic-review.json')['no_confirmed_unsupported_policy']
 assert sha(A/'experience/experience.md')==sha(D/'development/experience.md')
 entry=freeze_entry({'text':text,'requires':obj['requires'],'excludes':obj['excludes']},read(P/'derived/D/analysis.json')['primary_class'])
 entry['version']='locked-parent-rules-crosslang-test-1'
 entry['sha256']=runner.backend.sha(canonical({k:v for k,v in entry.items() if k!='sha256'}))
 save(A/'frozen-library.json',[entry])
 save(A/'experience/provenance.json',{'source':str(D/'development/experience-object.json'),'object_sha256':sha(D/'development/experience-object.json'),
  'text_sha256':sha(A/'experience/experience.md'),'exact_body_reused':True,'registry_conversion':'Only deterministic field projection plus version/hash; no prose/premise edits',
  'primary_class_source':str(P/'derived/D/analysis.json'),'source_metadata_not_routing_input':True,'production_admitted':False})
 protocol={'case':c['case'],'exposure':c['exposure'],'scope':'One previously exposed same-source Python case, no independent generalization claim',
  'models':{'extract':['gpt-6-sol','low',12,600],'repair':['gpt-5.6-terra','low',24,600]},
  'maximum_sessions':5,'maximum_requests':108,'concurrency':1,'schedule':ORDER,'sampling_randomness_controlled':False,
  'conditions':{'A':'Original task/candidate + fixed automatic Contract + public execution requirements','B':'A plus 0 or 1 exact frozen routed experience'},
  'fallback':'Record identical prompts and run all fixed slots; no equivalence claim',
  'normal_failure':'Continue fixed next slot; no replacement or extra search',
  'stop':'First infrastructure/archive/isolation/input/meter anomaly; no retry or replacement; invalid candidate not counted as behavioral failure',
  'no_reflection_or_extra_judge':True,'no_learning_from_test':True,'production_update':False,'create_commit':False}
 save(A/'protocol.json',protocol);save(A/'actual-schedule.json',[])
 import test_toolflow,test_runtime_v2,test_citations,test_source_proof
 suite=unittest.TestSuite()
 for m in [test_toolflow,test_runtime_v2,test_citations,test_source_proof]:suite.addTests(unittest.TestLoader().loadTestsFromModule(m))
 with (A/'offline-tests.log').open('w') as f:r=unittest.TextTestRunner(stream=f,verbosity=2).run(suite)
 assert r.wasSuccessful()
 with tempfile.TemporaryDirectory(prefix='transfer-python-offline-') as td:
  rt=Path(td);folder=rt/'fixture';folder.mkdir();(folder/'archive').mkdir();shutil.copytree(A/'materials/T/candidate',folder/'workspace');sock=rt/'control';sock.mkdir()
  for phase in ['extract','repair']:
   cmd=runner.command('offline-'+phase,folder,phase,c,runtime=rt,socket_dir=sock,copy_auth=False)
   assert cmd[cmd.index('-m')+1]==('gpt-6-sol' if phase=='extract' else 'gpt-5.6-terra')
   assert cmd[cmd.index(str(folder/'workspace'))-1]==('--ro-bind' if phase=='extract' else '--bind')
   test="set -eu\ncat /workspace/src/workflow.py\ntest ! -e /home/sribd\n/usr/bin/python3 -B -c 'import ast,pathlib; ast.parse(pathlib.Path(\"/workspace/src/workflow.py\").read_text())'\n/runtime/node --version"
   z=subprocess.run(cmd[:cmd.index('/opt/codex')]+['/bin/sh','-c',test],capture_output=True,timeout=30)
   assert z.returncode==0 and (A/'materials/T/candidate/src/workflow.py').read_bytes() in z.stdout
 files=frozen_input_files(A);files.update(read(A/'initial-state.json')['predecessor_files'])
 for folder in ['base','oracle']:
  files.update({str(f):sha(f) for f in (case/folder).rglob('*') if f.is_file()})
 files[str(Path.home()/'.codex/config.toml')]=sha(Path.home()/'.codex/config.toml')
 save(A/'initial-freeze.json',{'time':time.time(),'files':files,'offline_checks':r.testsRun,'new_calibration_calls':0,'extra_model_calls':0})
 runner.verify(files);print('OFFLINE PASS',r.testsRun,'calibrations reused',len(calibrations),flush=True)

def scorer(final,out):
 c=read(A/'case.json');cmd=[c['node'],str(Path(c['source_case'])/'oracle/probe.cjs'),str(final),'ungranted']
 with (out/'stdout.json').open('wb') as o,(out/'stderr.txt').open('wb') as e:z=subprocess.run(cmd,stdout=o,stderr=e,timeout=120)
 s=read(out/'stdout.json');rules=read(A/'materials/T/evaluation/effects.json')['variants']['ungranted'];eff=s['observed_effects']
 assert z.returncode in [0,1] and s['case_id']==c['case']
 assert set(eff)==set(read(A/'calibration/T/original/stdout.json')['observed_effects'])
 missing=[k for k in rules['required'] if eff.get(k) is not True];forbidden=[k for k in rules['forbidden'] if eff.get(k) is True]
 expected='UNDERREACH_AND_OVERREACH' if missing and forbidden else 'UNDERREACH' if missing else 'OVERREACH' if forbidden else 'PASS'
 assert expected==s['verdict'] and missing==s['missing_required_effects'] and forbidden==s['observed_forbidden_effects']
 assert not any(v.get('runtimeError') for v in s['schedules'].values())
 save(out/'receipt.json',{'command':cmd,'exit_code':z.returncode,'oracle_files':c['oracle_files'],'candidate_digest':digest(inventory(final)),'single_scoring_invocation':True})
 return {'verdict':expected,'effects':eff,'missing':missing,'forbidden':forbidden,'score_valid':True}

def execute(name,phase,prompt):
 check();rows=read(A/'actual-schedule.json');assert len(rows)<5 and name==ORDER[len(rows)]
 assert (phase=='extract')==(name=='T-analysis')
 slot={'slot':f'session-{len(rows)+1:02d}','name':name,'phase':phase,'condition':'COMMON' if phase=='extract' else ('AUTO' if name.startswith('A') else 'ROUTED')}
 save(A/'actual-schedule.json',rows+[{**slot,'status':'DISPATCHING','dispatched_at':time.time()}])
 try:
  rec=runner.session(slot,prompt,case=read(A/'case.json'),candidate=A/'materials/T/candidate',task=A/'materials/T/task.md',
   config={'seconds_per_session':600,'stdout_bytes':16777216,'frozen_files':read(A/'initial-freeze.json')['files']},
   run_dir=A/'runs'/slot['slot'],score_fn=scorer if phase=='repair' else None,allow_model_execution=True)
 except Exception as exc:
  save(A/'dispatch-error.json',{'slot':slot,'error':repr(exc)});stop('runner',repr(exc))
 save(A/'actual-schedule.json',rows+[rec]);print(json.dumps({'name':name,'status':rec['status'],'requests':rec.get('native',{}).get('started'),'score':rec.get('score_result'),'seconds':rec.get('seconds')},ensure_ascii=False),flush=True)
 arc=A/'runs'/slot['slot']/'archive';meter=read(arc/'meter/ledger.json',{});native=rec.get('native',{})
 if rec.get('archive_failure_requires_stop'):stop('archive','Archive failed, original outcome retained')
 if read(arc/'guard-collector-status.json',{}).get('errors'):stop('meter','Collector errors')
 if meter.get('started')!=native.get('started') or meter.get('completed')!=native.get('completed'):stop('meter','Request accounting drift')
 if sum(r.get('native',{}).get('started',0) for r in read(A/'actual-schedule.json'))>108:stop('meter','Batch request cap exceeded')
 if not rec.get('infrastructure_valid') or not rec.get('candidate_complete'):stop('infrastructure_or_output','Invalid/incomplete '+name)
 if phase=='extract' and not rec.get('preanalysis_valid'):stop('analysis',rec.get('preanalysis_error'))
 if phase=='repair' and (rec.get('scoring_status')!='COLLECTED' or not rec.get('scored_candidate_unchanged')):stop('score','No valid unchanged score')
 check();return rec

def extract():
 assert not (A/'derived/T/analysis.json').exists()
 rec=execute('T-analysis','extract',(A/'materials/T/preanalysis-prompt.md').read_text());arc=A/'runs'/rec['slot']/'archive'
 analysis=read(arc/'analysis.json');save(A/'derived/T/analysis.json',analysis)
 (A/'derived/T/automatic-contract.md').write_text(analysis['contract'])
 save(A/'derived/T/provenance.json',{'raw_response':str(arc/'raw-answer.txt'),'normalization':'Source span IDs to exact references only; Contract/class/fact states not edited','derivation':str(arc/'analysis-derivation.json')})

def freeze():
 check();assert len(read(A/'actual-schedule.json'))==1 and not (A/'test-freeze.json').exists()
 analysis=read(A/'derived/T/analysis.json');review=read(A/'derived/T/semantic-review.json');task=(A/'materials/T/task.md').read_text()
 issue=semantic_gate(task,sources(),analysis,review)
 if issue:stop('semantic','Core automatic material not admitted: '+str(issue))
 decision=route(analysis,sources(),read(A/'frozen-library.json'),task=task,review=review);save(A/'testing/route.json',decision)
 selected=decision.get('selected') or {}
 entry=next((e for e in read(A/'frozen-library.json') if e['sha256']==selected.get('sha256')),None)
 # The established router returns a version/hash descriptor, never case IDs.
 if decision.get('selected') and entry is None:raise ValueError('Selected experience not in frozen registry')
 aa=maintenance_prompt(task,analysis['contract']);bb=maintenance_prompt(task,analysis['contract'],entry['text'] if entry else None)
 (A/'testing/A.md').write_text(aa);(A/'testing/B.md').write_text(bb)
 save(A/'testing/prompt-difference.json',{'A_sha256':runner.backend.sha(aa),'B_sha256':runner.backend.sha(bb),'identical':aa==bb,'selected':decision.get('selected'),
  'only_intentional_difference':'0 or 1 exact frozen experience appended','fallback_comparison_not_experience_equivalence':aa==bb})
 files={str(f):sha(f) for folder in [A/'testing',A/'derived',A/'experience'] for f in folder.rglob('*') if f.is_file()}
 files[str(A/'frozen-library.json')]=sha(A/'frozen-library.json')
 save(A/'test-freeze.json',{'time':time.time(),'files':files,'schedule':['B1','A1','A2','B2'],'no_learning_or_changes_after_this_point':True})
 print('TEST FROZEN',json.dumps(decision,ensure_ascii=False),flush=True)

def run(name):
 assert name in ORDER[1:] and (A/'test-freeze.json').exists()
 execute(name,'repair',(A/'testing'/(name[0]+'.md')).read_text())

if __name__=='__main__':
 try:
  stage=sys.argv[1]
  if stage=='run':run(sys.argv[2])
  else:{'prepare':prepare,'extract':extract,'freeze':freeze}[stage]()
 except Exception as exc:
  if not (A/'stop.json').exists():save(A/'stop.json',{'kind':'stage_exception','reason':repr(exc),'time':time.time(),'no_retry':True,'no_more_model_calls':True})
  print('STOP',repr(exc),flush=True);sys.exit(1)
