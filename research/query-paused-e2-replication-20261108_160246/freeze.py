"""One immutable replication freeze after all offline checks and before any formal call."""
import sys,json,time
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A))
import runner as r
from archive import save,sha
read=lambda p:json.loads(Path(p).read_text())
assert not (A/'protocol.json').exists() and not (A/'runs').exists()
assert read(A/'offline-validation.json')['status']=='PASS'
assert read(A/'host-config-isolation.json')['offline_proof']=='PASS' and not read(A/'host-config-isolation.json')['proof_pending']
S=Path(read(A/'sources.json')['sole_source']);r.verify(read(A/'protected-files.json'))
assert (A/'prompts/AUTO.md').read_bytes()==(S/'prompts/AUTO.md').read_bytes();assert (A/'prompts/AUTO_EXP.md').read_bytes()==(S/'prompts/AUTO_EXP.md').read_bytes()
assert sha(A/'NEW_EXPERIENCE.md')=='85c058e4065322155ac3ae3a8486df020da62745c3c64f25db5fd1b7570904c1'
save(A/'experience-freeze.json',{'candidate':'source frozen E2','not_generated_this_batch':True,'unmodified':True,'before_any_maintenance':True,'source':str(S/'experience-freeze.json'),'files':{str(p):sha(p) for p in [A/'NEW_EXPERIENCE.md',A/'prompts/AUTO.md',A/'prompts/AUTO_EXP.md',A/'automatic-contract.md']}})
files={str(p):sha(p) for p in A.rglob('*') if p.is_file()}
files.update(read(S/'protocol.json')['files']);r.verify(files)
save(A/'protocol.json',{'name':'frozen-E2-same-case-independent-replication','frozen_at':time.time(),'before_first_model_call':True,'files':files,'analysis_rules':'PLAN.md','schedule_seed':2026110803,'max_sessions':6,'max_requests':144,'max_session_seconds_total':3600,'max_external_scores':6,'no_training_or_experience_revision':True})
(A/'protocol.sha256').write_text(sha(A/'protocol.json')+'\n');print('FROZEN',sha(A/'protocol.json'),'files',len(files),'real model/scorer calls so far: 0')
