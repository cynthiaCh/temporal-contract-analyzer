"""Inline observations, frozen ranking and stable-ID edits; synthetic models only."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from temporal_contract_analyzer import compact_experience as compact,experience_approval as approval,experience_learning as learning,business_retrieval as retrieval
from temporal_contract_analyzer.tempoevo_v4 import Trajectory,read
from temporal_contract_analyzer.core import EvidenceError
from test_business_retrieval import item,TASK
from test_tempoevo_v4 import Backend

class LearningTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.store=self.root/'library';self.store.mkdir();self.file=self.store/'entries.json'
        self.file.write_text(json.dumps(dict(schema_version=compact.VERSION,experiences=[item('save','Keep accepted work.'),item('other','Keep accepted work.')])) )
        self.source=self.root/'source';self.source.mkdir();(self.source/'main.py').write_text('value = 0\n')
    def prepare(self,name,**kw):
        config=dict(task=TASK,candidate=str(self.source),store=str(self.store),condition='structured',mode='learning',
            visible_evaluator=dict(command=['synthetic-visible']),training_evaluator=dict(command=['synthetic-training']),task_id='case-1')
        config.update(kw);loop=Trajectory(self.root/name);loop.prepare(config);return loop
    def test_first_pass_skips_extraction_and_testing_never_writes_usage(self):
        loop=self.prepare('first');backend=Backend();state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'));self.assertNotIn('extract',[r[0] for r in backend.calls])
        self.assertFalse((loop.root/'candidate-pool/success.json').exists())
        before=self.file.read_bytes()
        loop=self.prepare('test',mode='testing',training_evaluator=None,gold_evaluator=dict(command=['synthetic-gold']),memory_snapshot=approval.freeze(self.store))
        self.assertEqual(loop.run(Backend(),execute=True)['status'],'scored');self.assertEqual(self.file.read_bytes(),before)
    def test_observations_are_idempotent_model_specific_and_do_not_change_content(self):
        snapshot=approval.freeze(self.store);bundles={e['bundle']['id']:e['bundle'] for e in snapshot['entries']};expected={'save':bundles['save']['sha256']}
        for _ in range(2):learning.record_usage(self.store,'case-a','model-a',expected,{'save':'adopted'})
        learning.record_usage(self.store,'case-b','model-b',expected,{'save':'misleading'})
        current=compact.load(self.file)['experiences'][0];metadata=current['learning']
        self.assertEqual(metadata['usage_by_model']['model-a']['positive_cases'],1)
        self.assertEqual(metadata['usage_by_model']['model-a']['delivered_cases'],1)
        self.assertEqual(learning.score(metadata,'model-a'),1);self.assertEqual(learning.score(metadata,'model-b'),-1)
        self.assertEqual(compact._bundle(self.file,current)[0],bundles['save'])
        self.assertEqual(approval.validate_snapshot(self.store,snapshot),snapshot)
        learning.record_usage(self.store,'case-c','model-a',{'save':'0'*64},{'save':'rule_error'})
        self.assertEqual(compact.load(self.file)['experiences'][0]['review']['decision'],'accept')
    def test_weight_is_frozen_and_not_exposed_to_selector(self):
        metadata=learning.empty();metadata['usage_by_model']['model-a']=dict(delivered_cases=1,positive_cases=1,negative_cases=0,cases={'case-a':'adopted'})
        value=compact.load(self.file);value['experiences'][1]['learning']=metadata;self.file.write_text(json.dumps(value))
        snapshot=approval.freeze(self.store);entries=snapshot['entries'];bundles=[e['bundle'] for e in entries]
        recalled=retrieval.recall(TASK,{},bundles,learning={e['bundle']['sha256']:e.get('learning') for e in entries},model='model-a')
        self.assertEqual(recalled['candidates'][0]['id'],'other')
        payload=retrieval.payload(TASK,{}, {},recalled)
        self.assertNotIn('weights',payload);self.assertNotIn('learning',json.dumps(payload))
    def test_contribution_requires_delivered_rule_and_changed_code(self):
        bundle=approval.freeze(self.store)['entries'][0]['bundle']
        attempts=[dict(acceptance_passed=False,candidate_sources={'main.py':'value = 1\n'},delivered_sha256s=[bundle['sha256']]),
                  dict(acceptance_passed=True,candidate_sources={'main.py':'value = 2\n'},delivered_sha256s=[bundle['sha256']])]
        row=dict(experience_sha256=bundle['sha256'],rule_id=bundle['rules'][0]['id'],rule_quote=bundle['rules'][0]['body'],decision='adopted',
            before=dict(file='main.py',quote='value = 1'),after=dict(file='main.py',quote='value = 2'),
            supporting_evidence=[dict(file='TASK',quote='Preserve accepted work.')],reason='Synthetic contrast.')
        result,issues=learning.contributions([row],[bundle],attempts,TASK,{})
        self.assertEqual(result,{bundle['id']:'adopted'});self.assertFalse(issues)
        row['after']['quote']='invented change';result,issues=learning.contributions([row],[bundle],attempts,TASK,{})
        self.assertFalse(result);self.assertTrue(issues)
    def test_pipeline_credits_only_the_evidenced_entry_and_replays_once(self):
        class Crediting(Backend):
            def execute(inner,kind,payload,*args):
                result=super().execute(kind,payload,*args)
                if kind=='extract':
                    bundle=payload['related_experiences'][0];rule=bundle['rules'][0]
                    result['output']['contributions']=[dict(experience_sha256=bundle['sha256'],rule_id=rule['id'],rule_quote=rule['body'],
                        decision='adopted',before=dict(file='main.py',quote='value = 1'),after=dict(file='main.py',quote='value = 2'),
                        supporting_evidence=[dict(file='TASK',quote='Preserve accepted work.')],reason='Synthetic observed adoption, not causal proof.')]
                return result
        loop=self.prepare('credit');state=loop.run(Crediting(2),execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'))
        self.assertEqual(len(state['contribution_decisions']),1)
        values=compact.load(self.file)['experiences']
        self.assertEqual(sum(sum(r['positive_cases'] for r in v.get('learning',learning.empty())['usage_by_model'].values()) for v in values),1)
        before=self.file.read_bytes();loop.run(Crediting(2),execute=True);self.assertEqual(self.file.read_bytes(),before)

    def test_concurrent_counting_and_rule_error_pause(self):
        from concurrent.futures import ThreadPoolExecutor
        snapshot=approval.freeze(self.store);bundle=snapshot['entries'][0]['bundle'];expected={bundle['id']:bundle['sha256']}
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda _:learning.record_usage(self.store,'same-case','model-a',expected,{bundle['id']:'adopted'}),range(8)))
        row=compact.load(self.file)['experiences'][0]['learning']['usage_by_model']['model-a']
        self.assertEqual(row['delivered_cases'],1);self.assertEqual(row['positive_cases'],1)
        learning.record_usage(self.store,'bad-case','model-a',expected,{bundle['id']:'rule_error'})
        saved=compact.load(self.file)['experiences'][0]
        self.assertEqual(saved['review']['decision'],'revise');self.assertEqual(saved['learning']['usage_by_model']['model-a']['negative_cases'],1)
        self.assertNotIn(bundle['id'],compact.active_view(self.store)['active_ids'])
        self.assertEqual(approval.validate_snapshot(self.store,snapshot),snapshot)

    def test_in_place_revision_keeps_id_and_old_snapshot(self):
        snapshot=approval.freeze(self.store);bundle=snapshot['entries'][0]['bundle']
        experience=dict(labels=bundle['labels'],requires=bundle['requires'],excludes=bundle['excludes'],rules=[{k:r[k] for k in ('category','body')} for r in bundle['rules']],limitations=[])
        experience['rules'][1]['body']='Capture document identity before saving.'
        record=dict(experience=experience,abstract='Bind deferred saves to the accepting document.',related_experiences=[bundle],
            reflection_update=dict(operation='revise',target_sha256s=[bundle['sha256']]),learning=learning.empty())
        compact.publish_candidate(self.store,record)
        saved=compact.load(self.file)['experiences'];self.assertEqual(len(saved),2);self.assertEqual(saved[0]['id'],bundle['id'])
        self.assertEqual(saved[0]['review']['decision'],'pending');self.assertEqual(saved[0]['summary']['review']['decision'],'pending')
        self.assertEqual(approval.validate_snapshot(self.store,snapshot),snapshot)
        compact.publish_candidate(self.store,record);self.assertEqual(len(compact.load(self.file)['experiences']),2)
    def test_editing_a_consolidated_entry_does_not_revive_retired_sources(self):
        value=compact.load(self.file);parent,retired=value['experiences']
        retired['superseded']=True
        parent['proposal']=dict(operation='revise',target_ids=[retired['id']],target_sha256s=[compact._bundle(self.file,retired)[0]['sha256']])
        self.file.write_text(json.dumps(value));snapshot=approval.freeze(self.store)
        self.assertEqual(len(snapshot['entries']),1);bundle=snapshot['entries'][0]['bundle']
        experience=dict(labels=bundle['labels'],requires=bundle['requires'],excludes=bundle['excludes'],
            rules=[dict(category=r['category'],body=r['body']+' Retain later accepted work.') for r in bundle['rules']],limitations=[])
        compact.publish_candidate(self.store,dict(experience=experience,related_experiences=[bundle],
            reflection_update=dict(operation='revise',target_sha256s=[bundle['sha256']])))
        self.assertFalse(approval.freeze(self.store)['entries'])
        saved=compact.load(self.file)['experiences'][0];self.assertNotIn('proposal',saved)
        compact.save_review(self.store,dict(id=saved['id'],expected_record=compact._bundle(self.file,saved)[0]['sha256'],
            expected_review=saved['review'],reviewer='Synthetic reviewer',decision='accept'))
        self.assertEqual([e['bundle']['id'] for e in approval.freeze(self.store)['entries']],[saved['id']])
        self.assertEqual(approval.validate_snapshot(self.store,snapshot),snapshot)

    def test_failed_then_successful_records_actual_model_without_full_bank_or_source_copies(self):
        loop=self.prepare('contrast');backend=Backend(2);state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'))
        candidate=read(loop.root/'candidate-pool/success.json');self.assertEqual(candidate['learning']['initial_priority'],1)
        self.assertEqual(candidate['learning']['origin']['reflection_model'],loop.verify()['model']['model'])
        payload=next(p for role,p,*_ in backend.calls if role=='extract')
        self.assertNotIn('experience_catalog',payload)
        self.assertTrue(all('candidate_sources' not in a for a in payload['trajectory']))
        self.assertLessEqual(len(payload['related_experiences']),3)
