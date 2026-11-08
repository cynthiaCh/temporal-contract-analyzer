import pathlib as P,json,hashlib,shutil,tempfile,subprocess,collections,csv,random,os,time
R=P.Path.cwd();B=R.parent/'temporal-contract-bench-git';C=B/'case-clusters/download-polling-restoration';PREV=R/'research/contract-repair-e1-mechanism-v1-20261108';S=R/'research/contract-repair-small-v1-20261108';A=R/'research/contract-repair-e1-cluster-hard-v1-20261108';A.mkdir(exist_ok=False);O=P.Path(tempfile.mkdtemp(prefix='contract-e1-cluster-hard-',dir='/tmp'));(A/'runtime-location.txt').write_text(str(O)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def hashes(p):return {str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file()}
def inv(p):return {k:{'sha256':v} for k,v in hashes(p).items()}
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
initial={'status':subprocess.check_output(['git','status','--short'],text=True),'diff':subprocess.check_output(['git','diff','--binary'],text=True),'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'AGENTS':'No applicable AGENTS.md at repository or ancestor directories; unrelated archived GEPA AGENTS.md not applicable.'};save(O/'initial-git.json',initial)
protected={str(p):sha(p) for root in [S,PREV,R/'research/u2-contract-repair-diagnostic-v1-20261108',C] for p in root.rglob('*') if p.is_file() and p.name!='auth.json' and '.runtime' not in p.parts};save(O/'protected-files.json',protected)
for n in ['native_backend.py','read_policy.py','request_guard.py','research-config.toml','models-cache.snapshot.json','extraction.schema.json','contract_extraction_K1.md','EXPERIENCE.md','experience-approval.json','runner.py']:
 shutil.copyfile(PREV/n,O/n)
assert sha(O/'EXPERIENCE.md')=='57527138a98bfa0d34a432ca82e7b863694b33818aa5a9a3c032ad69f4aaed1e'
shutil.copyfile(S/'offline-validation.json',O/'prior-offline-validation.json')
xs=json.loads(P.Path('/tmp/download-history-discovery.json').read_text());reg=json.loads((C/'cluster.json').read_text());registry={d['id']:d for d in reg['arms']};save(O/'cluster-registry.json',reg)
# Survey metadata only. Duplicated archived runs share immutable identity and are counted once.
seen={};survey=[]
for x in xs:
 d=x['data']
 if not d.get('model'):continue
 ident=tuple(d.get(k) for k in ['case_id','model','reasoning_effort','condition','started_at_utc','prompt_sha256','candidate_tree_sha256'])
 if not d.get('started_at_utc'):ident+=(x['path'],)
 if ident in seen:seen[ident]['duplicate_paths'].append(x['path']);continue
 p=P.Path(x['path']);term=d.get('termination_reason');valid=d.get('status')=='COMPLETED' and d.get('agent_exit_code')==0 and d.get('score_exit_code',0) in [0,1] and d.get('verdict') in ['PASS','UNDERREACH','OVERREACH','UNDERREACH_AND_OVERREACH'] and term not in ['STEP_LIMIT_OR_ERROR','STEP_LIMIT','TIMEOUT']
 row={'case':d.get('case_id'),'registered':d.get('case_id') in registry,'model':d['model'],'effort':d.get('reasoning_effort'),'condition':d.get('condition'),'start_sha':d.get('workspace_input_tree_sha256',d.get('base_tree_sha256')),'prompt_sha256':d.get('prompt_sha256'),'status':d.get('status'),'termination':term,'reported_valid_completion':valid,'verdict':d.get('verdict'),'run':x['path'],'duplicate_paths':[],'run_sha256':sha(p)};survey.append(row);seen[ident]=row
save(O/'history-survey.json',{'scanned_records':len(xs),'unique_model_metadata_rows':len(survey),'note':'Completion metadata is only a survey, not final admission; selected historical candidates separately hash-verified and re-scored. Cross-model, effort, starting tree and prompt strata retained, never pooled as target-model repetitions.','rows':survey})
node=B/'results/student-case-expansion-runtime/node18/bin/node';ids=['download-polling-restoration-explicit-vue2-eval-v2','download-polling-restoration-explicit-vue3-eval-v2'];cases=[];selection=[]
for idx,cid in enumerate(ids,1):
 src=C/'arms'/cid;m=json.loads((src/'case.json').read_text());assert not list(src.rglob('AGENTS.md'));dest=O/'materials'/cid;shutil.copytree(src/'base',dest/'candidate');shutil.copyfile(src/m['diagnostic_tasks']['maintenance']['core_prompt'],dest/'task.md');save(dest/'origin.json',{'manifest':str(src/'case.json'),'manifest_sha256':sha(src/'case.json'),'candidate_files':hashes(src/'base'),'task_sha256':sha(dest/'task.md'),'provenance':m['provenance']})
 c={'case':cid,'index':idx,'source_case':str(src),'node':str(node),'candidate_files':hashes(src/'base'),'task_sha256':sha(dest/'task.md'),'case_manifest_sha256':sha(src/'case.json'),'oracle_files':hashes(src/'oracle'),'calibration':[],'history':[]}
 input_sha=digest(inv(src/'base'))
 for batch in ['qwen-core24-optimized-v4-20261007','qwen-core24-quality-v5-20261007']:
  bp=B/'results'/batch;plan=json.loads((bp/'plan.json').read_text());job=next(j for j in plan['jobs'] if j['case_id']==cid and j['condition']=='latent-maintenance');hp=bp/'jobs'/job['id'];run=json.loads((hp/'run.json').read_text());score=json.loads((hp/'score/score.json').read_text());assert run['workspace_input_tree_sha256']==input_sha;assert digest(inv(hp/'candidate'))==run['candidate_tree_sha256'];assert run['status']=='COMPLETED' and run['agent_exit_code']==0 and run['termination_reason']=='TASK_DONE' and run['recovered_tool_format_errors']==0;assert score['case_id']==cid and score['verdict']==run['verdict'] and score['verdict']!='PASS'
  h=O/'history'/cid/batch;h.mkdir(parents=True);shutil.copytree(hp/'candidate',h/'candidate')
  for orig,n in [(hp/'run.json','run.json'),(hp/'score/score.json','score.json'),(hp/'control/prompt.md','prompt.md')]:
   assert orig.is_file();shutil.copyfile(orig,h/n)
  assert sha(h/'prompt.md')==run['prompt_sha256']
  rc=subprocess.run([str(node),str(src/'oracle/probe.cjs'),str(h/'candidate'),'ungranted'],capture_output=True,text=True,timeout=90);(h/'recheck.stdout.json').write_text(rc.stdout);(h/'recheck.stderr.txt').write_text(rc.stderr);sc=json.loads(rc.stdout);assert rc.returncode==1 and sc['observed_effects']==score['observed_effects'] and sc['verdict']==score['verdict']
  changes=[rel for rel,hsh in c['candidate_files'].items() if not (hp/'candidate'/rel).exists() or sha(hp/'candidate'/rel)!=hsh]
  rec={'batch':batch,'run':str(hp/'run.json'),'run_sha256':sha(hp/'run.json'),'candidate_tree_sha256':run['candidate_tree_sha256'],'input_tree_sha256':input_sha,'prompt_sha256':run['prompt_sha256'],'model':run['model'],'effort':run.get('reasoning_effort'),'temperature':plan['temperature'],'workflow':plan['agent_configuration'],'condition':'bare task + candidate + historical Qwen public scaffolding; NO automatic Contract, NO E1','valid_behavior_failures':1,'valid_runs':1,'verdict':score['verdict'],'missing':score['missing_required_effects'],'forbidden':score['observed_forbidden_effects'],'source_changes':changes,'current_oracle_replay_exact':True,'not_original_code_calibration':True};c['history'].append(rec)
 # Zero-model calibrated scorer admission, unchanged original oracle and assertions.
 labels=[('unchanged',None),('reference-bounded',src/m['references']['bounded'])]+[(q.replace('/','-'),src/q) for q in m['mutants']]
 for label,overlay in labels:
  d=O/'calibration'/cid/label;shutil.copytree(src/'base',d/'candidate')
  if overlay:shutil.copytree(overlay,d/'candidate',dirs_exist_ok=True)
  cmd=[str(node),str(src/'oracle/probe.cjs'),str(d/'candidate'),'ungranted'];st=time.time();z=subprocess.run(cmd,capture_output=True,text=True,timeout=90);(d/'stdout.json').write_text(z.stdout);(d/'stderr.txt').write_text(z.stderr);sc=json.loads(z.stdout);assert sc['case_id']==cid and z.returncode in [0,1];assert (sc['verdict']=='PASS')==(label=='reference-bounded')
  rec={'label':label,'command':cmd,'seconds':time.time()-st,'exit_code':z.returncode,'verdict':sc['verdict'],'effects':sc['observed_effects'],'raw':str(d/'stdout.json')};save(d/'receipt.json',rec);c['calibration'].append(rec)
 cases.append(c);print(cid,'history exact replays PASS; base/reference/6 mutants PASS',flush=True)
save(O/'cohort.json',{'cases':cases});save(O/'selection.json',{'selected':ids,'selection_before_any_new_model_call':True,'history_evidence_strength':'weak target-difficulty evidence: repeated same Qwen model/effort/input but two different prompts/workflows. Not repeated automatic-Contract failures; target Terra/medium bare and human-Contract each have one PASS per selected case. A single run per distinct target input condition is not treated as stable automatic-Contract ceiling.','failures_not_pooled_across_model_or_effort_or_start':True,'reason_for_these_two':'Both are registered derived same-source explicit lifecycle arms with >=2 normally completed, tool-format-error-free Qwen failures on identical current bases, exact raw score replay, and visible foreground/background/disposal/generation policy. Vue3 shows historical adjacent-background start regression; both fail newly queued retry schedules. Vue2 includes an actual TASK_DONE model run delivering no source change (not a calibration); reported separately.','excluded':{'explicit-react18':'recent exact A=3/3 and B=3/3 PASS; ceiling; not primary difficulty','low-cue-react18':'E1 source arm, not canonical core or a new derivative; unresolved visible foreground close/precise loading scoring policy','react18':'canonical arm; repeated bare-task Terra failures exist but foreground cancellation/reopen policy not supported by visible task/base; not admitted with hidden normative contract','other_models':'not added to selected Qwen failure counts','other_versions_and_unregistered_aliases':'not transferred across IDs or starting trees','STEP_LIMIT_OR_ERROR_and_execution_anomalies':'excluded even if run.status says COMPLETED'}})
# Exact common prompts inherited from latest valid experiment. No research checklist or case-specific augmentation.
seed=2026110804;rng=random.Random(seed);slots=[]
for c in cases:
 cid=c['case'];task=(O/'materials'/cid/'task.md').read_text();pr=O/'prompts'/cid;pr.mkdir(parents=True)
 old=(PREV/'prompts/download-polling-restoration-explicit-react18/A.template.md').read_text();common=old[old.index('以下为辅助材料。'):];a=task+'\n\n'+common;(pr/'A.template.md').write_text(a);(pr/'B.template.md').write_text(a+'\n\n'+(O/'EXPERIENCE.md').read_text());e=(PREV/'prompts/download-polling-restoration-explicit-react18/extraction.md').read_text();(pr/'extraction.md').write_text(task+'\n\n'+e[e.index('只读取 /workspace'):]);slots.append({'slot':f'c{c["index"]}-x01','case':cid,'phase':'extract','condition':'extraction','repeat':None})
 for rep in range(1,4):
  groups=['A','B'];rng.shuffle(groups)
  for g in groups:slots.append({'slot':f'c{c["index"]}-r{rep}-{g}','case':cid,'phase':'repair','condition':g,'repeat':rep})
save(O/'schedule.json',{'seed':seed,'model_seed':None,'seed_scope':'scheduling only','serial':True,'slots':slots})
for srcname in ['cluster.json','README.md','runtime-cases.json']:shutil.copyfile(C/srcname,O/('source-'+srcname))
shutil.copyfile('/tmp/discover_cluster_history.py',O/'discover_history.py');shutil.copyfile('/tmp/prepare_e1_cluster_hard.py',O/'prepare.py')
for p in O.rglob('*'):
 if p.is_file() and '.runtime' not in p.parts:
  q=A/p.relative_to(O);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
print('RUNTIME',O)
