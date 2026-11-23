"""Offline online-learning loop, with simulated models and deterministic scoring."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import test_tempoevo_v4 as fixtures
import test_experience_memory as memory_fixtures
from temporal_contract_analyzer import online_memory,experience_approval as approval,experience_memory as memory
from temporal_contract_analyzer.tempoevo_v4 import read
from temporal_contract_analyzer.core import EvidenceError

class OnlineTests(unittest.TestCase):
    setUp=fixtures.V4Tests.setUp
    prepare=fixtures.V4Tests.prepare

    def online(self,task_id,**kw):
        config=dict(learning_policy='online',online_memory=str(self.root/'provisional'),task_id=task_id,condition='bm25')
        config.update(kw);return self.prepare(**config)

    def test_prepared_later_task_uses_new_unreviewed_candidate_immediately(self):
        first=self.online('first');second=self.online('second')  # both prepared before any learning
        self.assertEqual(first.run(fixtures.Backend(2),execute=True)['status'],'passed')
        self.assertEqual(memory.records(self.store),[]);self.assertEqual(approval.freeze(self.store)['entries'],[])
        receipt=read(first.root/'candidate-pool/success-online.json');self.assertEqual(receipt['status'],'available_for_subsequent_training')
        with self.assertRaisesRegex(EvidenceError,'categorized library'):first.publish_candidate('success')
        self.assertEqual(approval.freeze(self.store)['entries'],[])
        b=fixtures.Backend(2);state=second.run(b,execute=True);self.assertEqual(state['status'],'passed',state.get('error'))
        delivery=read(second.root/'delivery.json');self.assertEqual(delivery['provisional_sha256s'],[receipt['candidate_sha256']])
        self.assertIn('unreviewed provisional',b.calls[0][1]['experience']);self.assertIn('Verify accepted identity',b.calls[0][1]['experience'])
        self.assertTrue(list((self.root/'provisional/usage').glob('*.json')))
        self.assertEqual(len(list((self.root/'provisional/entries').glob('*.json'))),1)  # exact duplicate becomes evidence supplement
        self.assertEqual(read(second.root/'candidate-pool/success-online.json')['status'],'evidence_only')
        self.assertEqual(approval.freeze(self.store)['entries'],[])


    def test_default_structured_training_uses_business_selection_with_provisional_fallback(self):
        first=self.online('first');first.run(fixtures.Backend(2),execute=True)
        loop=self.online('abstract-training',condition='structured',training_recipe='v8-compatible-v1',
            task='Preserve accepted work. Keep the entry snapshot.')
        self.assertEqual(loop.verify()['retrieval_profile'],'business-source-v1')
        backend=fixtures.Backend(2);state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'))
        self.assertTrue(read(loop.root/'delivery.json')['provisional_sha256s'])
        kinds=[kind for kind,*_ in backend.calls]
        self.assertIn('selection',kinds);self.assertNotIn('routing',kinds)
        self.assertEqual(read(loop.root/'retrieval/selection-1-recall.json')['candidate_policy'],
                         'local_extractive_summary_top6_full_text_verification')
        self.assertEqual(approval.freeze(self.store)['entries'],[])

    def test_snapshot_stays_fixed_during_task_and_resume_does_not_duplicate(self):
        first=self.online('first');first.run(fixtures.Backend(2),execute=True)
        second=self.online('second');b=fixtures.Backend(2)
        state=second.run(b,execute=True);before=read(second.root/'online-snapshot.json')
        third=self.online('third');third.run(fixtures.Backend(2),execute=True)
        count=len(b.calls);second.run(b,execute=True)
        self.assertEqual(len(b.calls),count);self.assertEqual(read(second.root/'online-snapshot.json'),before)
        changed=deepcopy(before);changed['entries']=[];second.save('online-snapshot.json',changed)
        with self.assertRaises(EvidenceError):second.verify()

    def test_frozen_learning_and_testing_never_consume_pool(self):
        first=self.online('first');first.run(fixtures.Backend(2),execute=True)
        frozen=self.prepare(condition='bm25');frozen.run(fixtures.Backend(2),execute=True)
        self.assertFalse((frozen.root/'online-snapshot.json').exists());self.assertEqual(read(frozen.root/'delivery.json')['selected_sha256s'],[])
        testing=self.prepare(mode='testing',condition='bm25',memory_snapshot=approval.freeze(self.store),gold_evaluator={'command':['synthetic-gold']})
        testing.run(fixtures.Backend(2),execute=True)
        self.assertFalse((testing.root/'online-snapshot.json').exists())
        for config in [dict(mode='testing'),dict(condition='contract'),dict(condition='baseline'),dict(online_memory=str(self.store))]:
            with self.assertRaises(EvidenceError):self.online('invalid',**config)
        with self.assertRaises(EvidenceError):self.prepare(online_memory=str(self.root/'provisional'))

    def test_failed_trajectory_does_not_invent_an_expert_candidate(self):
        loop=self.online('failed');state=loop.run(fixtures.Backend(99),execute=True)
        self.assertEqual(state['status'],'awaiting_expert_summary');self.assertEqual(list((self.root/'provisional/entries').glob('*.json')),[])
        self.assertIsNone(read(loop.root/'expert-summary-task.json')['expert'])
        expert=dict(expert='Synthetic human',confirmed_conclusions=[],unverified_hypotheses=[],unresolved_behaviors=['Still failing'],boundaries_counterexamples=[],suggested_checks=[],experience=dict(labels=['I'],requires=['entry_snapshot'],excludes=[],rules=[dict(category='verification',body='Check accepted identity after reentry.')],limitations=['Failure summary; not a successful repair']))
        loop.submit_expert(expert)
        snapshot=online_memory.capture(self.root/'provisional',self.root/'other','other')
        self.assertEqual(len(snapshot['entries']),1);self.assertFalse(snapshot['entries'][0]['record']['effectiveness_verified'])
        self.assertEqual(memory.records(self.store),[])

    def test_same_task_exclusion_idempotence_and_pool_tamper(self):
        loop=self.online('first');loop.run(fixtures.Backend(2),execute=True);record=read(loop.root/'candidate-pool/success.json')
        online_memory.append(self.root/'provisional',loop.root,'first',record)
        self.assertEqual(len(list((self.root/'provisional/entries').glob('*.json'))),1)
        self.assertEqual(online_memory.capture(self.root/'provisional',self.root/'replicate','first')['entries'],[])
        path=next((self.root/'provisional/entries').glob('*.json'));value=json.loads(path.read_text());value['task_id']='forged';path.write_text(json.dumps(value))
        with self.assertRaises(EvidenceError):online_memory.capture(self.root/'provisional',self.root/'x','x')

    def test_candidate_arriving_during_model_call_is_not_read_mid_trajectory(self):
        first=self.online('first');first.run(fixtures.Backend(2),execute=True)
        record=read(first.root/'candidate-pool/success.json');record['experience']['rules'][0]['body']='Additional training guidance for accepted identity.'
        loop=self.online('second');base=fixtures.Backend(2)
        execute=base.execute
        def call(stage,*args):
            if stage=='contract':online_memory.append(self.root/'provisional',self.root/'concurrent','concurrent',record)
            return execute(stage,*args)
        base.execute=call;state=loop.run(base,execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'))
        self.assertEqual(len(read(loop.root/'online-snapshot.json')['entries']),1)
        self.assertEqual(len(online_memory.capture(self.root/'provisional',self.root/'later','later')['entries']),2)
