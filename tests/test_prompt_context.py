import unittest
from copy import deepcopy
from temporal_contract_analyzer.prompt_context import compact,MAX_CHARS
from temporal_contract_analyzer.core import canonical
from temporal_contract_analyzer.experience_routing import analysis_prompt
class PromptContextTests(unittest.TestCase):
 def test_small_payload_unchanged(self):
  p=dict(task='task',sources={'a.py':'value=1'});value,report=compact(p);self.assertEqual(value,p);self.assertFalse(report['compacted'])
 def test_large_payload_is_indexed_and_original_evidence_not_mutated(self):
  p=dict(task='Implement AsyncSubject clear',sources={'src/workflow.py':'value=1','rxjs/src/internal/AsyncSubject.ts':'export class AsyncSubject {}','huge.ts':'x'*1200000},trajectory=[dict(candidate_sources={'huge.ts':'y'*1200000})]);old=deepcopy(p)
  value,report=compact(p);self.assertEqual(p,old);self.assertTrue(report['compacted']);self.assertLessEqual(len(canonical(value)),MAX_CHARS)
  self.assertEqual(value['sources']['src/workflow.py'],'value=1');self.assertNotIn('huge.ts',value['sources']);self.assertTrue(any(z['path']=='huge.ts' for z in report['indexes'][0]['files']))
 def test_routing_does_not_duplicate_public_source_bodies(self):
  prompt=analysis_prompt('task',{'main.py':'unique_body_that_should_only_appear_once'},None,embed_sources=False)
  self.assertNotIn('unique_body_that_should_only_appear_once',prompt);self.assertIn('taxonomy',prompt)
if __name__=='__main__':unittest.main()
