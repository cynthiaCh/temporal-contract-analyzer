"""Reuse exact calibrated cases; replace only citation schema/public instructions."""
import json,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A))
from archive import save,sha
from citations import catalog,schema,fingerprint,INSTRUCTIONS
from toolflow import PREDICATES
import runner

def read(p):return json.loads(Path(p).read_text())
def main():
 assert not (A/'prepared.json').exists()
 started=time.time();cases=read(A/'cases.json');legacy=read(A/'extraction.schema.json')
 for c in cases:
  alias=c['alias'];root=A/'materials'/alias/'candidate'
  assert runner.backend.hashes(root)==c['candidate_files']
  assert sha(A/'materials'/alias/'task.md')==c['task_sha256']
  assert runner.backend.hashes(Path(c['source_case'])/'oracle')==c['oracle_files']
  sources={str(p.relative_to(root)):p.read_text() for p in root.rglob('*') if p.is_file() and p.suffix in ['.md','.js','.py']}
  sources['TASK']=(A/'materials'/alias/'task.md').read_text()
  cat=catalog(sources);save(A/'materials'/alias/'source-catalog.json',cat)
  generated=schema(cat,legacy);save(A/'materials'/alias/'extraction.schema.json',generated)
  assert len(cat['entries'])*3<1000,'Use supported bounded enum subset; no unsupported schema escalation'
  c['extraction_schema']=str(A/'materials'/alias/'extraction.schema.json');c['source_catalog_sha256']=fingerprint(cat)
  ast=read(A/'materials'/alias/'ast.json')
  public={'TASK':sources['TASK'],'taxonomy':read(A/'taxonomy.json')['classes'],'predicates':PREDICATES,
          'AST':{'status':ast['status'],'summary':ast['summary'],'limitations':ast['limitations']},
          'source_catalog':cat}
  prompt=INSTRUCTIONS+json.dumps(public,ensure_ascii=False)
  assert all(case['case'] not in prompt for case in cases)
  (A/'materials'/alias/'preanalysis-prompt.md').write_text(prompt)
  for receipt_path in (A/'calibration'/alias).glob('*/receipt.json'):
   r=read(receipt_path);assert r['score_valid'] and r['oracle_files']==c['oracle_files']
   score=read(receipt_path.parent/'stdout.json');assert score['verdict']==r['verdict']
 save(A/'cases.json',cases)
 protocol=read(A/'audit-v1/protocol.json')
 protocol.update(version='one-pair-v2-source-span-ids',previous_batch='transfer-progress-one-pair-pilot-20261109_085552',
  previous_batch_remains_stopped=True,new_authorization='User fix; independent new batch, no disguised retry of v1.',
  evidence_conversion='Python maps exact source span IDs to file/line/quote; no model claim rewriting or old-output salvage',
  new_native_calibration_invocations=0,calibrations_reused=18)
 save(A/'protocol.json',protocol)
 save(A/'prepared.json',{'time':time.time(),'seconds':time.time()-started,'model_calls':0,'native_calibrations':0,'calibrations_reused':18})
 print('Prepared v2, source spans',[(c['alias'],len(read(A/'materials'/c['alias']/'source-catalog.json')['entries'])) for c in cases],flush=True)

if __name__=='__main__':main()
