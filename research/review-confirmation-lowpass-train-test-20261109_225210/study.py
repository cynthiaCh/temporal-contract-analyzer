"""Explicit bounded English-only 1-train / 2-test study, no old scheduler."""
import ast,json,shutil,subprocess,sys,tempfile,time,unittest
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A))
import runner
from archive import save,sha,inventory,digest
from citations import catalog,schema,fingerprint,INSTRUCTIONS
from qualifiers import GUIDANCE,cues
from english_validation import require_english_material
from toolflow import PREDICATES,canonical,maintenance_prompt,semantic_gate,route,freeze_entry
from feedback import feedback
ORDER=['D-analysis','D-AUTO-1','D-AUTO-2','reflection','D-development-1','D-development-2','T1-analysis','T2-analysis','T1-B1','T1-A1','T2-A1','T2-B1','T1-A2','T1-B2','T2-B2','T2-A2']
EXT=['.md','.py','.js','.jsx','.ts','.tsx','.vue']
ENV='\nPreinstalled public dependencies are read-only at /runtime/node_modules. No dependency installation is needed or allowed. For optional local JavaScript syntax checks, the installed esbuild and Babel parser may be required by absolute path. Source evidence and test assertions must come from the current candidate, not dependency internals.\n'

def read(p,default=None):return json.loads(Path(p).read_text()) if Path(p).exists() else default
def cases():return {c['alias']:c for c in read(A/'cases.json')}
def journal():return read(A/'actual-schedule.json',[])
def sources(alias):
 root=A/'materials'/alias/'candidate';s={str(f.relative_to(root)):f.read_text() for f in root.rglob('*') if f.is_file() and f.suffix in EXT};s['TASK']=(A/'materials'/alias/'task.md').read_text();return s
def common(alias):return maintenance_prompt(sources(alias)['TASK'],approved(alias)['contract'])+ENV

def stop(kind,reason):
 save(A/'stop.json',{'kind':kind,'reason':reason,'time':time.time(),'no_retry':True,'no_more_model_calls':True});raise RuntimeError(reason)
def check():
 assert not (A/'stop.json').exists(),'Already stopped; no retry'
 runner.verify(read(A/'initial-freeze.json')['files'])
 for name in ['analysis-freeze-D.json','reflection-freeze.json','experience-freeze.json','library-freeze.json','test-freeze.json']:
  if (A/name).exists():runner.verify(read(A/name)['files'])
def approved(alias):
 analysis=read(A/'derived'/alias/'analysis.json');review=read(A/'derived'/alias/'semantic-review.json');assert analysis and review,'Source-bound AI review missing'
 issue=semantic_gate(sources(alias)['TASK'],sources(alias),analysis,review)
 if issue:stop('semantic','Core automatic material conflict: '+str(issue))
 return analysis

def invoke_score(alias,final,out,calibration=False):
 c=cases()[alias];out.mkdir(parents=True,exist_ok=True);before=inventory(final);cmd=[c['node'],str(Path(c['source_case'])/'oracle/probe.cjs'),str(final),'ungranted'];start=time.time()
 with (out/'stdout.json').open('wb') as o,(out/'stderr.txt').open('wb') as e:z=subprocess.run(cmd,stdout=o,stderr=e,timeout=120)
 s=read(out/'stdout.json');rules=read(A/'materials'/alias/'evaluation/effects.json')['variants']['ungranted'];eff=s['observed_effects'];missing=[k for k in rules['required'] if eff.get(k) is not True];forbidden=[k for k in rules['forbidden'] if eff.get(k) is True]
 expected='UNDERREACH_AND_OVERREACH' if missing and forbidden else 'UNDERREACH' if missing else 'OVERREACH' if forbidden else 'PASS'
 errors=[{'schedule':k,'error':v['runtimeError']} for k,v in s['schedules'].items() if v.get('runtimeError')]
 valid=(z.returncode in [0,1] and s['case_id']==c['case'] and set(eff)==set(rules['required']+rules['forbidden']) and all(type(v) is bool for v in eff.values()) and expected==s['verdict'] and missing==s['missing_required_effects'] and forbidden==s['observed_forbidden_effects'] and inventory(final)==before)
 if calibration and errors:valid=False
 save(out/'receipt.json',{'command':cmd,'exit_code':z.returncode,'oracle_files':c['oracle_files'],'candidate_before':before,'candidate_digest':digest(before),'candidate_unchanged':inventory(final)==before,'score_valid':valid,'runtime_errors':errors,'verdict':s['verdict'],'seconds':time.time()-start,'single_invocation':True,'offline_calibration':calibration,'runtime_policy':'Completed, source-read, format-valid final candidates retain the original scorer verdict, including product syntax/runtime/protocol failures. Scorer timeout/unparseable result or changed environment is infrastructure failure, not a behavior failure.'})
 if not valid:raise ValueError('Invalid scoring interface or calibration environment: '+alias)
 return {'verdict':expected,'effects':eff,'missing':missing,'forbidden':forbidden,'score_valid':True,'runtime_errors':errors}

def prepare():
 assert not (A/'initial-freeze.json').exists();runner.verify(read(A/'initial-state.json')['historical_files']);cal=[];start=time.time();cc=list(cases().values())
 for c in cc:
  alias=c['alias'];src=Path(c['source_case']);mat=A/'materials'/alias
  assert runner.backend.hashes(mat/'candidate')==c['candidate_files']==runner.backend.hashes(src/'base')
  assert runner.backend.hashes(src/'oracle')==c['oracle_files'];assert sha(mat/'task.md')==c['task_sha256']
  ss=sources(alias);cat=catalog(ss);save(mat/'source-catalog.json',cat);save(mat/'extraction.schema.json',schema(cat,read(A/'extraction.schema.json')));c['source_catalog_sha256']=fingerprint(cat);c['extraction_schema']=str(mat/'extraction.schema.json')
  shapes=[]
  for file,body in ss.items():
   if file.endswith('.py'):
    tree=ast.parse(body);shapes.append({'file':file,'parser':'Python ast','functions':[{'name':n.name,'line':n.lineno} for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)],'classes':[{'name':n.name,'line':n.lineno} for n in ast.walk(tree) if isinstance(n,ast.ClassDef)]})
   elif file.endswith(('.js','.jsx')):
    js="const p=require(process.argv[1]);const fs=require('fs');const t=p.parse(fs.readFileSync(process.argv[2],'utf8'),{sourceType:'module',plugins:['jsx']});const rows=[];function w(n){if(!n||typeof n!=='object')return;if(n.type&&/Function|Class|Method/.test(n.type))rows.push({type:n.type,name:n.id?.name||n.key?.name||null,line:n.loc?.start.line});for(const [k,v]of Object.entries(n))if(!['loc','start','end'].includes(k))if(Array.isArray(v))v.forEach(w);else if(v&&typeof v==='object')w(v)}w(t);console.log(JSON.stringify(rows));"
    z=subprocess.run([c['node'],'-e',js,str(Path(c['public_dependencies'])/'@babel/parser'),str(mat/'candidate'/file)],capture_output=True,text=True,timeout=30);assert z.returncode==0,z.stderr;shapes.append({'file':file,'parser':'Installed Babel parser with JSX','nodes':json.loads(z.stdout)})
  astinfo={'status':'parsed','summary':shapes,'limitations':'Syntactic structure only; no temporal-policy inference. No AST pattern match does not imply that a mechanism is absent.'};save(mat/'ast.json',astinfo)
  payload={'TASK':ss['TASK'],'taxonomy':read(A/'taxonomy.json')['classes'],'predicates':PREDICATES,'AST':astinfo,'source_catalog':cat,'qualifier_cues':cues(ss['TASK'],cat)}
  prompt='Write all generated prose in English; retain exact source quotations and opaque identifiers. TASK is virtual prompt text, not /workspace/TASK. Read the actual source bodies separately.\n'+GUIDANCE+INSTRUCTIONS+json.dumps(payload,ensure_ascii=False)
  assert all(x['case'] not in prompt for x in cc) and c['independent_unit_id'] not in prompt
  require_english_material(prompt,alias+' preanalysis');(mat/'preanalysis-prompt.md').write_text(prompt)
  e=read(mat/'evaluation/effects.json');rules=e['variants']['ungranted'];desc={x['id']:x['description'] for x in e['effects']};save(mat/'standards.json',[{'effect':k,'expected':k in rules['required'],'description':desc[k],'policy_support':'Original effects adapter, current task/docs/source and explicit AI-assisted preservation inferences; labels are not causes.'} for k in rules['required']+rules['forbidden']])
 save(A/'cases.json',cc)
 for c in cc:
  alias=c['alias'];src=Path(c['source_case']);variants=[('original',None)]+[('reference-'+p.name,p) for p in sorted((src/'reference').iterdir()) if p.is_dir()]+[('mutant-'+p.name,p) for p in sorted((src/'mutants').iterdir()) if p.is_dir()]
  for name,overlay in variants:
   out=A/'calibration'/alias/name;candidate=out/'candidate';shutil.copytree(src/'base',candidate)
   if overlay:shutil.copytree(overlay,candidate,dirs_exist_ok=True)
   score=invoke_score(alias,candidate,out,True)
   if name=='reference-bounded':assert score['verdict']=='PASS',(alias,name,score)
   elif name=='reference-expanded':assert score['verdict']=='OVERREACH',(alias,name,score)
   else:assert score['verdict']!='PASS',(alias,name,score)
   cal.append({'alias':alias,'variant':name,'verdict':score['verdict'],'receipt_sha256':sha(out/'receipt.json')})
  print('CALIBRATED',alias,len(variants),'original/reference/mutant variants',flush=True)
 save(A/'calibration-summary.json',{'results':cal,'seconds':time.time()-start,'model_calls':0})
 import test_toolflow,test_runtime_v2,test_citations,test_source_proof,test_qualifiers
 suite=unittest.TestSuite()
 for m in [test_toolflow,test_runtime_v2,test_citations,test_source_proof,test_qualifiers]:suite.addTests(unittest.TestLoader().loadTestsFromModule(m))
 with (A/'offline-tests.log').open('w') as f:r=unittest.TextTestRunner(stream=f,verbosity=2).run(suite)
 assert r.wasSuccessful()
 namespace=[]
 for c in cc:
  with tempfile.TemporaryDirectory(prefix='review-offline-') as tmp:
   rt=Path(tmp);f=rt/'fixture';f.mkdir();(f/'archive').mkdir();shutil.copytree(A/'materials'/c['alias']/'candidate',f/'workspace');sock=rt/'control';sock.mkdir()
   for phase in ['extract','repair']:
    cmd=runner.command('offline-'+phase,f,phase,c,runtime=rt,socket_dir=sock,copy_auth=False);assert cmd[cmd.index(str(f/'workspace'))-1]==('--ro-bind' if phase=='extract' else '--bind')
    target='src/workflow.py' if c['alias']=='D' else 'src/Workspace.jsx' if c['alias']=='T1' else 'src/workspace.js'
    body='set -eu\ncat /workspace/'+target+'\ntest ! -e /home/sribd\ntest ! -e /workspace/oracle\n/runtime/node --version\n'
    if phase=='repair':body+='/runtime/node -e \'require("/runtime/node_modules/react");require("/runtime/node_modules/jquery");require("/runtime/node_modules/esbuild");require("/runtime/node_modules/@babel/parser")\'\n'
    z=subprocess.run(cmd[:cmd.index('/opt/codex')]+['/bin/sh','-c',body],capture_output=True,timeout=30);assert z.returncode==0,z.stderr;assert (A/'materials'/c['alias']/'candidate'/target).read_bytes() in z.stdout;namespace.append({'alias':c['alias'],'phase':phase,'source_read':True,'benchmark_hidden':True,'public_dependencies_available':True})
 save(A/'offline-validation.json',{'tests_passed':r.testsRun,'namespaces':namespace,'calibrations':len(cal),'new_model_calls':0,'source_extensions':['.py','.js','.jsx','.ts','.tsx','.vue'],'failure_replay':'Original stream interruption and null usage replay included; incomplete candidates remain unscored.'})
 save(A/'actual-schedule.json',[])
 save(A/'protocol.json',{'version':'lowpass-review-one-train-two-test-english-1','fixed_schedule':ORDER,'models':{'extract':['gpt-6-sol','low',12,600],'repair':['gpt-5.6-terra','low',24,600],'reflect':['gpt-5.6-terra','medium',12,600]},'maximum_sessions':16,'maximum_requests':336,'concurrency':1,'sampling_controlled':False,'language':'English for all model-visible owned material and generated prose; exact source citations remain verbatim.','development':'One new D analysis, two fresh independent AUTO baselines, one tool-free fresh reflection, two independent experience revalidations. No old experience or test feedback.','admission':'At least one evidenced target/overall relation improves relative to AUTO; no unsupported policy; record all losses. Not a both-PASS gate.','tests':'After library freeze, each T independently analyzed once; existing conservative router selects zero or one entry. A/B share one fixed Contract, original source, requirements and tools; only routed body is added. Two independent repeats per arm.','empty_library_or_all_pass':'Both D AUTO PASS: no experience generated and stop; unsupported candidate or no development improvement: stop before tests. No case replacement.','normal_failure':'Continue fixed next slot. Complete valid final candidates can fail the original scorer due to source syntax/runtime/protocol errors; preserve the original vectors and runtime traces.','stop':'First service/isolation/archive/meter/input anomaly, unresolved core semantic conflict, or invalid output: preserve partial/raw data and stop without retry or extra candidate.','no_extra_calls':'No GEPA, judge, connection preflight, retry, replacement or next round.','production_update':False,'create_commit':False})
 protected={str(p):sha(p) for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['actual-schedule.json','report.py'] and p.suffix!='.log'}
 protected.update(read(A/'initial-state.json')['historical_files'])
 for c in cc:
  for folder in ['base','oracle']:
   protected.update({str(p):sha(p) for p in (Path(c['source_case'])/folder).rglob('*') if p.is_file()})
 deps=Path(cc[0]['public_dependencies']);protected.update({str(p):sha(p) for p in deps.rglob('*') if p.is_file()})
 protected[str(Path.home()/'.codex/config.toml')]=sha(Path.home()/'.codex/config.toml');protected[str(runner.backend.BINARY)]=sha(runner.backend.BINARY)
 save(A/'initial-freeze.json',{'files':protected,'time':time.time(),'model_calls_before_freeze':0,'report_is_derived_not_actor_input':True});check();print('OFFLINE PASS',r.testsRun,'checks and',len(cal),'calibrations',flush=True)

def execute(name,phase,alias,prompt,condition,candidate=None,task=None):
 check();rows=journal();assert len(rows)<16 and ORDER[len(rows)]==name;assert sum(r['phase']==phase for r in rows)<{'extract':3,'repair':12,'reflect':1}[phase];require_english_material(prompt,name)
 slot={'slot':'session-%02d'%(len(rows)+1),'name':name,'phase':phase,'alias':alias,'condition':condition};save(A/'actual-schedule.json',rows+[{**slot,'status':'DISPATCHING','dispatched_at':time.time()}]);c=dict(cases()[alias])
 if phase=='reflect':c.pop('candidate_files');c.pop('task_sha256')
 try:rec=runner.session(slot,prompt,case=c,candidate=candidate or A/'materials'/alias/'candidate',task=task or A/'materials'/alias/'task.md',config={'seconds_per_session':600,'stdout_bytes':16777216,'frozen_files':read(A/'initial-freeze.json')['files']},run_dir=A/'runs'/slot['slot'],score_fn=(lambda final,out:invoke_score(alias,final,out)) if phase=='repair' else None,allow_model_execution=True)
 except Exception as e:save(A/'dispatch-error.json',{'slot':slot,'error':repr(e)});stop('runner',repr(e))
 save(A/'actual-schedule.json',rows+[rec]);print(json.dumps({'name':name,'status':rec['status'],'requests':rec.get('native',{}).get('started'),'seconds':rec.get('seconds'),'score':rec.get('score_result',{}).get('verdict'),'missing':rec.get('score_result',{}).get('missing')},ensure_ascii=False),flush=True)
 arc=A/'runs'/rec['slot']/'archive';meter=read(arc/'meter/ledger.json',{});native=rec.get('native',{})
 if rec.get('archive_failure_requires_stop'):stop('archive','Archive failure; original service outcome retained')
 if read(arc/'guard-collector-status.json',{}).get('errors'):stop('meter','Collector error')
 if meter.get('started')!=native.get('started') or meter.get('completed')!=native.get('completed'):stop('meter','Request accounting drift')
 if sum(r.get('native',{}).get('started',0) for r in journal())>336:stop('meter','Batch request limit')
 if not rec.get('infrastructure_valid') or not rec.get('candidate_complete'):stop('infrastructure_or_output','Invalid/incomplete '+name)
 if phase=='extract' and not rec.get('preanalysis_valid'):stop('analysis',rec.get('preanalysis_error'))
 if phase=='repair' and (rec.get('scoring_status')!='COLLECTED' or not rec.get('scored_candidate_unchanged')):stop('score','No valid unchanged score')
 check();return rec

def extract(alias):
 assert not (A/'derived'/alias/'analysis.json').exists()
 if alias!='D':assert (A/'library-freeze.json').exists()
 rec=execute(alias+'-analysis','extract',alias,(A/'materials'/alias/'preanalysis-prompt.md').read_text(),'COMMON');arc=A/'runs'/rec['slot']/'archive';x=read(arc/'analysis.json');save(A/'derived'/alias/'analysis.json',x);(A/'derived'/alias/'automatic-contract.md').write_text(x['contract']);save(A/'derived'/alias/'provenance.json',{'raw_object':str(arc/'raw-analysis-object.json'),'raw_response':str(arc/'raw-answer.txt'),'citation_fields_only_normalization':True,'Contract_class_and_fact_states_unedited':True})
def baseline(n):
 alias='D';approved(alias);prompt=common(alias);(A/'development').mkdir(exist_ok=True)
 if n==1:
  (A/'development/AUTO-prompt.md').write_text(prompt)
  files={str(p):sha(p) for p in (A/'derived/D').rglob('*') if p.is_file()};files[str(A/'development/AUTO-prompt.md')]=sha(A/'development/AUTO-prompt.md');save(A/'analysis-freeze-D.json',{'time':time.time(),'files':files,'same_public_input_for_both_AUTO_and_development':True})
 else:assert prompt==(A/'development/AUTO-prompt.md').read_text()
 execute('D-AUTO-'+str(n),'repair',alias,prompt,'AUTO')
 if n==2:
  records=[r for r in journal() if r['name'].startswith('D-AUTO-')];save(A/'development/baselines.json',records)
  if all(r['score_result']['verdict']=='PASS' for r in records):save(A/'development/no-experience.json',{'reason':'Both AUTO pass; no observed failure feedback. No old experience or harder replacement substituted.'});stop('training_all_pass','Both D AUTO pass; stop with no new experience')

def build_reflection():
 check();approved('D');assert len(journal())==3
 from review_training_adapter import build
 from locked_scope import revision_schema
 ledger,prompt=build();save(A/'reflection.schema.json',revision_schema(ledger,PREDICATES));(A/'training/reflection-prompt.md').write_text(prompt);(A/'training/reflection-task.md').write_text('One fresh English rules/unresolved candidate; no tools, seed, test data or retry.\n');(A/'training/model-workspace').mkdir();save(A/'training/model-workspace/payload.json',read(A/'training/reflection-input.json'))
 files={str(p):sha(p) for p in (A/'training').rglob('*') if p.is_file()};files.update({str(A/n):sha(A/n) for n in ['reflection.schema.json','locked-metadata.json']});save(A/'reflection-freeze.json',{'time':time.time(),'files':files,'one_candidate':True})
def reflect():
 from locked_scope import assemble
 from handoff import validate_candidate,render,numbered_rules
 rec=execute('reflection','reflect','D',(A/'training/reflection-prompt.md').read_text(),'LEARN',A/'training/model-workspace',A/'training/reflection-task.md');arc=A/'runs'/rec['slot']/'archive';raw=(arc/'raw-answer.txt').read_bytes();(A/'development/reflection-raw.txt').write_bytes(raw)
 try:
  obj=json.loads(raw);save(A/'development/raw-rule-revision.json',obj);ledger=read(A/'training/evidence-ledger.json');candidate,composition=assemble(obj,read(A/'locked-metadata.json'),ledger,PREDICATES);save(A/'development/experience-object.json',candidate);save(A/'development/composition.json',composition);text=render(candidate);require_english_material(text,'experience');(A/'development/experience.md').write_text(text)
  if any(c['case'] in text for c in cases().values()) or any(s['effect'] in text for s in read(A/'materials/D/standards.json')) or '```' in text or 'src/' in text:raise ValueError('Case/grading/path/patch leakage in delivered bodies')
  save(A/'development/structural-review.json',validate_candidate(candidate,ledger,PREDICATES));save(A/'development/rule-evidence.json',{'rules':numbered_rules(candidate),'applicability':candidate['applicability'],'unresolved':candidate['unresolved']});save(A/'development/derivation.json',{'origin':'Exact raw model rules/unresolved plus locked D mechanism metadata; deterministic numbering and body rendering','raw_response_sha256':sha(A/'development/reflection-raw.txt'),'rendered_sha256':sha(A/'development/experience.md'),'no_prose_rewrite':True})
 except Exception as e:save(A/'development/rejection.json',{'reason':repr(e),'raw_preserved':True});stop('candidate_structure',repr(e))
def develop(n):
 from handoff import semantic_gate as gate,render
 check();candidate=read(A/'development/experience-object.json');decision=gate(candidate,read(A/'training/evidence-ledger.json'),PREDICATES,read(A/'development/semantic-review.json'));save(A/'development/content-review.json',decision)
 if not decision['development_eligible']:stop('candidate_semantics','AI-assisted review rejected the single candidate')
 text=render(candidate);assert text==(A/'development/experience.md').read_text();prompt=(A/'development/AUTO-prompt.md').read_text()+'\n\nThe following is the frozen experience body. Check applicability against current evidence:\n'+text
 if n==1:
  (A/'development/revalidation-prompt.md').write_text(prompt);files={str(p):sha(p) for p in (A/'development').rglob('*') if p.is_file()};save(A/'experience-freeze.json',{'time':time.time(),'files':files})
 else:assert prompt==(A/'development/revalidation-prompt.md').read_text()
 execute('D-development-'+str(n),'repair','D',prompt,'AUTO_NEW_EXPERIENCE')
 if n==2:
  standards=read(A/'materials/D/standards.json');bases=read(A/'development/baselines.json');dev=[r for r in journal() if r['name'].startswith('D-development-')];comparisons=[]
  for d in dev:comparisons.append({'slot':d['slot'],'vs_each_AUTO':[feedback(read(A/'runs'/b['slot']/'archive/score/stdout.json'),[read(A/'runs'/d['slot']/'archive/score/stdout.json')],standards)['runs'][0] for b in bases]})
  save(A/'development/comparisons.json',comparisons);eligible=any(row['improvements'] for r in comparisons for row in r['vs_each_AUTO']);save(A/'development/admission.json',{'eligible':eligible,'no_confirmed_unsupported_policy':True,'all_regressions_retained':True,'both_PASS_not_required':True,'production_admitted':False})
  if not eligible:stop('no_development_improvement','No grounded target/overall improvement in two fixed development runs')
def freeze_library():
 check();assert read(A/'development/admission.json')['eligible'];candidate=read(A/'development/experience-object.json');entry=freeze_entry({'text':(A/'development/experience.md').read_text(),'requires':candidate['requires'],'excludes':candidate['excludes']},approved('D')['primary_class']);entry['version']='fresh-review-binding-english-1';entry['sha256']=runner.backend.sha(canonical({k:v for k,v in entry.items() if k!='sha256'}));save(A/'frozen-library.json',[entry]);files={str(p):sha(p) for p in (A/'development').rglob('*') if p.is_file()};files[str(A/'frozen-library.json')]=sha(A/'frozen-library.json');save(A/'library-freeze.json',{'time':time.time(),'files':files,'no_learning_after_freeze':True})
def freeze_tests():
 check();assert len(journal())==8
 for alias in ['T1','T2']:
  analysis=approved(alias);decision=route(analysis,sources(alias),read(A/'frozen-library.json'),task=sources(alias)['TASK'],review=read(A/'derived'/alias/'semantic-review.json'));dest=A/'testing'/alias;save(dest/'route.json',decision);aa=common(alias);entry=read(A/'frozen-library.json')[0] if decision['selected'] else None;bb=aa if entry is None else aa+'\n\nThe following is the frozen experience body. Check applicability against current evidence:\n'+entry['text'];(dest/'A.md').write_text(aa);(dest/'B.md').write_text(bb);save(dest/'prompt-difference.json',{'A_sha256':runner.backend.sha(aa),'B_sha256':runner.backend.sha(bb),'identical':aa==bb,'selected':decision['selected'],'only_intentional_difference':'0 or 1 exact frozen experience appended'})
 files={str(p):sha(p) for root in [A/'testing',A/'derived/T1',A/'derived/T2'] for p in root.rglob('*') if p.is_file()};save(A/'test-freeze.json',{'time':time.time(),'files':files,'remaining_order':ORDER[8:],'sampling_controlled':False})
def test(name):
 assert name in ORDER[8:] and (A/'test-freeze.json').exists();alias,armrep=name.split('-');execute(name,'repair',alias,(A/'testing'/alias/(armrep[0]+'.md')).read_text(),'AUTO' if armrep[0]=='A' else 'ROUTED')

if __name__=='__main__':
 try:
  command=sys.argv[1]
  if command=='extract':extract(sys.argv[2])
  elif command=='baseline':baseline(int(sys.argv[2]))
  elif command=='develop':develop(int(sys.argv[2]))
  elif command=='test':test(sys.argv[2])
  else:{'prepare':prepare,'build-reflection':build_reflection,'reflect':reflect,'freeze-library':freeze_library,'freeze-tests':freeze_tests}[command]()
 except Exception as e:
  if not (A/'stop.json').exists():save(A/'stop.json',{'kind':'stage_exception','reason':repr(e),'time':time.time(),'no_retry':True,'no_more_model_calls':True})
  print('STOP',repr(e),flush=True);sys.exit(1)
