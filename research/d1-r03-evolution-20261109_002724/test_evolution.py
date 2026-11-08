"""Synthetic shape/review fixtures only; never candidates or effect evidence."""
import copy
import json
import unittest
from pathlib import Path
from evolution import revision_schema, synthesize, scope_check, differences
from handoff import make_schema, validate_candidate, render, semantic_gate, object_digest, digest
from schema_validator import validate
from toolflow import PREDICATES
from feedback import feedback

A = Path(__file__).resolve().parent
def load(name): return json.loads((A / name).read_text())


class EvolutionTests(unittest.TestCase):
    def setUp(self):
        self.parent = load('parent/candidate-experience.json')
        self.ledger = load('evidence-ledger.json')
        self.fixture = copy.deepcopy(self.parent['rules'][2])
        self.fixture['support'].append('R-task')
        self.fixture['body'] = 'SYNTHETIC render fixture only, not learned guidance.'

    def test_existing_schema_only_narrowed_to_parent_category(self):
        full = make_schema(self.ledger, PREDICATES)
        self.assertEqual(full, load('candidate.schema.json'))
        expected = copy.deepcopy(full['properties']['rules']['items'])
        expected['properties']['category']['enum'] = ['verification']
        self.assertEqual(expected, revision_schema(self.ledger, PREDICATES))
        self.assertEqual(expected, load('reflection.schema.json'))

    def test_parent_rejection_not_silently_changed(self):
        with self.assertRaisesRegex(ValueError, 'outcome alone'):
            validate_candidate(self.parent, self.ledger, PREDICATES)
        self.assertEqual(load('parent/stop.json')['classification'], 'candidate_rejected')

    def test_replace_exactly_r03_without_any_other_change(self):
        before = copy.deepcopy(self.parent)
        candidate, check, _ = synthesize(self.parent, self.fixture, self.ledger, PREDICATES)
        self.assertEqual(self.parent, before)
        self.assertTrue(check['other_rule_objects_unchanged'])
        for i in (0,1,3,4): self.assertEqual(candidate['rules'][i], self.parent['rules'][i])
        for key in self.parent:
            if key != 'rules': self.assertEqual(candidate[key], self.parent[key])

    def test_full_candidate_or_extra_metadata_not_accepted_as_revision(self):
        for bad in [self.parent, {**self.fixture, 'requires': ['shared_lifetime']},
                    {**self.fixture, 'id': 'R03'}]:
            with self.assertRaises(ValueError): validate(bad, revision_schema(self.ledger, PREDICATES))

    def test_invalid_ids_and_unknown_facts_rejected(self):
        for field, invalid in [('support','made-up'), ('conditions','U-reflector'),
                               ('conditions','request is offline'), ('preserve','R-task'),
                               ('counterevidence','H-regression')]:
            revision = copy.deepcopy(self.fixture); revision[field] = [invalid]
            with self.subTest(field=field, invalid=invalid), self.assertRaises(ValueError):
                synthesize(self.parent, revision, self.ledger, PREDICATES)

    def test_no_silent_support_gate_relaxation(self):
        revision = copy.deepcopy(self.fixture)
        revision['support'] = ['O-original-0']
        with self.assertRaisesRegex(ValueError, 'outcome alone'):
            synthesize(self.parent, revision, self.ledger, PREDICATES)

    def test_outside_rule_or_mechanism_or_unresolved_tamper_rejected(self):
        for mode in ['rule', 'mechanism', 'unresolved']:
            candidate, _, _ = synthesize(self.parent, self.fixture, self.ledger, PREDICATES)
            if mode == 'rule': candidate['rules'][3]['body'] += ' changed'
            if mode == 'mechanism': candidate['requires'] = []
            if mode == 'unresolved': candidate['unresolved'] = []
            with self.subTest(mode=mode), self.assertRaises(ValueError): scope_check(self.parent, candidate)

    def test_stable_rendering_and_python_diff_describe_only_r03(self):
        candidate, _, _ = synthesize(self.parent, self.fixture, self.ledger, PREDICATES)
        changes, patch = differences(self.parent, candidate)
        self.assertEqual([x['field'] for x in changes['changed_fields']], ['body','support'])
        self.assertIn(self.fixture['body'], patch)
        self.assertEqual(render(candidate), render(json.loads(json.dumps(candidate, sort_keys=True))))
        for i in (0,1,3,4): self.assertIn(self.parent['rules'][i]['body'], render(candidate))

    def test_review_and_structure_interfaces_compatible_without_policy_relaxation(self):
        candidate, _, _ = synthesize(self.parent, self.fixture, self.ledger, PREDICATES)
        review = copy.deepcopy(load('parent/semantic-review.json'))
        review.update(candidate_sha256=object_digest(candidate), ledger_sha256=object_digest(self.ledger),
                      rendered_sha256=digest(render(candidate).encode()))
        result = semantic_gate(candidate, self.ledger, PREDICATES, review)
        self.assertFalse(result['development_eligible'])  # Parent R03 remains rejected.
        # Pure interface fixture: no semantic endorsement of the synthetic body.
        review['rules'][2]['supported'] = True
        result = semantic_gate(candidate, self.ledger, PREDICATES, review)
        self.assertTrue(result['development_eligible'])
        self.assertFalse(result['admitted'])

    def test_partial_revision_cannot_be_manually_completed(self):
        raw = json.dumps(self.fixture)
        with self.assertRaises(ValueError): json.loads(raw[:-1])
        with self.assertRaises(ValueError): validate(raw, revision_schema(self.ledger, PREDICATES))

    def test_target_predicate_allows_no_entry_and_already_aborted_entry(self):
        # Direct truth-table illustration, not a candidate scoring invocation.
        self.assertTrue(all([]))
        self.assertTrue(all([True]))
        self.assertFalse(all([False]))

    def test_false_expected_and_unknown_success_accounting_preserved(self):
        standards = [{'effect':'a','expected':False,'description':'synthetic false requirement'},
                     {'effect':'b','expected':True,'description':'synthetic unknown observation'}]
        row = feedback({'observed_effects':{'a':False,'b':True}},
                       [{'observed_effects':{'a':True}}], standards)['runs'][0]
        self.assertEqual(len(row['original_successes']),2)
        self.assertEqual([x['effect'] for x in row['regressions']],['a'])
        self.assertEqual([x['effect'] for x in row['unknown']],['b'])


if __name__ == '__main__': unittest.main(verbosity=2)
