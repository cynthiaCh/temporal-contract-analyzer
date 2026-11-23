"""V4 state machine uses synthetic models and deterministic local evaluations only."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
import json
from temporal_contract_analyzer import experience_memory as memory
from temporal_contract_analyzer.tempoevo_v4 import Trajectory, MODEL, CONTRACT_FIELDS, read
from temporal_contract_analyzer.core import EvidenceError


def contract():
    return dict({k:[] for k in CONTRACT_FIELDS},scope=['Public task'],
        obligations=[dict(id='preserve',text='Preserve accepted work.')],
        supporting_evidence=[dict(file='TASK',quote='Preserve accepted work.')])


class Backend:
    def __init__(self, passes=1, diagnosis='implementation_gap', revise=False, delete=False, invalid=None):
        self.passes=passes;self.diagnosis=diagnosis;self.revise=revise;self.delete=delete;self.invalid=invalid;self.calls=[]
    def execute(self,stage,payload,model,limits,directory):
        self.calls.append((stage,deepcopy(payload),deepcopy(model),deepcopy(limits)))
        if self.invalid==stage:return dict(valid=False,error='synthetic timeout',requests=1,model=MODEL)
        if stage=='contract':out=contract()
        elif stage=='selection':
            evidence=[dict(file='TASK',quote=payload['task'])]
            business='business_obligations' in payload.get('schema',{}).get('properties',{})
            obligations=([dict(id='preserve',text='Preserve accepted work.',evidence=evidence)] if business else payload['obligations'])
            out=dict(assessments=[dict(sha256=c['sha256'],relevance='direct',
                premises=[dict(condition='Synthetic public obligation',status='supported',evidence=evidence)],
                object_mapping='Synthetic accepted work',contribution='Synthetic entry preservation',
                covered_obligations=[o['id'] for o in obligations],supporting_evidence=evidence,
                redundant_with=[],reason='Synthetic applicability fixture; not evidence of real semantic correctness.') for c in payload['candidates']])
            if business:
                out['business_obligations']=obligations
                for row,candidate in zip(out['assessments'],payload['candidates']):
                    row['predicate_findings']=[dict(kind=k,predicate=key,state='known' if k=='requires' else 'contradicted',evidence=evidence)
                        for k in ('requires','excludes') for key in candidate[k]]
        elif stage=='diagnosis':
            after=deepcopy(payload['contract_before'])
            if self.revise:after['checkpoints'].append('Check completion before navigation.')
            if self.delete:after['obligations']=[]
            out=dict(diagnosis=self.diagnosis,contract_after=after,structured_delta=['Add checkpoint'] if self.revise else [],
                supporting_evidence=[dict(file='TASK',quote='Preserve accepted work.')],remaining_unknowns=[],explanation='Synthetic diagnosis.')
        elif stage=='extract':out=dict(labels=['I'],requires=['entry_snapshot'],excludes=[],rules=[dict(category='verification',body='Verify accepted identity through reentry.')],limitations=['Synthetic fixture'])
        else:
            sources=deepcopy(payload['candidate_sources']);n=int(sources['main.py'].split('=')[1])+1;sources['main.py']='value = '+str(n)+'\n'
            return dict(valid=True,requests=1,tokens=dict(total_tokens=10),model=MODEL,candidate_sources=sources)
        if stage=='extract':out=dict(experience=out,abstract='Preserve accepted identity across callback reentry.',contributions=[],update=dict(operation='new',target_sha256s=[],reason='Synthetic new rule.',change_summary=['Independent synthetic increment.'],failure_attribution='experience_gap',supporting_attempts=[a['number'] for a in payload['trajectory']]))
        return dict(valid=True,requests=1,tokens=dict(total_tokens=10),model=MODEL,output=out)
    def evaluate(self,stage,payload,directory):
        n=int((Path(payload['candidate'])/'main.py').read_text().split('=')[1])
        if stage=='gold':return dict(valid=True,passed=n>=self.passes,hidden_failures=['SECRET_GOLD'])
        return dict(valid=True,passed=n>=self.passes,observations=[dict(actual=n,passed=n>=self.passes)],regressions=[],unknowns=[],hidden_failures=['SECRET_VISIBLE_EXTRA'])


class V4Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.source=self.root/'source';self.source.mkdir();(self.source/'main.py').write_text('value = 0\n')
        self.store=self.root/'memory';memory.initialize(self.store)
    def prepare(self, **changes):
        cfg=dict(task='Preserve accepted work.',candidate=str(self.source),store=str(self.store),mode='learning',condition='contract',visible_evaluator=dict(command=['synthetic-visible']),training_evaluator=dict(command=['synthetic-training']))
        cfg.update(changes)
        if cfg['mode']=='testing':cfg.pop('training_evaluator',None)
        loop=Trajectory(self.root/('run-'+str(len(list(self.root.glob('run-*'))))));loop.prepare(cfg);return loop

    def test_legacy_runtime_and_agent_changes_do_not_block_testing(self):
        from temporal_contract_analyzer import experience_approval as approval
        agent=self.root/'agent';agent.write_text('previous agent')
        loop=self.prepare(mode='testing',condition='baseline',binary=str(agent),
            memory_snapshot=approval.freeze(self.store),visible_evaluator=None,
            gold_evaluator=dict(command=['synthetic-gold']))
        binding=read(loop.root/'binding.json')
        self.assertNotIn('runtime',binding);self.assertNotIn('implementation',binding)
        self.assertNotIn(str(agent),binding['evaluators'])
        binding.update(implementation='old runner',runtime={str(self.root/'removed-module.py'):'old runtime'})
        binding['evaluators'][str(agent)]='legacy agent checksum';loop.save('binding.json',binding)
        agent.write_text('updated agent')
        state=loop.run(Backend(),execute=True)
        self.assertEqual(state['status'],'scored');self.assertTrue(state['gold_result']['passed'])

    def test_changed_trusted_scoring_input_remains_rejected(self):
        grader=self.root/'grader.py';grader.write_text('original scorer')
        loop=self.prepare(training_evaluator=dict(command=['python3',str(grader)]))
        grader.write_text('different scorer')
        with self.assertRaisesRegex(EvidenceError,'Trusted evaluator input changed'):loop.verify()
    def test_v8_recipe_uses_public_and_gold_acceptance_without_reflection_payload(self):
        class PublicFailsFirst(Backend):
            def evaluate(self,stage,payload,directory):
                result=super().evaluate(stage,payload,directory)
                if stage!='gold':
                    n=int((Path(payload['candidate'])/'main.py').read_text().split('=')[1])
                    result['passed']=n>=2
                return result
        loop=self.prepare(training_recipe='v8-compatible-v1')
        backend=PublicFailsFirst(1);state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'))
        self.assertEqual(len(state['attempts']),2)
        self.assertFalse(state['attempts'][0]['acceptance_passed'])
        self.assertIn('diagnosis',[role for role,*_ in backend.calls])
        for role,payload,*_ in backend.calls:
            if role=='action':self.assertNotIn('within_task_reflections',payload)
        self.assertIn('training_acceptance',state['attempts'][0]['feedback'])


    def test_v8_recipe_cannot_be_used_in_testing_or_without_public_evaluator(self):
        from temporal_contract_analyzer import experience_approval as approval
        with self.assertRaises(EvidenceError):
            self.prepare(training_recipe='v8-compatible-v1',visible_evaluator=None)
        with self.assertRaises(EvidenceError):
            self.prepare(mode='testing',training_recipe='v8-compatible-v1',memory_snapshot=approval.freeze(self.store),gold_evaluator=dict(command=['synthetic-gold']))


    def test_invalid_retrieval_profiles_do_not_silently_change_testing(self):
        with self.assertRaises(EvidenceError):self.prepare(retrieval_profile='unknown')
        with self.assertRaises(EvidenceError):self.prepare(retrieval_profile='source-bound-v8')
        with self.assertRaises(EvidenceError):self.prepare(condition='structured',training_recipe='v8-compatible-v1',retrieval_profile='semantic-v11')

    def test_testing_supplement_binds_real_approval_from_separate_store(self):
        from temporal_contract_analyzer import compact_experience as compact, experience_approval as approval
        directory=self.root/'supplement';directory.mkdir();file=directory/'experiences.json'
        item=dict(id='supplement-example',title='Synthetic approved supplement',labels=['I'],requires=['entry_snapshot'],excludes=[],
            applicability='Use an entry snapshot.',event_relation='Keep accepted identity.',preservation='Retain accepted work.',
            exclusion='Confirm public policy.',verification='Exercise reentry.')
        value=dict(schema_version=compact.VERSION,experiences=[item]);file.write_text(json.dumps(value))
        base=approval.freeze(self.store)
        cfg=dict(mode='testing',condition='structured',
            memory_snapshot=base,gold_evaluator=dict(command=['synthetic-gold']))
        pending=dict(store=str(directory),snapshot=approval.freeze(directory))
        with self.assertRaises(EvidenceError):self.prepare(**cfg,approved_memory_supplements=[pending])
        value['experiences'][0]['review']=dict(reviewer='Synthetic test reviewer',decision='accept',at='2026-11-16T00:00:00Z')
        file.write_text(json.dumps(value));snapshot=approval.freeze(directory);supplement=dict(store=str(directory),snapshot=snapshot)
        bad=deepcopy(snapshot);bad['entries'][0]['expert_decision']['reviewer']='forged'
        with self.assertRaises(EvidenceError):self.prepare(**cfg,approved_memory_supplements=[dict(store=str(directory),snapshot=bad)])
        with self.assertRaises(EvidenceError):self.prepare(**cfg,approved_memory_supplements=[supplement,supplement])
        with self.assertRaises(EvidenceError):self.prepare(approved_memory_supplements=[supplement])
        loop=self.prepare(**cfg,approved_memory_supplements=[supplement]);protocol=loop.verify()
        self.assertEqual(protocol['memory_snapshot']['entries'],snapshot['entries'])
        self.assertEqual(protocol['memory_snapshot']['entries'][0]['expert_decision']['reviewer'],'Synthetic test reviewer')
        self.assertEqual(read(loop.root/'memory-snapshot.json'),protocol['memory_snapshot'])
        state=loop.run(Backend(),execute=True);self.assertEqual(state['status'],'scored',state.get('error'))
        self.assertEqual(len(state['attempts']),1);self.assertEqual(approval.freeze(self.store),base)

    def test_first_pass_stops_and_is_staged_not_approved(self):
        loop=self.prepare();backend=Backend();state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'));self.assertEqual(len(state['attempts']),1)
        self.assertEqual([r[0] for r in backend.calls],['contract','action'])
        self.assertEqual(memory.records(self.store),[])
        with self.assertRaisesRegex(EvidenceError,'first-pass'):loop.publish_candidate('success')
        self.assertEqual(memory.records(self.store),[])
        from temporal_contract_analyzer import experience_approval as approval
        self.assertEqual(approval.freeze(self.store)['entries'],[])
        count=len(backend.calls);loop.run(backend,execute=True);self.assertEqual(len(backend.calls),count)
    def test_second_third_pass_use_real_previous_candidate(self):
        for n in (2,3):
            loop=self.prepare();backend=Backend(n);state=loop.run(backend,execute=True)
            self.assertEqual(state['status'],'passed',state.get('error'));self.assertEqual(len(state['attempts']),n)
            actions=[p for role,p,_,_ in backend.calls if role=='action']
            self.assertEqual([int(p['candidate_sources']['main.py'].split('=')[1]) for p in actions],list(range(n)))
            self.assertTrue(all(p['contract']==contract() for p in actions))
    def test_three_failures_wait_for_real_expert(self):
        loop=self.prepare();state=loop.run(Backend(99),execute=True)
        self.assertEqual(state['status'],'awaiting_expert_summary',state.get('error'))
        self.assertEqual(len(state['attempts']),3);self.assertIsNone(read(loop.root/'expert-summary-task.json')['expert'])
        with self.assertRaises(EvidenceError):loop.submit_expert({})
        self.assertFalse((loop.root/'candidate-pool').exists())
    def test_contract_revision_and_forbidden_deletion(self):
        loop=self.prepare();state=loop.run(Backend(2,'contract_gap',revise=True),execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'));self.assertEqual(len(state['diagnoses']),1)
        revision=read(loop.root/'revisions/2.json');self.assertEqual(revision['contract_before']['obligations'],revision['contract_after']['obligations'])
        bad=self.prepare();state=bad.run(Backend(2,'both',delete=True),execute=True)
        self.assertEqual(state['status'],'passed');self.assertEqual(len(state['attempts']),2)
        self.assertEqual(state['contract'],contract());self.assertTrue(state['preparation_warnings'])
    def test_testing_gold_separation_and_no_memory_writes(self):
        from temporal_contract_analyzer import experience_approval as approval
        loop=self.prepare(mode='testing',memory_snapshot=approval.freeze(self.store),gold_evaluator=dict(command=['synthetic-gold']))
        backend=Backend(2);before=list(self.store.rglob('*'));state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'scored',state.get('error'));self.assertFalse(state['gold_result']['passed'])
        self.assertNotIn('extract',[r[0] for r in backend.calls]);self.assertEqual(before,list(self.store.rglob('*')))
        for _,payload,_,_ in backend.calls:
            self.assertNotIn('SECRET',json.dumps(payload))
        with self.assertRaises(EvidenceError):loop.publish_candidate('success')

    def test_testing_defaults_to_business_selection_without_contract_review(self):
        from temporal_contract_analyzer import experience_approval as approval
        loop=self.prepare(mode='testing',condition='structured',memory_snapshot=approval.freeze(self.store),gold_evaluator=dict(command=['synthetic-gold']))
        p=loop.verify();self.assertEqual(p['retrieval_profile'],'business-source-v1')
        self.assertIsNone(p['contract_review_policy']);self.assertEqual(p['total_request_cap'],48)
        backend=Backend();state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'scored',state.get('error'))
        self.assertEqual([c[0] for c in backend.calls],['contract','action'])
        self.assertFalse(any(s['key'].startswith('contract-review') for s in state['stages']))
        self.assertEqual(sum(s['kind']=='gold' for s in state['stages']),1)
        self.assertNotIn('contract_review',next(c[1] for c in backend.calls if c[0]=='action'))

    def test_removed_contract_review_protocol_is_read_only(self):
        from temporal_contract_analyzer import experience_approval as approval
        cfg=dict(mode='testing',memory_snapshot=approval.freeze(self.store),gold_evaluator=dict(command=['synthetic-gold']))
        with self.assertRaisesRegex(EvidenceError,'read-only'):
            self.prepare(**cfg,contract_review_policy='public_contract_review_3_versions_v1')
        loop=self.prepare(**cfg);summary=(loop.root/'summary.json').read_bytes()
        p=read(loop.root/'protocol.json');p['contract_review_policy']='public_contract_review_3_versions_v1';loop.save('protocol.json',p)
        self.assertEqual(loop.report(),json.loads(summary))
        self.assertEqual((loop.root/'summary.json').read_bytes(),summary)
        with self.assertRaisesRegex(EvidenceError,'read-only'):loop.run(Backend(),execute=True)
    def test_invalid_stage_is_not_three_failures_or_retried(self):
        loop=self.prepare();backend=Backend(invalid='action');state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'execution_invalid');self.assertEqual(state['attempts'],[])
        count=len(backend.calls);loop.run(backend,execute=True);self.assertEqual(len(backend.calls),count)
        self.assertFalse((loop.root/'expert-summary-task.json').exists())
    def test_cancel_and_partial_stage_no_silent_replay(self):
        loop=self.prepare();loop.cancel();b=Backend();self.assertEqual(loop.run(b,execute=True)['status'],'cancelled');self.assertEqual(b.calls,[])
        loop=self.prepare();state=loop.state();state['stages']=[dict(key='contract',kind='contract',status='started')];loop.save('state.json',state)
        b=Backend();self.assertEqual(loop.run(b,execute=True)['status'],'execution_invalid');self.assertEqual(b.calls,[])
    def test_baseline_has_equal_actions_without_contract_or_memory(self):
        loop=self.prepare(condition='baseline');b=Backend(3);state=loop.run(b,execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'))
        self.assertEqual([r[0] for r in b.calls],['action','action','action','extract'])
        self.assertTrue(all(p['contract'] is None and p['experience'] is None for role,p,_,_ in b.calls if role=='action'))
    def test_testing_baseline_only_actions_and_final_gold(self):
        class Recorded(Backend):
            def __init__(self):super().__init__();self.evaluations=[]
            def evaluate(self,stage,payload,directory):
                self.evaluations.append(stage)
                return super().evaluate(stage,payload,directory)
        from temporal_contract_analyzer.experience_approval import freeze
        loop=self.prepare(condition='baseline',mode='testing',max_attempts=1,memory_snapshot=freeze(self.store),
                          gold_evaluator=dict(command=['synthetic-gold']),visible_evaluator=None)
        self.assertEqual(loop.verify()['total_request_cap'],24)
        b=Recorded();state=loop.run(b,execute=True)
        self.assertEqual(state['status'],'scored',state.get('error'))
        self.assertEqual([r[0] for r in b.calls],['action'])
        self.assertEqual(b.evaluations,['gold'])
        self.assertIsNone(b.calls[0][1]['contract'])
        self.assertIsNone(b.calls[0][1]['experience'])
        self.assertFalse((loop.root/'expert-summary-task.json').exists())

    def test_model_budget_and_original_snapshot_are_fixed(self):
        loop=self.prepare();p=loop.verify();self.assertEqual(p['total_request_cap'],120)
        b=Backend(3);loop.run(b,execute=True);self.assertTrue(all(m==MODEL for _,_,m,_ in b.calls))
        self.assertEqual((loop.root/'original/main.py').read_text(),'value = 0\n')
        with self.assertRaises(EvidenceError):self.prepare(max_attempts=4)

    def test_task_citation_alias_still_requires_matching_public_content(self):
        from temporal_contract_analyzer.tempoevo_v4 import evidence_valid
        for name in ('TASK','original task','Original task',' task '):
            evidence_valid([dict(file=name,quote='Preserve accepted work.')],'Preserve accepted work.',{})
            with self.assertRaises(EvidenceError):
                evidence_valid([dict(file=name,quote='Delete accepted work.')],'Preserve accepted work.',{})
        with self.assertRaises(EvidenceError):
            evidence_valid([dict(file='unknown source',quote='Preserve accepted work.')],'Preserve accepted work.',{})

    def test_markdown_citations_tolerate_inline_code_formatting_not_changed_words(self):
        from temporal_contract_analyzer.tempoevo_v4 import evidence_valid
        sources={'README.md':'`start()` may emit\nmore packets before `showProgress` returns.',
                 'main.js':'const key = `original`;'}
        evidence_valid([dict(file='README.md',quote='start() may emit more packets before showProgress returns.')],'',sources)
        for name,quote in [('README.md','begin() may emit more packets'),('main.js','const key = original;')]:
            with self.subTest(source=name):
                with self.assertRaises(EvidenceError):evidence_valid([dict(file=name,quote=quote)],'',sources)

    def test_extraction_schema_uses_the_review_library_vocabulary(self):
        from temporal_contract_analyzer.tempoevo_v4 import EXPERIENCE_SCHEMA
        from temporal_contract_analyzer._session_runtime.schema_validator import validate
        valid=dict(labels=['I'],requires=['entry_snapshot'],excludes=[],
            rules=[dict(category='verification',body='Verify accepted identity.')],limitations=[])
        validate(valid,EXPERIENCE_SCHEMA)
        for field,value in [('labels',['visit-lifetime']),('requires',['Confirm ownership']),
                            ('excludes',['Do not change another consumer']),
                            ('rules',[dict(category='startup-ordering',body='Verify startup.')])]:
            with self.subTest(field=field):
                invalid=deepcopy(valid);invalid[field]=value
                with self.assertRaises(ValueError):validate(invalid,EXPERIENCE_SCHEMA)
    def test_independent_repeats_start_from_identical_original(self):
        a=self.prepare();b=self.prepare();self.assertEqual(a.verify()['original_inventory'],b.verify()['original_inventory'])
        for loop in (a,b):self.assertEqual(loop.run(Backend(),execute=True)['attempts'][0]['candidate_sources']['main.py'],'value = 1\n')

    def test_fixed_contract_ablation_keeps_action_budget(self):
        from temporal_contract_analyzer import experience_approval as approval
        task='Preserve accepted work.'
        loop=self.prepare(condition='fixed_contract')
        state=loop.run(Backend(3),execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'));self.assertEqual(len(state['attempts']),3)
        self.assertEqual(len(state['diagnoses']),2)
        self.assertTrue(all(not d['structured_delta'] for d in state['diagnoses']))

    def test_human_summary_remains_failure_candidate_not_success(self):
        loop=self.prepare();loop.run(Backend(99),execute=True)
        summary=dict(expert='SYNTHETIC_HUMAN',confirmed_conclusions=[],unverified_hypotheses=[],
            unresolved_behaviors=['Still failing'],boundaries_counterexamples=['Synthetic'],suggested_checks=['Recheck'],
            experience=dict(labels=['I'],requires=['entry_snapshot'],excludes=[],rules=[dict(category='verification',body='Check retained selection identity.')],limitations=['Not a successful repair']))
        task=loop.submit_expert(summary);self.assertEqual(task['expert'],'SYNTHETIC_HUMAN')
        with self.assertRaisesRegex(EvidenceError,'categorized library'):loop.publish_candidate('expert')
        self.assertFalse(read(loop.root/'candidate-pool/expert.json')['effectiveness_verified'])
        self.assertEqual(loop.state()['status'],'awaiting_content_review')
        from temporal_contract_analyzer import experience_approval as approval
        self.assertEqual(approval.freeze(self.store)['entries'],[])
        with self.assertRaises(EvidenceError):loop.submit_expert(summary)

    def test_evaluator_is_bound_and_mutations_invalidate(self):
        script=self.root/'visible.py';script.write_text('print("visible")')
        loop=self.prepare(visible_evaluator=dict(command=['python3',str(script)]))
        script.write_text('print("changed")')
        with self.assertRaises(EvidenceError):loop.verify()

    def test_actual_native_adapter_receives_fixed_model_and_separate_stage(self):
        from unittest.mock import patch
        from temporal_contract_analyzer.tempoevo_backend import NativeV4Backend
        adapter=NativeV4Backend(dict(binary='/synthetic/codex'))
        payload=dict(task='Public task',sources={'main.py':'value = 0\n'},schema={})
        directory=self.root/'adapter';directory.mkdir()
        fake=dict(completed=True,infrastructure_valid=True,output=contract(),usage=dict(requests_started=1,total_usage=dict(total_tokens=7)))
        with patch('temporal_contract_analyzer.execution_backend.NativeBackend.execute',return_value=fake) as call:
            result=adapter.execute('diagnosis',payload,MODEL,dict(requests=12,seconds=600),directory)
        self.assertTrue(result['valid']);self.assertEqual(call.call_args[0][1],'analysis')
        self.assertEqual(call.call_args[0][0]['execution_policy'],'tempoevo-trajectory-v13')
        self.assertEqual(result['requests'],1)

    def test_action_adapter_accepts_complete_candidate_without_read_audit(self):
        from unittest.mock import patch
        from temporal_contract_analyzer.tempoevo_backend import NativeV4Backend
        adapter=NativeV4Backend(dict(binary='/synthetic/codex'))
        payload=dict(task='Public task',sources={'main.py':'value = 0\n'})
        fake=dict(completed=True,infrastructure_valid=True,scoring_admissible=True,
            final_candidate=str(self.source),receipt=dict(source_body_proofs=[]),
            usage=dict(requests_started=1,total_usage=dict(total_tokens=7)))
        with patch('temporal_contract_analyzer.execution_backend.NativeBackend.execute',return_value=fake):
            result=adapter.execute('action',payload,MODEL,dict(requests=24,seconds=600),self.root/'action-adapter')
        self.assertTrue(result['valid'],result)
        self.assertEqual(result['native_receipt']['source_body_proofs'],[])
        self.assertEqual(result['candidate_sources'],{'main.py':'value = 0\n'})

    def test_action_adapter_still_rejects_invalid_candidate_or_archive(self):
        from unittest.mock import patch
        from temporal_contract_analyzer.tempoevo_backend import NativeV4Backend
        adapter=NativeV4Backend(dict(binary='/synthetic/codex'))
        fake=dict(completed=True,infrastructure_valid=True,scoring_admissible=False,
            final_candidate=str(self.source),usage=dict(requests_started=1))
        with patch('temporal_contract_analyzer.execution_backend.NativeBackend.execute',return_value=fake):
            result=adapter.execute('action',dict(task='Public task',sources={'main.py':'value = 0\n'}),MODEL,
                dict(requests=24,seconds=600),self.root/'invalid-action-adapter')
        self.assertFalse(result['valid']);self.assertEqual(result['error'],'Candidate or archive validation failed')

    def test_native_evaluator_writes_artifacts_outside_the_frozen_candidate(self):
        import sys
        from temporal_contract_analyzer.tempoevo_backend import NativeV4Backend
        directory=self.root/'evaluation';directory.mkdir()
        script=self.root/'evaluate.py'
        script.write_text('import json,sys\nfrom pathlib import Path\n'
            'assert (Path(sys.argv[-1])/"main.py").read_text()=="value = 0\\n"\n'
            'Path("score-artifact.json").write_text("{}")\n'
            'print(json.dumps(dict(passed=True)))\n')
        result=NativeV4Backend({}).evaluate('gold',dict(candidate=str(self.source),
            evaluator=dict(command=[sys.executable,str(script)])),directory)
        self.assertTrue(result['valid'],result)
        self.assertTrue(result['passed'])
        self.assertTrue((directory/'score-artifact.json').is_file())
        self.assertEqual(sorted(p.name for p in self.source.iterdir()),['main.py'])

    def test_cancellation_during_stage_keeps_accounting_and_stops(self):
        loop=self.prepare()
        class CancelBackend(Backend):
            def execute(inner,*args):
                result=super().execute(*args);loop.cancel();return result
        state=loop.run(CancelBackend(),execute=True)
        self.assertEqual(state['status'],'cancelled');self.assertEqual(state['stages'][0]['requests'],1)
        self.assertEqual(len(state['stages']),1)

    def test_frozen_retrieval_delivers_approved_only_before_contract(self):
        import test_experience_memory as fixtures
        f=fixtures.MemoryTests('test_storage_preserves_single_source_body_and_evidence');f.setUp();self.addCleanup(f.doCleanups)
        approved=f.add();pending=deepcopy(f.payload);pending.update(id='not-approved');pending['review']['status']='candidate'
        memory.add(f.store,pending,[f.source])
        for condition in ('structured','bm25'):
            loop=self.prepare(store=str(f.store),condition=condition,
                task='Preserve accepted work. Keep the entry snapshot.')
            backend=Backend();state=loop.run(backend,execute=True)
            self.assertEqual(state['status'],'passed',state.get('error'))
            delivery=read(loop.root/'delivery.json');self.assertEqual(delivery['selected_sha256s'],[approved['sha256']])
            contract_call=next(c for c in backend.calls if c[0]=='contract')
            self.assertIn(approved['rules'][0]['body'],contract_call[1]['experience'])
            if condition=='structured':
                self.assertEqual(backend.calls[0][0],'selection')
                self.assertEqual([c['sha256'] for c in backend.calls[0][1]['candidates']],[approved['sha256']])

    def test_no_ast_testing_keeps_sources_memory_contract_and_final_score(self):
        from unittest.mock import patch
        from temporal_contract_analyzer import experience_approval as approval
        import test_experience_memory as fixtures
        f=fixtures.MemoryTests('test_storage_preserves_single_source_body_and_evidence')
        f.setUp();self.addCleanup(f.doCleanups);approved=f.add()
        with patch('temporal_contract_analyzer.preanalysis.analyze_candidate',side_effect=AssertionError('AST must not run')):
            loop=self.prepare(store=str(f.store),mode='testing',condition='structured',ast_policy='disabled',
                task='Preserve accepted work. Keep the entry snapshot.',memory_snapshot=approval.freeze(f.store),
                gold_evaluator=dict(command=['synthetic-gold']),visible_evaluator=None)
        backend=Backend();state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'scored',state.get('error'))
        self.assertTrue(state['gold_result']['passed'])
        self.assertEqual([c[0] for c in backend.calls],['selection','contract','action'])
        for stage,payload,_,_ in backend.calls:
            self.assertEqual(payload['ast'],{})
            self.assertEqual(payload['sources'],{'main.py':'value = 0\n'})
            if stage in ('contract','action'):self.assertIn(approved['rules'][0]['body'],payload['experience'])
        self.assertEqual(loop.verify()['total_request_cap'],48)
        self.assertEqual(read(loop.root/'ast-evidence.json'),{})
        self.assertEqual((loop.root/'original/main.py').read_text(),'value = 0\n')

    def test_unknown_ast_policy_is_rejected(self):
        with self.assertRaisesRegex(EvidenceError,'Invalid AST policy'):
            self.prepare(ast_policy='maybe')

    def test_cli_prepare_status_never_call_models(self):
        from temporal_contract_analyzer.cli import main
        from contextlib import redirect_stdout
        from io import StringIO
        from unittest.mock import patch
        config=self.root/'config.json';config.write_text(json.dumps(dict(task='Preserve accepted work.',candidate=str(self.source),store=str(self.store),mode='learning',condition='contract',visible_evaluator=dict(command=['synthetic-visible']),training_evaluator=dict(command=['synthetic-training']))))
        root=self.root/'cli'
        with patch('temporal_contract_analyzer.tempoevo_backend.NativeV4Backend.execute',side_effect=AssertionError('No models')),redirect_stdout(StringIO()):
            self.assertEqual(main(['tempoevo','prepare',str(config),'--root',str(root)]),0)
            self.assertEqual(main(['tempoevo','status','--root',str(root)]),0)

    def test_shortened_budget_does_not_claim_three_failures(self):
        loop=self.prepare(max_attempts=2);state=loop.run(Backend(99),execute=True)
        self.assertEqual(state['status'],'repair_exhausted');self.assertEqual(len(state['attempts']),2)
        self.assertFalse((loop.root/'expert-summary-task.json').exists())

    def test_native_archive_store_cannot_receive_new_versions(self):
        loop=self.prepare();loop.run(Backend(2),execute=True)
        with self.assertRaisesRegex(EvidenceError,'categorized library'):loop.publish_candidate('success')
        self.assertEqual(memory.records(self.store),[])

    def test_wrong_actual_model_stops_without_a_behavioral_failure(self):
        loop=self.prepare()
        class WrongModel(Backend):
            def execute(inner,*args):
                result=super().execute(*args);result['model']=dict(model='wrong',reasoning_effort='low');return result
        state=loop.run(WrongModel(),execute=True)
        self.assertEqual(state['status'],'execution_invalid');self.assertEqual(state['attempts'],[])
        self.assertEqual(loop.report()['requests'],1)

    def test_structured_revision_rechecks_from_same_frozen_bank(self):
        loop=self.prepare(condition='structured')
        state=loop.run(Backend(2,'contract_gap',revise=True),execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'))
        self.assertTrue((loop.root/'revisions/2-delivery.json').exists())
        self.assertEqual(loop.verify()['memory_snapshot_sha256'],read(loop.root/'memory-snapshot.json')['sha256'])


    def test_completed_contract_checkpoint_reuses_archive_without_double_billing(self):
        from temporal_contract_analyzer.tempoevo_v4 import CONTRACT_SCHEMA
        loop=self.prepare();p=loop.verify();backend=Backend();loop.retrieve(p)
        payload=dict(task=p['task'],sources={'main.py':'value = 0\n'},ast=read(loop.root/'ast-evidence.json'),experience=None,schema=CONTRACT_SCHEMA)
        loop._step(p,backend,'contract','contract',payload)
        state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'))
        self.assertEqual([r[0] for r in backend.calls].count('contract'),1)
        self.assertEqual(loop.report()['requests'],2)

    def test_invalid_overbudget_measurement_is_retained(self):
        loop=self.prepare()
        class Overspend(Backend):
            def execute(inner,*args):
                result=super().execute(*args);result['requests']=100;return result
        state=loop.run(Overspend(),execute=True)
        self.assertEqual(state['status'],'execution_invalid');self.assertEqual(loop.report()['requests'],100)
