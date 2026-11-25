"""Owner saves remain immediately consumable by the existing retrieval library."""
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from temporal_contract_analyzer import owner_experience as owner, compact_experience as compact
from temporal_contract_analyzer.core import EvidenceError


class OwnerExperienceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Path(self.temp.name)
        owner.initialize(self.store)
        self.record = dict(title='Capture entry', labels=['I'], requires=['entry_snapshot'], excludes=[],
                           abstract='Capture accepted identity before callbacks.',
                           **{key: 'Keep entry identity.' for key, _ in compact.SECTIONS})

    def save(self, revision=None, record=None):
        return owner.change(self.store, dict(action='save', id='personal-entry', revision=revision,
                                            record=record or self.record))['entries'][0]

    def test_save_update_delete_restore_and_conflict(self):
        first = self.save()
        self.assertIn(first['id'], compact.active_view(self.store)['active_ids'])
        self.assertEqual(compact.reviewed_summaries(self.store)[first['id']]['text'], self.record['abstract'])
        updated = deepcopy(self.record)
        updated['event_relation'] = 'Capture the original document before dispatch.'
        second = self.save(first['revision'], updated)
        self.assertIn(second['id'], compact.reviewed_summaries(self.store))
        with self.assertRaises(EvidenceError):
            self.save(first['revision'])
        self.assertEqual(owner.listing(self.store)['entries'][0]['revision'], second['revision'])
        owner.change(self.store, dict(action='delete', id=second['id'], revision=second['revision']))
        self.assertEqual(owner.listing(self.store)['entries'], [])
        saved = next(h for h in owner.history(self.store)['history'] if h['action'] == 'delete')['record']
        restored = {key: saved[key] for key in self.record if key != 'abstract'}
        restored['abstract'] = saved['summary']['text']
        self.save(record=restored)
        self.assertIn(first['id'], compact.reviewed_summaries(self.store))

    def test_invalid_save_leaves_library_unchanged(self):
        first = self.save()
        invalid = deepcopy(self.record)
        invalid['requires'] = ['invented-mechanism']
        with self.assertRaises(EvidenceError):
            self.save(first['revision'], invalid)
        self.assertEqual(owner.listing(self.store)['entries'][0]['revision'], first['revision'])
        self.assertEqual(owner.history(self.store)['history'], [])

    def test_owner_save_replaces_pending_suggestion(self):
        first = self.save()
        file = self.store/'personal.json'
        value = compact.load(file)
        draft = deepcopy(value['experiences'][0])
        draft['review'] = dict(reviewer=None, decision='pending', at=None)
        value['experiences'][0]['pending_revision'] = dict(base_record='0'*64, item=draft)
        compact._write(file, value)
        entry = owner.listing(self.store)['entries'][0]
        result = self.save(entry['revision'])
        self.assertNotIn('pending_revision', result['record'])
        self.assertIn(first['id'], compact.reviewed_summaries(self.store))
