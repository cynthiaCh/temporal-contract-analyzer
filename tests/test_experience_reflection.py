"""Offline reflection proposals, lineage and review boundaries."""
from copy import deepcopy
import json
import unittest
from temporal_contract_analyzer import experience_reflection as reflection,experience_memory as memory,experience_approval as approval
from temporal_contract_analyzer.core import EvidenceError
from temporal_contract_analyzer.tempoevo_v4 import read
import test_tempoevo_v4 as fixtures
import test_experience_memory as mf

class ReflectionTests(unittest.TestCase):
    setUp=fixtures.V4Tests.setUp
    prepare=fixtures.V4Tests.prepare

    def bundle(self, identifier='entry-binding'):
        fixture=mf.MemoryTests();fixture.setUp();self.addCleanup(fixture.temp.cleanup)
        payload=deepcopy(fixture.payload);payload['id']=identifier
        return memory.add(self.store,payload,[fixture.source])

    def experience(self,b):
        return dict(labels=b['labels'],requires=b['requires'],excludes=b['excludes'],rules=[{k:r[k] for k in ('category','body')} for r in b['rules']],limitations=['Synthetic reflection'])

    def update(self,operation,targets):
        return dict(operation=operation,target_sha256s=targets,reason='Synthetic source-supported change.',change_summary=['Add checkpoint'],failure_attribution='experience_gap',supporting_attempts=[1])





    def test_forged_targets_delta_and_implementation_blame_are_rejected(self):
        a=self.bundle();exp=self.experience(a);exp['rules'][0]['body']+=' New boundary.'
        for change in [dict(target_sha256s=['f'*64]),dict(supporting_attempts=[3]),dict(change_summary=[]),dict(failure_attribution='implementation_gap')]:
            update=self.update('revise',[a['sha256']]);update.update(change)
            with self.assertRaises(EvidenceError):reflection.plan(exp,update,[a],1)
        with self.assertRaises(EvidenceError):reflection.plan(exp,self.update('evidence',[a['sha256']]),[a],1)

    def test_new_duplicate_is_deterministically_diverted(self):
        a=self.bundle();u=self.update('new',[])
        result=reflection.plan(self.experience(a),u,[a],1)
        self.assertEqual(result['operation'],'evidence');self.assertEqual(result['target_sha256s'],[a['sha256']])

    def test_explicit_merge_of_duplicate_ids_preserves_all_targets(self):
        a=self.bundle();b=self.bundle('duplicate-entry')
        result=reflection.plan(self.experience(a),self.update('merge',[a['sha256'],b['sha256']]),[a,b],1)
        self.assertEqual(result['operation'],'merge');self.assertEqual(len(result['target_sha256s']),2)

    def test_reflection_uses_frozen_shortlist_not_unreviewed_live_records(self):
        a=self.bundle();p=dict(condition='structured',task='Capture entry identity',memory_snapshot=dict(entries=[dict(bundle=a)]))
        self.assertEqual([b['sha256'] for b in reflection.related(p,dict(selected_sha256s=[a['sha256']]))],[a['sha256']])
        p['condition']='baseline';self.assertEqual(reflection.related(p,{}),[])

    def test_update_search_is_independent_of_five_entry_solver_delivery(self):
        a=self.bundle();bundles=[]
        for i in range(20):
            value=deepcopy(a);value.update(id='synthetic-'+str(i),sha256=str(i).zfill(64));bundles.append(value)
        p=dict(condition='structured',task='Capture entry identity',memory_snapshot=dict(entries=[dict(bundle=b) for b in bundles]))
        related=reflection.related(p,dict(selected_sha256s=[bundles[-1]['sha256']]))
        self.assertEqual(len(related),3)
        self.assertEqual(related[0],bundles[-1])
        self.assertLessEqual({b['sha256'] for b in related},{b['sha256'] for b in bundles})
        p['condition']='baseline';self.assertEqual(reflection.related(p,{}),[])

    def test_new_with_existing_guidance_needs_an_independent_increment(self):
        a=self.bundle();exp=self.experience(a);exp['rules'][0]['body']+=' Independent operation.'
        for missing in ('change_summary','supporting_attempts'):
            update=self.update('new',[]);update[missing]=[]
            with self.assertRaises(EvidenceError):reflection.plan(exp,update,[a],1)

    def test_expert_failure_summary_can_propose_revision_without_claiming_success(self):
        from unittest.mock import patch
        a=self.bundle();loop=self.prepare()
        with patch('temporal_contract_analyzer.experience_reflection.related',return_value=[a]):state=loop.run(fixtures.Backend(99),execute=True)
        self.assertEqual(state['status'],'awaiting_expert_summary')
        self.assertFalse((loop.root/'candidate-pool').exists())
        exp=self.experience(a);exp['rules'][-1]['body']+=' Inspect unresolved boundaries.'
        summary=dict(expert='Synthetic human',confirmed_conclusions=[],unverified_hypotheses=[],unresolved_behaviors=['Still failing'],boundaries_counterexamples=[],suggested_checks=[],experience=exp,reflection_update=self.update('revise',[a['sha256']]))
        loop.submit_expert(summary)
        with self.assertRaisesRegex(EvidenceError,'categorized library'):loop.publish_candidate('expert')
        self.assertEqual(loop.state()['status'],'awaiting_content_review')
        self.assertFalse(read(loop.root/'candidate-pool/expert.json')['effectiveness_verified'])

    def test_single_extraction_call_receives_related_context_and_emits_update(self):
        from unittest.mock import patch
        a=self.bundle();exp=self.experience(a);update=self.update('new',[])
        class Backend(fixtures.Backend):
            def execute(self,kind,payload,model,limits,directory):
                result=super().execute(kind,payload,model,limits,directory)
                if kind=='extract':
                    self.asserted=payload['related_experiences']
                    result['output']=dict(experience=exp,update=dict(update,supporting_attempts=[1,2]),abstract='Preserve accepted identity.',contributions=[])
                return result
        loop=self.prepare();backend=Backend(2)
        with patch('temporal_contract_analyzer.experience_reflection.related',return_value=[a]):state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'));self.assertEqual(backend.asserted,[a])
        self.assertEqual(len([c for c in backend.calls if c[0]=='extract']),1)
        self.assertEqual(read(loop.root/'candidate-pool/success.json')['reflection_update']['operation'],'evidence')
