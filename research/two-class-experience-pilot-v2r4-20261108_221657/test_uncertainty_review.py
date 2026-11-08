import json,unittest
from pathlib import Path
from toolflow import validate_analysis,route,canonical,digest
from test_structured_pipeline import fixture

class UncertaintyReview(unittest.TestCase):
 def test_real_complete_output_is_not_rejected_for_non_exhaustiveness(self):
  r3=Path(__file__).resolve().parent.parent/'two-class-experience-pilot-v2r3-20261108_221141'
  a=json.loads((r3/'runs/D1-preanalysis-v2r3/archive/raw-answer.txt').read_text());root=r3/'materials/D1/candidate'
  src={str(p.relative_to(root)):p.read_text() for p in root.rglob('*') if p.is_file() and p.suffix in ['.md','.js']};src['TASK']=(r3/'materials/D1/task.md').read_text()
  self.assertTrue(a['consistency']['unknowns']);self.assertFalse(a['consistency']['conflicts'])
  self.assertIsNone(validate_analysis(a,src))
 def test_core_policy_unknown_in_veto_still_blocks(self):
  a=fixture();src={'src/unit.py':'shared_value = 1'};task='fixture task'
  review={'contract_sha256':digest(a['contract']),'task_sha256':digest(task),'sources_sha256':digest(canonical(src)),'reviewer':'execution_agent_visible_input_only','approved':False,'conflicts':[],'unknowns':['actual persistence policy unresolved'],'evidence':a['evidence'],'findings':[]}
  self.assertEqual(route(a,src,[],task=task,review=review)['reason'],'unresolved_semantic_conflict')
 def test_explicit_model_conflict_still_blocks(self):
  a=fixture();a['consistency']['conflicts']=['incompatible requirements'];self.assertEqual(validate_analysis(a,{}),'unbound_semantic_claim')

if __name__=='__main__':unittest.main()
