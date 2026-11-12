"""Offline failure coverage and next-round consumption, not effect evidence."""
from copy import deepcopy
import json
import unittest

import test_development_v2 as fixtures
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


class FailureLoopTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.DevelopmentTests('test_success_can_extract_and_no_update_is_normal')
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)

    def test_failed_no_update_persists_and_reaches_the_next_reflection(self):
        first=self.fixture.prepare('first');backend=fixtures.Backend(no_update=True)
        result=first.run(backend=backend)
        self.assertEqual(result['status'],'repair_exhausted',result.get('error'))
        self.assertTrue(result['followup_required'])
        stored=json.loads((first.root/'failure-learning.json').read_text())
        self.assertEqual(stored['status'],'repair_exhausted')
        self.assertTrue(stored['failures'])
        self.assertEqual(len(stored['review']),len(stored['failures']))
        self.assertEqual(stored['review'][0]['diagnosis'],'unknown')
        second=self.fixture.prepare('second')
        prior=json.loads((second.root/'prior-failures.json').read_text())
        self.assertEqual(prior,[stored])
        other=fixtures.Backend(no_update=True,success=True)
        self.assertEqual(second.run(backend=other)['status'],'no_update')
        context=json.loads((second.root/'reflection-input.json').read_text())
        self.assertEqual(context['previous_failed_attempts'],[stored])
        self.assertIn('failure_review',other.calls[-1]['prompt'])
        self.assertNotIn('previous_failed_attempts',other.calls[0]['prompt'])
        self.assertEqual(learning.prior(self.fixture.store,self.fixture.visible('transfer-a')),[])

    def test_invalid_reflection_keeps_failures_for_future_diagnosis(self):
        class MissingReview(fixtures.Backend):
            def execute(self,*args,**kwargs):
                result=super().execute(*args,**kwargs)
                if args[1]=='reflect':result['output'].pop('failure_review',None)
                return result
        loop=self.fixture.prepare();backend=MissingReview(no_update=True)
        result=loop.run(backend=backend)
        self.assertEqual(result['status'],'reflection_incomplete')
        records=learning.prior(self.fixture.store,self.fixture.visible('source'))
        self.assertEqual(len(records),1)
        self.assertTrue(records[0]['failures'])
        self.assertIsNone(records[0]['review'])
        self.assertEqual(len(backend.calls),3)

    def test_first_failure_survives_an_incomplete_second_repair(self):
        class IncompleteSecond(fixtures.Backend):
            def execute(self,*args,**kwargs):
                result=super().execute(*args,**kwargs)
                if args[4].name=='START-2':result['completed']=False
                return result
        loop=self.fixture.prepare();result=loop.run(backend=IncompleteSecond())
        self.assertEqual(result['status'],'stopped')
        records=learning.prior(self.fixture.store,self.fixture.visible('source'))
        self.assertTrue(records[0]['failures'])
        self.assertEqual({r['slot'] for r in records[0]['failures']},{'START-1'})

    def test_watch_stops_for_followup_without_spending_more_requests(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from types import SimpleNamespace
        from unittest.mock import patch, MagicMock
        from temporal_contract_analyzer.evolution_cli import run
        root=self.fixture.root/'watch';root.mkdir()
        (root/'protocol.json').write_text(json.dumps(dict(schema_version='experience-development-v3')))
        worker=MagicMock();worker.run.return_value=dict(status='repair_exhausted')
        args=SimpleNamespace(root=root,evolution_action='work',execute=True,watch=True,poll_seconds=1)
        with patch('temporal_contract_analyzer.experience_workflow.Workflow',return_value=worker), \
                patch('time.sleep') as sleep,redirect_stdout(StringIO()):
            self.assertEqual(run(args),1)
        self.assertEqual(worker.run.call_count,1)
        sleep.assert_not_called()

    def test_legacy_frozen_batch_keeps_its_original_output_contract(self):
        loop=self.fixture.prepare()
        path=loop.root/'protocol.json';protocol=json.loads(path.read_text());protocol.pop('failure_learning')
        path.write_text(json.dumps(protocol))
        result=loop.run(backend=fixtures.Backend(no_update=True))
        self.assertEqual(result['status'],'no_update',result.get('error'))
        self.assertFalse((loop.root/'failure-learning.json').exists())

    def test_followup_records_real_scores_without_claiming_a_causal_gain(self):
        loop=self.fixture.prepare();loop.run(backend=fixtures.Backend(no_update=True))
        p=loop.verify()
        learning.record_validation(loop.root,p,'synthetic-candidate',
            [fixtures.outcome(True),fixtures.outcome(True)],dict(lost=[],unknown=[]),False)
        record=json.loads((loop.root/'failure-learning.json').read_text())
        check=record['source_validation']['synthetic-candidate']
        self.assertEqual(check['status'],'not_reproduced')
        self.assertEqual(check['actual_scores'],2)
        self.assertFalse(check['prompt_changed'])
        self.assertEqual(check['effect_attribution'],'not_established')
        self.assertEqual(record['status'],'repair_exhausted')
        learning.record_validation(loop.root,p,'synthetic-pending',
            [fixtures.outcome(True)],dict(lost=[],unknown=[]),True)
        record=json.loads((loop.root/'failure-learning.json').read_text())
        self.assertEqual(record['source_validation']['synthetic-pending']['status'],'unresolved')


if __name__=='__main__':unittest.main()
