import pathlib as P,json,hashlib,shutil,subprocess,tempfile,sys,time,datetime
sys.dont_write_bytecode=True
A=P.Path(__file__).resolve().parent; R=A.parents[1]; B=R.parent/'temporal-contract-bench-git'; OLD=R/'research/contract-repair-e1-cluster-hard-v1-20261108'
O=P.Path(tempfile.mkdtemp(prefix='transfer-reflection-',dir='/tmp'));(A/'runtime-location.txt').write_text(str(O)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def hashes(p):return {str(f.relative_to(p)):sha(f) for f in sorted(p.rglob('*')) if f.is_file()}
save(A/'initial-git.json',{'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'status':subprocess.check_output(['git','status','--short'],text=True),'diff':subprocess.check_output(['git','diff','--binary'],text=True),'note':'Initial inspection before directory creation was clean. No applicable ancestor AGENTS.md found.'})
for n in ['native_backend.py','read_policy.py','request_guard.py','research-config.toml','models-cache.snapshot.json','extraction.schema.json','runner.py']:
 shutil.copyfile(OLD/n,A/n)
shutil.copyfile(R/'research/contract-extraction-evolution-u2-v2-20261107/contract_extraction_K1.md',A/'contract_extraction_K1.md')
shutil.copyfile(R/'research/contract-repair-small-v1-20261108/offline-validation.json',A/'prior-offline-validation.json')
# Research-only adaptations before formal freeze; authentication always outside repository.
p=A/'native_backend.py';s=p.read_text().replace("profile=OUT/'.runtime'/call","profile=Path((OUT/'runtime-location.txt').read_text().strip())/'.runtime'/call");p.write_text(s)
p=A/'runner.py';s=p.read_text().replace(".rglob('*.js')", ".rglob('*')").replace("lines={s.strip() for s in f.read_text().splitlines()", "if f.suffix not in ['.js','.py']:continue\n   lines={s.strip() for s in f.read_text().splitlines()")
s=s.replace("profile=O/'.runtime'/call", "profile=Path((O/'runtime-location.txt').read_text().strip())/'.runtime'/call")
p.write_text(s)
cluster=B/'case-clusters/transfer-retry-handoff';reg=json.loads((cluster/'cluster.json').read_text());ids=['transfer-progress-composition-v4-vanilla','transfer-progress-composition-v4-window-cued-python3-eval-v2'];cases=[]
node=B/'results/student-case-expansion-runtime/node18/bin/node'
assert node.is_file()
for i,cid in enumerate(ids,1):
 arm=next(a for a in reg['arms'] if a['id']==cid);src=cluster/arm['path'];m=json.loads((src/'case.json').read_text());assert m['id']==cid and m['independent_unit_id']=='transfer-retry-abort-handoff'
 assert not list((src/'base').rglob('AGENTS.md'))
 d=A/'materials'/cid;shutil.copytree(src/'base',d/'candidate');shutil.copyfile(src/m['diagnostic_tasks']['maintenance']['core_prompt'],d/'task.md')
 # Frozen evaluator materials live only on evaluation side; no scoring paths mounted to CLI.
 shutil.copytree(src/'oracle',d/'evaluation');shutil.copyfile(src/'case.json',d/'manifest.json')
 c={'case':cid,'index':i,'source_case':str(src),'node':str(node),'candidate_files':hashes(src/'base'),'task_sha256':sha(d/'task.md'),'case_manifest_sha256':sha(src/'case.json'),'oracle_files':hashes(src/'oracle'),'calibration':[]}
 for label,overlay in [('unchanged',None),('reference-bounded',src/m['references']['bounded']),('reference-expanded',src/m['references']['expanded'])]+[(q.replace('/','-'),src/q) for q in m['mutants']]:
  dest=A/'calibration'/cid/label;shutil.copytree(src/'base',dest/'candidate')
  if overlay:shutil.copytree(overlay,dest/'candidate',dirs_exist_ok=True)
  cmd=[str(node),str(src/'oracle/probe.cjs'),str(dest/'candidate'),'ungranted'];st=time.time();z=subprocess.run(cmd,capture_output=True,text=True,timeout=90);(dest/'stdout.json').write_text(z.stdout);(dest/'stderr.txt').write_text(z.stderr)
  sc=json.loads(z.stdout); assert sc['case_id']==cid and z.returncode in [0,1],(cid,label,z.stderr)
  assert (sc['verdict']=='PASS')==(label=='reference-bounded'),(cid,label,sc['verdict'])
  rec={'label':label,'command':cmd,'seconds':time.time()-st,'exit_code':z.returncode,'verdict':sc['verdict'],'effects':sc['observed_effects'],'raw':str(dest/'stdout.json')};save(dest/'receipt.json',rec);c['calibration'].append(rec)
 cases.append(c);print(cid,'calibration complete',flush=True)
save(A/'cohort.json',{'cases':cases});shutil.copyfile(cluster/'cluster.json',A/'cluster-registry.json')
selection=R/'refine-logs/case-selection-v2-20261108';expected=json.loads((selection/'selection-evidence.json').read_text())['input_hashes'];checks={}
for c in cases:
 src=P.Path(c['source_case']);checks[c['case']]={rel:sha(src/rel)==h for rel,h in expected[c['case']].items()};assert all(checks[c['case']].values())
save(A/'version-correspondence.json',checks)
for n in ['README.md','SELECTION.md','EXPERIMENT_PLAN.md','protocol.json','selection-evidence.json']:shutil.copyfile(selection/n,A/('prior-'+n))
for c in cases:
 cid=c['case'];p=A/'prompts'/cid;p.mkdir(parents=True);task=(A/'materials'/cid/'task.md').read_text()
 old=(OLD/'prompts/download-polling-restoration-explicit-vue2-eval-v2/extraction.md').read_text();suffix=old[old.index('只读取 /workspace'):];assert (A/'contract_extraction_K1.md').read_text().strip() in suffix
 (p/'extraction.md').write_text(task+'\n\n'+suffix)
 runtime='Python自检使用 /usr/bin/python3 -B，并记录 --version' if c['index']==2 else 'Node自检使用 /runtime/node，并记录 --version'
 (p/'AUTO.template.md').write_text(task+'\n\n以下为辅助材料。依据原任务和项目证据核查其适用性；存在冲突或证据不足时不要盲目执行。\n{{FROZEN_AUTOMATIC_CONTRACT}}\n\n完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器、其他槽位或网络。'+runtime+'；不安装依赖。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围；补丁从独立工作区归档。\n')
# Protect all tracked files plus original case trees, source skill and prior evidence; no auth content.
tracked=subprocess.check_output(['git','ls-files','-z'],cwd=R).decode().split('\0');protected={str(R/f):sha(R/f) for f in tracked if f and (R/f).is_file()}
for c in cases:
 for f in P.Path(c['source_case']).rglob('*'):
  if f.is_file():protected[str(f)]=sha(f)
save(A/'protected-files.json',protected)
print('BATCH',A,'RUNTIME',O)
