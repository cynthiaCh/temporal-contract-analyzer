"""Freeze once after offline checks, before any authorized maintenance launch."""
import sys,json,time
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A))
from archive import save,sha
import runner as r
assert not (A/'protocol.json').exists() and not (A/'runs').exists()
assert json.loads((A/'offline-validation.json').read_text())['status']=='PASS'
r.verify(json.loads((A/'protected-files.json').read_text()))
files={str(p):sha(p) for p in A.rglob('*') if p.is_file() and 'offline' not in p.relative_to(A).parts}
# Exact historical dependencies, source oracle, CLI, global configuration remain frozen.
old=Path(json.loads((A/'sources.json').read_text())['source_batch'])
files.update(json.loads((old/'protocol.json').read_text())['files'])
r.verify(files)
save(A/'protocol.json',{'name':'frozen-experience-same-case-exploratory-followup','frozen_at':time.time(),'before_first_formal_call':True,'max_sessions':6,'max_requests':144,'files':files,'analysis_rules':'PLAN.md','schedule':'schedule.json','old_admission_unchanged':True,'new_admission_allows_local_regression':True})
(A/'protocol.sha256').write_text(sha(A/'protocol.json')+'\n')
print('FROZEN',sha(A/'protocol.json'),'files',len(files),'maintenance calls so far: 0')
