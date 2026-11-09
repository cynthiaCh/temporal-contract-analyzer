"""Derived fixtures only; historical output/rejection remains unmodified."""
import copy,json,unittest
from pathlib import Path
from locked_scope import metadata,revision_schema,assemble
from schema_validator import validate
from toolflow import PREDICATES
from handoff import render
A=Path(__file__).resolve().parent
P=A.parent/'transfer-progress-one-pair-pilot-v2a-20261109_092536'
Q=A.parent/'transfer-progress-evolution-20261109_100402'

class LockedScope(unittest.TestCase):
 def setUp(self):
  self.parent=json.loads((P/'development/experience-object.json').read_text())
  self.rejected=json.loads((Q/'development/experience-object.json').read_text())
  self.ledger=json.loads((A/'training/evidence-ledger.json').read_text())
  self.locked=metadata(self.parent)
  self.fixture={k:copy.deepcopy(self.rejected[k]) for k in ['rules','unresolved']}
 def test_old_full_output_rejected_instead_of_stripping_metadata(self):
  with self.assertRaises(ValueError):validate(self.rejected,revision_schema(self.ledger,PREDICATES))
 def test_model_cannot_add_or_overwrite_any_locked_field(self):
  for k in self.locked:
   v=copy.deepcopy(self.fixture);v[k]=copy.deepcopy(self.rejected[k])
   with self.assertRaises(ValueError):assemble(v,self.locked,self.ledger,PREDICATES)
 def test_deterministic_merge_render_and_no_input_mutation(self):
  before=copy.deepcopy((self.fixture,self.locked))
  one,proof=assemble(self.fixture,self.locked,self.ledger,PREDICATES)
  two,_=assemble(self.fixture,self.locked,self.ledger,PREDICATES)
  self.assertEqual(one,two);self.assertEqual(render(one),render(two))
  self.assertEqual(metadata(one),self.locked);self.assertEqual(one['rules'],self.fixture['rules'])
  self.assertEqual((self.fixture,self.locked),before);self.assertTrue(proof['no_policy_or_evidence_synthesis'])
  self.assertNotIn('boundary_persistence',one['requires'])
 def test_unsupported_new_rule_evidence_still_rejected(self):
  v=copy.deepcopy(self.fixture);v['rules'][0]['support']=['invented']
  with self.assertRaises(ValueError):assemble(v,self.locked,self.ledger,PREDICATES)
 def test_unknown_in_locked_prerequisite_does_not_pass(self):
  v=copy.deepcopy(self.locked);v['applicability'][0]['status']='unknown'
  with self.assertRaises(ValueError):assemble(self.fixture,v,self.ledger,PREDICATES)
 def test_incomplete_model_output_not_completed(self):
  for v in [{},{'rules':self.fixture['rules']},{'unresolved':[]},None]:
   with self.assertRaises(ValueError):assemble(v,self.locked,self.ledger,PREDICATES)
 def test_missing_preservation_and_counterevidence_still_rejected(self):
  for key in ['preserve','counterevidence']:
   v=copy.deepcopy(self.fixture)
   for r in v['rules']:r[key]=[]
   with self.assertRaises(ValueError):assemble(v,self.locked,self.ledger,PREDICATES)

if __name__=='__main__':unittest.main()
