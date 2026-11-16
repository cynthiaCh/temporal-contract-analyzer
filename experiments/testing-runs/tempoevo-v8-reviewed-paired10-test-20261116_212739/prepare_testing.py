"""Trusted zero-model calibration and preparation of frozen A/B testing."""
import csv,hashlib,json,shutil,subprocess,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parent
REPO=Path('/home/sribd/Downloads/wangshu/temporal-contract-analyzer')
sys.path.insert(0,str(REPO))
from temporal_contract_analyzer.swe_tempoc_inputs import case_input
from temporal_contract_analyzer.tempoevo_backend import NativeV4Backend
args=json.loads((ROOT/'prepare-A.json').read_text())
def option(name):return args[args.index(name)+1]
bench=Path(option('--swe-tempoc-root'));image=option('--grader-image')
rows=list(csv.DictReader(Path(option('--selection-file')).open(encoding='utf-8-sig')))
assert len(rows)==10 and all(r['split']=='testing' for r in rows)
roster={r['case_id']:r for r in json.loads((bench/'benchmark/swe-tempoc.json').read_text())['cases']}
files={}
for row in rows:
 for p in (bench/roster[row['case_id']]['manifest']).parent.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts:files[p.relative_to(bench).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
code="import sys,json,hashlib;from pathlib import Path;f=json.load(sys.stdin);bad=[k for k,v in f.items() if not (Path('/opt/swe-tempoc')/k).is_file() or hashlib.sha256((Path('/opt/swe-tempoc')/k).read_bytes()).hexdigest()!=v];print(json.dumps(dict(files_checked=len(f),mismatches=bad)))"
check=subprocess.run(['docker','run','--rm','-i','--pull=never','--network','none','--read-only','--entrypoint','python3',image,'-B','-c',code],input=json.dumps(files),capture_output=True,text=True,check=True)
result=json.loads(check.stdout);(ROOT/'selected-case-image-verification.json').write_text(json.dumps(result,indent=2)+'\n');assert not result['mismatches'],result

def calibrate(row):
 cid=row['case_id'];r=ROOT/'calibration'/cid;r.mkdir(parents=True)
 c=case_input(cid,bench);manifest=c['case_record']['manifest'];m=json.loads((bench/manifest).read_text())
 (r/'case.json').write_text(json.dumps(dict(manifest=manifest))+'\n')
 ev=dict(image=image,inputs={str(r/'case.json'):'/checks/case.json',str(REPO/'tools/tempoevo-docker/gold.py'):'/checks/gold.py'},command=['/usr/bin/python3','/checks/gold.py'],seconds=180)
 controls=[]
 for name,overlay in [('original',None),('reference',m['references']['bounded']),('negative',m['mutants'][0])]:
  subject=r/name;shutil.copytree(c['candidate'],subject)
  if overlay:shutil.copytree((bench/manifest).parent/overlay,subject,dirs_exist_ok=True)
  output=r/'checks'/name;output.mkdir(parents=True)
  raw=NativeV4Backend({}).evaluate('gold',dict(candidate=str(subject),evaluator=ev),output)
  (output/'result.json').write_text(json.dumps(raw,indent=2)+'\n')
  item=dict(control=name,valid=raw.get('valid'),passed=raw.get('passed'),verdict=raw.get('verdict'));controls.append(item)
  assert item['valid'] is True and item['passed']==(name=='reference'),(cid,item)
 result=dict(case_id=cid,controls=controls);print(json.dumps(result),flush=True);return result
with ThreadPoolExecutor(max_workers=2) as pool:calibration=list(pool.map(calibrate,rows))
(ROOT/'calibration.json').write_text(json.dumps(dict(valid=True,cases=10,controls=30,results=calibration),indent=2)+'\n')

def prepare(label):
 command=json.loads((ROOT/('prepare-'+label+'.json')).read_text())
 with (ROOT/('prepare-'+label+'.log')).open('w') as log:process=subprocess.run(command,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
 assert process.returncode==0,(label,process.returncode)
 progress=json.loads((Path(command[command.index('--root')+1])/'progress.json').read_text());assert len(progress)==10 and all(r['status']=='prepared' for r in progress)
 print(json.dumps(dict(arm=label,prepared=10,model_calls=0)),flush=True)
with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(prepare,['A','B']))
print(json.dumps(dict(valid=True,prepared=20,calibration_controls=30,model_calls=0)),flush=True)
