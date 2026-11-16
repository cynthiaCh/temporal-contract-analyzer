import json,tempfile,unittest,hashlib
from pathlib import Path
from temporal_contract_analyzer import evaluation_split as split
from temporal_contract_analyzer.core import EvidenceError

class IncrementalSplitTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.selection=self.root/'selection.csv';self.selection.write_text('frozen selection\n');self.registry=self.root/'split.json'
  self.value=dict(schema_version='tempoevo-incremental-split-v1',selection_file=str(self.selection),selection_sha256=hashlib.sha256(self.selection.read_bytes()).hexdigest(),training_case_ids=['train'+str(x) for x in range(70)],testing_case_ids=['test'+str(x) for x in range(30)],independence={'unseen':False},testing_policy={'gold':'final_only'})
  self.write()
 def write(self):self.registry.write_text(json.dumps(self.value))
 def config(self,cid,mode):return dict(task_id=cid,mode=mode,evaluation_split_file=str(self.registry))
 def test_roles_are_enforced_in_both_directions(self):
  self.assertEqual(split.enforce(self.config('train0','learning'))['role'],'training')
  self.assertEqual(split.enforce(self.config('test0','testing'))['role'],'testing')
  for cid,mode in [('test0','learning'),('train0','testing')]:
   with self.assertRaises(EvidenceError):split.enforce(self.config(cid,mode))
 def test_explicit_registry_refuses_missing_or_unknown_case(self):
  with self.assertRaises(EvidenceError):split.enforce(self.config('unknown','learning'))
  self.registry.unlink()
  with self.assertRaises(EvidenceError):split.enforce(self.config('train0','learning'))
 def test_frozen_registry_and_selection_cannot_drift(self):
  cfg=self.config('test0','testing');cfg['evaluation_split']=split.enforce(cfg)
  self.value['independence']['unseen']=True;self.write()
  with self.assertRaises(EvidenceError):split.enforce(cfg)
  self.selection.write_text('changed')
  with self.assertRaises(EvidenceError):split.enforce(self.config('test0','testing'))
 def test_duplicate_ids_or_wrong_denominator_rejected(self):
  self.value['testing_case_ids'][0]='train0';self.write()
  with self.assertRaises(EvidenceError):split.enforce(self.config('train0','learning'))
 def test_legacy_registry_still_works(self):
  self.assertEqual(split.assignment('draft-autosave-handoff-vanilla-port-react')['role'],'training')

if __name__=='__main__':unittest.main()
