"""Offline regression tests. Synthetic candidates below are test fixtures only."""
import copy
import json
import unittest
from pathlib import Path
from handoff import (verify_ledger, assemble_payload, check_candidate,
                     object_digest, pointer, digest)
from feedback import feedback, checks

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text())


def fixture():
    # Structural unit fixture, not a learned candidate or admitted experience.
    return {'text': 'SYNTHETIC UNIT FIXTURE: preserve evidenced conditions.',
            'requires': ['shared_lifetime'], 'excludes': [], 'unresolved': [],
            'rules': [{'id': 'r1', 'quote': 'preserve evidenced conditions.',
                       'support': ['R-task'], 'conditions': ['F-ownership'],
                       'preserve': ['C-ownership', 'C-cached', 'C-events'],
                       'counterevidence': ['O-auto1-0', 'O-auto2-0', 'O-auto1-1', 'O-auto2-1'],
                       'counterevidence_resolution': 'Synthetic review fixture only.',
                       'causal_status': 'source_reasoning'}]}


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.ledger = load('evidence-ledger.json')

    def test_frozen_source_and_observation_anchors(self):
        self.assertEqual(len(verify_ledger(ROOT, self.ledger)), len(self.ledger['entries']))
        self.assertEqual(pointer({'a/b': [{'~': None}]}, '/a~1b/0/~0'), None)

    def test_source_digest_drift_rejected(self):
        self.ledger['files']['inputs/task.md']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'digest mismatch'):
            verify_ledger(ROOT, self.ledger)

    def test_quote_and_json_observation_tamper_rejected(self):
        for eid, key, value in [('F-ownership', 'quote', 'invented'),
                                ('O-original-0', 'value', {'passed': False})]:
            ledger = copy.deepcopy(self.ledger)
            next(e for e in ledger['entries'] if e['id'] == eid)['anchors'][0][key] = value
            with self.assertRaises(ValueError):
                verify_ledger(ROOT, ledger)

    def test_no_test_reference_or_prior_experience_in_payload(self):
        payload = assemble_payload(ROOT, self.ledger, load('feedback.json'))
        self.assertEqual({m['artifact'] for m in payload['materials']}, set(self.ledger['files']))
        self.assertFalse(any('audit/' in x for x in self.ledger['files']))
        for role in ['test_score', 'reference_patch', 'old_experience']:
            ledger = copy.deepcopy(self.ledger)
            ledger['files']['inputs/task.md']['role'] = role
            with self.assertRaisesRegex(ValueError, 'untrusted provenance'):
                assemble_payload(ROOT, ledger, load('feedback.json'))

    def test_injected_feedback_rejected(self):
        changed = load('feedback.json')
        changed['external_test_feedback'] = 'not allowed'
        with self.assertRaisesRegex(ValueError, 'feedback differs'):
            assemble_payload(ROOT, self.ledger, changed)

    def test_path_escape_rejected(self):
        self.ledger['files']['../escape'] = {'role': 'training_task', 'sha256': '0'*64}
        with self.assertRaisesRegex(ValueError, 'untrusted provenance'):
            verify_ledger(ROOT, self.ledger)

    def test_real_score_deltas_keep_improvements_and_regressions(self):
        result = load('feedback.json')
        for run in result['runs']:
            self.assertEqual([len(run[k]) for k in ['actual_successes', 'original_successes',
                                                   'retained_original_successes', 'improvements', 'regressions']],
                             [27, 21, 19, 8, 2])
            self.assertEqual(len(run['all_checks']), 75)
            self.assertEqual(len(run['failed_checks']), 7)

    def test_unknown_does_not_erase_original_success_or_become_failure(self):
        result = feedback({'observed_effects': {'x': True}}, [{}],
                          [{'effect': 'x', 'expected': True, 'description': 'fixture'}])['runs'][0]
        self.assertEqual(len(result['original_successes']), 1)
        self.assertEqual(len(result['unknown']), 1)
        self.assertEqual(result['regressions'], [])
        self.assertEqual(result['differences'], [])

    def test_both_check_collections_and_missing_schema(self):
        rows, unknown = checks({'schedules': {'x': {'checks': [{'passed': False}],
                                                   'assertions': [{'passed': True}]}, 'y': {}}})
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(unknown), 1)

    def test_fixture_never_auto_admitted(self):
        result = check_candidate(fixture(), self.ledger)
        self.assertTrue(result['structural_support_valid'])
        self.assertFalse(result['admitted'])
        self.assertEqual(result['semantic_status'], 'pending')

    def test_forged_evidence_and_unknown_applicability_rejected(self):
        for field, values in [('support', ['forged']), ('conditions', ['U-reflector']),
                               ('support', ['O-auto1-0']), ('support', ['H-regression'])]:
            candidate = fixture()
            candidate['rules'][0][field] = values
            with self.assertRaises(ValueError):
                check_candidate(candidate, self.ledger)

    def test_text_tamper_and_missing_preservation_rejected(self):
        candidate = fixture()
        candidate['text'] = 'different text'
        with self.assertRaises(ValueError):
            check_candidate(candidate, self.ledger)
        candidate = fixture()
        candidate['rules'][0]['preserve'] = ['C-events']
        with self.assertRaises(ValueError):
            check_candidate(candidate, self.ledger)

    def test_cause_upgrade_and_nested_json_string_rejected(self):
        candidate = fixture()
        candidate['rules'][0]['causal_status'] = 'verified_cause'
        with self.assertRaises(ValueError):
            check_candidate(candidate, self.ledger)
        with self.assertRaises(ValueError):
            check_candidate(json.dumps(fixture()), self.ledger)

    def test_known_counterevidence_cannot_be_dropped(self):
        candidate = fixture()
        candidate['rules'][0]['counterevidence'] = []
        with self.assertRaisesRegex(ValueError, 'counterevidence omitted'):
            check_candidate(candidate, self.ledger)

    def test_semantic_review_is_bound_and_cannot_admit_without_development(self):
        candidate = fixture()
        review = {'candidate_sha256': object_digest(candidate), 'ledger_sha256': object_digest(self.ledger),
                  'reviewer': 'execution_agent', 'rules': [{'id': 'r1', 'supported': False,
                                                          'evidence': ['R-task'], 'reason': 'Unit fixture has no established entailment.'}]}
        result = check_candidate(candidate, self.ledger, review)
        self.assertEqual(result['semantic_status'], 'rejected_by_execution_agent')
        self.assertFalse(result['admitted'])
        review['candidate_sha256'] = '0'*64
        with self.assertRaises(ValueError):
            check_candidate(candidate, self.ledger, review)

    def test_real_rejected_candidate_preserved_without_rewriting(self):
        raw = load('audit/old/experience-candidate.json')
        replay = load('audit/rejected-candidate-replay.json')
        self.assertEqual(digest(raw['text'].encode()), replay['text_sha256'])
        self.assertFalse(replay['admitted'])
        for issue in replay['issues']:
            self.assertIn(issue['quote'], raw['text'])
        with self.assertRaises(ValueError):
            check_candidate(raw, self.ledger)  # Legacy schema is not silently upgraded.

    def test_scope_limit_differs_from_unresolved_policy(self):
        candidate = fixture()
        candidate['unresolved'] = [{'statement': 'Unexamined upstream behavior.', 'impact': 'scope_limit'}]
        def review_for(value):
            return {'candidate_sha256': object_digest(value), 'ledger_sha256': object_digest(self.ledger),
                    'reviewer': 'execution_agent', 'all_normative_rules_covered': True,
                    'preservation_obligations_checked': True, 'counterevidence_handled': True,
                    'rules': [{'id': 'r1', 'supported': True, 'evidence': ['R-task'],
                               'reason': 'Synthetic test of disposition only; no real candidate.'}]}
        result = check_candidate(candidate, self.ledger, review_for(candidate))
        self.assertEqual(result['semantic_status'], 'supported_by_execution_agent')
        self.assertFalse(result['admitted'])
        candidate['unresolved'][0]['impact'] = 'policy'
        result = check_candidate(candidate, self.ledger, review_for(candidate))
        self.assertEqual(result['semantic_status'], 'rejected_by_execution_agent')


if __name__ == '__main__':
    unittest.main(verbosity=2)
