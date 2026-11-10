"""Synthetic expert actions; never represent real user approval."""
from copy import deepcopy
import unittest

import test_experience_memory as fixtures
from temporal_contract_analyzer import experience_memory as memory, experience_approval as approval
from temporal_contract_analyzer.core import EvidenceError


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        fixture = fixtures.MemoryTests('test_storage_preserves_single_source_body_and_evidence')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.f = fixture
        self.bundle = memory.add(fixture.store, fixture.payload, [fixture.source])

    def request(self, decision='accept'):
        return dict(reviewer='SYNTHETIC_EXPERT_FIXTURE', decision=decision, scope='exploratory',
            reason='Synthetic test decision, not an independent human approval.',
            rules=[dict(rule_id=r['id'], supported=True, reason='Synthetic test finding.')
                   for r in self.bundle['rules']])

    def test_research_admission_does_not_activate(self):
        self.assertEqual(approval.active(self.f.store), [])
        self.assertEqual(memory.retrieve(self.f.store, self.f.visible())['route']['reason'],
                         'no_expert_activated_experience')

    def test_exact_expert_acceptance_and_unreviewed_child(self):
        approval.decide(self.f.store, self.bundle['sha256'], self.request())
        child = deepcopy(self.f.payload)
        child.update(version='v2', parent_sha256=self.bundle['sha256'])
        child['review']['status']='candidate'
        second = memory.add(self.f.store, child, [self.f.source])
        self.assertEqual(approval.active(self.f.store)[0]['bundle'], self.bundle)
        approval.decide(self.f.store, second['sha256'], self.request('reject'))
        self.assertEqual(approval.active(self.f.store)[0]['bundle'], self.bundle)
        approval.decide(self.f.store, second['sha256'], self.request())
        self.assertEqual(approval.active(self.f.store)[0]['bundle'], second)

    def test_incomplete_or_unsupported_expert_findings_cannot_activate(self):
        for field in ('reviewer', 'rules'):
            bad=self.request();bad[field]=[] if field=='rules' else ''
            with self.assertRaises(EvidenceError):approval.decide(self.f.store,self.bundle['sha256'],bad)
        bad=self.request();bad['rules'][0]['supported']=False
        with self.assertRaises(EvidenceError):approval.decide(self.f.store,self.bundle['sha256'],bad)
        self.assertEqual(approval.active(self.f.store), [])

    def test_review_reasons_may_be_empty_but_must_be_text(self):
        request = self.request()
        request['reason'] = ''
        for rule in request['rules']:
            rule['reason'] = ''
        for field in ('overall', 'rule'):
            invalid = deepcopy(request)
            if field == 'overall': invalid['reason'] = None
            else: invalid['rules'][0]['reason'] = None
            with self.subTest(field=field), self.assertRaises(EvidenceError):
                approval.decide(self.f.store, self.bundle['sha256'], invalid)
        saved = approval.decide(self.f.store, self.bundle['sha256'], request)
        self.assertEqual(saved['reason'], '')
        self.assertTrue(all(rule['reason'] == '' for rule in saved['rules']))
        self.assertEqual(approval.active(self.f.store)[0]['bundle'], self.bundle)

    def test_frozen_snapshot_survives_later_activation(self):
        approval.decide(self.f.store,self.bundle['sha256'],self.request())
        frozen=approval.freeze(self.f.store)
        child=deepcopy(self.f.payload);child.update(version='v2',parent_sha256=self.bundle['sha256'])
        child['rules'][1]['body']='A revised synthetic relation.'
        second=memory.add(self.f.store,child,[self.f.source])
        approval.decide(self.f.store,second['sha256'],self.request())
        old=memory.retrieve(self.f.store,self.f.visible(),frozen['sha256'],frozen)
        self.assertEqual(old['selected_memory_record']['sha256'],self.bundle['sha256'])
        self.assertEqual(memory.retrieve(self.f.store,self.f.visible())['selected_memory_record']['sha256'],second['sha256'])

    def test_tampering_or_new_digest_cannot_inherit_old_approval(self):
        approval.decide(self.f.store,self.bundle['sha256'],self.request())
        frozen=approval.freeze(self.f.store)
        frozen['entries'][0]['bundle']['rules'][0]['body']='Changed'
        with self.assertRaises(EvidenceError):approval.validate_snapshot(self.f.store,frozen)

    def test_explicit_rejection_of_active_version_disables_without_rollback(self):
        approval.decide(self.f.store,self.bundle['sha256'],self.request())
        approval.decide(self.f.store,self.bundle['sha256'],self.request('reject'))
        self.assertEqual(approval.active(self.f.store),[])
