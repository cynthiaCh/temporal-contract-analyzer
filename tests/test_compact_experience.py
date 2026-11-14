"""Single-file content, retrieval and review without generated sidecar files."""
import json
from pathlib import Path
import tempfile
import unittest

from temporal_contract_analyzer import compact_experience as compact
from temporal_contract_analyzer import experience_memory as memory, experience_approval as approval
from temporal_contract_analyzer.core import EvidenceError


class CompactExperienceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'experiences.json'
        self.value = dict(schema_version=compact.VERSION,
            review=dict(reviewer='Synthetic reviewer', decision='accept', at='2026-11-15T00:00:00Z'),
            experiences=[dict(id='entry-binding', title='Entry binding <example>', labels=['I'],
                requires=['entry_snapshot'], excludes=[], applicability='Accepted work retains entry identity.',
                event_relation='Capture entry values.', preservation='Retain accepted work.',
                exclusion='Check current cancellation policy.', verification='Navigate during a callback.')])
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.value))

    def test_read_search_and_freeze_create_no_sidecars(self):
        records=memory.records(self.path)
        self.assertEqual(len(records), 1)
        self.assertEqual(memory.search(self.path, 'entry')['results'][0]['id'], 'entry-binding')
        snapshot=approval.freeze(self.path)
        self.assertEqual(approval.validate_snapshot(self.path, snapshot), snapshot)
        self.assertEqual(approval.active(self.path)[0]['bundle'], records[0])
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_unaccepted_content_is_not_delivered(self):
        self.value['review']['decision']='revise'
        self.save()
        self.assertEqual(approval.freeze(self.path)['entries'], [])
        self.assertEqual(approval.active(self.path), [])

    def test_changed_content_cannot_validate_an_old_snapshot(self):
        snapshot=approval.freeze(self.path)
        self.value['experiences'][0]['event_relation']='Changed recommendation.'
        self.save()
        with self.assertRaises(EvidenceError):
            approval.validate_snapshot(self.path, snapshot)

    def test_duplicate_ids_and_invalid_predicates_are_rejected(self):
        self.value['experiences'].append(dict(self.value['experiences'][0]))
        self.save()
        with self.assertRaises(EvidenceError): memory.records(self.path)
        self.value['experiences'].pop()
        self.value['experiences'][0]['requires']=['invented-predicate']
        self.save()
        with self.assertRaises(EvidenceError): memory.records(self.path)

    def test_page_shows_the_file_and_escapes_content(self):
        html=compact.page(self.path).decode()
        self.assertIn(str(self.path), html)
        self.assertIn('Entry binding &lt;example&gt;', html)
        self.assertNotIn('Entry binding <example>', html)


if __name__ == '__main__':
    unittest.main()
