"""Synthetic public-source applicability assessments; no model or Gold calls."""
from copy import deepcopy
import unittest
from unittest.mock import patch
import test_experience_memory as fixtures
import test_tempoevo_v4 as trajectory_fixtures
from temporal_contract_analyzer import semantic_retrieval as retrieval,experience_memory as memory
from temporal_contract_analyzer.core import EvidenceError

class RetrievalTests(unittest.TestCase):
    setUp=fixtures.MemoryTests.setUp

    def setup_recall(self,count=2):
        visible=fixtures.MemoryTests.visible(self)
        bundles=[]
        for i in range(count):
            value=deepcopy(self.payload);value['id']='experience-'+str(i)
            value['rules'][0]['body']='Save accepted entry snapshot '+str(i)
            bundles.append(memory.seal(value))
        recalled=retrieval.recall(visible['task'],{},visible['analysis'],bundles)
        return visible,bundles,recalled

    def assessment(self,code,task,relevance='direct'):
        evidence=[dict(file='TASK',quote=task)]
        return dict(sha256=code,relevance=relevance,
            premises=[dict(condition='Accepted entry snapshot',status='supported',evidence=evidence)],
            object_mapping='Entry document maps to accepted command',contribution='Preserve accepted command identity',
            covered_obligations=['O1'],supporting_evidence=evidence,redundant_with=[],reason='Synthetic assessment')

    def choose(self,visible,bundles,recalled,rows):
        return retrieval.select(dict(assessments=rows),recalled,visible['analysis'],visible['task'],{},bundles)

    def test_matching_labels_do_not_admit_unsupported_domain_premise(self):
        v,b,r=self.setup_recall();rows=[self.assessment(c['sha256'],v['task']) for c in r['candidates']]
        bad=rows[0];bad['premises'].append(dict(condition='Retained progress decoding audit exists',status='unknown',evidence=[]))
        chosen=self.choose(v,b,r,rows)
        self.assertEqual(chosen['selected_sha256s'],[rows[1]['sha256']])
        self.assertEqual(next(d for d in chosen['route']['assessments'] if d['sha256']==bad['sha256'])['selection_reason'],'unsupported_or_irrelevant')

    def test_unknown_weak_and_contradicted_are_not_quota_filler(self):
        for relevance in ['unknown','weak','not_applicable']:
            v,b,r=self.setup_recall(1);row=self.assessment(r['candidates'][0]['sha256'],v['task'],relevance)
            self.assertEqual(self.choose(v,b,r,[row])['selected_sha256s'],[])
        row['relevance']='direct';row['premises'][0]['status']='contradicted'
        self.assertIsNone(self.choose(v,b,r,[row])['experience_text'])

    def test_cross_domain_transfer_requires_supported_mapping_and_public_quotes(self):
        v,b,r=self.setup_recall(1);row=self.assessment(r['candidates'][0]['sha256'],v['task'],'transferable')
        self.assertEqual(self.choose(v,b,r,[row])['selected_sha256s'],[row['sha256']])
        row['supporting_evidence'][0]['quote']='REFERENCE_IMPLEMENTATION_SECRET'
        with self.assertRaises(EvidenceError):self.choose(v,b,r,[row])

    def test_missing_and_duplicate_assessments_are_invalid(self):
        v,b,r=self.setup_recall();row=self.assessment(r['candidates'][0]['sha256'],v['task'])
        with self.assertRaises(EvidenceError):self.choose(v,b,r,[row,row])
        with self.assertRaises(ValueError):self.choose(v,b,r,[row])

    def test_duplicate_text_is_suppressed_even_if_model_omits_redundancy(self):
        v,b,r=self.setup_recall();rows=[self.assessment(c['sha256'],v['task']) for c in r['candidates']]
        chosen=self.choose(v,b,r,rows)
        self.assertEqual(len(chosen['selected_sha256s']),1)
        self.assertIn('redundant',[d['selection_reason'] for d in chosen['route']['assessments']])

    def test_text_budget_is_enforced_on_actual_delivery(self):
        v,b,r=self.setup_recall(1);row=self.assessment(r['candidates'][0]['sha256'],v['task'])
        with patch.object(retrieval,'MAX_CHARACTERS',10):
            chosen=self.choose(v,b,r,[row]);self.assertIsNone(chosen['experience_text'])
            self.assertEqual(chosen['route']['assessments'][0]['selection_reason'],'text_budget')

    def test_five_entry_cap_and_complementary_obligation_coverage(self):
        v,b,_=self.setup_recall(8)
        topics=['invoice amount currency payment receipt', 'document buffer trailing save timer',
                'query signal reconnect observer cancellation', 'packet decoder arrival frame sequence',
                'generator iterator cleanup await return', 'modal listener shutdown disposal subscription',
                'transaction journal commit durable ordering', 'command response identity callback navigation']
        for bundle,topic in zip(b,topics):
            for rule in bundle['rules']:rule['body']='Preserve accepted entry: '+topic
            sealed=memory.seal({k:value for k,value in bundle.items() if k not in ('sha256','body_sha256')})
            bundle.clear();bundle.update(sealed)
        r=retrieval.recall(v['task'],{},v['analysis'],b)
        rows=[self.assessment(c['sha256'],v['task']) for c in r['candidates']]
        v['analysis']['obligation_labels'].append(dict(code='A',statement='Retain accepted action.',evidence=[dict(file='TASK',line=1,quote='accepted')]))
        rows[-1]['relevance']='transferable';rows[-1]['covered_obligations']=['O2']
        chosen=self.choose(v,b,r,rows)
        self.assertEqual(len(chosen['selected_sha256s']),5)
        self.assertIn(rows[-1]['sha256'],chosen['selected_sha256s'])
        self.assertLessEqual(len(chosen['experience_text']),retrieval.MAX_CHARACTERS)

    def test_recall_is_bounded_and_stable_under_library_order(self):
        v,b,r=self.setup_recall(23)
        reverse=retrieval.recall(v['task'],{},v['analysis'],list(reversed(b)))
        self.assertEqual(len(r['candidates']),20)
        self.assertEqual(r['candidates'],reverse['candidates'])
        self.assertEqual(r['eligible_count'],23)

    def test_unsupported_mechanism_never_reaches_semantic_model(self):
        v,b,r=self.setup_recall(1);v['analysis']['facts'][0].update(state='unknown',evidence=[])
        self.assertEqual(retrieval.recall(v['task'],{},v['analysis'],b)['candidates'],[])

    def test_prompt_and_schema_use_only_public_inputs(self):
        v,b,r=self.setup_recall(1)
        p=retrieval.payload(v['task'],{}, {},v['analysis'],r)
        self.assertNotIn('gold',p);self.assertNotIn('verdict',p);self.assertIn('all material scenario prerequisites',p['instruction'])
        self.assertNotIn('audit',p['candidates'][0])

class RetrievalTrajectoryTests(unittest.TestCase):
    setUp=trajectory_fixtures.V4Tests.setUp
    prepare=trajectory_fixtures.V4Tests.prepare

    def test_selection_budget_and_historical_execution_boundary(self):
        from temporal_contract_analyzer.tempoevo_v4 import read,VERSION
        loop=self.prepare(condition='structured');p=loop.verify()
        self.assertEqual(p['total_request_cap'],168)
        self.assertEqual(p['limits']['selection']['requests'],12)
        self.assertEqual(p['retrieval_policy']['max_experiences'],5)
        p['schema_version']='tempoevo-trajectory-v10';loop.save('protocol.json',p)
        with self.assertRaisesRegex(EvidenceError,'Historical'):loop.verify()
        self.assertEqual(VERSION,'tempoevo-trajectory-v11')

    def test_contract_revision_reassesses_and_completed_stages_are_not_rebilled(self):
        from temporal_contract_analyzer.tempoevo_v4 import read
        f=fixtures.MemoryTests();f.setUp();self.addCleanup(f.doCleanups);f.add()
        analysis=f.visible()['analysis']
        loop=self.prepare(condition='structured',store=str(f.store),routing_analysis=analysis,
            task='Preserve accepted work. Keep the entry snapshot.')
        class Revising(trajectory_fixtures.Backend):
            def execute(inner,*args):
                result=super().execute(*args)
                if args[0]=='diagnosis':result['output']['routing_analysis']=analysis
                return result
        backend=Revising(2,'contract_gap',revise=True)
        state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'))
        self.assertEqual([s['key'] for s in state['stages'] if s['kind']=='selection'],['selection-1','selection-2'])
        self.assertEqual(len(state['attempts']),2)
        count=len(backend.calls);loop.run(backend,execute=True);self.assertEqual(len(backend.calls),count)
        self.assertEqual(read(loop.root/'revisions/2-delivery.json')['route']['schema_version'],retrieval.VERSION)
