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

    def record(self,operation='revise'):
        a=self.bundle();b=self.bundle('second-entry') if operation=='merge' else None
        related=[a]+([b] if b else []);experience=self.experience(a)
        if operation!='evidence':experience['rules'][-1]['body']+=' Verify later reuse.'
        update=reflection.plan(experience,self.update(operation,[x['sha256'] for x in related]),related,1)
        loop=self.prepare();loop.run(fixtures.Backend(),execute=True)
        record=read(loop.root/'candidate-pool/success.json');record.update(experience=experience,related_experiences=related,reflection_update=update)
        loop.save('candidate-pool/success.json',record)
        return loop,a,b

    def test_revision_and_merge_retain_lineage_without_inheriting_acceptance(self):
        loop,a,_=self.record('revise');code=loop.publish_candidate('success')
        bundle=next(b for b in memory.records(self.store) if b['sha256']==code)
        self.assertEqual(bundle['id'],a['id']);self.assertEqual(bundle['parent_sha256'],a['sha256'])
        self.assertEqual(bundle['review']['status'],'candidate');self.assertEqual(approval.freeze(self.store)['entries'],[])
        self.assertEqual(loop.publish_candidate('success'),code)
        self.assertEqual(next(b for b in memory.records(self.store) if b['sha256']==a['sha256']),a)

    def test_merge_has_one_primary_parent_and_all_source_targets(self):
        loop,a,b=self.record('merge');code=loop.publish_candidate('success')
        bundle=next(x for x in memory.records(self.store) if x['sha256']==code)
        self.assertEqual(bundle['parent_sha256'],a['sha256'])
        self.assertIn(b['sha256'],' '.join(bundle['audit']['notes']))
        self.assertEqual(len(memory.records(self.store)),3)

    def test_duplicate_is_evidence_only_review_is_separate_and_idempotent(self):
        loop,a,_=self.record('evidence');code=loop.publish_candidate('success')
        self.assertEqual(len(memory.records(self.store)),1);self.assertEqual(loop.publish_candidate('success'),code)
        self.assertEqual(reflection.proposals(self.store)[0]['proposal']['status'],'awaiting_human_review')
        with self.assertRaises(EvidenceError):reflection.review_evidence(self.store,code,dict(reviewer='',decision='accept',reason='test'))
        reflection.review_evidence(self.store,code,dict(reviewer='Synthetic Human',decision='accept',reason='Synthetic evidence checked'))
        self.assertEqual(len(reflection.proposals(self.store)[0]['decisions']),1)
        self.assertEqual(reflection.proposals(self.store)[0]['review_status'],'accept')
        self.assertEqual(approval.freeze(self.store)['entries'],[]);self.assertEqual(memory.records(self.store),[a])

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

    def test_expert_failure_summary_can_propose_revision_without_claiming_success(self):
        from unittest.mock import patch
        a=self.bundle();loop=self.prepare()
        with patch('temporal_contract_analyzer.experience_reflection.related',return_value=[a]):state=loop.run(fixtures.Backend(99),execute=True)
        self.assertEqual(state['status'],'awaiting_expert_summary')
        self.assertFalse((loop.root/'candidate-pool').exists())
        exp=self.experience(a);exp['rules'][-1]['body']+=' Inspect unresolved boundaries.'
        summary=dict(expert='Synthetic human',confirmed_conclusions=[],unverified_hypotheses=[],unresolved_behaviors=['Still failing'],boundaries_counterexamples=[],suggested_checks=[],experience=exp,reflection_update=self.update('revise',[a['sha256']]))
        loop.submit_expert(summary);code=loop.publish_candidate('expert')
        bundle=next(x for x in memory.records(self.store) if x['sha256']==code)
        self.assertEqual(bundle['parent_sha256'],a['sha256']);self.assertEqual(loop.state()['status'],'awaiting_content_review')
        self.assertFalse(read(loop.root/'candidate-pool/expert.json')['effectiveness_verified'])

    def test_single_extraction_call_receives_related_context_and_emits_update(self):
        from unittest.mock import patch
        a=self.bundle();exp=self.experience(a);update=self.update('new',[])
        class Backend(fixtures.Backend):
            def execute(self,kind,payload,model,limits,directory):
                result=super().execute(kind,payload,model,limits,directory)
                if kind=='extract':
                    self.asserted=payload['related_experiences']
                    result['output']=dict(experience=exp,update=update)
                return result
        loop=self.prepare();backend=Backend()
        with patch('temporal_contract_analyzer.experience_reflection.related',return_value=[a]):state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'));self.assertEqual(backend.asserted,[a])
        self.assertEqual(len([c for c in backend.calls if c[0]=='extract']),1)
        self.assertEqual(read(loop.root/'candidate-pool/success.json')['reflection_update']['operation'],'evidence')
