"""Current guidance excludes only unambiguous accepted replacements."""
from copy import deepcopy
import json
import unittest
from temporal_contract_analyzer import compact_experience as compact,experience_approval as approval,experience_memory as memory
from temporal_contract_analyzer.core import EvidenceError
import test_compact_experience as fixtures


class CompactLifecycleTests(unittest.TestCase):
    setUp=fixtures.CompactExperienceTests.setUp
    save=fixtures.CompactExperienceTests.save
    request=fixtures.CompactExperienceTests.request
    per_item_reviews=fixtures.CompactExperienceTests.per_item_reviews

    def add(self,key,targets=(),decision='accept',hashes=None):
        item=deepcopy(self.value['experiences'][0]);item['id']=key
        item['event_relation']='Updated guidance '+key
        item['review']=dict(reviewer='Synthetic reviewer',decision=decision,at='2026-11-17T00:00:00Z') if decision!='pending' else dict(reviewer=None,decision='pending',at=None)
        if targets:
            item['proposal']=dict(operation='revise' if len(targets)==1 else 'merge',target_ids=list(targets))
            if hashes is not None:item['proposal']['target_sha256s']=hashes
        self.value['experiences'].append(item);self.save();return item

    def ids(self):return {r['bundle']['id'] for r in approval.freeze(self.path)['entries']}

    def test_accepted_revision_replaces_parent_and_preserves_frozen_history(self):
        self.per_item_reviews()
        before=self.path.read_bytes();snapshot=approval.freeze(self.path)
        self.add('v2',['entry-binding'],decision='pending')
        self.assertEqual(self.ids(),{'entry-binding'})
        compact.save_review(self.path,self.request('v2'))
        self.assertEqual(self.ids(),{'v2'})
        self.assertEqual({r['bundle']['id'] for r in approval.active(self.path)},{'v2'})
        self.assertEqual(len(memory.records(self.path)),2)
        html=compact.page(self.path).decode()
        self.assertNotIn('data-target="entry-binding"',html)
        self.assertNotIn('data-id="entry-binding"',html)
        self.assertNotIn('value="superseded"',html)
        self.assertIn('data-target="v2"',html)
        self.assertEqual(approval.validate_snapshot(self.path,snapshot),snapshot)
        original=json.loads(before)['experiences'][0]
        self.assertEqual(compact.load(self.path)['experiences'][0],original)

    def test_chain_merge_and_rejection_restore_accepted_sources(self):
        self.add('v2',['entry-binding']);self.add('other')
        self.add('merged',['v2','other'])
        self.assertEqual(self.ids(),{'merged'})
        result=compact.save_review(self.path,self.request('merged','reject'))
        self.assertEqual(self.ids(),{'v2','other'})
        self.assertEqual(set(result['lifecycle']['active_ids']),{'v2','other'})
        html=compact.page(self.path).decode()
        self.assertNotIn('data-lifecycle="superseded"',html)
        self.assertIn('data-lifecycle="reject"',html)

    def test_conflicting_missing_and_cyclic_lineages_are_visible_and_reported(self):
        self.add('a',['entry-binding']);self.add('b',['entry-binding'])
        self.add('orphan',['missing'])
        self.add('cycle-a',['cycle-b']);self.add('cycle-b',['cycle-a'])
        view=compact.active_view(self.path)
        self.assertEqual(len(self.ids()),6)
        self.assertEqual({i['code'] for i in view['issues']},{'conflicting_replacements','unresolved_target','replacement_cycle'})
        self.assertEqual(view['superseded_ids'],[])

    def test_explicitly_accepted_merge_can_resolve_historical_competing_branches(self):
        self.add('a',['entry-binding']);self.add('b',['entry-binding'])
        self.assertEqual(self.ids(),{'entry-binding','a','b'})
        self.add('merged',['a','b'])
        self.assertEqual(self.ids(),{'merged'})
        self.assertEqual(compact.active_view(self.path)['issues'],[])

    def test_exact_target_drift_is_not_applied(self):
        self.add('v2',['entry-binding'],hashes=['f'*64])
        view=compact.active_view(self.path)
        self.assertEqual(self.ids(),{'entry-binding','v2'})
        self.assertEqual(view['issues'][0]['code'],'stale_target')

    def test_new_publication_requires_and_preserves_a_written_title(self):
        target=memory.records(self.path)[0]
        experience=dict(labels=target['labels'],requires=target['requires'],excludes=target['excludes'],
                        rules=[dict(category=r['category'],body=r['body']) for r in target['rules']],limitations=[])
        record=dict(experience=experience,reflection_update=dict(operation='new',target_sha256s=[]),related_experiences=[])
        before=self.path.read_bytes()
        with self.assertRaisesRegex(EvidenceError,'descriptive experience title'):
            compact.publish_candidate(self.path,record)
        self.assertEqual(self.path.read_bytes(),before)
        record['title']='Bind accepted work before callbacks'
        compact.publish_candidate(self.path,record)
        item=next(i for i in compact.load(self.path)['experiences'] if i['id']!='entry-binding')
        self.assertEqual(item['title'],record['title'])
        self.assertNotEqual(item['title'],experience['rules'][0]['body'])

    def test_new_publication_binds_target_and_prevents_stale_branch_acceptance(self):
        target=memory.records(self.path)[0]
        exp=dict(labels=target['labels'],requires=target['requires'],excludes=target['excludes'],
                 rules=[dict(category=r['category'],body=r['body']+' Additional check.') for r in target['rules']],limitations=[])
        record=dict(experience=exp,reflection_update=dict(operation='revise',target_sha256s=[target['sha256']]),related_experiences=[target])
        result=compact.publish_candidate(self.path,record)
        candidate=compact.load(self.path)['experiences'][0]
        self.assertEqual(candidate['id'],'entry-binding')
        self.assertEqual(len(compact.load(self.path)['experiences']),1)
        compact.save_review(self.path,self.request(candidate['id']))
        self.assertEqual(self.ids(),{candidate['id']})
        compact.save_review(self.path,self.request(candidate['id']))
        self.assertEqual(self.ids(),{candidate['id']})
        self.value=compact.load(self.path)
        self.add('stale-branch',['entry-binding'],decision='pending',hashes=[target['sha256']])
        before=self.path.read_bytes()
        with self.assertRaises(EvidenceError):compact.save_review(self.path,self.request('stale-branch'))
        self.assertEqual(self.path.read_bytes(),before)
        self.assertEqual(compact.publish_candidate(self.path,record),result)

    def test_reviewed_exact_merge_retires_sources_with_incomplete_old_ancestry(self):
        self.per_item_reviews()
        self.add('old-a',['missing-old-parent-a'])
        self.add('old-b',['missing-old-parent-b'])
        self.add('unrelated')
        snapshot=approval.freeze(self.path)
        originals={i['id']:deepcopy(i) for i in compact.load(self.path)['experiences']}
        records={b['id']:b for b in memory.records(self.path)}
        self.add('merged',['old-a','old-b'],decision='pending',
                 hashes=[records[k]['sha256'] for k in ('old-a','old-b')])
        self.assertEqual(self.ids(),{'entry-binding','old-a','old-b','unrelated'})
        result=compact.save_review(self.path,self.request('merged'))
        self.assertEqual(self.ids(),{'entry-binding','unrelated','merged'})
        self.assertEqual(set(result['lifecycle']['superseded_ids']),{'old-a','old-b'})
        self.assertNotIn('merged',result['lifecycle']['unresolved_ids'])
        saved={i['id']:i for i in compact.load(self.path)['experiences']}
        for key,original in originals.items():self.assertEqual(saved[key],original)
        self.assertEqual(approval.validate_snapshot(self.path,snapshot),snapshot)
        compact.save_review(self.path,self.request('merged','reject'))
        self.assertEqual(self.ids(),{'entry-binding','old-a','old-b','unrelated'})

    def test_exact_merge_with_changed_or_missing_source_cannot_retire_other_sources(self):
        self.add('old-a',['missing-old-parent'])
        self.add('old-b')
        records={b['id']:b for b in memory.records(self.path)}
        self.add('stale-merge',['old-a','old-b'],hashes=['f'*64,records['old-b']['sha256']])
        self.add('missing-merge',['old-b','not-present'],hashes=[records['old-b']['sha256'],'e'*64])
        view=compact.active_view(self.path)
        self.assertNotIn('old-a',view['superseded_ids'])
        self.assertNotIn('old-b',view['superseded_ids'])
        self.assertIn('stale_target',{i['code'] for i in view['issues']})


if __name__=='__main__':unittest.main()
