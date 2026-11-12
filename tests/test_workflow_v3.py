"""Current V3 workflow: source analysis, scored repairs, failure review and human acceptance."""
from copy import deepcopy
from pathlib import Path
import json
import unittest
import uuid
import fcntl
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import test_development_v2 as fixtures
from temporal_contract_analyzer import experience_approval as approval,experience_memory as memory
from temporal_contract_analyzer import experience_lifecycle as life,experience_screening as screening
from temporal_contract_analyzer.experience_workflow import Workflow,FrozenEvaluation,HUMAN_ONLY
from temporal_contract_analyzer.core import EvidenceError


class FakeBackend(fixtures.Backend):
    def __init__(self,contract_block=False,candidate_block=False,bad_citation=False,hook=None,**kwargs):
        super().__init__(**kwargs);self.bad_citation=bad_citation;self.hook=hook

    def execute(self,p,role,prompt,schema,directory):
        if role in ('contract_check','candidate_check'):
            raise AssertionError('Removed AI audit stage must never execute')
        if self.hook:self.hook(directory.name,p)
        result=super().execute(p,role,prompt,schema,directory)
        if role=='analysis' and self.bad_citation:
            result['output']['obligation_labels'][0]['evidence'][0]['quote']='NOT IN THE SOURCE'
        return result


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.DevelopmentTests('test_success_can_extract_and_no_update_is_normal')
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.root=self.fixture.root;self.store=self.fixture.store

    def prepare(self,**updates):
        config=self.fixture.config();config.update(updates)
        loop=Workflow(self.root/('flow-'+uuid.uuid4().hex));loop.prepare_config(config);return loop

    def fresh_store(self):
        self.store=self.root/('memory-'+uuid.uuid4().hex);memory.initialize(self.store);self.fixture.store=self.store

    def accept(self,code,auto=True,decision='accept',request_id=None):
        req=approval.review_template(self.store,code);req.update(reviewer='SYNTHETIC_NAMED_HUMAN',decision=decision,
            reason='Synthetic human content review, not a real approval.',auto_enable=auto,request_id=request_id or uuid.uuid4().hex)
        for row in req['rules']:row.update(supported=True,reason='Synthetic source check.')
        return approval.decide(self.store,code,req),req

    def edit(self,code):
        bundle=next(b for b in memory.records(self.store) if b['sha256']==code)
        rules=deepcopy(bundle['rules']);rules[0]['body']+=' Check ownership after reentry.'
        child=life.edit(self.store,code,dict(request_id=uuid.uuid4().hex,actor='SYNTHETIC_EDITOR',reason='Synthetic edit.',
            rules=rules,labels=bundle['labels'],requires=bundle['requires'],excludes=bundle['excludes']))
        return child,rules

    def test_default_and_old_configuration_use_only_the_new_workflow(self):
        for supplied in (None,'ai-evidence-v3'):
            self.fresh_store()
            loop=self.prepare(**({} if supplied is None else dict(review_policy=supplied)))
            p=loop.verify();self.assertEqual(p['review_policy'],HUMAN_ONLY)
            self.assertEqual(p['initial_request_cap'],300);self.assertEqual(p['global_request_cap'],540)
            self.assertEqual(set(p['roles']),{'analysis','repair','reflect'})
            self.assertFalse(any(s['role'] in ('contract_check','candidate_check') for s in p['slots']))
            backend=FakeBackend(contract_block=True,candidate_block=True)
            state=loop.run(execute=True,backend=backend)
            self.assertEqual(state['status'],'awaiting_human_review',state.get('error'))
            self.assertEqual([call['role'] for call in backend.calls],['repair','repair','reflect'])
            meta=life.view(self.store,state['candidate_sha256'])
            self.assertEqual(meta['ai_status'],'not_run');self.assertTrue(meta['content_review_available'])
            self.assertFalse((loop.root/'candidate-ai-check.json').exists())
            self.assertFalse(approval.decisions(self.store))
            self.assertEqual(json.loads((loop.root/'summary.json').read_text())['AI_audit'],'not_run')

    def test_failed_no_update_requires_followup_and_does_not_restart(self):
        loop=self.prepare();backend=FakeBackend(no_update=True)
        state=loop.run(execute=True,backend=backend)
        self.assertEqual(state['status'],'repair_exhausted',state.get('error'))
        self.assertTrue(state['followup_required']);self.assertTrue(state['development_done'])
        self.assertFalse(memory.records(self.store));count=len(backend.calls)
        loop.run(execute=True,backend=backend);self.assertEqual(len(backend.calls),count)
        self.assertEqual(len(json.loads((loop.root/'failure-learning.json').read_text())['review']),2)

    def test_two_passes_can_end_without_a_rule_delta(self):
        loop=self.prepare();backend=FakeBackend(no_update=True,success=True)
        with self.assertRaises(EvidenceError):loop.run(backend=backend)
        self.assertEqual(loop.run(execute=True,backend=backend)['status'],'no_update')
        count=len(backend.calls);loop.run(execute=True,backend=backend)
        self.assertEqual(len(backend.calls),count);self.assertEqual(memory.records(self.store),[])

    def test_default_cli_prepares_runs_reviews_and_measures_without_ai_audits(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from temporal_contract_analyzer.cli import main
        cfg=self.fixture.config();cfg['visible']=None
        config=self.root/'cli-config.json';config.write_text(json.dumps(cfg));root=self.root/'cli-batch'
        backend=FakeBackend()
        with patch('temporal_contract_analyzer.experience_workflow.backend_for',return_value=backend),redirect_stdout(StringIO()):
            self.assertEqual(main(['experience-evolution','prepare',str(config),'--root',str(root)]),0)
            self.assertEqual(backend.calls,[])
            self.assertEqual(main(['experience-evolution','run','--root',str(root),'--execute']),0)
            loop=Workflow(root);state=loop.state()
            self.assertEqual(state['status'],'awaiting_human_review',state.get('error'))
            self.assertEqual([c['role'] for c in backend.calls],['analysis','repair','repair','reflect'])
            self.accept(state['candidate_sha256']);count=len(backend.calls)
            self.assertTrue(approval.freeze(self.store)['entries'])
            self.assertEqual(main(['experience-evolution','work','--root',str(root),'--execute']),0)
            self.assertEqual(loop.state()['status'],'enabled')
            self.assertEqual(len(backend.calls)-count,10)
            self.assertFalse(any(c['role'].endswith('_check') for c in backend.calls))
            summary=json.loads((root/'summary.json').read_text())
            self.assertEqual(summary['AI_audit'],'not_run')

    def test_schema_invalid_reflection_stops_without_paid_replay(self):
        class MissingFailureReview(FakeBackend):
            def execute(self,*args,**kwargs):
                result=super().execute(*args,**kwargs)
                if args[1]=='reflect':result['output'].pop('failure_review')
                return result
        loop=self.prepare();backend=MissingFailureReview()
        state=loop.run(execute=True,backend=backend)
        self.assertEqual(state['status'],'reflection_incomplete',state.get('error'))
        count=len(backend.calls);loop.run(execute=True,backend=backend)
        self.assertEqual(len(backend.calls),count)
        self.assertTrue(json.loads((loop.root/'failure-learning.json').read_text())['failures'])

    def test_generated_analysis_has_no_audit_and_keeps_original_proposals(self):
        cfg=self.fixture.config();cfg['visible']=None
        for peer in cfg['cohort']['transfers']:peer['visible']=None
        loop=self.prepare(**cfg);backend=FakeBackend();state=loop.run(execute=True,backend=backend)
        self.assertEqual(state['status'],'awaiting_human_review',state.get('error'))
        self.assertEqual(sum(c['role']=='analysis' for c in backend.calls),3)
        self.assertFalse(any(c['role'].endswith('_check') for c in backend.calls))
        for key in loop.verify()['cases']:
            folder=loop.root/'cases'/key/'analysis'
            visible=json.loads((folder.parent/'approved-visible.json').read_text())
            self.assertEqual(visible['analysis'],json.loads((folder/'raw-analysis.json').read_text()))
            self.assertFalse(visible['review']['approved'])
            self.assertFalse((folder/'ai-check.json').exists())

    def test_bad_citation_is_diagnostic_and_not_a_repair_admission_gate(self):
        loop=self.prepare(visible=None);backend=FakeBackend(no_update=True,bad_citation=True)
        state=loop.run(execute=True,backend=backend)
        self.assertEqual(state['status'],'repair_exhausted',state.get('error'))
        self.assertEqual(sum(c['role']=='repair' for c in backend.calls),2)
        folder=loop.root/'cases/source/analysis'
        self.assertTrue(json.loads((folder/'analysis-notes.json').read_text())['warnings'])
        self.assertEqual(json.loads((loop.root/'starting-route.json').read_text())['route']['condition'],'AUTO')

    def test_content_acceptance_is_immediately_eligible_before_effect_measurement(self):
        loop=self.prepare();backend=FakeBackend();code=loop.run(execute=True,backend=backend)['candidate_sha256']
        count=len(backend.calls);decision,request=self.accept(code,auto=False)
        self.assertEqual(len(backend.calls),count)
        self.assertEqual(approval.decide(self.store,code,request),decision)
        self.assertEqual(approval.freeze(self.store)['entries'][0]['bundle']['sha256'],code)
        self.assertFalse(screening.qualified(self.store,code));self.assertFalse(approval.active(self.store))
        loop.run(execute=True,backend=backend)
        self.assertTrue(screening.qualified(self.store,code))
        self.assertFalse(approval.active(self.store))
        self.assertEqual(life.metadata(self.store,code)['ai_status'],'not_run')

    def test_accepted_experience_does_not_need_positive_effects_for_selection(self):
        for no_gain,source_loss in ((True,False),(False,True)):
            self.fresh_store()
            loop=self.prepare();backend=FakeBackend();code=loop.run(execute=True,backend=backend)['candidate_sha256']
            self.accept(code);backend.no_gain=no_gain;backend.source_loss=source_loss
            state=loop.run(execute=True,backend=backend)
            self.assertEqual(state['status'],'enabled',state.get('error'))
            self.assertFalse(screening.qualified(self.store,code))
            self.assertIn(code,[e['bundle']['sha256'] for e in approval.freeze(self.store)['entries']])
            count=len(backend.calls);loop.run(execute=True,backend=backend);self.assertEqual(len(backend.calls),count)

    def test_edit_can_be_reviewed_immediately_but_needs_its_own_acceptance(self):
        loop=self.prepare();backend=FakeBackend();parent=loop.run(execute=True,backend=backend)['candidate_sha256']
        child,_=self.edit(parent);count=len(backend.calls)
        self.assertEqual(life.metadata(self.store,child['sha256'])['ai_status'],'not_run')
        self.assertIsNone(life.latest_acceptance(self.store,child['sha256']))
        self.accept(parent,decision='reject');self.accept(child['sha256'])
        self.assertEqual(len(backend.calls),count)
        state=loop.run(execute=True,backend=backend)
        self.assertEqual(state['status'],'enabled',state.get('error'))
        self.assertEqual(approval.active(self.store)[0]['bundle']['sha256'],child['sha256'])
        self.assertFalse(any(c['role'].endswith('_check') for c in backend.calls))

    def test_rejection_during_validation_stops_future_slots(self):
        loop=self.prepare();backend=FakeBackend();code=loop.run(execute=True,backend=backend)['candidate_sha256'];self.accept(code)
        backend.hook=lambda slot,p:self.accept(code,auto=False,decision='reject') if slot=='SOURCE-NEW-1' else None
        loop.run(execute=True,backend=backend)
        self.assertFalse(any(c['slot']=='SOURCE-NEW-2' for c in backend.calls))
        self.assertEqual(life.metadata(self.store,code)['status'],'rejected')
        self.assertFalse(approval.freeze(self.store)['entries'])

    def test_rejection_or_revision_before_worker_never_dispatches_repairs(self):
        for decision in ('reject','revise'):
            self.fresh_store()
            loop=self.prepare();backend=FakeBackend();code=loop.run(execute=True,backend=backend)['candidate_sha256']
            self.accept(code,decision=decision);count=len(backend.calls)
            loop.run(execute=True,backend=backend);self.assertEqual(len(backend.calls),count)
            self.assertEqual(life.metadata(self.store,code)['status'],'rejected' if decision=='reject' else 'revision_requested')

    def test_changed_common_analysis_stops_before_more_execution(self):
        loop=self.prepare();backend=FakeBackend();code=loop.run(execute=True,backend=backend)['candidate_sha256'];self.accept(code)
        path=loop.root/'cases/source/approved-visible.json';visible=json.loads(path.read_text())
        visible['analysis']['contract']='A changed proposal.';path.write_text(json.dumps(visible))
        count=len(backend.calls);state=loop.run(execute=True,backend=backend)
        self.assertEqual(state['status'],'infrastructure_error');self.assertEqual(len(backend.calls),count)

    def test_execution_cancel_and_unknown_accounting_do_not_retry(self):
        for kwargs in (dict(unknown_usage=True),dict(fail='START-1')):
            loop=self.prepare();backend=FakeBackend(**kwargs);state=loop.run(execute=True,backend=backend)
            self.assertEqual(state['status'],'infrastructure_error',state.get('error'))
            count=len(backend.calls);loop.run(execute=True,backend=backend);self.assertEqual(len(backend.calls),count)
        loop=self.prepare();backend=FakeBackend(no_update=True,success=True);loop.run(execute=True,backend=backend)
        count=len(backend.calls);life.cancel(loop.root)
        self.assertEqual(loop.run(execute=True,backend=backend)['status'],'cancelled');self.assertEqual(len(backend.calls),count)

    def test_worker_lock_prevents_duplicate_execution(self):
        loop=self.prepare();backend=FakeBackend()
        with (self.store/'evolution-execution.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaises(EvidenceError):loop.run(execute=True,backend=backend)
        self.assertFalse(backend.calls)

    def test_final_evaluation_uses_new_analysis_without_learning_or_audits(self):
        cfg=dict(kind='evaluation',store=str(self.store),binary='/synthetic/codex',node='/synthetic/node',
            review_policy='ai-evidence-v3',milestones=[],excluded_source_units=['source','transfer-a','transfer-b'],
            tasks=[dict(case_id='holdout',visible=None,calibration={'synthetic':True},
                lineage=dict(source_unit='holdout',derived_from=[],prior_exposure='Synthetic holdout.'),
                holdout=dict(used_for_generation=False,used_for_selection=False,used_for_tuning=False))])
        loop=FrozenEvaluation(self.root/'evaluation');loop.prepare_config(cfg);backend=FakeBackend()
        state=loop.run(execute=True,backend=backend)
        self.assertEqual(state['status'],'evaluation_complete',state.get('error'))
        self.assertEqual(sum(c['role']=='analysis' for c in backend.calls),1)
        self.assertFalse(any(c['role'] in ('reflect','contract_check','candidate_check') for c in backend.calls))
        self.assertEqual(memory.records(self.store),[]);self.assertFalse((self.store/'failure-learning').exists())


if __name__=='__main__':unittest.main()
