"""Zero-model calibration reuse and preparation of public-source selector seeds."""
import csv,json,hashlib,subprocess,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent/'temporal-contract-analyzer';sys.path.insert(0,str(REPO))
from temporal_contract_analyzer.swe_tempoc_inputs import case_input
from temporal_contract_analyzer.core import sha
read=lambda p:json.loads(p.read_text())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
plan=read(ROOT/'plan.json');bench=REPO.parent/'swe-tempoc';rows=list(csv.DictReader((ROOT/'training_70_cases.csv').open(encoding='utf-8-sig')));assert len(rows)==70
from concurrent.futures import ThreadPoolExecutor
from temporal_contract_analyzer.tempoevo_backend import NativeV4Backend
files={}
for row in rows:
 current=case_input(row['case_id'],bench)
 for f in (bench/current['case_record']['manifest']).parent.rglob('*'):
  if f.is_file() and '__pycache__' not in f.parts:files[f.relative_to(bench).as_posix()]=sha(f.read_bytes())
def calibrate(row):
 cid=row['case_id'];c=case_input(cid,bench);base=ROOT/'calibration'/cid;manifest=c['case_record']['manifest'];m=read(bench/manifest);base.mkdir(parents=True,exist_ok=True)
 write(base/'case.json',dict(manifest=manifest))
 ev=dict(image=plan['backend']['grader_image'],inputs={str(base/'case.json'):'/checks/case.json',str(REPO/'tools/tempoevo-docker/gold.py'):'/checks/gold.py'},command=['/usr/bin/python3','/checks/gold.py'],seconds=180)
 if m.get('schema_version')=='python-pilot-0.1':ev['inputs'][str(REPO/'tools/tempoevo-docker/python_gold.py')]=ev['inputs'].pop(str(REPO/'tools/tempoevo-docker/gold.py'))
 receipts=[]
 for name,overlay in [('original',None),('reference',m.get('reference') or m['references']['bounded']),('negative',m['mutants'][0])]:
  target=base/name/'result.json'
  if target.exists() and not read(target).get('valid'):
   shutil.move(str(target),str(target.with_name('invalid-attempt1.json')))
  if target.exists():raw=read(target)
  else:
   subject=base/'subjects'/name
   if not subject.exists():shutil.copytree(c['candidate'],subject)
   if overlay:shutil.copytree((bench/manifest).parent/overlay,subject,dirs_exist_ok=True)
   out=base/'checks'/name
   if out.exists():out=base/'checks'/(name+'-corrected-python-adapter')
   out.mkdir(parents=True);raw=NativeV4Backend({}).evaluate('gold',dict(candidate=str(subject),evaluator=ev),out);write(target,raw)
  assert raw.get('valid') is True and raw['passed']==(name=='reference'),(cid,name,raw.get('error'))
  receipts.append(dict(case_id=cid,control=name,source=str(target),source_sha256=sha(target.read_bytes()),copy=str(target),copy_sha256=sha(target.read_bytes())))
 print('calibrated '+cid,flush=True);return receipts
with ThreadPoolExecutor(max_workers=8) as pool:receipts=[x for group in pool.map(calibrate,rows) for x in group]
write(ROOT/'calibration-reuse.json',dict(valid=True,controls=210,model_independent=True,newly_executed=True,reused=False,receipts=receipts));write(ROOT/'benchmark-file-hashes.json',files)
code="import sys,json,hashlib;from pathlib import Path;d=json.load(sys.stdin);bad=[k for k,v in d.items() if not (Path('/opt/swe-tempoc')/k).is_file() or hashlib.sha256((Path('/opt/swe-tempoc')/k).read_bytes()).hexdigest()!=v];print(json.dumps(dict(files_checked=len(d),mismatches=bad)))"
r=subprocess.run(['docker','run','--rm','-i','--pull=never','--network','none','--read-only','--entrypoint','python3',plan['backend']['grader_image'],'-B','-c',code],input=json.dumps(files),text=True,capture_output=True,check=True);check=json.loads(r.stdout);assert not check['mismatches'];write(ROOT/'selected-case-image-verification.json',check)
args=[sys.executable,'-B',str(REPO/'tools/tempoevo-docker/prepare_selected.py'),'--root',str(ROOT/'selection-seeds-v2'),'--selection-file',str(ROOT/'training_70_cases.csv'),'--swe-tempoc-root',str(bench),'--evaluation-split',str(REPO/'cases/split.json'),'--evaluation-purpose','training_replay','--solver-image',plan['backend']['solver_image'],'--grader-image',plan['backend']['grader_image'],'--binary',plan['binary'],'--model-config',str(ROOT/'model-profiles.json'),'--model-profile','sol61-medium','--store',str(ROOT/'experience-library'),'--memory-snapshot',str(ROOT/'memory-snapshot.json'),'--mode','testing','--condition','structured','--retrieval-profile','business-source-v1','--limit','70']
write(ROOT/'seed-command.json',args)
with (ROOT/'prepare-seeds-v2.log').open('w') as log:subprocess.run(args,cwd=REPO,stdout=log,stderr=subprocess.STDOUT,check=True)
subprocess.run([sys.executable,'-B',str(ROOT/'validate.py')],cwd=REPO,check=True)
