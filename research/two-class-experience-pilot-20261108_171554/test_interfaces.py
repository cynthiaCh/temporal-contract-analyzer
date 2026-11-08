import copy
import json
import unittest
from interfaces import digest, route, differences, visible_input


class OfflineInterfaces(unittest.TestCase):
    def setUp(self):
        self.sources = {'source.py': 'shared work\nretired view\n'}
        self.analysis = {'primary_class': 'synthetic', 'facts': [
            {'predicate': 'shared', 'state': 'known', 'evidence': {
                'file': 'source.py', 'line': 1, 'quote': 'shared work'}}]}
        self.entry = {'text': 'Synthetic fixture only.', 'version': 1,
                      'primary_class': 'synthetic', 'requires': ['shared'], 'excludes': []}
        self.entry['sha256'] = digest(json.dumps(self.entry, ensure_ascii=False, sort_keys=True))

    def run_route(self, library=None):
        return route(self.analysis, [self.entry] if library is None else library,
                     ['synthetic'], self.sources)

    def test_match(self):
        self.assertEqual(self.run_route()['condition'], 'ROUTED')

    def test_unknown(self):
        self.analysis['primary_class'] = 'unknown'
        self.assertEqual(self.run_route()['reason'], 'unknown_class')

    def test_empty(self):
        self.assertEqual(self.run_route([])['reason'], 'empty_class')

    def test_missing(self):
        self.analysis['facts'] = []
        self.assertEqual(self.run_route()['condition'], 'AUTO')

    def test_contradiction(self):
        self.analysis['facts'][0]['state'] = 'contradicted'
        self.assertEqual(self.run_route()['condition'], 'AUTO')

    def test_conflict(self):
        self.assertEqual(self.run_route([self.entry, copy.deepcopy(self.entry)])['reason'], 'unresolved_conflict')

    def test_tampering(self):
        self.entry['text'] += 'changed'
        self.assertEqual(self.run_route()['reason'], 'digest_mismatch')

    def test_metadata(self):
        self.analysis['case_id'] = 'invisible'
        self.assertEqual(self.run_route()['reason'], 'unexpected_analysis_metadata')
        self.assertEqual(set(visible_input('task', self.sources, [])), {'task', 'sources', 'ast'})

    def test_bad_evidence(self):
        self.analysis['facts'][0]['evidence']['quote'] = 'imagined mechanism'
        self.assertEqual(self.run_route()['reason'], 'unverified_fact')

    def test_feedback(self):
        result = differences({'a': False, 'b': True}, {'a': True, 'b': False},
                             {'a': True, 'b': True, 'c': True})
        for key in ('improvements', 'regressions', 'existing_successes', 'unknown'):
            self.assertEqual(len(result[key]), 1)
        self.assertEqual(result['explanations'], [])

    def test_exclusion_must_be_resolved_absent(self):
        self.entry['excludes'] = ['retired']
        self.entry.pop('sha256')
        self.entry['sha256'] = digest(json.dumps(self.entry, ensure_ascii=False, sort_keys=True))
        self.assertEqual(self.run_route()['condition'], 'AUTO')
        fact = {'predicate': 'retired', 'state': 'known', 'evidence': {
            'file': 'source.py', 'line': 2, 'quote': 'retired view'}}
        self.analysis['facts'].append(fact)
        self.assertEqual(self.run_route()['condition'], 'AUTO')
        fact['state'] = 'contradicted'
        self.assertEqual(self.run_route()['condition'], 'ROUTED')

    def test_applicability_tampering(self):
        self.entry['requires'] = ['other']
        self.assertEqual(self.run_route()['reason'], 'digest_mismatch')

    def test_fact_conflict(self):
        other = copy.deepcopy(self.analysis['facts'][0])
        other['state'] = 'contradicted'
        self.analysis['facts'].append(other)
        self.assertEqual(self.run_route()['reason'], 'conflicting_facts')


if __name__ == '__main__':
    unittest.main()
