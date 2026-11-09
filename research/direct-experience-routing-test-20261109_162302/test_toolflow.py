import copy
import json
import unittest
from toolflow import (PREDICATES, validate_analysis, freeze_entry, route, maintenance_prompt,
                      feedback, public_material, extraction_prompt, canonical, digest)


class ToolflowTests(unittest.TestCase):
    def setUp(self):
        self.sources = {'src/unit.py': 'shared state\nper attempt\n'}
        proof = [{'file': 'src/unit.py', 'line': 1, 'quote': 'shared state'}]
        self.analysis = {'contract': 'fixture', 'primary_class': 'T4', 'secondary_tags': [],
                         'evidence': proof, 'facts': [{'predicate': 'shared_lifetime', 'state': 'known', 'evidence': proof}]}
        self.task='Repair a reported defect while preserving shared state.'
        self.review={'contract_sha256':digest(self.analysis['contract']),'task_sha256':digest(self.task),
                     'sources_sha256':digest(canonical(self.sources)),'reviewer':'execution_agent_visible_input_only',
                     'approved':True,'conflicts':[],'unknowns':[],'evidence':proof,'findings':[]}
        self.entry = freeze_entry({'text': 'synthetic experience', 'requires': ['shared_lifetime'], 'excludes': []}, 'T4')

    def result(self, library=None):
        return route(self.analysis, self.sources, [self.entry] if library is None else library, task=self.task, review=self.review)

    def test_positive(self):
        self.assertEqual(self.result()['condition'], 'ROUTED')

    def test_unknown(self):
        self.analysis['primary_class'] = 'unknown'
        self.assertEqual(self.result()['reason'], 'unknown_class')

    def test_empty(self):
        self.assertEqual(self.result([])['reason'], 'empty_library')

    def test_missing(self):
        self.analysis['facts'] = []
        self.assertEqual(self.result()['condition'], 'AUTO')

    def test_contradictory(self):
        self.analysis['facts'][0]['state'] = 'contradicted'
        self.assertEqual(self.result()['condition'], 'AUTO')

    def test_duplicate_fact(self):
        self.analysis['facts'].append(copy.deepcopy(self.analysis['facts'][0]))
        self.assertEqual(self.result()['reason'], 'duplicate_or_conflicting_fact')

    def test_conflict(self):
        self.assertEqual(self.result([self.entry, copy.deepcopy(self.entry)])['reason'], 'unresolved_multiple_experience_conflict')

    def test_text_tampering(self):
        self.entry['text'] += 'tampered'
        self.assertEqual(self.result()['reason'], 'digest_tampering')

    def test_applicability_tampering(self):
        self.entry['requires'] = ['observer_lifetime']
        self.assertEqual(self.result()['reason'], 'digest_tampering')

    def test_evidence_tampering(self):
        self.analysis['evidence'][0]['quote'] = 'not present'
        self.assertEqual(self.result()['reason'], 'primary_class_without_source_evidence')

    def test_invisible_analysis_metadata(self):
        for key in ['case_id', 'cluster', 'historical_score', 'reference_patch']:
            a = dict(self.analysis, **{key: 'secret'})
            self.assertEqual(route(a, self.sources, [self.entry])['condition'], 'AUTO')

    def test_invisible_registry_metadata(self):
        self.entry['source_case'] = 'secret'
        self.assertEqual(self.result()['reason'], 'invisible_or_invalid_registry_fields')

    def test_exclusions_unknown_then_absent(self):
        self.entry = freeze_entry({'text': 'fixture', 'requires': ['shared_lifetime'],
                                   'excludes': ['different_ownership_policy']}, 'T4')
        self.assertEqual(self.result()['condition'], 'AUTO')
        self.analysis['facts'].append({'predicate': 'different_ownership_policy', 'state': 'contradicted',
                                       'evidence': self.analysis['evidence']})
        self.assertEqual(self.result()['condition'], 'ROUTED')

    def test_ab_identical_on_fallback_and_raw_on_hit(self):
        a = maintenance_prompt('task', 'contract')
        self.assertEqual(a, maintenance_prompt('task', 'contract', None))
        b = maintenance_prompt('task', 'contract', self.entry['text'])
        self.assertTrue(b.endswith(self.entry['text']))
        self.assertNotIn('primary_class', a)

    def test_public_input_no_management(self):
        p = public_material('task', self.sources, {}, [])
        self.assertEqual(set(p), {'task', 'sources', 'AST', 'taxonomy', 'predicates'})
        with self.assertRaises(TypeError):
            public_material('task', self.sources, {}, [], case_id='secret')
        self.assertNotIn('source_case', extraction_prompt(p))

    def test_generic_feedback(self):
        original = {'observed_effects': {'one': False, 'two': True}}
        repaired = {'verdict': 'FAIL', 'observed_effects': {'one': True, 'two': False}, 'schedules': {}}
        standards = [{'effect': key, 'expected': True, 'description': key} for key in ['one', 'two', 'missing']]
        row = feedback(original, [repaired], standards)['runs'][0]
        self.assertEqual(len(row['improvements']), 1)
        self.assertEqual(len(row['regressions']), 1)
        self.assertEqual(len(row['original_successes']), 1)
        self.assertEqual(len(row['unknown']), 1)


if __name__ == '__main__':
    unittest.main()
