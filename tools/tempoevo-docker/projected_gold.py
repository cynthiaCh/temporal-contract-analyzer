"""Restore omitted ORIGINAL public files for derived RxJS cases; unchanged probe."""
import hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,'/opt/swe-tempoc')
from swe_tempoc import classify
cfg=json.loads(Path('/checks/case.json').read_text());case=(Path('/opt/swe-tempoc')/cfg['manifest']).parent;m=json.loads((case/'case.json').read_text());projection=cfg['projection'];candidate=Path(sys.argv[-1])
with tempfile.TemporaryDirectory(prefix='tca-derived-public-') as tmp:
 full=Path(tmp)/'repository';shutil.copytree(case/'base',full)
 for name,digest in projection['files_sha256'].items():
  rel=Path(name)
  if rel.is_absolute() or '..' in rel.parts or hashlib.sha256((full/rel).read_bytes()).hexdigest()!=digest:raise ValueError('Frozen public projection identity mismatch')
  if not (candidate/rel).exists():(full/rel).unlink()
 for p in candidate.rglob('*'):
  if p.is_symlink():raise ValueError('Candidate symlink')
  if p.is_file():
   dest=full/p.relative_to(candidate);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
 p=subprocess.run(['/opt/swe-tempoc/.swe-tempoc/toolchains/node-v16.20.2/bin/node',str(case/m['oracle']['probe']),str(full),'ungranted'],capture_output=True,text=True,timeout=270)
 sys.stderr.write(p.stderr);expected=[s['id'] for s in json.loads((case/m['oracle']['schedules']).read_text())['schedules']]
 result,report=classify(p.stdout,p.returncode,m['id'],expected);valid=result.get('valid_scored') is True
 print(json.dumps(dict(valid=valid,passed=valid and report['verdict']=='PASS',verdict=report['verdict'] if valid else None,full_score=report,error=result.get('error'))))
