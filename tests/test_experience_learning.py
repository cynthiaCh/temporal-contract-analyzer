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

    def test_unchanged_context_cannot_credit_or_discredit_guidance(self):
        bundle=approval.freeze(self.store)['entries'][0]['bundle']
        before='unchanged_a = 1\nunchanged_b = 2\nresult = 0\n'
        after='unchanged_a = 1\nunchanged_b = 2\nresult = 3\n'
        attempts=[dict(acceptance_passed=False,candidate_sources={'main.py':before},delivered_sha256s=[bundle['sha256']]),
                  dict(acceptance_passed=True,candidate_sources={'main.py':after},delivered_sha256s=[bundle['sha256']])]
        row=dict(experience_sha256=bundle['sha256'],rule_id=bundle['rules'][0]['id'],rule_quote=bundle['rules'][0]['body'],
            before=dict(file='main.py',quote='unchanged_a = 1'),after=dict(file='main.py',quote='unchanged_b = 2'),
            supporting_evidence=[dict(file='TASK',quote='Preserve accepted work.')],reason='Unchanged context.')
        for decision in ('adopted','misleading','rule_error'):
            result,issues=learning.contributions([dict(row,decision=decision)],[bundle],attempts,TASK,{})
            self.assertFalse(result);self.assertTrue(issues)
        # Context on a changed line is still not itself changed code.
        attempts[0]['candidate_sources']['main.py']='unchanged_a = 1; unchanged_b = 2; result = 0\n'
        attempts[1]['candidate_sources']['main.py']='unchanged_a = 1; unchanged_b = 2; result = 3\n'
        result,issues=learning.contributions([dict(row,decision='adopted')],[bundle],attempts,TASK,{})
        self.assertFalse(result);self.assertTrue(issues)

    def test_additions_and_deletions_allow_context_only_at_the_same_edit(self):
        bundle=approval.freeze(self.store)['entries'][0]['bundle']
        for old,new,before_quote,after_quote in [
            ('run()\n','if ready:\n    run()\n','run()','if ready:'),
            ('bad()\ngood()\n','good()\n','bad()','good()'),
            ('good()\n','good()\npublish()\n','good()','publish()'),
            ('good()\nbad()\n','good()\n','bad()','good()'),
        ]:
            with self.subTest(before=old):
                attempts=[dict(acceptance_passed=False,candidate_sources={'main.py':old},delivered_sha256s=[bundle['sha256']]),
                          dict(acceptance_passed=True,candidate_sources={'main.py':new},delivered_sha256s=[bundle['sha256']])]
                row=dict(experience_sha256=bundle['sha256'],rule_id=bundle['rules'][0]['id'],rule_quote=bundle['rules'][0]['body'],decision='adopted',
                    before=dict(file='main.py',quote=before_quote),after=dict(file='main.py',quote=after_quote),
                    supporting_evidence=[dict(file='TASK',quote='Preserve accepted work.')],reason='Synthetic paired edit.')
                result,issues=learning.contributions([row],[bundle],attempts,TASK,{})
                self.assertEqual(result,{bundle['id']:'adopted'});self.assertFalse(issues)

    def test_unrelated_edits_cannot_be_paired_for_credit(self):
        old={'main.py':'left = 0\nkeep()\nright = 0\n'}
        new={'main.py':'left = 1\nkeep()\nright = 1\n'}
        self.assertFalse(learning._changed_pair(dict(file='main.py',quote='left = 0'),dict(file='main.py',quote='right = 1'),old,new))

    def test_third_attempt_credits_an_earlier_change_only_if_retained(self):
        bundle=approval.freeze(self.store)['entries'][0]['bundle']
        attempts=[dict(acceptance_passed=False,candidate_sources={'main.py':'bound = False\nother = False\n'},delivered_sha256s=[bundle['sha256']]),
                  dict(acceptance_passed=False,candidate_sources={'main.py':'bound = True\nother = False\n'},delivered_sha256s=[bundle['sha256']]),
                  dict(acceptance_passed=True,candidate_sources={'main.py':'bound = True\nother = True\n'},delivered_sha256s=[bundle['sha256']])]
        row=dict(experience_sha256=bundle['sha256'],rule_id=bundle['rules'][0]['id'],rule_quote=bundle['rules'][0]['body'],decision='adopted',
            before=dict(file='main.py',quote='bound = False'),after=dict(file='main.py',quote='bound = True'),
            supporting_evidence=[dict(file='TASK',quote='Preserve accepted work.')],reason='Second-attempt change survives final success.')
        result,issues=learning.contributions([row],[bundle],attempts,TASK,{})
        self.assertEqual(result,{bundle['id']:'adopted'});self.assertFalse(issues)
        attempts[-1]['candidate_sources']['main.py']='bound = False\nother = True\n'
        result,issues=learning.contributions([row],[bundle],attempts,TASK,{})
        self.assertFalse(result);self.assertTrue(issues)

    def test_invalid_reflection_keeps_success_and_records_deliveries_without_credit(self):
        class InvalidReflection(Backend):
            def execute(inner,kind,payload,*args):
                result=super().execute(kind,payload,*args)
                if kind=='extract':result['output']['update']['supporting_attempts']=[2]
                return result
        loop=self.prepare('invalid-reflection');backend=InvalidReflection(2)
        state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'passed');self.assertTrue(state['training_accepted']);self.assertTrue(state['finalized'])
        self.assertEqual(state['extraction_disposition'],'failed');self.assertIn('failed and successful',state['extraction_error'])
        self.assertFalse((loop.root/'candidate-pool/success.json').exists())
        self.assertTrue(any(v.get('learning',{}).get('usage_by_model') for v in compact.load(self.file)['experiences']))
        summary=read(loop.root/'summary.json');self.assertEqual(summary['extraction_error'],state['extraction_error'])
        count=len(backend.calls);before=self.file.read_bytes();loop.run(backend,execute=True)
        self.assertEqual(len(backend.calls),count);self.assertEqual(self.file.read_bytes(),before)

    def test_usage_write_failure_does_not_invalidate_repair(self):
        from unittest.mock import patch
        loop=self.prepare('usage-failure')
        with patch('temporal_contract_analyzer.experience_learning.record_usage',side_effect=OSError('Synthetic write failure')):
            state=loop.run(Backend(),execute=True)
        self.assertEqual(state['status'],'passed');self.assertTrue(state['finalized'])
        self.assertIn('Synthetic write failure',state['learning_error'])

    def test_revision_preserves_latest_same_id_statistics_without_extra_initial_credit(self):
        bundle=approval.freeze(self.store)['entries'][0]['bundle'];expected={bundle['id']:bundle['sha256']}
        learning.record_usage(self.store,'old-case','model-a',expected,{bundle['id']:'adopted'})
        record=self.revision_record();record['learning']=learning.empty(priority=1)
        compact.publish_candidate(self.store,record)
        learning.record_usage(self.store,'during-review','model-a',expected,{bundle['id']:'rule_error'})
        before=deepcopy(compact.load(self.file)['experiences'][0]['learning'])
        self.review_draft('accept')
        saved=compact.load(self.file)['experiences'][0]
        self.assertEqual(saved['learning'],before);self.assertEqual(learning.score(saved['learning'],'model-a'),0)
        self.assertEqual(saved['review']['decision'],'accept')

    def test_revision_retains_known_origin_and_fills_unknown_origin(self):
        original=self.file.read_bytes()
        origin=dict(reflection_model='model-a',reflection_effort='medium',repair_model='model-a',first_success_attempt=2)
        newer=dict(origin,reflection_model='model-b',repair_model='model-b')
        for previous in (None,origin):
            with self.subTest(origin=previous):
                self.file.write_bytes(original)
                value=compact.load(self.file);value['experiences'][0]['learning']=learning.empty(previous)
                self.file.write_text(json.dumps(value))
                record=self.revision_record();record['learning']=learning.empty(newer,1)
                compact.publish_candidate(self.store,record);self.review_draft('accept')
                saved=compact.load(self.file)['experiences'][0]['learning']
                self.assertEqual(saved['origin'],previous or newer);self.assertEqual(saved['initial_priority'],0)

    def revision_record(self,merge=False):
        bundles=[e['bundle'] for e in approval.freeze(self.store)['entries']]
        b=bundles[0]
        experience=dict(labels=b['labels'],requires=b['requires'],excludes=b['excludes'],
            rules=[dict(category=r['category'],body=r['body']+' Revised checkpoint.') for r in b['rules']],limitations=[])
        return dict(experience=experience,related_experiences=bundles,abstract='Revised guidance.',
            reflection_update=dict(operation='merge' if merge else 'revise',target_sha256s=[b['sha256'] for b in (bundles if merge else bundles[:1])]))

    def test_rejected_revision_keeps_original_and_allows_replacement_draft(self):
        original=approval.freeze(self.store)
        record=self.revision_record();compact.publish_candidate(self.store,record)
        self.review_draft('reject')
        self.assertEqual(approval.freeze(self.store),original)
        record['experience']['rules'][1]['body']+=' Another proposed check.'
        compact.publish_candidate(self.store,record)
        self.assertEqual(approval.freeze(self.store),original)
        self.assertEqual(compact.load(self.file)['experiences'][0]['pending_revision']['item']['review']['decision'],'pending')

    def test_merge_draft_retires_targets_only_after_acceptance(self):
        original=approval.freeze(self.store)
        record=self.revision_record(merge=True);compact.publish_candidate(self.store,record)
        self.assertEqual(approval.freeze(self.store),original)
        self.review_draft('reject')
        self.assertEqual(approval.freeze(self.store),original)
        self.review_draft('accept')
        current=approval.freeze(self.store)
        self.assertEqual([e['bundle']['id'] for e in current['entries']],['save'])
        self.assertNotEqual(current['entries'][0]['bundle'],original['entries'][0]['bundle'])
        self.assertEqual(approval.validate_snapshot(self.store,original),original)

    def test_stale_merge_target_cannot_replace_accepted_primary(self):
        original=approval.freeze(self.store)
        compact.publish_candidate(self.store,self.revision_record(merge=True))
        value=compact.load(self.file);value['experiences'][1]['event_relation']='Separately revised target.'
        self.file.write_text(json.dumps(value));before=self.file.read_bytes()
        with self.assertRaisesRegex(EvidenceError,'target changed'):self.review_draft('accept')
        self.assertEqual(self.file.read_bytes(),before)
        self.assertEqual(approval.freeze(self.store)['entries'][0]['bundle'],original['entries'][0]['bundle'])

    def test_pending_draft_cannot_overwrite_a_different_unreviewed_draft(self):
        record=self.revision_record();compact.publish_candidate(self.store,record)
        record['experience']['rules'][1]['body']+=' Conflicting draft.'
        before=self.file.read_bytes()
        with self.assertRaisesRegex(EvidenceError,'different revision draft'):compact.publish_candidate(self.store,record)
        self.assertEqual(self.file.read_bytes(),before)

    def test_concurrent_counting_and_rule_error_preserves_approval(self):
        from concurrent.futures import ThreadPoolExecutor
        snapshot=approval.freeze(self.store);bundle=snapshot['entries'][0]['bundle'];expected={bundle['id']:bundle['sha256']}
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda _:learning.record_usage(self.store,'same-case','model-a',expected,{bundle['id']:'adopted'}),range(8)))
        row=compact.load(self.file)['experiences'][0]['learning']['usage_by_model']['model-a']
        self.assertEqual(row['delivered_cases'],1);self.assertEqual(row['positive_cases'],1)
        learning.record_usage(self.store,'bad-case','model-a',expected,{bundle['id']:'rule_error'})
        saved=compact.load(self.file)['experiences'][0]
        self.assertEqual(saved['review']['decision'],'accept');self.assertEqual(saved['learning']['usage_by_model']['model-a']['negative_cases'],1)
        self.assertIn(bundle['id'],compact.active_view(self.store)['active_ids'])
        self.assertIn('bad-case',compact.page(self.store).decode())
        self.assertEqual(approval.validate_snapshot(self.store,snapshot),snapshot)

    def test_in_place_revision_keeps_id_and_old_snapshot(self):
        snapshot=approval.freeze(self.store);bundle=snapshot['entries'][0]['bundle']
        experience=dict(labels=bundle['labels'],requires=bundle['requires'],excludes=bundle['excludes'],rules=[{k:r[k] for k in ('category','body')} for r in bundle['rules']],limitations=[])
        experience['rules'][1]['body']='Capture document identity before saving.'
        record=dict(experience=experience,abstract='Bind deferred saves to the accepting document.',related_experiences=[bundle],
            reflection_update=dict(operation='revise',target_sha256s=[bundle['sha256']]),learning=learning.empty())
        compact.publish_candidate(self.store,record)
        saved=compact.load(self.file)['experiences'];self.assertEqual(len(saved),2);self.assertEqual(saved[0]['id'],bundle['id'])
        self.assertEqual(saved[0]['review']['decision'],'accept')
        draft=saved[0]['pending_revision']['item']
        self.assertEqual(draft['review']['decision'],'pending');self.assertEqual(draft['summary']['review']['decision'],'pending')
        self.assertEqual(approval.freeze(self.store)['entries'][0]['bundle'],bundle)
        self.assertIn('Revision draft; accepted guidance remains active',compact.page(self.store).decode())
        self.assertEqual(approval.validate_snapshot(self.store,snapshot),snapshot)
        compact.publish_candidate(self.store,record);self.assertEqual(len(compact.load(self.file)['experiences']),2)
        compact.save_summary(self.store,dict(id=draft['id'],expected_record=compact._bundle(self.file,draft)[0]['sha256'],
            expected_summary=draft['summary'],text='Reviewed draft summary.',expert_questions='None.',reviewer='Reviewer',decision='accept'))
        self.assertEqual(approval.freeze(self.store)['entries'][0]['bundle'],bundle)
        self.review_draft('accept')
        promoted=compact.load(self.file)['experiences'][0]
        self.assertNotIn('pending_revision',promoted)
        self.assertEqual(promoted['event_relation'],'Capture document identity before saving.')
        self.assertEqual(approval.freeze(self.store)['entries'][0]['retrieval_summary']['text'],'Reviewed draft summary.')
        self.assertEqual(approval.validate_snapshot(self.store,snapshot),snapshot)

    def review_draft(self,decision):
        owner=compact.load(self.file)['experiences'][0];draft=owner['pending_revision']['item']
        return compact.save_review(self.store,dict(id=draft['id'],expected_record=compact._bundle(self.file,draft)[0]['sha256'],
            expected_review=draft['review'],reviewer='Synthetic reviewer',decision=decision))
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
        self.assertEqual([e['bundle']['id'] for e in approval.freeze(self.store)['entries']],[bundle['id']])
        self.review_draft('accept')
        saved=compact.load(self.file)['experiences'][0];self.assertNotIn('proposal',saved)
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
        self.assertLessEqual(len(payload['related_experiences']),5)
