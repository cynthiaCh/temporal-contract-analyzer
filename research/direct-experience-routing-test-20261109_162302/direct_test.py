"""Explicit two-slot direct routing test; no scheduler, retry or learning."""
import ast,json,shutil,subprocess,sys,tempfile,time,unittest
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A))
import runner
from archive import save,sha,inventory,digest
from citations import catalog,schema,fingerprint,INSTRUCTIONS
from qualifiers import cues,GUIDANCE
from toolflow import PREDICATES,canonical,route,maintenance_prompt,semantic_gate
ORDER=['T-analysis','T-maintenance']
def read(p,default=None):return json.loads(Path(p).read_text()) if Path(p).exists() else default
def sources():
 root=A/'materials/T/candidate'
 out={str(f.relative_to(root)):f.read_text() for f in root.rglob('*') if f.is_file() and f.suffix in ['.md','.py']}
 out['TASK']=(A/'materials/T/task.md').read_text();return out

def stop(kind,reason):
 save(A/'stop.json',{'kind':kind,'reason':reason,'time':time.time(),'no_retry':True,'no_more_model_calls':True});raise RuntimeError(reason)
def check():
 assert not (A/'stop.json').exists(),'Batch already stopped'
 runner.verify(read(A/'initial-freeze.json')['files'])
 if (A/'maintenance-freeze.json').exists():runner.verify(read(A/'maintenance-freeze.json')['files'])

def invoke_score(final,out,*,calibration=False):
 c=read(A/'case.json');out.mkdir(parents=True,exist_ok=True);before=inventory(final)
 cmd=[c['node'],str(Path(c['source_case'])/'oracle/probe.cjs'),str(final),'ungranted']
 with (out/'stdout.json').open('wb') as o,(out/'stderr.txt').open('wb') as e:
  z=subprocess.run(cmd,stdout=o,stderr=e,timeout=120)
 s=read(out/'stdout.json');rules=read(A/'materials/T/evaluation/effects.json')['variants']['ungranted'];eff=s['observed_effects']
 expected_keys=set(rules['required']+rules['forbidden'])
 missing=[k for k in rules['required'] if eff.get(k) is not True];forbidden=[k for k in rules['forbidden'] if eff.get(k) is True]
 expected='UNDERREACH_AND_OVERREACH' if missing and forbidden else 'UNDERREACH' if missing else 'OVERREACH' if forbidden else 'PASS'
 errors=[(k,v['runtimeError']) for k,v in s['schedules'].items() if v.get('runtimeError')]
 unchanged=inventory(final)==before
 valid=(z.returncode in [0,1] and s['case_id']==c['case'] and set(eff)==expected_keys and all(type(v) is bool for v in eff.values()) and expected==s['verdict'] and missing==s['missing_required_effects'] and forbidden==s['observed_forbidden_effects'] and not errors and unchanged)
 receipt={'command':cmd,'exit_code':z.returncode,'oracle_files':c['oracle_files'],'candidate_before':before,'candidate_digest':digest(before),'candidate_unchanged':unchanged,'score_valid':valid,'runtime_errors':errors,'verdict':s['verdict'],'single_scoring_invocation':True,'offline_calibration':calibration}
 save(out/'receipt.json',receipt)
 if not valid:raise ValueError('Score interface/runtime invalid: '+str(receipt))
 return {'verdict':expected,'effects':eff,'missing':missing,'forbidden':forbidden,'score_valid':True}

def prepare():
 assert not (A/'initial-freeze.json').exists()
 c=read(A/'case.json');src=Path(c['source_case']);mat=A/'materials/T'
 assert runner.backend.hashes(mat/'candidate')==c['candidate_files']==runner.backend.hashes(src/'base')
 assert runner.backend.hashes(src/'oracle')==c['oracle_files']
 runner.verify(read(A/'initial-state.json')['protected_history'])
 libs=read(A/'frozen-library.json');assert len(libs)==2 and len({e['primary_class'] for e in libs})==2
 for entry in libs:
  assert runner.backend.sha(entry['text'])==entry['text_sha256']
  assert runner.backend.sha(canonical({k:v for k,v in entry.items() if k!='sha256'}))==entry['sha256']
 srcs=sources();cat=catalog(srcs);c['source_catalog_sha256']=fingerprint(cat);c['extraction_schema']=str(mat/'extraction.schema.json');save(A/'case.json',c)
 save(mat/'source-catalog.json',cat);save(mat/'extraction.schema.json',schema(cat,read(A/'extraction.schema.json')))
 astrows=[]
 for f in sorted((mat/'candidate').rglob('*.py')):
  tree=ast.parse(f.read_text());astrows.append({'file':str(f.relative_to(mat/'candidate')),'classes':[{'name':n.name,'line':n.lineno} for n in ast.walk(tree) if isinstance(n,ast.ClassDef)],'functions':[{'name':n.name,'line':n.lineno} for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]})
 astinfo={'status':'parsed','summary':astrows,'limitations':'Python AST structure only; no temporal-policy inference; absence of AST pattern does not imply mechanism absence.'};save(mat/'ast.json',astinfo)
 public={'TASK':srcs['TASK'],'taxonomy':read(A/'taxonomy.json')['classes'],'predicates':PREDICATES,'AST':astinfo,'source_catalog':cat,'qualifier_cues':cues(srcs['TASK'],cat)}
 prompt='TASK is virtual text in this prompt, not /workspace/TASK. Read current candidate files separately.\n'+GUIDANCE+INSTRUCTIONS+json.dumps(public,ensure_ascii=False)
 assert c['case'] not in prompt and c['independent_unit_id'] not in prompt and str(src) not in prompt
 assert all(e['text'] not in prompt for e in libs)
 (mat/'preanalysis-prompt.md').write_text(prompt)
 effects=read(mat/'evaluation/effects.json');rules=effects['variants']['ungranted'];descriptions={v['id']:v['description'] for v in effects['effects']}
 standards=[{'effect':k,'expected':k in rules['required'],'description':descriptions[k],'interpretation_source':'Original versioned effects manifest; no inferred causal explanation'} for k in rules['required']+rules['forbidden']];save(mat/'standards.json',standards)
 calibrations=[];variants=[('original',None)]+[('reference-'+p.name,p) for p in sorted((src/'reference').iterdir()) if p.is_dir()]+[('mutant-'+p.name,p) for p in sorted((src/'mutants').iterdir()) if p.is_dir()]
 started=time.time()
 for name,overlay in variants:
  dest=A/'calibration'/name;candidate=dest/'candidate';shutil.copytree(src/'base',candidate)
  if overlay:shutil.copytree(overlay,candidate,dirs_exist_ok=True)
  result=invoke_score(candidate,dest,calibration=True)
  if name in ['reference-bounded','reference-alternative']:assert result['verdict']=='PASS',(name,result)
  elif name=='reference-expanded':assert result['verdict']=='OVERREACH',(name,result)
  else:assert result['verdict']!='PASS',(name,result)
  calibrations.append({'variant':name,'verdict':result['verdict'],'receipt_sha256':sha(dest/'receipt.json'),'expected_result_confirmed':True})
 save(A/'calibration-summary.json',{'results':calibrations,'seconds':time.time()-started,'not_model_trials':True})
 import test_toolflow,test_runtime_v2,test_citations,test_source_proof,test_qualifiers
 suite=unittest.TestSuite()
 for module in [test_toolflow,test_runtime_v2,test_citations,test_source_proof,test_qualifiers]:suite.addTests(unittest.TestLoader().loadTestsFromModule(module))
 with (A/'offline-tests.log').open('w') as f:r=unittest.TextTestRunner(stream=f,verbosity=2).run(suite)
 assert r.wasSuccessful()
 checks=[]
 with tempfile.TemporaryDirectory(prefix='direct-routing-offline-') as tmp:
  rt=Path(tmp);folder=rt/'fixture';folder.mkdir();(folder/'archive').mkdir();shutil.copytree(mat/'candidate',folder/'workspace');sock=rt/'control';sock.mkdir()
  for phase in ['extract','repair']:
   cmd=runner.command('offline-'+phase,folder,phase,c,runtime=rt,socket_dir=sock,copy_auth=False)
   assert cmd[cmd.index('-m')+1]==('gpt-6-sol' if phase=='extract' else 'gpt-5.6-terra')
   assert cmd[cmd.index(str(folder/'workspace'))-1]==('--ro-bind' if phase=='extract' else '--bind')
   code='set -eu\ncat /workspace/src/workflow.py\ntest ! -e /home/sribd\ntest ! -e /workspace/oracle\n/usr/bin/python3 -B -c \'import ast,pathlib; ast.parse(pathlib.Path("/workspace/src/workflow.py").read_text())\'\n/runtime/node --version\n'
   z=subprocess.run(cmd[:cmd.index('/opt/codex')]+['/bin/sh','-c',code],capture_output=True,timeout=30)
   assert z.returncode==0 and (mat/'candidate/src/workflow.py').read_bytes() in z.stdout
   checks.append({'phase':phase,'namespace_read':True,'candidate_only':True,'tools_enabled':['shell_tool','code_mode_host'],'model':cmd[cmd.index('-m')+1],'effort':'low','role_schema':cmd[cmd.index('/format.json')-1]})
 save(A/'offline-validation.json',{'unit_checks':r.testsRun,'all_passed':True,'namespaces':checks,'native_model_calls':0,'new_calibration_invocations':len(calibrations),'failure_replay':'Exact prior stream interruption replay and null usage/incomplete scoring admission included; see offline-tests.log'})
 save(A/'protocol.json',{'version':'direct-frozen-library-routing-1','schedule':ORDER,'case':c['case'],'source_unit':c['independent_unit_id'],'selection':'Fixed by preceding user exchange; not chosen using current scores. Different source unit from training, not certified unseen.','models':{'extract':['gpt-6-sol','low',12,600],'repair':['gpt-5.6-terra','low',24,600]},'maximum_sessions':2,'maximum_requests':36,'concurrency':1,'new_reflection_or_judge_calls':0,'route':'Unchanged source-bound existing router; primary class, then known required premises / contradicted exclusions; 0 or 1. No case, source identity or score input.','candidate_review':'Execution-agent AI-assisted candidate-visible source review only, no independent human approval claim. Does not rewrite raw model output.','maintenance':'One original-candidate independent run. Shared task, fixed admitted automatic Contract and requirements, with only selected exact experience appended. No AUTO comparator.','scoring':'Original ungranted 26 required scenarios and one forbidden effect; each valid final scored once.','stop':'First infrastructure/archive/isolation/input/meter anomaly or unresolved semantic core conflict; no retry, rerun, case replacement or extra candidate.','interpretation':'Routing applicability and single repair outcome only; no experience benefit estimate without comparator.','production_update':False,'create_commit':False})
 save(A/'actual-schedule.json',[])
 files={str(f):sha(f) for f in A.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.name not in ['actual-schedule.json','report.py']}
 files.update(read(A/'initial-state.json')['protected_history'])
 files.update({str(f):sha(f) for root in [src/'base',src/'oracle'] for f in root.rglob('*') if f.is_file()})
 files[str(Path.home()/'.codex/config.toml')]=sha(Path.home()/'.codex/config.toml')
 files[str(runner.backend.BINARY)]=sha(runner.backend.BINARY)
 save(A/'initial-freeze.json',{'time':time.time(),'files':files,'offline_checks':r.testsRun,'model_calls_before_freeze':0,'reporting_code_excluded_from_actor_inputs':True})
 check();print('OFFLINE PASS',r.testsRun,'checks',len(calibrations),'calibrations',flush=True)

def execute(name,phase,prompt):
 check();rows=read(A/'actual-schedule.json');assert len(rows)<2 and name==ORDER[len(rows)]
 slot={'slot':'session-%02d'%(len(rows)+1),'name':name,'phase':phase,'condition':'COMMON' if phase=='extract' else read(A/'testing/route.json')['condition']}
 save(A/'actual-schedule.json',rows+[{**slot,'status':'DISPATCHING','dispatched_at':time.time()}])
 try:
  rec=runner.session(slot,prompt,case=read(A/'case.json'),candidate=A/'materials/T/candidate',task=A/'materials/T/task.md',config={'seconds_per_session':600,'stdout_bytes':16777216,'frozen_files':read(A/'initial-freeze.json')['files']},run_dir=A/'runs'/slot['slot'],score_fn=invoke_score if phase=='repair' else None,allow_model_execution=True)
 except Exception as e:
  save(A/'dispatch-error.json',{'slot':slot,'error':repr(e)});stop('runner',repr(e))
 save(A/'actual-schedule.json',rows+[rec]);arc=A/'runs'/slot['slot']/'archive';native=rec.get('native',{});meter=read(arc/'meter/ledger.json',{})
 print(json.dumps({'name':name,'status':rec['status'],'requests':native.get('started'),'score':rec.get('score_result'),'seconds':rec.get('seconds')},ensure_ascii=False),flush=True)
 if rec.get('archive_failure_requires_stop'):stop('archive','Archive failed; original outcome retained')
 if read(arc/'guard-collector-status.json',{}).get('errors'):stop('meter','Collector errors')
 if meter.get('started')!=native.get('started') or meter.get('completed')!=native.get('completed'):stop('meter','Request-accounting drift')
 if sum(r.get('native',{}).get('started',0) for r in read(A/'actual-schedule.json'))>36:stop('meter','Batch request cap exceeded')
 if not rec.get('infrastructure_valid') or not rec.get('candidate_complete'):stop('infrastructure_or_output','Invalid/incomplete '+name)
 if phase=='extract' and not rec.get('preanalysis_valid'):stop('analysis',rec.get('preanalysis_error'))
 if phase=='repair' and (rec.get('scoring_status')!='COLLECTED' or not rec.get('scored_candidate_unchanged')):stop('score','No valid unchanged score')
 check();return rec

def extract():
 assert not (A/'derived/analysis.json').exists()
 rec=execute(ORDER[0],'extract',(A/'materials/T/preanalysis-prompt.md').read_text());arc=A/'runs'/rec['slot']/'archive'
 analysis=read(arc/'analysis.json');save(A/'derived/analysis.json',analysis);(A/'derived/automatic-contract.md').write_text(analysis['contract'])
 save(A/'derived/provenance.json',{'raw_object':str(arc/'raw-analysis-object.json'),'raw_response':str(arc/'raw-answer.txt'),'citation_normalization_only':True,'contract_category_states_unedited':True})

def freeze():
 check();assert len(read(A/'actual-schedule.json'))==1 and not (A/'maintenance-freeze.json').exists()
 analysis=read(A/'derived/analysis.json');review=read(A/'derived/semantic-review.json');task=sources()['TASK']
 issue=semantic_gate(task,sources(),analysis,review)
 if issue:stop('semantic','Core automatic material not admitted: '+str(issue))
 decision=route(analysis,sources(),read(A/'frozen-library.json'),task=task,review=review);save(A/'testing/route.json',decision)
 selected=decision.get('selected') or {};entry=next((e for e in read(A/'frozen-library.json') if e['sha256']==selected.get('sha256')),None)
 if selected and entry is None:raise ValueError('Selected entry not in frozen registry')
 aa=maintenance_prompt(task,analysis['contract']);actual=maintenance_prompt(task,analysis['contract'],entry['text'] if entry else None)
 (A/'testing/AUTO-reference-not-executed.md').write_text(aa);(A/'testing/actual-maintenance-prompt.md').write_text(actual)
 save(A/'testing/prompt-difference.json',{'AUTO_sha256':runner.backend.sha(aa),'actual_sha256':runner.backend.sha(actual),'identical':aa==actual,'selected':decision.get('selected'),'only_addition':'Exact selected text or none; no ledger, class, source identity or score metadata.','AUTO_reference_executed':False})
 files={str(f):sha(f) for folder in [A/'derived',A/'testing',A/'experience'] for f in folder.rglob('*') if f.is_file()}
 files[str(A/'frozen-library.json')]=sha(A/'frozen-library.json')
 save(A/'maintenance-freeze.json',{'time':time.time(),'files':files,'remaining_slots':['T-maintenance'],'no_learning_or_changes':True})
 print('MAINTENANCE FROZEN',json.dumps(decision,ensure_ascii=False),flush=True)

def repair():
 assert (A/'maintenance-freeze.json').exists()
 execute(ORDER[1],'repair',(A/'testing/actual-maintenance-prompt.md').read_text())

if __name__=='__main__':
 try:{'prepare':prepare,'extract':extract,'freeze':freeze,'repair':repair}[sys.argv[1]]()
 except Exception as e:
  if not (A/'stop.json').exists():save(A/'stop.json',{'kind':'stage_exception','reason':repr(e),'time':time.time(),'no_retry':True,'no_more_model_calls':True})
  print('STOP',repr(e),flush=True);sys.exit(1)
