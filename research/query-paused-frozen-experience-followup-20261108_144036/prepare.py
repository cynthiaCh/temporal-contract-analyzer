"""One-time source verification and byte-exact reuse. Never calls a model."""
import sys,json,hashlib,shutil,subprocess,random,time
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;O=A.parent/'query-paused-same-case-low-20261108_140200';ROOT=A.parent.parent
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def verify(d):
 for p,h in d.items():assert sha(p)==h,p
assert not (A/'sources.json').exists()
save(A/'initial-state.json',{'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'status':subprocess.check_output(['git','status','--short'],text=True),'tracked_diff':subprocess.check_output(['git','diff','HEAD'],text=True),'checked_instructions':'No applicable ancestor/root/research AGENTS.md found before work','source':str(O),'time':time.time()})
verify(read(O/'protocol.json')['files']);verify(read(O/'protected-files.json'))
assert sha(O/'protocol.json')==(O/'protocol.sha256').read_text().strip()
for n in ['contract-freeze.json','experience-freeze.json']:verify(read(O/n)['files'])
for mf in [O/'ARTIFACTS.sha256',*O.glob('runs/*/archive/ARTIFACTS.sha256')]:
 for line in mf.read_text().splitlines():
  h,f=line.split('  ',1);assert sha(mf.parent/f)==h,(mf,f)
c=read(O/'cohort.json');assert read(O/'materials/manifest.json')['id']==c['case'];assert sha(O/'materials/manifest.json')==c['manifest_sha256']
fc=read(O/'frozen-config.json');assert sha(fc['CLI_binary'])==fc['CLI_sha256'];verify(read(O/'scorer-dependencies.json')['files'])
a=(O/'prompts/AUTO.md').read_text();b=a+'\n\n'+(O/'NEW_EXPERIENCE.md').read_text()
for slot in ['base-1','base-2','reval-1','reval-2']:
 d=O/'runs'/slot/'archive';cfg=read(d/'input/config.json');assert (cfg['model'],cfg['effort'],cfg['requests_per_session'],cfg['seconds_per_session'])==('gpt-5.6-terra','low',24,600)
 assert (d/'input/actual-prompt.md').read_text()==(a if slot.startswith('base') else b)
 cmd=read(d/'command.json');assert cmd[cmd.index('-m')+1]=='gpt-5.6-terra' and 'model_reasoning_effort="low"' in cmd
names=['runner.py','archive.py','native_backend.py','guard_server.py','guard_client.py','request_guard.py','read_policy.py','prompts.py','research-config.toml','models-cache.snapshot.json','extraction.schema.json','reflection.schema.json','cohort.json','automatic-contract.md','automatic-contract-full.md','NEW_EXPERIENCE.md','scorer-dependencies.json','training-targets.json']
provenance={}
for n in names:shutil.copyfile(O/n,A/n);provenance[n]={'source':str(O/n),'sha256':sha(A/n),'byte_identical':True}
shutil.copytree(O/'materials',A/'materials')
(A/'prompts').mkdir();(A/'prompts/AUTO.md').write_text(a);(A/'prompts/AUTO_EXP.md').write_text(b)
for n in ['REPORT.md','frozen-config.json','offline-validation.json','offline-validation.log','current-case-preflight.json','acceptance.json','experience-review.json','experience-freeze.json','contract-freeze.json','summary.json','scope-review.json','experience-evidence.json']:
 p=A/'source-evidence'/n;p.parent.mkdir(exist_ok=True);shutil.copyfile(O/n,p)
for row in c['calibration']:
 for f in (O/'calibration'/row['label']).iterdir():
  if f.is_file():p=A/'source-evidence/calibration'/row['label']/f.name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,p)
# Preserve all existing user/source files, including the untracked historical batch.
protected=dict(read(O/'protected-files.json'))
for p in O.rglob('*'):
 if p.is_file() and not p.is_symlink():protected[str(p.resolve())]=sha(p)
save(A/'protected-files.json',protected)
slots=[];rng=random.Random(20261108)
for rep in [1,2,3]:
 arms=['A','B'];rng.shuffle(arms)
 for arm in arms:slots.append({'slot':f'block-{rep}-{arm}','case':c['case'],'phase':'repair','condition':'AUTO' if arm=='A' else 'AUTO_EXP','repeat':rep,'arm':arm})
save(A/'schedule.json',{'seed':20261108,'seed_scope':'schedule only, not model sampling','slots':slots})
save(A/'sources.json',{'source_batch':str(O),'case_from_manifest':c['case'],'manifest_sha256':c['manifest_sha256'],'reuse':provenance,'A_prompt_sha256':sha(A/'prompts/AUTO.md'),'B_prompt_sha256':sha(A/'prompts/AUTO_EXP.md'),'only_intended_prompt_difference':'B = A + two newline characters + byte-exact NEW_EXPERIENCE.md','all_four_development_maintenance_configurations_match':True,'old_archive_protocol_and_dependency_hashes_verified':True,'calibration_reused':len(c['calibration']),'no_calibration_rerun':True,'old_admission':read(O/'acceptance.json'),'protected_files':len(protected)})
save(A/'frozen-config.json',{**fc,'roles':{'repair':['gpt-5.6-terra','low',24,'maintenance']},'max_sessions':6,'max_underlying_requests':144,'cumulative_session_seconds':3600,'concurrency':1,'no_reflection_extraction_gepa':True,'source_batch':str(O),'same_case_development':True,'exploratory_followup_after_development':True,'independent_generalization':False})
print(json.dumps({'prepared':str(A),'case':c['case'],'schedule':[s['slot'] for s in slots],'model_calls':0,'protected_files':len(protected)}))
