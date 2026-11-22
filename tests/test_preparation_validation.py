"""Recovery flow tests use synthetic scoring; recorded fixtures contain no Gold data."""
from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest

from temporal_contract_analyzer import experience_memory as memory, experience_approval as approval
from temporal_contract_analyzer import preparation_validation as advisory, experience_routing as routing, taxonomy
from temporal_contract_analyzer.tempoevo_v4 import Trajectory, MODEL, read
from temporal_contract_analyzer.core import EvidenceError
from test_tempoevo_v4 import Backend, contract


class AdvisoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.source=self.root/'source';self.source.mkdir()
        (self.source/'main.py').write_text('value = 0\n')
        self.store=self.root/'store';memory.initialize(self.store)

    def prepare(self,**changes):
        cfg=dict(task='Preserve accepted work.',candidate=str(self.source),store=str(self.store),condition='contract',
                 mode='testing',gold_evaluator=dict(command=['synthetic-gold']),memory_snapshot=approval.freeze(self.store))
        cfg.update(changes)
        if cfg['mode']=='learning':cfg['training_evaluator']=cfg.pop('gold_evaluator')
        loop=Trajectory(self.root/('run-'+str(len(list(self.root.glob('run-*'))))))
        loop.prepare(cfg);return loop

    def test_unsupported_positive_and_negative_facts_become_unknown_and_cannot_route(self):
        anchor=dict(file='TASK',line=1,quote='Preserve accepted work.')
        raw=dict(taxonomy_version=taxonomy.VERSION,contract='Preserve accepted work.',
            obligation_labels=[dict(code='I',statement='Keep entry.',evidence=[anchor]),dict(code='L',statement='Unsupported label.',evidence=[])],
            facts=[dict(predicate='entry_snapshot',state='known',evidence=[]),
                   dict(predicate='inline_reentry',state='contradicted',evidence=[dict(anchor,quote='invented')]),
                   dict(predicate='boundary_persistence',state='known',evidence=[anchor])],unknowns=[])
        original=deepcopy(raw);checked,warnings=advisory.analysis(raw,'Preserve accepted work.',{})
        self.assertEqual(raw,original);self.assertEqual([x['state'] for x in checked['facts']],['unknown','unknown','known'])
        self.assertEqual([x['code'] for x in checked['obligation_labels']],['I']);self.assertEqual(len(warnings),3)
        library=[routing.freeze_entry('Capture entry.', ['I'],['entry_snapshot'],[],'fixture')]
        review=routing.review_template(checked,'Preserve accepted work.',{},text_grounding=True)
        review.update(reviewer='unreviewed_model_analysis',approved=False,reason='Synthetic fixture.')
        self.assertIsNone(routing.route(checked,{},library,task='Preserve accepted work.',review=review)['selected'])

    def test_invalid_draft_is_corrected_once_or_discarded_before_action(self):
        for correct in (True,False):
            class BadDraft(Backend):
                def execute(inner,kind,payload,*args):
                    result=super().execute(kind,payload,*args)
                    if kind=='contract' and 'version' not in payload and not (correct and 'validation_feedback' in payload):
                        result['output']['supporting_evidence'][0]['quote']='Invented requirement'
                    return result
            loop=self.prepare();backend=BadDraft();state=loop.run(backend,execute=True)
            self.assertEqual(state['status'],'scored',state.get('error'));self.assertEqual(len(state['attempts']),1)
            drafts=[c for c in backend.calls if c[0]=='contract' and 'version' not in c[1]]
            self.assertEqual(len(drafts),2);self.assertEqual(drafts[1][3]['requests'],11)
            self.assertLess(drafts[1][3]['seconds'],drafts[0][3]['seconds'])
            action=next(c[1] for c in backend.calls if c[0]=='action')
            self.assertEqual(action['contract'],contract() if correct else None)
            self.assertTrue(action['preparation_warnings']);self.assertNotIn('SECRET_GOLD',json.dumps(backend.calls))
            self.assertEqual(sum(s['kind']=='gold' for s in state['stages']),1)
            self.assertEqual(loop.report()['preparation_corrections'],1)
            self.assertNotIn('contract_review',state)

    def test_full_preparation_budget_does_not_spend_action_reserve_on_correction(self):
        class ExhaustedDraft(Backend):
            def execute(inner,kind,payload,*args):
                result=super().execute(kind,payload,*args)
                if kind=='contract':result.update(requests=12,output={})
                return result
        loop=self.prepare();backend=ExhaustedDraft();state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'scored',state.get('error'))
        self.assertEqual([x[0] for x in backend.calls],['contract','action'])
        self.assertEqual(next(x[3]['requests'] for x in backend.calls if x[0]=='action'),24)
        self.assertEqual(loop.report()['requests'],13)

    def test_malformed_output_is_recoverable_but_runtime_and_boundary_errors_are_not(self):
        for failure in ('invalid_output',None,'timeout','tool_policy_denied','infrastructure_error','transient_transport_error'):
            class FailedDraft(Backend):
                def execute(inner,kind,payload,*args):
                    if kind=='contract':
                        inner.calls.append((kind,deepcopy(payload),deepcopy(args[0]),deepcopy(args[1])))
                        return dict(valid=False,requests=1,model=MODEL,error='synthetic '+str(failure),failure_type=failure)
                    return super().execute(kind,payload,*args)
            loop=self.prepare();backend=FailedDraft();state=loop.run(backend,execute=True)
            if failure=='invalid_output':
                self.assertEqual(state['status'],'scored',state.get('error'));self.assertEqual(len(state['attempts']),1)
            else:
                self.assertEqual(state['status'],'execution_invalid');self.assertEqual(len(state['attempts']),0)
                self.assertNotIn('action',[x[0] for x in backend.calls])

    def test_identity_or_usage_violation_is_never_softened(self):
        for bad in ('model','usage'):
            class BadReceipt(Backend):
                def execute(inner,*args):
                    result=super().execute(*args)
                    if bad=='model':result['model']=dict(model='wrong',reasoning_effort='low')
                    else:result['requests']=13
                    return result
            loop=self.prepare();state=loop.run(BadReceipt(),execute=True)
            self.assertEqual(state['status'],'execution_invalid');self.assertEqual(state['attempts'],[])

    def test_qoder_reserves_correction_budget_and_retains_malformed_answer(self):
        loop=self.prepare();p=loop.verify();p['model_settings']['provider']['wire_api']='qoder_cli'
        calls=[]
        class Malformed:
            def execute(inner,kind,payload,model,limits,directory):
                calls.append((deepcopy(payload),dict(limits)))
                if len(calls)==1:
                    (directory/'raw-answer.txt').write_text('{"ready": tru}')
                    return dict(valid=False,requests=9,model=model,failure_type='invalid_output',error='Malformed JSON')
                return dict(valid=True,requests=1,model=model,output={'ready':True})
        result=loop._preparation_output(p,Malformed(),'contract','contract',dict(task=p['task'],sources={'main.py':'value = 0\n'}),lambda x:x)
        self.assertEqual(result,{'ready':True})
        self.assertEqual(calls[0][1]['requests'],9)
        self.assertLessEqual(calls[0][1]['seconds'],480)
        self.assertEqual(calls[1][1]['requests'],3)
        self.assertEqual(calls[1][0]['validation_feedback']['previous_response'],'{"ready": tru}')
        self.assertIn('Do not restart analysis',calls[1][0]['validation_feedback']['instruction'])

    def test_qoder_preparation_output_limit_uses_only_remaining_budget(self):
        loop=self.prepare();p=loop.verify();p['model_settings']['provider']['wire_api']='qoder_cli';calls=[]
        class Limited:
            def execute(inner,kind,payload,model,limits,directory):
                calls.append(dict(limits))
                if len(calls)==1:return dict(valid=False,requests=9,model=model,failure_type='preparation_output_limit',error='Output limit')
                return dict(valid=True,requests=1,model=model,output={'ready':True})
        self.assertEqual(loop._preparation_output(p,Limited(),'contract','contract',dict(task=p['task'],sources={}),lambda x:x),{'ready':True})
        self.assertEqual([x['requests'] for x in calls],[9,3])

    def test_unusable_routing_output_falls_back_without_matching_experience(self):
        class NoRouting(Backend):
            def execute(inner,kind,payload,*args):
                if kind=='routing':
                    inner.calls.append((kind,deepcopy(payload),args[0],args[1]))
                    return dict(valid=True,requests=1,model=MODEL,output={})
                return super().execute(kind,payload,*args)
        loop=self.prepare(condition='structured',retrieval_profile='source-bound-v8');backend=NoRouting()
        state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'scored',state.get('error'))
        self.assertEqual([c[0] for c in backend.calls].count('routing'),2)
        self.assertEqual(read(loop.root/'delivery.json')['selected_sha256s'],[])
        self.assertEqual(read(loop.root/'routing-analysis.json')['facts'],[])
        self.assertEqual(len(state['attempts']),1)

    def test_invalid_semantic_selection_is_withdrawn_and_action_continues(self):
        from unittest.mock import patch
        class NoSelection(Backend):
            def execute(inner,kind,payload,*args):
                result=super().execute(kind,payload,*args)
                if kind=='selection':result['output']={}
                return result
        analysis=dict(taxonomy_version=taxonomy.VERSION,contract='Preserve accepted work.',obligation_labels=[],facts=[],unknowns=[])
        recalled=dict(candidates=[dict(sha256='a'*64,id='synthetic',text='Synthetic recalled entry')],mechanism_route={})
        loop=self.prepare(condition='structured',retrieval_profile='semantic-v11',routing_analysis=analysis);backend=NoSelection()
        with patch('temporal_contract_analyzer.semantic_retrieval.recall',return_value=recalled):state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'scored',state.get('error'));self.assertEqual(len(state['attempts']),1)
        self.assertEqual([c[0] for c in backend.calls].count('selection'),2)
        self.assertEqual(read(loop.root/'delivery.json')['reason'],'invalid_selection_discarded')
        self.assertIsNone(next(c[1] for c in backend.calls if c[0]=='action')['experience'])

    def test_protected_files_and_invalid_gold_remain_hard_failures(self):
        (self.source/'README.md').write_text('Public requirements.')
        class ChangedChecks(Backend):
            def execute(inner,*args):
                result=super().execute(*args)
                if args[0]=='action':result['candidate_sources']['README.md']='Changed requirements'
                return result
        loop=self.prepare(protected_paths=['README.md']);backend=ChangedChecks();state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'execution_invalid');self.assertFalse(any(s['kind']=='gold' for s in state['stages']))
        class BrokenGold(Backend):
            def evaluate(inner,*args):return dict(valid=False,error='synthetic grader failure',failure_type='infrastructure_error')
        loop=self.prepare();state=loop.run(BrokenGold(),execute=True)
        self.assertEqual(state['status'],'execution_invalid');self.assertEqual(len(state['attempts']),1)
        self.assertNotIn('gold_result',state)

    def test_recovered_output_must_still_match_its_archive_hash(self):
        class BadOutput(Backend):
            def execute(inner,kind,payload,model,limits,directory):
                inner.calls.append((kind,deepcopy(payload),model,limits))
                return dict(valid=False,requests=1,model=model,failure_type='invalid_output',error='Unparseable output')
        loop=self.prepare();backend=BadOutput();protocol=loop.verify()
        with self.assertRaises(advisory.OutputError):
            loop._step(protocol,backend,'contract','contract',dict(task=protocol['task'],sources={'main.py':'value = 0\n'}),budget_group='contract')
        path=loop.root/'stages/contract/result.json';path.write_text(path.read_text()+'\n')
        state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'execution_invalid');self.assertIn('result drift',state['error'])
        self.assertEqual(len(backend.calls),1);self.assertEqual(state['attempts'],[])

    def test_diagnostic_weakening_is_discarded_instead_of_ending_training(self):
        loop=self.prepare(mode='learning');backend=Backend(2,'both',delete=True)
        state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'));self.assertEqual(len(state['attempts']),2)
        self.assertEqual(state['contract'],contract());self.assertFalse(state['diagnoses'][0]['contract_changed'])
        self.assertTrue(state['diagnoses'][0]['diagnostic_fallback'])


if __name__=='__main__':unittest.main()
