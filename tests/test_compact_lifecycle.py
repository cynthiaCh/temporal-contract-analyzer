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
        self.assertIn('已被替代，不参与新检索',compact.page(self.path).decode())
        self.assertEqual(approval.validate_snapshot(self.path,snapshot),snapshot)
        original=json.loads(before)['experiences'][0]
        self.assertEqual(compact.load(self.path)['experiences'][0],original)

    def test_chain_merge_and_rejection_restore_accepted_sources(self):
        self.add('v2',['entry-binding']);self.add('other')
        self.add('merged',['v2','other'])
        self.assertEqual(self.ids(),{'merged'})
        compact.save_review(self.path,self.request('merged','reject'))
        self.assertEqual(self.ids(),{'v2','other'})

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

    def test_new_publication_binds_target_and_prevents_stale_branch_acceptance(self):
        target=memory.records(self.path)[0]
        exp=dict(labels=target['labels'],requires=target['requires'],excludes=target['excludes'],
                 rules=[dict(category=r['category'],body=r['body']+' Additional check.') for r in target['rules']],limitations=[])
        record=dict(experience=exp,reflection_update=dict(operation='revise',target_sha256s=[target['sha256']]),related_experiences=[target])
        result=compact.publish_candidate(self.path,record)
        candidate=next(i for i in compact.load(self.path)['experiences'] if i['id']!='entry-binding')
        self.assertEqual(candidate['proposal']['target_sha256s'],[target['sha256']])
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


if __name__=='__main__':unittest.main()
