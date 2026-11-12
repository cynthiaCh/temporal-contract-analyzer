"""Human-only default workflow using temporary stores and a fake backend only."""
from copy import deepcopy
import json
from pathlib import Path
import uuid
import unittest

import test_development_v2 as fixtures
from test_workflow_v3 import FakeBackend
import test_workflow_v3 as v3
from temporal_contract_analyzer import experience_approval as approval, experience_memory as memory
from temporal_contract_analyzer import experience_lifecycle as life,experience_routing as routing,experience_updates as updates
from temporal_contract_analyzer.experience_workflow import Workflow,HUMAN_ONLY
from temporal_contract_analyzer.core import EvidenceError


class SimpleWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.DevelopmentTests('test_success_can_extract_and_no_update_is_normal')
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.root=self.fixture.root;self.store=self.fixture.store

    def prepare(self,**changes):
        cfg=self.fixture.config();cfg.update(changes)
        loop=Workflow(self.root/('simple-'+uuid.uuid4().hex));loop.prepare_config(cfg);return loop

    def accept(self,code,auto=True,decision='accept',request_id=None):
        return v3.WorkflowTests.accept(self,code,auto,decision,request_id)

    def test_default_has_no_audit_slots_or_audit_approval(self):
        loop=self.prepare();p=loop.verify();backend=FakeBackend(contract_block=True,candidate_block=True)
        self.assertEqual(p['review_policy'],HUMAN_ONLY)
        self.assertEqual(p['initial_request_cap'],300)
        self.assertEqual(p['global_request_cap'],540)
        self.assertFalse(any(s['role'] in ('contract_check','candidate_check') for s in p['slots']))
        state=loop.run(execute=True,backend=backend)
        self.assertEqual(state['status'],'awaiting_human_review',state.get('error'))
        self.assertEqual([c['role'] for c in backend.calls],['repair','repair','reflect'])
        meta=life.view(self.store,state['candidate_sha256'])
        self.assertEqual(meta['ai_status'],'not_run');self.assertTrue(meta['content_review_available'])
        self.assertEqual(meta['validation_status'],'not_started');self.assertEqual(approval.decisions(self.store),[])
        self.assertFalse((loop.root/'candidate-ai-check.json').exists())
        view=json.loads((loop.root/'cases/source/approved-visible.json').read_text())
        self.assertFalse(view['review']['approved']);self.assertEqual(view['review']['reviewer'],'unreviewed_model_analysis')
        self.assertEqual(memory.records(self.store)[0]['review']['status'],'candidate')
        self.assertFalse(approval.active(self.store))

    def test_bad_quotation_is_nonblocking_and_preserved_not_silently_fixed(self):
        class BadQuoteBackend(FakeBackend):
            def execute(inner,p,role,prompt,schema,directory):
                r=super().execute(p,role,prompt,schema,directory)
                if role=='analysis':
                    r['output']['obligation_labels'][0]['evidence'][0]['quote']='accepted = True followed by another line'
                return r
        cfg=self.fixture.config();cfg['visible']=None;cfg['cohort']['transfers'][1]['visible']=None
        loop=self.prepare(**cfg);backend=BadQuoteBackend(no_update=True)
        state=loop.run(execute=True,backend=backend)
        self.assertEqual(state['status'],'no_update',state.get('error'))
        self.assertEqual(sum(c['role']=='repair' for c in backend.calls),2)
        self.assertFalse(any(c['role'] in ('contract_check','candidate_check') for c in backend.calls))
        for key in ('source','transfer-2'):
            folder=loop.root/'cases'/key/'analysis'
            raw=json.loads((folder/'raw-analysis.json').read_text())
            effective=json.loads((folder.parent/'approved-visible.json').read_text())
            self.assertEqual(effective['analysis'],raw)
            self.assertTrue(json.loads((folder/'analysis-notes.json').read_text())['warnings'])
        route=json.loads((loop.root/'starting-route.json').read_text())
        self.assertEqual(route['route']['condition'],'AUTO')
        count=len(backend.calls);loop.run(execute=True,backend=backend);self.assertEqual(count,len(backend.calls))

    def test_valid_source_premises_can_route_without_claiming_semantic_approval(self):
        loop=self.prepare();state=loop.run(execute=True,backend=FakeBackend());bundle=memory.records(self.store)[0]
        v=json.loads((loop.root/'cases/source/approved-visible.json').read_text())
        decision=updates.route_view(v,[bundle])
        self.assertEqual(decision['route']['condition'],'ROUTED')
        self.assertEqual(decision['route']['reason'],'unreviewed_analysis_source_premises')
        self.assertFalse(v['review']['approved'])
        v['analysis']['facts'][0]['state']='unknown';v['analysis']['facts'][0]['evidence']=[]
        # A changed analysis cannot reuse the old snapshot binding.
        self.assertEqual(updates.route_view(v,[bundle])['route']['condition'],'AUTO')

    def run_effect(self,auto):
        loop=self.prepare();backend=FakeBackend();state=loop.run(execute=True,backend=backend);code=state['candidate_sha256']
        before=len(backend.calls);self.accept(code,auto=auto)
        self.assertEqual(len(backend.calls),before)
        state=loop.run(execute=True,backend=backend)
        self.assertEqual(life.metadata(self.store,code)['validation_status'],'passed',state.get('error'))
        self.assertEqual(life.metadata(self.store,code)['ai_status'],'not_run')
        self.assertEqual(state['status']=='enabled',auto)
        self.assertFalse(any(c['role'] in ('contract_check','candidate_check') for c in backend.calls))
        count=len(backend.calls);loop.run(execute=True,backend=backend);self.assertEqual(count,len(backend.calls))

    def test_review_only_does_not_enable(self):self.run_effect(False)
    def test_human_authorized_enable_still_uses_actual_effect_gate(self):self.run_effect(True)

    def test_edit_requires_exact_new_acceptance_and_fresh_effects_not_ai(self):
        loop=self.prepare();backend=FakeBackend();code=loop.run(execute=True,backend=backend)['candidate_sha256']
        self.accept(code);parent=next(b for b in memory.records(self.store) if b['sha256']==code)
        rules=deepcopy(parent['rules']);rules[0]['body']+=' Verify source ownership after reentry.'
        child=life.edit(self.store,code,dict(request_id=uuid.uuid4().hex,actor='SYNTHETIC_EDITOR',reason='Synthetic wording change.',
            rules=rules,labels=parent['labels'],requires=parent['requires'],excludes=parent['excludes']))
        meta=life.view(self.store,child['sha256']);self.assertTrue(meta['content_review_available']);self.assertEqual(meta['ai_status'],'not_run')
        self.assertIsNone(life.latest_acceptance(self.store,child['sha256']));self.assertEqual(meta['validation_status'],'not_started')
        self.accept(code,decision='reject')
        count=len(backend.calls);loop.run(execute=True,backend=backend);self.assertEqual(count,len(backend.calls))
        self.accept(child['sha256']);state=loop.run(execute=True,backend=backend)
        self.assertEqual(state['status'],'enabled',state.get('error'))
        self.assertEqual(approval.active(self.store)[0]['bundle']['sha256'],child['sha256'])

    def test_unknown_cost_or_infrastructure_still_stop_without_retry(self):
        for kwargs in (dict(unknown_usage=True),dict(fail='START-1')):
            loop=self.prepare();backend=FakeBackend(**kwargs);state=loop.run(execute=True,backend=backend)
            self.assertEqual(state['status'],'infrastructure_error',state.get('error'))
            count=len(backend.calls);loop.run(execute=True,backend=backend);self.assertEqual(count,len(backend.calls))
            self.assertFalse(any(c['role']=='reflect' for c in backend.calls))

    def test_reject_still_prevents_effect_dispatch(self):
        loop=self.prepare();backend=FakeBackend();code=loop.run(execute=True,backend=backend)['candidate_sha256']
        self.accept(code,decision='reject');count=len(backend.calls)
        loop.run(execute=True,backend=backend);self.assertEqual(count,len(backend.calls))
        self.assertFalse(approval.active(self.store))


if __name__=='__main__':unittest.main()
