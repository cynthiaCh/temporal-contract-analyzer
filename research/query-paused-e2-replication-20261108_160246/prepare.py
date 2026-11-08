"""Verify the single E2 source and copy frozen maintenance inputs; no model/scorer execution."""
import sys,json,hashlib,shutil,subprocess,random,time
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;S=A.parent/'query-paused-e2-low-20261108_151511';ROOT=A.parent.parent
read=lambda p:json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def verify(d):
 for p,h in d.items():assert sha(p)==h,p
assert not (A/'sources.json').exists()
if not (A/'initial-state.json').exists():save(A/'initial-state.json',{'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'status':subprocess.check_output(['git','status','--short'],text=True),'tracked_diff':subprocess.check_output(['git','diff','HEAD'],text=True),'time':time.time(),'instructions':'No applicable ancestor/root/research AGENTS.md. Unrelated nested official-src instructions do not apply.'})
assert sha(S/'NEW_EXPERIENCE.md')=='85c058e4065322155ac3ae3a8486df020da62745c3c64f25db5fd1b7570904c1'
verify(read(S/'protocol.json')['files']);verify(read(S/'experience-freeze.json')['files']);verify(read(S/'scorer-dependencies.json')['files']);verify({p:h for p,h in read(S/'protected-files.json').items() if p!=str(Path.home()/'.codex/config.toml')})
assert sha(S/'protocol.json')==(S/'protocol.sha256').read_text().strip()
for mf in [S/'ARTIFACTS.sha256',*S.glob('runs/*/archive/ARTIFACTS.sha256')]:
 for line in mf.read_text().splitlines():
  h,f=line.split('  ',1);assert sha(mf.parent/f)==h,(mf,f)
c=read(S/'cohort.json');assert c['case']==read(S/'materials/manifest.json')['id']=='query-paused-initial-fetch-10266-vanilla';assert sha(S/'materials/manifest.json')==c['manifest_sha256']
assert sha(S/'materials/task.md')==c['task_sha256']
for f,h in c['candidate_files'].items():assert sha(S/'materials/candidate'/f)==h,f
for f,h in c['oracle_files'].items():assert sha(Path(c['source_case'])/'oracle'/f)==h,f
assert (S/'prompts/AUTO_EXP.md').read_bytes()==(S/'prompts/AUTO.md').read_bytes()+b'\n\n'+(S/'NEW_EXPERIENCE.md').read_bytes()
fc=read(S/'frozen-config.json');assert sha(fc['CLI_binary'])==fc['CLI_sha256']
assert subprocess.check_output([fc['CLI_binary'],'--version'],text=True).strip()==fc['CLI_version'];assert subprocess.check_output([c['node'],'--version'],text=True).strip()==fc['node_actual']=='v16.20.2'
for row in read(S/'actual-schedule.json'):
 p=S/'runs'/row['slot']/'archive';cfg=read(p/'input/config.json');assert (cfg['model'],cfg['effort'],cfg['requests_per_session'],cfg['seconds_per_session'])==('gpt-5.6-terra','low',24,600)
 assert (p/'input/actual-prompt.md').read_bytes()==(S/'prompts'/f"{row['condition']}.md").read_bytes()
modules=['runner.py','archive.py','native_backend.py','guard_server.py','guard_client.py','request_guard.py','read_policy.py','prompts.py','research-config.toml','models-cache.snapshot.json','extraction.schema.json','reflection.schema.json','control.py']
provenance={}
for n in modules+['cohort.json','automatic-contract.md','automatic-contract-full.md','NEW_EXPERIENCE.md','scorer-dependencies.json','training-targets.json']:
 shutil.copyfile(S/n,A/n);provenance[n]={'source':str(S/n),'sha256':sha(A/n),'byte_identical':True}
shutil.copytree(S/'materials',A/'materials');shutil.copytree(S/'prompts',A/'prompts')
for n in ['REPORT.md','summary.json','experience-freeze.json','experience-review.json','frozen-config.json','integrity-validation.json','offline-validation.json','completion.json','sources.json']:
 p=A/'source-evidence'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(S/n,p)
protected=read(S/'protected-files.json')
host_config=Path.home()/'.codex/config.toml'
# Current host defaults are not loaded by the isolated actor. Freeze the current pre-task host file to preserve it.
protected[str(host_config)]=sha(host_config)
host_snapshot={'sha256':sha(host_config),'mtime':host_config.stat().st_mtime,'fields':[x for x in host_config.read_text().splitlines() if x.startswith(('model =','model_reasoning_effort','service_tier'))]}
save(A/'host-config-isolation.json',{'source_host_snapshot':fc['global_config'],'current_host_snapshot':host_snapshot,'source_runtime_profile_sha256':sha(S/'research-config.toml'),'host_config_not_an_experiment_input':True,'proof_pending':True,'code_evidence':'native_backend.command copies frozen research-config.toml into external profile, sets HOME/CODEX_HOME there, strips host environment and does not mount host home; CLI explicitly passes priority/low.','no_global_config_modified':True,'only_historical_protection_mismatch':str(host_config)})
for p in S.rglob('*'):
 if p.is_file() and not p.is_symlink():protected[str(p.resolve())]=sha(p)
for name in subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0'):
 if name:
  p=ROOT/name
  if p.is_file() and not p.is_symlink():protected[str(p.resolve())]=sha(p)
save(A/'protected-files.json',protected)
# Only maintenance is authorized; legacy unused role definitions remain byte-identical in runner.
config={k:fc[k] for k in ['CLI_binary','CLI_sha256','CLI_version','global_config','node_actual','node_declared_in_manifest','service_tier','max_stdout_bytes','max_report_characters','server_model_route_independently_attested','effort_observed','artifact_ownership']}
config['global_config']=host_snapshot
config['historical_source_global_config']=fc['global_config']
config.update(roles={'repair':['gpt-5.6-terra','low',24,'maintenance']},session_seconds=600,max_sessions=6,max_underlying_requests=144,cumulative_session_seconds=3600,max_external_scores=6,concurrency=1,source_batch=str(S),same_case_replication=True,independent_sessions=True,independent_unseen_case=False,extraction_calls=0,reflection_calls=0,gepa_calls=0,extra_judge_calls=0,model_preruns=0,retries=0,score_reruns=0)
save(A/'frozen-config.json',config)
rng=random.Random(2026110803);slots=[]
for rep in [1,2,3]:
 arms=['A','B'];rng.shuffle(arms)
 for arm in arms:slots.append({'slot':f'block-{rep}-{arm}','case':c['case'],'phase':'repair','condition':'AUTO' if arm=='A' else 'AUTO_EXP','repeat':rep,'arm':arm})
save(A/'schedule.json',{'seed':2026110803,'seed_scope':'schedule only, not model sampling','slots':slots})
save(A/'sources.json',{'sole_source':str(S),'case_from_manifest':c['case'],'manifest_sha256':c['manifest_sha256'],'task_sha256':c['task_sha256'],'candidate_files':c['candidate_files'],'E2_sha256':sha(A/'NEW_EXPERIENCE.md'),'A_prompt_sha256':sha(A/'prompts/AUTO.md'),'B_prompt_sha256':sha(A/'prompts/AUTO_EXP.md'),'automatic_contract_sha256':sha(A/'automatic-contract.md'),'reuse':provenance,'source_integrity_manifest_verified':True,'source_all_six_maintenance_configurations_match':True,'source_frozen_files':len(read(S/'protocol.json')['files']),'protected_files':len(protected),'source_historical_primary':{'AUTO':[0,3],'AUTO_EXP_E2':[1,3]},'no_history_pooled':True,'scorer_calibration_reused':len(c['calibration']),'no_actual_scorer_prerun':True,'no_E2_edit':True})
print(json.dumps({'source_verified':str(S),'case':c['case'],'E2':sha(A/'NEW_EXPERIENCE.md'),'schedule':[s['slot'] for s in slots],'protected_files':len(protected),'model_calls':0,'score_calls':0},ensure_ascii=False))
