import json,tempfile,unittest
from pathlib import Path
import runner
A=Path(__file__).resolve().parent

class SourceProof(unittest.TestCase):
 def test_actual_v2_combined_cat_proves_all_seven_sources(self):
  root=A.parent/'transfer-progress-one-pair-pilot-v2a-20261109_092536/runs/session-01/archive'
  events=[json.loads(l) for l in (root/'events.jsonl').read_text().splitlines()]
  proofs=runner.source_proof(events,root/'input/original')
  self.assertEqual(len({p['source'] for p in proofs}),7)
  self.assertTrue(all(p['proof_kind']=='complete_body_from_nonzero_read' for p in proofs))
 def test_nonzero_read_requires_full_file_not_just_three_lines(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);body='first_complete_evidence_line = 1\nsecond_complete_evidence_line = 2\nthird_complete_evidence_line = 3\nfourth_complete_evidence_line = 4\n'
   (root/'unit.py').write_text(body)
   def events(text,cmd):return [{'type':'item.completed','item':{'type':'command_execution','exit_code':1,'command':cmd,'aggregated_output':text}}]
   self.assertEqual(runner.source_proof(events(''.join(body.splitlines(True)[:3]),'cat missing unit.py'),root),[])
   self.assertTrue(runner.source_proof(events(body,'cat missing unit.py'),root))
   self.assertEqual(runner.source_proof(events(body,'echo source_body'),root),[])
   self.assertEqual(runner.source_proof(events('', 'cat missing unit.py'),root),[])
 def test_input_freeze_excludes_mutable_journal_and_controller_log(self):
  from evolve import frozen_input_files
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   for name in ['candidate.py','actual-schedule.json','stop.json','controller.log','initial-freeze.json']:(root/name).write_text('fixture')
   frozen=frozen_input_files(root)
   self.assertEqual(set(frozen),{str(root/'candidate.py')})
   (root/'actual-schedule.json').write_text('expected dispatch update')
   (root/'controller.log').write_text('new progress')
   self.assertEqual(frozen,frozen_input_files(root))

if __name__=='__main__':unittest.main(verbosity=2)
