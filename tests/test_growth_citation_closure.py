"""Pure citation-validation checks for the independent closure adapter."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'experiments/experience-growth/train70-test30-20261118'
sys.path.insert(0,str(HERE))
import close_citation_invalid as closure
from temporal_contract_analyzer.delegated_review import REVIEW_SCHEMA

class CitationClosureTests(unittest.TestCase):
    def check_quote(self,quote):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/'candidate';folder.mkdir()
            output=dict(decision='accept',reason='supported',rules=[dict(rule_id='R01',supported=True,reason='source',evidence=[dict(file='TASK',quote=quote)])])
            (folder/'result.json').write_text(json.dumps(dict(valid=True,output=output)))
            payload=dict(schema=REVIEW_SCHEMA,public_context=dict(task='The original public task.',sources={}),candidate=dict(rules=[dict(id='R01')]))
            (folder/'input.json').write_text(json.dumps(payload))
            return closure.citation_failure(folder/'result.json')
    def test_valid_original_quote_is_not_closed(self):
        self.assertIsNone(self.check_quote('original public task'))
    def test_invented_quote_replays_strict_rejection(self):
        failure=self.check_quote('invented requirement')
        self.assertEqual(failure['layer'],'frozen_ai_review_source_evidence')
        self.assertTrue(failure['original_validator_reproduced'])
        self.assertEqual(failure['rejected_rules'][0]['rule_id'],'R01')
if __name__=='__main__':unittest.main()
