"""Offline re-admission after a proven read-evidence false negative; no LLM."""
import json,sys,time
from pathlib import Path
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A));sys.dont_write_bytecode=True
import runner
from archive import save,sha
from citations import normalize
from toolflow import validate_analysis
def read(p):return json.loads(Path(p).read_text())
def main():
 assert not (A/'actual-schedule.json').exists()
 root=A/'runs/session-01/archive';old=read(root/'receipt.json');case=read(A/'cases.json')[0]
 assert old['infrastructure_valid'] and old['output_format_valid'] and old['preanalysis_valid'] is False
 assert old['preanalysis_error']=="ValueError('source body not read')"
 events=[json.loads(l) for l in (root/'events.jsonl').read_text().splitlines()]
 proofs=runner.source_proof(events,root/'input/original');assert len({p['source'] for p in proofs})==7
 assert all(p['proof_kind']=='complete_body_from_nonzero_read' for p in proofs)
 assert runner.backend.hashes(root/'input/original')==case['candidate_files']
 assert sha(root/'input/task.md')==case['task_sha256']
 src={str(p.relative_to(root/'input/original')):p.read_text() for p in (root/'input/original').rglob('*') if p.is_file() and p.suffix in ['.js','.py','.md']}
 src['TASK']=(root/'input/task.md').read_text()
 raw=read(root/'raw-analysis-object.json');assert raw==json.loads((root/'raw-answer.txt').read_text())
 analysis,derivation=normalize(raw,src,read(A/'extraction.schema.json'),case['source_catalog_sha256'])
 assert validate_analysis(analysis,src) is None
 save(A/'admission-recheck/analysis.json',analysis);save(A/'admission-recheck/derivation.json',derivation)
 save(A/'admission-recheck/original-receipt.json',old)
 corrected={**old,'preanalysis_valid':True,'preanalysis_error':None,'prior_preanalysis_error':old['preanalysis_error'],
  'source_body_proofs':proofs,'reused_model_session':True,'new_model_invocations':0,
  'admission_origin':'offline correction of complete-source-read false negative; original receipt remains unchanged',
  'admission_recheck':'admission-recheck/corrected-receipt.json'}
 save(A/'admission-recheck/corrected-receipt.json',corrected)
 save(A/'admission-recheck/audit.json',{'time':time.time(),'original_status_preserved':True,'new_model_calls':0,
  'raw_object_sha256':sha(root/'raw-analysis-object.json'),'raw_response_sha256':sha(root/'raw-answer.txt'),
  'proof_policy':'For nonzero read commands require complete exact current file body, named in the read command, with >=3 substantial source lines; never infer reads from exit code alone.',
  'seven_full_files_verified':True,'model_contract_category_claims_and_fact_states_changed':False,
  'semantic_review_still_required':True})
 save(A/'actual-schedule.json',[corrected]);save(A/'derived/D/analysis.json',analysis)
 (A/'derived/D/automatic-contract.md').write_text(analysis['contract'])
 save(A/'derived/D/provenance.json',{'origin':'reused exact valid raw v2 model output; program-derived citation fields and offline source-read admission correction',
  'source':str(root/'raw-answer.txt'),'source_sha256':sha(root/'raw-answer.txt'),'new_model_calls':0,'derivation':'admission-recheck/derivation.json'})
 protocol=read(A/'protocol.json');protocol.update(version='one-pair-v2a-source-read-proof-correction',
   v2_original_stop_preserved=True,v2_preanalysis_reused_without_new_call=True,
   maximum_sessions_including_reused=11,maximum_requests_including_reused=228,
   source_read_gate='Exit0: existing line proof; nonzero read: full current body plus command filename and >=3 source lines required.')
 save(A/'protocol.json',protocol)
 print('Offline re-admission PASS: exact v2 output, seven full source bodies; no new model request')
if __name__=='__main__':main()
