"""Explicit offline reflection handoff, using only synthetic cases/stores."""
from copy import deepcopy
import json
from pathlib import Path
import threading
import unittest
from unittest.mock import patch
from urllib.request import build_opener,ProxyHandler

import test_development_v2 as fixtures
from test_workflow_v3 import FakeBackend
from temporal_contract_analyzer import experience_updates as updates,experience_memory as memory,experience_approval as approval,experience_lifecycle as life
from temporal_contract_analyzer.core import EvidenceError
from temporal_contract_analyzer.experience_workflow import Workflow
from temporal_contract_analyzer.experience_candidate_handoff import materialize
from temporal_contract_analyzer.memory_review import ReviewServer


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.DevelopmentTests('test_success_can_extract_and_no_update_is_normal')
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.root=self.fixture.root;self.store=self.fixture.store

    def stopped(self):
        original_schema=updates.schema
        def legacy_schema(*args,**kwargs):
            schema=original_schema(*args,**kwargs);item=deepcopy(schema['properties']['changes']['items']['anyOf'][0])
            item['properties']['rule_id']=dict(type=['string','null'])
            schema['properties']['changes']['items']=item;return schema
        class LegacyBackend(FakeBackend):
            def execute(self,p,role,prompt,schema,directory):
                result=super().execute(p,role,prompt,schema,directory)
                if role=='reflect':result['output']['changes'][0]['rule_id']='R01'
                return result
        source=Workflow(self.root/'source-batch');source.prepare_config(self.fixture.config())
        # This fixture intentionally represents the frozen legacy response protocol.
        protocol=json.loads((source.root/'protocol.json').read_text());protocol.pop('reflection_delta_protocol',None)
        (source.root/'protocol.json').write_text(json.dumps(protocol))
        with patch.object(updates,'schema',side_effect=legacy_schema):
            state=source.run(execute=True,backend=LegacyBackend())
        self.assertEqual(state['status'],'reflection_incomplete',state.get('error'))
        self.assertFalse((source.root/'candidate.json').exists())
        self.assertTrue((source.root/'raw-reflection.json').exists())
        return source

    def test_materialization_visible_in_review_is_idempotent_and_never_calls_models(self):
        source=self.stopped();before=(source.root/'state.json').read_bytes();raw=(source.root/'raw-reflection.json').read_bytes()
        destination=self.root/'handoff'
        with patch('temporal_contract_analyzer.evolution_backend.NativeBackend.execute',side_effect=AssertionError('No provider call')):
            result=materialize(source.root,destination);again=materialize(source.root,destination)
        self.assertEqual(result['candidate_sha256'],again['candidate_sha256']);self.assertTrue(again['already_materialized'])
        self.assertEqual(len(memory.records(self.store)),1)
        bundle=memory.records(self.store)[0];value=json.loads(raw)
        self.assertEqual(bundle['rules'][0]['body'],value['changes'][0]['body'])
        self.assertEqual(bundle['labels'],value['labels']);self.assertEqual(bundle['requires'],value['requires'])
        self.assertEqual(life.metadata(self.store,bundle['sha256'])['ai_status'],'pending')
        self.assertEqual((source.root/'state.json').read_bytes(),before);self.assertEqual((source.root/'raw-reflection.json').read_bytes(),raw)
        self.assertFalse((source.root/'candidate.json').exists());self.assertFalse((destination/'execution-authorization.json').exists())
        self.assertEqual(approval.decisions(self.store),[]);self.assertEqual(approval.active(self.store),[])
        request=approval.review_template(self.store,bundle['sha256']);request.update(decision='accept',reviewer='SYNTHETIC_OPERATOR')
        for row in request['rules']:row['supported']=True
        with self.assertRaises(EvidenceError):approval.decide(self.store,bundle['sha256'],request)
        server=ReviewServer(self.store);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            opener=build_opener(ProxyHandler({}))
            with opener.open(server.url+'/api/library') as response:library=json.load(response)
            self.assertEqual(library['records'][0]['sha256'],bundle['sha256'])
            with opener.open(server.url+'/api/records/'+bundle['sha256']) as response:record=json.load(response)
            self.assertEqual(record['workflow']['ai_status'],'pending');self.assertFalse(record['workflow']['execution_authorized'])
        finally:server.shutdown();server.server_close();thread.join(3)

    def test_explicit_worker_only_runs_remaining_check_and_never_repeats_source_starts(self):
        source=self.stopped();destination=self.root/'handoff';result=materialize(source.root,destination)
        loop=Workflow(destination);backend=FakeBackend()
        with self.assertRaises(EvidenceError):loop.run(backend=backend)
        self.assertEqual(backend.calls,[])
        state=loop.run(execute=True,backend=backend)
        self.assertEqual(state['status'],'awaiting_human_review',state.get('error'))
        self.assertEqual([c['role'] for c in backend.calls],['candidate_check'])
        self.assertEqual(life.metadata(self.store,result['candidate_sha256'])['ai_status'],'passed')
        self.assertEqual(approval.decisions(self.store),[])
        loop.run(execute=True,backend=backend);self.assertEqual(len(backend.calls),1)
        self.assertTrue(all(destination in Path(c['input_path']).parents for c in loop.verify()['cases'].values()))

    def test_lost_receipt_does_not_reset_completed_authorized_task(self):
        source=self.stopped();destination=self.root/'handoff';result=materialize(source.root,destination)
        loop=Workflow(destination);backend=FakeBackend();loop.run(execute=True,backend=backend)
        state_before=(destination/'state.json').read_bytes();authorization=(destination/'execution-authorization.json').read_bytes()
        receipt=self.store/'workflow/handoffs'/(source.verify()['batch_id']+'.json');receipt.unlink()
        again=materialize(source.root,destination)
        self.assertTrue(again['already_materialized']);self.assertEqual(again['candidate_sha256'],result['candidate_sha256'])
        self.assertEqual((destination/'state.json').read_bytes(),state_before)
        self.assertEqual((destination/'execution-authorization.json').read_bytes(),authorization)
        loop.run(execute=True,backend=backend);self.assertEqual(len(backend.calls),1)

    def test_ambiguous_ids_or_policy_changes_do_not_publish(self):
        source=self.stopped();p=source.verify();context=json.loads((source.root/'reflection-input.json').read_text())
        value=json.loads((source.root/'raw-reflection.json').read_text())
        value['changes'][0]['rule_id']='R99'
        with self.assertRaises(EvidenceError):updates.recover_program_numbering(value,p['cases']['source']['visible'],context['ledger'],{})
        self.assertEqual(memory.records(self.store),[])
        with self.assertRaises(EvidenceError):materialize(source.root,source.root)
        original=json.loads((source.root/'runs/EXTRACT/result.json').read_text());original['completed']=False
        (source.root/'runs/EXTRACT/result.json').write_text(json.dumps(original))
        with self.assertRaises(EvidenceError):materialize(source.root,self.root/'bad-handoff')
        self.assertEqual(memory.records(self.store),[])

    def test_rejection_or_revision_before_pending_check_prevents_dispatch(self):
        source=self.stopped();destination=self.root/'handoff';result=materialize(source.root,destination)
        code=result['candidate_sha256'];loop=Workflow(destination)
        def reject():
            request=approval.review_template(self.store,code)
            request.update(decision='reject',reviewer='SYNTHETIC_REVIEWER')
            approval.decide(self.store,code,request)
        reject();backend=FakeBackend();state=loop.run(execute=True,backend=backend)
        self.assertEqual(backend.calls,[]);self.assertEqual(state['status'],'rejected')
        # Re-review with an explicit request for revision also cannot launch checks.
        request=approval.review_template(self.store,code);request.update(decision='revise',reviewer='SYNTHETIC_REVIEWER')
        approval.decide(self.store,code,request);loop.run(execute=True,backend=backend);self.assertEqual(backend.calls,[])

    def test_rejection_during_check_is_not_overwritten_by_AI_completion(self):
        source=self.stopped();destination=self.root/'handoff';result=materialize(source.root,destination)
        code=result['candidate_sha256'];loop=Workflow(destination)
        def reject(slot,p):
            if slot=='CANDIDATE-CHECK':
                request=approval.review_template(self.store,code)
                request.update(decision='reject',reviewer='SYNTHETIC_REVIEWER')
                approval.decide(self.store,code,request)
        backend=FakeBackend(hook=reject);state=loop.run(execute=True,backend=backend)
        self.assertEqual([c['role'] for c in backend.calls],['candidate_check'])
        self.assertEqual(state['status'],'rejected');self.assertEqual(life.metadata(self.store,code)['status'],'rejected')
        self.assertEqual(approval.active(self.store),[])


if __name__=='__main__':unittest.main()
