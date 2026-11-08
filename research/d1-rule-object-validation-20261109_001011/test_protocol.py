"""Zero-model checks. All constructed candidates are SYNTHETIC test fixtures."""
import copy
import json
import unittest
from pathlib import Path
from handoff import (make_schema, render, numbered_rules, validate_candidate,
                     semantic_gate, object_digest, digest, verify_ledger,
                     assemble_payload, VERSION, CATEGORIES)
from schema_validator import validate
from feedback import feedback, checks
from toolflow import PREDICATES

A = Path(__file__).resolve().parent


def load(name):
    return json.loads((A / name).read_text())


def fixture():
    """Shape fixture only, with no claim of learned policy or effect."""
    return {'version': VERSION, 'requires': ['shared_lifetime'], 'excludes': [],
            'applicability': [{'predicate': 'shared_lifetime', 'status': 'known',
                              'evidence': ['F-ownership'], 'explanation': 'SYNTHETIC fixture.'}],
            'rules': [{'category': category, 'body': 'SYNTHETIC fixture body ' + str(i),
                       'support': ['R-task'], 'conditions': ['F-ownership'],
                       'preserve': ['C-ownership', 'C-cached', 'C-events'],
                       'counterevidence': ['O-auto1-0', 'O-auto2-0', 'O-auto1-1', 'O-auto2-1'],
                       'explanation': 'SYNTHETIC, not a model output or semantic endorsement.',
                       'causal_status': 'source_reasoning'} for i, category in enumerate(CATEGORIES)],
            'unresolved': []}


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.ledger = load('evidence-ledger.json')

    def test_no_duplicate_text_quote_or_model_rule_id(self):
        candidate = fixture()
        self.assertNotIn('text', candidate)
        self.assertTrue(all(not ({'quote', 'id', 'text'} & set(r)) for r in candidate['rules']))
        self.assertTrue(validate_candidate(candidate, self.ledger, PREDICATES)['structure_valid'])
        candidate['text'] = 'a second copy'
        with self.assertRaises(ValueError):
            validate_candidate(candidate, self.ledger, PREDICATES)

    def test_rendering_deterministic_and_bodies_exactly_once(self):
        candidate = fixture()
        rendered = render(candidate)
        self.assertEqual(rendered, render(json.loads(json.dumps(candidate, sort_keys=True))))
        self.assertEqual([r['id'] for r in numbered_rules(candidate)], ['R01','R02','R03','R04','R05'])
        for r in candidate['rules']:
            self.assertEqual(rendered.count(r['body']), 1)
        self.assertNotIn('R-task', rendered)
        self.assertNotIn('SYNTHETIC, not a model output', rendered)

    def test_illegal_id_and_explanation_prose_rejected_by_schema(self):
        for field, value in [('support', 'invented-ID'), ('conditions', 'A request is offline.'),
                             ('preserve', 'preserve existing background work'), ('counterevidence', 'outside-ledger')]:
            candidate = fixture(); candidate['rules'][0][field] = [value]
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate(candidate, make_schema(self.ledger, PREDICATES))

    def test_evidence_kind_out_of_bounds_rejected(self):
        for field in ['support', 'conditions', 'counterevidence']:
            for value in ['U-reflector', 'H-regression', 'shared_lifetime', 'C-cached']:
                candidate = fixture(); candidate['rules'][0][field] = [value]
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    validate_candidate(candidate, self.ledger, PREDICATES)

    def test_unknown_or_unmet_required_mechanism_not_applicable(self):
        for status in ['unknown', 'contradicted']:
            candidate = fixture(); candidate['applicability'][0]['status'] = status
            with self.assertRaisesRegex(ValueError, 'Unknown/unmet'):
                validate_candidate(candidate, self.ledger, PREDICATES)

    def test_unknown_exclusion_cannot_silently_pass(self):
        candidate = fixture(); candidate['excludes'] = ['different_ownership_policy']
        candidate['applicability'].append({'predicate': 'different_ownership_policy', 'status': 'unknown',
                                          'evidence': [], 'explanation': 'Unknown synthetic fixture.'})
        with self.assertRaisesRegex(ValueError, 'Unknown/unmet'):
            validate_candidate(candidate, self.ledger, PREDICATES)

    def test_predicates_and_supporting_evidence_are_different_namespaces(self):
        candidate = fixture(); candidate['requires'] = ['R-task']
        with self.assertRaises(ValueError):
            validate_candidate(candidate, self.ledger, PREDICATES)
        candidate = fixture(); candidate['applicability'][0]['evidence'] = ['shared_lifetime']
        with self.assertRaises(ValueError):
            validate_candidate(candidate, self.ledger, PREDICATES)

    def test_missing_category_preservation_counterexample_rejected(self):
        for mode in ['category', 'preserve', 'counter']:
            candidate = fixture()
            if mode == 'category': candidate['rules'][0]['category'] = 'event_relation'
            for rule in candidate['rules']:
                if mode == 'preserve': rule['preserve'] = ['C-events']
                if mode == 'counter': rule['counterevidence'] = []
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                validate_candidate(candidate, self.ledger, PREDICATES)

    def test_outcome_only_does_not_authorize_policy(self):
        candidate = fixture(); candidate['rules'][0]['support'] = ['O-auto1-0']
        with self.assertRaisesRegex(ValueError, 'outcome alone'):
            validate_candidate(candidate, self.ledger, PREDICATES)

    def test_old_failed_raw_object_is_not_silently_converted(self):
        raw = (A / 'audit/previous-run/reflection-raw.txt').read_bytes()
        candidate = json.loads(raw)
        self.assertEqual(candidate, load('audit/previous-run/candidate-experience.json'))
        self.assertEqual(load('audit/previous-run/stop.json')['classification'], 'candidate_rejected')
        with self.assertRaises(ValueError):
            validate_candidate(candidate, self.ledger, PREDICATES)

    def test_partial_output_not_completed_or_accepted(self):
        raw = json.dumps(fixture()).encode()
        for cut in [1, len(raw)//2, len(raw)-1]:
            with self.assertRaises((ValueError, UnicodeDecodeError)):
                json.loads(raw[:cut])
        with self.assertRaises(ValueError):
            validate_candidate(json.dumps(fixture()), self.ledger, PREDICATES)

    def test_synthetic_conversion_fixture_is_explicitly_not_model_output(self):
        derived = load('offline/derived-fixture.json')
        self.assertEqual(derived['provenance']['kind'], 'synthetic_derived_test_fixture')
        self.assertFalse(derived['provenance']['is_model_candidate'])
        self.assertFalse(derived['provenance']['is_effect_evidence'])

    def test_false_expectations_original_success_regression_unknown(self):
        standards = [{'effect': k, 'expected': False, 'description': 'SYNTHETIC false expectation'}
                     for k in ['kept', 'lost', 'improved', 'unknown']]
        original = {'observed_effects': {'kept': False, 'lost': False, 'improved': True, 'unknown': False}}
        repair = {'observed_effects': {'kept': False, 'lost': True, 'improved': False}}
        row = feedback(original, [repair], standards)['runs'][0]
        self.assertEqual([r['effect'] for r in row['original_successes']], ['kept', 'lost', 'unknown'])
        self.assertEqual([r['effect'] for r in row['regressions']], ['lost'])
        self.assertEqual([r['effect'] for r in row['improvements']], ['improved'])
        self.assertEqual([r['effect'] for r in row['retained_original_successes']], ['kept'])
        self.assertEqual([r['effect'] for r in row['unknown']], ['unknown'])

    def test_complete_real_feedback_retains_entire_vector(self):
        for row in load('feedback.json')['runs']:
            self.assertEqual([len(row[k]) for k in ['relations', 'actual_successes', 'original_successes',
                                                   'retained_original_successes', 'improvements', 'regressions']],
                             [29, 27, 21, 19, 8, 2])
            self.assertEqual(len(row['all_checks']), 75)
            self.assertEqual(len(row['failed_checks']), 7)
        rows, unknown = checks({'schedules': {'a': {'checks': [{'passed': False}], 'assertions': [{'passed': True}]}}})
        self.assertEqual(len(rows), 2); self.assertFalse(unknown)

    def test_ledger_and_payload_remain_frozen_training_only(self):
        verify_ledger(A, self.ledger)
        payload = assemble_payload(A, self.ledger, load('feedback.json'))
        self.assertEqual(len(payload['materials']), len(self.ledger['files']))
        ledger = copy.deepcopy(self.ledger)
        ledger['files']['inputs/task.md']['role'] = 'test_score'
        with self.assertRaises(ValueError):
            assemble_payload(A, ledger, load('feedback.json'))
        ledger = copy.deepcopy(self.ledger)
        ledger['files']['inputs/task.md']['sha256'] = '0'*64
        with self.assertRaises(ValueError): verify_ledger(A, ledger)

    def test_semantics_still_required_and_review_hash_bound(self):
        candidate = fixture(); text = render(candidate)
        result = validate_candidate(candidate, self.ledger, PREDICATES)
        self.assertFalse(result['admitted'])
        review = {'reviewer': 'execution_agent', 'AI_assisted': True,
            'candidate_sha256': object_digest(candidate), 'ledger_sha256': object_digest(self.ledger),
            'rendered_sha256': digest(text.encode()), 'all_normative_rules_covered': True,
            'preservation_obligations_checked': True, 'counterevidence_handled': True,
            'rules': [{'id': r['id'], 'supported': True, 'evidence': ['R-task'], 'reason': 'Synthetic review fixture only.'}
                      for r in numbered_rules(candidate)],
            'applicability': [{'predicate': 'shared_lifetime', 'supported': False,
                               'evidence': ['F-ownership'], 'reason': 'Synthetic semantic rejection.'}], 'unresolved': []}
        result = semantic_gate(candidate, self.ledger, PREDICATES, review)
        self.assertFalse(result['development_eligible'])
        review['candidate_sha256'] = '0'*64
        with self.assertRaises(ValueError): semantic_gate(candidate, self.ledger, PREDICATES, review)


if __name__ == '__main__':
    unittest.main(verbosity=2)
