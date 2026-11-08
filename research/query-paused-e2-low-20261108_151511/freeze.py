"""Two-stage immutable freeze; no model or scoring execution."""
import sys,json,time
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A))
import runner as r
from archive import save,sha
read=lambda p:json.loads(Path(p).read_text())
stage=sys.argv[1];assert stage in ['reflection','maintenance'];assert not (A/'runs').exists();assert not (A/'stop.json').exists()
S=Path(read(A/'sources.json')['source_followup']);assert read(A/'offline-validation.json')['status']=='PASS'
r.verify(read(A/'protected-files.json'))
if stage=='reflection':
 assert not (A/'reflection-protocol.json').exists() and not (A/'training-runs').exists()
else:
 assert not (A/'protocol.json').exists();assert not read(A/'experience-review.json')['manual_content_review_pending']
 assert sha(A/'reflection-protocol.json')==(A/'reflection-protocol.sha256').read_text().strip();r.verify(read(A/'reflection-protocol.json')['files'])
 e=(A/'NEW_EXPERIENCE.md').read_text();assert e==(A/'training-runs/reflection/archive/experience.md').read_text()
 (A/'prompts/AUTO_EXP.md').write_text((A/'prompts/AUTO.md').read_text()+'\n\n'+e)
 assert (A/'prompts/AUTO.md').read_bytes()==(S/'prompts/AUTO.md').read_bytes()
 save(A/'experience-freeze.json',{'candidate':'E2','unmodified_raw_report':True,'before_any_maintenance':True,'files':{str(p):sha(p) for p in [A/'NEW_EXPERIENCE.md',A/'prompts/AUTO.md',A/'prompts/AUTO_EXP.md',A/'training-runs/reflection/archive/experience.md',A/'training-runs/reflection/archive/ARTIFACTS.sha256']}})
files={str(p):sha(p) for p in A.rglob('*') if p.is_file() and 'offline' not in p.relative_to(A).parts and p.name not in ['reflection-execution.log']}
files.update(read(S/'protocol.json')['files']);r.verify(files)
p=A/('reflection-protocol.json' if stage=='reflection' else 'protocol.json')
save(p,{'stage':stage,'frozen_at':time.time(),'files':files,'before_stage_model_calls':True,'max_stage_sessions':1 if stage=='reflection' else 6,'max_stage_requests':12 if stage=='reflection' else 144,'single_candidate':True,'analysis_rules':'PLAN.md','schedule':'schedule.json'})
p.with_suffix('.sha256').write_text(sha(p)+'\n');print(stage,'FROZEN',sha(p),'files',len(files))
