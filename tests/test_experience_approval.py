"""Synthetic expert actions; never represent real user approval."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import json
from threading import Barrier
import unittest
from unittest.mock import patch

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

    def child(self, version='v2', parent=None):
        value = deepcopy(self.f.payload)
        value.update(version=version, parent_sha256=parent or self.bundle['sha256'])
        return memory.add(self.f.store, value, [self.f.source])

    def test_reaccepting_parent_does_not_replace_active_child(self):
        approval.decide(self.f.store, self.bundle['sha256'], self.request())
        child = self.child()
        approval.decide(self.f.store, child['sha256'], self.request())
        before = (self.f.store/'active.json').read_bytes()
        approval.decide(self.f.store, self.bundle['sha256'], self.request())
        self.assertEqual(approval.active(self.f.store)[0]['bundle'], child)
        self.assertEqual((self.f.store/'active.json').read_bytes(), before)
        self.assertEqual(len(approval.decisions(self.f.store)), 3)

    def test_review_only_never_activates_and_existing_acceptance_can_activate(self):
        approval.decide(self.f.store, self.bundle['sha256'], self.request(), activate_version=False)
        self.assertEqual(approval.active(self.f.store), [])
        count = len(approval.decisions(self.f.store))
        approval.activate(self.f.store, self.bundle['sha256'], None, 'SYNTHETIC_OPERATOR')
        self.assertEqual(approval.active(self.f.store)[0]['bundle'], self.bundle)
        self.assertEqual(len(approval.decisions(self.f.store)), count)

    def test_rollback_requires_explicit_mode_and_compatible_accepted_ancestor(self):
        approval.decide(self.f.store, self.bundle['sha256'], self.request())
        child = self.child()
        approval.decide(self.f.store, child['sha256'], self.request())
        frozen = approval.freeze(self.f.store)
        with self.assertRaises(EvidenceError):
            approval.activate(self.f.store, self.bundle['sha256'], child['sha256'], 'SYNTHETIC_OPERATOR')
        approval.activate(self.f.store, self.bundle['sha256'], child['sha256'], 'SYNTHETIC_OPERATOR', rollback=True)
        self.assertEqual(approval.active(self.f.store)[0]['bundle'], self.bundle)
        self.assertEqual(approval.validate_snapshot(self.f.store, frozen), frozen)
        with self.assertRaises(EvidenceError):
            approval.activate(self.f.store, child['sha256'], self.bundle['sha256'], 'SYNTHETIC_OPERATOR', rollback=True)

    def test_missing_index_requires_explicit_migration_not_review_replay(self):
        approval.decide(self.f.store, self.bundle['sha256'], self.request())
        (self.f.store/'active.json').unlink()
        decisions_before = {p.name:p.read_bytes() for p in (self.f.store/'decisions').glob('*.json')}
        with self.assertRaises(EvidenceError):approval.active(self.f.store)
        self.assertFalse((self.f.store/'active.json').exists())
        approval.migrate_active(self.f.store, {self.bundle['id']:self.bundle['sha256']}, 'SYNTHETIC_MIGRATOR')
        self.assertEqual(approval.active(self.f.store)[0]['bundle'], self.bundle)
        self.assertEqual({p.name:p.read_bytes() for p in (self.f.store/'decisions').glob('*.json')}, decisions_before)
        with self.assertRaises(EvidenceError):
            approval.migrate_active(self.f.store, {}, 'SYNTHETIC_MIGRATOR')

    def test_unapproved_rejected_unknown_and_legacy_targets_cannot_activate(self):
        with self.assertRaises(EvidenceError):
            approval.activate(self.f.store, self.bundle['sha256'], None, 'SYNTHETIC_OPERATOR')
        with self.assertRaises(EvidenceError):
            approval.activate(self.f.store, 'f'*64, None, 'SYNTHETIC_OPERATOR')
        approval.decide(self.f.store, self.bundle['sha256'], self.request('reject'))
        with self.assertRaises(EvidenceError):
            approval.activate(self.f.store, self.bundle['sha256'], None, 'SYNTHETIC_OPERATOR')
        legacy = deepcopy(self.f.payload)
        legacy.update(id='legacy-entry', taxonomy_version=memory.LEGACY_TAXONOMY, labels=['T3'])
        old = memory.add(self.f.store, legacy, [self.f.source])
        approval.decide(self.f.store, old['sha256'], self.request())
        self.assertEqual(approval.active(self.f.store), [])
        with self.assertRaises(EvidenceError):
            approval.activate(self.f.store, old['sha256'], None, 'SYNTHETIC_OPERATOR', rollback=True)

    def test_legacy_parent_acceptance_after_native_child_cannot_reproduce_old_bug(self):
        legacy = deepcopy(self.f.payload)
        legacy.update(id='recode-entry', taxonomy_version=memory.LEGACY_TAXONOMY, labels=['T3'])
        old = memory.add(self.f.store, legacy, [self.f.source])
        native = deepcopy(legacy)
        native.update(version='native-v2', taxonomy_version=self.bundle['taxonomy_version'],
                      labels=['I'], parent_sha256=old['sha256'])
        child = memory.add(self.f.store, native, [self.f.source])
        approval.decide(self.f.store, child['sha256'], self.request())
        approval.decide(self.f.store, old['sha256'], self.request())
        self.assertEqual(approval.active(self.f.store)[0]['bundle'], child)
        self.assertEqual(memory.retrieve(self.f.store, self.f.visible())['route']['condition'], 'ROUTED')

    def test_stale_selection_and_stale_review_are_rejected_before_writes(self):
        approval.decide(self.f.store, self.bundle['sha256'], self.request())
        child = self.child()
        approval.decide(self.f.store, child['sha256'], self.request(), activate_version=False)
        count = len(approval.decisions(self.f.store))
        before = (self.f.store/'active.json').read_bytes()
        with self.assertRaises(EvidenceError):
            approval.activate(self.f.store, child['sha256'], None, 'SYNTHETIC_OPERATOR')
        with self.assertRaises(EvidenceError):
            approval.decide(self.f.store, child['sha256'], self.request(), expected_current=None)
        self.assertEqual((self.f.store/'active.json').read_bytes(), before)
        self.assertEqual(len(approval.decisions(self.f.store)), count)

    def test_concurrent_activations_cannot_replace_a_newer_pointer(self):
        approval.decide(self.f.store, self.bundle['sha256'], self.request())
        children = [self.child('branch-a'), self.child('branch-b')]
        for child in children:
            approval.decide(self.f.store, child['sha256'], self.request(), activate_version=False)
        barrier = Barrier(2)
        def select(child):
            barrier.wait(timeout=5)
            try:
                approval.activate(self.f.store, child['sha256'], self.bundle['sha256'], 'SYNTHETIC_OPERATOR')
                return True
            except EvidenceError:
                return False
        with ThreadPoolExecutor(2) as pool:
            result = list(pool.map(select, children))
        self.assertEqual(sorted(result), [False, True])

    def test_atomic_pointer_failure_retains_review_without_claiming_activation(self):
        approval.decide(self.f.store, self.bundle['sha256'], self.request())
        child = self.child()
        with patch.object(approval.archive, 'atomic_json', side_effect=OSError('Synthetic disk error')):
            with self.assertRaises(OSError):approval.decide(self.f.store, child['sha256'], self.request())
        self.assertEqual(approval.active(self.f.store)[0]['bundle'], self.bundle)
        self.assertEqual(approval.decisions(self.f.store)[-1]['candidate_sha256'], child['sha256'])
        approval.activate(self.f.store, child['sha256'], self.bundle['sha256'], 'SYNTHETIC_OPERATOR')
        self.assertEqual(approval.active(self.f.store)[0]['bundle'], child)

    def test_index_tampering_is_not_silently_repaired_from_reviews(self):
        approval.decide(self.f.store, self.bundle['sha256'], self.request())
        path = self.f.store/'active.json'
        value = json.loads(path.read_text())
        value['versions'] = {}
        path.write_text(json.dumps(value))
        with self.assertRaises(EvidenceError):approval.active(self.f.store)
        self.assertEqual(json.loads(path.read_text())['versions'], {})
