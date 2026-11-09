"""Zero-model lexical coverage regressions; no fixture is new model evidence."""
import copy,json,unittest
from pathlib import Path
from citations import catalog
from qualifiers import cues,coverage,GUIDANCE
A=Path(__file__).resolve().parent

class QualifierTests(unittest.TestCase):
 def test_real_old_failure_is_flagged_without_repair_or_reapproval(self):
  rejection=json.loads((A/'historical-extraction/rejection.json').read_text())
  task=rejection['candidate_visible_task'];contract=rejection['raw_automatic_contract'];before=copy.deepcopy((task,contract))
  result=coverage(task,contract,catalog({'TASK':task}))
  self.assertTrue(any('live' in row['missing_literal_words'] for row in result['findings']))
  self.assertEqual((task,contract),before);self.assertFalse(result['contract_rewritten']);self.assertIsNone(result['automatic_validity_decision'])
 def test_cues_have_exact_current_source_provenance(self):
  task='Reject writes with an obsolete revision after replacement. Preserve valid writes.';cat=catalog({'TASK':task})
  for row in cues(task,cat):
   self.assertEqual(task[row['start_column']:row['end_column']],row['quote'])
   self.assertTrue(row['evidence_ids']);self.assertTrue(all(x in {r['id'] for r in cat['entries']} for x in row['evidence_ids']))
 def test_source_reordering_is_deterministic(self):
  task='Ignore notifications without an owner; preserve activity while mounted.'
  self.assertEqual(cues(task,catalog({'TASK':task,'x':'data'})),cues(task,catalog({'x':'data','TASK':task})))
 def test_no_cue_does_not_invent_conditions(self):
  self.assertEqual(cues('Keep the public interface.',catalog({'TASK':'Keep the public interface.'})),[])
 def test_equivalent_wording_is_not_automatically_rejected(self):
  task='Reject writes with an obsolete revision.'
  result=coverage(task,'Do not write using an outdated version.',catalog({'TASK':task}))
  self.assertTrue(result['findings']);self.assertIsNone(result['automatic_validity_decision'])
 def test_without_and_only_conditions_are_source_text_not_new_policy(self):
  task='Run only when ready, and skip output without permission.'
  result=cues(task,catalog({'TASK':task}));self.assertEqual([r['cue'] for r in result],['only when','without'])
 def test_missing_modifier_detected_on_synthetic_non_query_example(self):
  task='Repair publication with obsolete ownership after replacement.'
  result=coverage(task,'Never publish after replacement.',catalog({'TASK':task}))
  self.assertTrue(any('obsolete' in x['missing_literal_words'] for x in result['findings']))
 def test_guidance_has_no_case_mapping_or_query_specific_answer(self):
  for text in ['query-paused','signal','T4','cached-paused','must not invoke']:self.assertNotIn(text,GUIDANCE)

if __name__=='__main__':unittest.main()
