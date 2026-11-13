"""Offline failure coverage and next-round consumption, not effect evidence."""
from copy import deepcopy
import json
import unittest

from temporal_contract_analyzer import failure_learning as learning, experience_updates as updates
from temporal_contract_analyzer.core import EvidenceError


class FailureReviewTests(unittest.TestCase):
    def setUp(self):
        self.visible=dict(analysis=dict(obligation_labels=[], facts=[]))
        self.ledger=dict(TASK=dict(kind='original_task'), **{'O-START-2':dict(kind='execution_observation')})
        self.record=dict(delivered=dict(rules=[dict(id='R01')]), failures=[dict(
            id='START-2:startup', observation_id='O-START-2')])
        self.value=dict(action='no_update',reason='Existing guidance is sufficient; implementation mismatch remains.',
            basis=['TASK'],parent_sha256=None,labels=None,requires=None,excludes=None,changes=[],unresolved=[],
            failure_review=[dict(failure_id='START-2:startup',diagnosis='execution_gap',
                guidance_rule_ids=['R01'],evidence=['O-START-2','TASK'],
                explanation='The retained patch does not implement the delivered ordering.',
                next_check='Invoke startup with an inline callback and verify the callback observes the installed listener.')])

    def compose(self, value):
        return updates.compose(value,self.visible,self.ledger,{},failure_context=self.record)

    def test_no_new_rule_requires_an_explicit_failure_review(self):
        self.assertIsNone(self.compose(self.value))
        value=deepcopy(self.value);value.pop('failure_review')
        with self.assertRaises(EvidenceError):self.compose(value)
        value=deepcopy(self.value);value['failure_review']=[]
        with self.assertRaises(EvidenceError):self.compose(value)

    def test_execution_claim_cannot_reference_undelivered_guidance(self):
        for rules in ([], ['R99']):
            value=deepcopy(self.value);value['failure_review'][0]['guidance_rule_ids']=rules
            with self.subTest(rules=rules),self.assertRaises(EvidenceError):self.compose(value)

    def test_attribution_needs_its_observation_and_task_source_basis(self):
        for evidence in (['TASK'], ['O-START-2']):
            value=deepcopy(self.value);value['failure_review'][0]['evidence']=evidence
            with self.subTest(evidence=evidence),self.assertRaises(EvidenceError):self.compose(value)
        value=deepcopy(self.value);value['failure_review'][0].update(diagnosis='unknown',
            guidance_rule_ids=[],evidence=['O-START-2'])
        self.assertIsNone(self.compose(value))

    def test_duplicate_rows_cannot_displace_an_unexplained_failure(self):
        self.record['failures'].append(dict(id='START-2:retirement',observation_id='O-START-2'))
        self.value['failure_review']*=2
        with self.assertRaisesRegex(EvidenceError,'exactly once'):self.compose(self.value)

    def test_empty_failures_or_no_guidance_do_not_emit_empty_schema_enums(self):
        def visit(schema):
            if isinstance(schema,dict):
                if 'enum' in schema:self.assertTrue(schema['enum'])
                for value in schema.values():visit(value)
            elif isinstance(schema,list):
                for value in schema:visit(value)
        for failures in ([],self.record['failures']):
            visit(learning.review_schema(dict(failures=failures,delivered=None),self.ledger))


class AvailabilityFollowupTests(unittest.TestCase):
    def setUp(self):
        from test_experience_memory import MemoryTests
        self.fixture=MemoryTests('test_storage_preserves_single_source_body_and_evidence')
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)

    def test_pending_match_is_not_approved_or_delivered_and_is_linked_for_review(self):
        from temporal_contract_analyzer import experience_memory as memory
        bundle=memory.add(self.fixture.store,self.fixture.payload,[self.fixture.source])
        availability=learning.bank_availability(self.fixture.visible(),[bundle],[],dict(selected_sha256s=[]))
        row=availability[0]
        self.assertTrue(row['matches']);self.assertFalse(row['approved_in_snapshot']);self.assertFalse(row['delivered'])
        self.assertEqual(row['gate'],'pending_review')
        record=dict(failures=[dict(slot='START-1')],review=[],repair_limit=2)
        actions=learning.followups(record,availability)
        self.assertEqual(actions[0]['kind'],'review_existing_candidates')
        self.assertEqual(actions[0]['candidate_sha256s'],[bundle['sha256']])
        self.assertEqual(actions[0]['status'],'awaiting_content_review')

    def test_rejected_match_does_not_become_an_approval_task(self):
        from temporal_contract_analyzer import experience_memory as memory
        bundle=memory.add(self.fixture.store,self.fixture.payload,[self.fixture.source])
        rows=learning.bank_availability(self.fixture.visible(),[bundle],[],dict(selected_sha256s=[]),
            [dict(candidate_sha256=bundle['sha256'],decision='reject')])
        self.assertEqual(rows[0]['gate'],'not_approved')
        record=dict(failures=[dict(slot='START-1')],review=[])
        self.assertFalse(any(r['kind']=='review_existing_candidates' for r in learning.followups(record,rows)))

    def test_approved_unmatched_guidance_requests_inspection_not_weakened_matching(self):
        bundle=self.fixture.add()
        rows=learning.bank_availability(self.fixture.visible('unknown'),[bundle],[bundle],dict(selected_sha256s=[]))
        self.assertEqual(rows[0]['gate'],'matching');self.assertFalse(rows[0]['matches'])
        record=dict(failures=[dict(slot='START-1')],review=[])
        actions=learning.followups(record,rows)
        self.assertEqual(actions[0]['kind'],'inspect_applicability')
        self.assertEqual(learning.followups(dict(failures=[],review=[]),rows),[])

    def test_followup_sidecar_is_consumed_without_rewriting_the_original(self):
        from temporal_contract_analyzer import archive
        store=self.fixture.store;visible=self.fixture.visible()
        record=dict(batch_id='synthetic-failure',source_key=learning.source_key(visible),
            failures=[dict(slot='START-1')],at='2026-01-01T00:00:00Z')
        path=store/'failure-learning/synthetic-failure.json';archive.atomic_json(path,record);before=path.read_bytes()
        sidecar=dict(learning_followups=[dict(kind='review_existing_candidates',candidate_sha256s=['fixture'])])
        archive.atomic_json(store/'failure-followups/synthetic-failure.json',sidecar)
        result=learning.prior(store,visible)
        self.assertEqual(result[0]['followup_snapshot'],sidecar)
        self.assertEqual(path.read_bytes(),before)

    def test_applicability_only_revision_keeps_all_rule_bodies(self):
        parent=self.fixture.add();visible=self.fixture.visible()
        visible['analysis']['facts'].append(dict(predicate='inline_reentry',state='contradicted',evidence=[]))
        value=dict(action='revise',reason='Synthetic source-supported boundary update.',basis=['TASK'],
            parent_sha256=parent['sha256'],labels=None,requires=None,excludes=['inline_reentry'],changes=[],unresolved=[])
        result=updates.compose(value,visible,dict(TASK=dict(kind='original_task')),{parent['sha256']:parent})
        self.assertEqual(result['rules'],parent['rules'])
        self.assertEqual(result['excludes'],['inline_reentry'])
