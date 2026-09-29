import concurrent.futures
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from temporal_contract_analyzer import archive, cli
from temporal_contract_analyzer.core import EvidenceError


SOURCE = '<template><div>😀</div></template><script setup>async function load(){await fetch(); store.save();}</script>'


class ReportArchiveTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root/'project'
        self.project.mkdir()
        self.store = self.root/'reports'
        self.file = self.project/'Demo.vue'
        self.file.write_text(SOURCE, encoding='utf-8')
        env = patch.dict(os.environ, {'TCA_CONFIG': str(self.root/'config.json'), 'TCA_REPORT_STORE': str(self.store)})
        env.start()
        self.addCleanup(env.stop)

    def scan(self, **labels):
        return archive.scan_path(self.project, self.store, **labels)

    def test_archive_captures_source_and_report_once_and_survives_source_edits(self):
        result = self.scan(label='before', task_id='task-1')
        meta = result['archive']
        self.assertEqual(meta['status'], 'parsed')
        self.assertEqual(meta['task_id'], 'task-1')
        self.file.write_text('<script setup>changed();</script>')
        self.assertEqual(archive.read_source(meta['report_id'], 'Demo.vue', self.store)['text'], SOURCE)
        self.assertEqual(archive.read_report(meta['report_id'], self.store)['report'], result['report'])
        self.assertTrue(archive.verify(meta['report_id'], self.store)['verified'])
        self.assertIn('effect-after-await', archive.layer_text(meta['report_id'], 'full', self.store))
        self.assertIn('Heuristic interpretations', archive.layer_text(meta['report_id'], 'review', self.store))

    def test_dirty_buffers_are_preserved_without_touching_disk(self):
        edited = SOURCE.replace('store.save()', 'store.publish()')
        result = archive.scan_and_archive(dict(mode='folder', root=str(self.project), overlays={'Demo.vue': edited,
                                                  'node_modules/secret.js': 'bad()', '../escape.js': 'bad()'}), self.store, origin='vscode')
        meta = result['archive']
        self.assertEqual(meta['input_kind'], 'editor_snapshot')
        self.assertEqual(meta['overlays'], ['Demo.vue'])
        self.assertEqual(self.file.read_text(), SOURCE)
        self.assertEqual(archive.read_source(meta['report_id'], 'Demo.vue', self.store)['text'], edited)
        with self.assertRaises(EvidenceError):
            archive.read_source(meta['report_id'], '../escape.js', self.store)

    def test_partial_failed_and_empty_scans_remain_visible(self):
        self.file.write_text('<script src="./other.js"></script>')
        partial = self.scan()['archive']
        self.assertEqual(partial['status'], 'partial')
        self.assertEqual(partial['layers'], [])
        with self.assertRaises(EvidenceError):
            archive.layer_text(partial['report_id'], 'facts', self.store)
        failed = archive.scan_path(self.root/'missing', self.store)['archive']
        self.assertEqual(failed['status'], 'failed')
        self.assertTrue(archive.verify(failed['report_id'], self.store)['verified'])
        self.assertIsNone(archive.read_report(failed['report_id'], self.store)['report'])
        self.file.unlink()
        empty = self.scan()['archive']
        self.assertEqual(empty['status'], 'empty')
        self.assertEqual(archive.list_reports(self.store)['total'], 3)

    def test_hash_tampering_and_extra_files_are_rejected(self):
        meta = self.scan()['archive']
        folder = Path(meta['archive_path'])
        snapshot = folder/'snapshot.json'
        original = snapshot.read_bytes()
        snapshot.write_text('{}')
        with self.assertRaisesRegex(EvidenceError, 'checksum'):
            archive.read_report(meta['report_id'], self.store)
        snapshot.write_bytes(original)
        (folder/'unexpected.txt').write_text('extra')
        with self.assertRaisesRegex(EvidenceError, 'inventory'):
            archive.verify(meta['report_id'], self.store)

    def test_snapshot_binding_is_verified_even_when_manifest_is_rehashed(self):
        meta = self.scan()['archive']
        folder = Path(meta['archive_path'])
        snapshot = json.loads((folder/'snapshot.json').read_text())
        snapshot['sources']['Demo.vue'] = '<script>different();</script>'
        archive.atomic_json(folder/'snapshot.json', snapshot)
        manifest = json.loads((folder/'manifest.json').read_text())
        manifest['files']['snapshot.json'] = archive.sha((folder/'snapshot.json').read_bytes())
        archive.atomic_json(folder/'manifest.json', manifest)
        with self.assertRaisesRegex(EvidenceError, 'binding'):
            archive.verify(meta['report_id'], self.store)

    def test_annotation_is_append_only_and_does_not_change_frozen_evidence(self):
        result = self.scan()
        meta, finding = result['archive'], result['report']['findings'][0]
        folder = Path(meta['archive_path'])
        original = {str(p): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
        first = archive.annotate(meta['report_id'], finding['id'], 'uncertain', '需要确认生命周期', self.store)
        second = archive.annotate(meta['report_id'], finding['id'], 'dismissed', '已有上层有效性检查', self.store)
        self.assertNotEqual(first['record_id'], second['record_id'])
        self.assertEqual(len(archive.read_report(meta['report_id'], self.store)['notes']), 2)
        self.assertEqual(original, {str(p): p.read_bytes() for p in folder.rglob('*') if p.is_file()})
        self.assertTrue(archive.verify(meta['report_id'], self.store)['verified'])

    def test_compare_is_bound_to_project_scope_and_actual_parser_identity(self):
        before = self.scan()['archive']
        self.file.write_text('<script setup>async function load(){await fetch();}</script>')
        after = self.scan(parent_report_id=before['report_id'])['archive']
        delta = archive.compare_reports(before['report_id'], after['report_id'], self.store)
        self.assertTrue(delta['comparable'])
        self.assertIn('effect-after-await', {f['rule'] for f in delta['removed_hints']})
        single = archive.scan_path(self.file, self.store)['archive']
        with self.assertRaises(EvidenceError):
            archive.compare_reports(before['report_id'], single['report_id'], self.store)
        with self.assertRaises(EvidenceError):
            archive.scan_path(self.file, self.store, parent_report_id=before['report_id'])
        partial = archive.scan_path(self.project, self.store, node=str(self.root/'missing-node'))['archive']
        self.assertFalse(archive.compare_reports(before['report_id'], partial['report_id'], self.store)['comparable'])

    def test_concurrent_scans_have_unique_complete_records_and_query_filters(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(lambda number: self.scan(label='scan-'+str(number)), range(3)))
        ids = {r['archive']['report_id'] for r in results}
        self.assertEqual(len(ids), 3)
        for report_id in ids:
            archive.verify(report_id, self.store)
        page = archive.list_reports(self.store, limit=1, offset=1)
        self.assertEqual(page['total'], 3)
        self.assertEqual(len(page['items']), 1)
        self.assertEqual(archive.list_reports(self.store, search='scan-1')['total'], 1)
        self.assertEqual(archive.list_reports(self.store, origin='codex')['total'], 0)

    def test_store_cannot_be_inside_candidate_or_contain_candidate(self):
        for store in (self.project/'reports', self.root):
            with self.assertRaises(EvidenceError):
                archive.scan_path(self.project, store)
        self.assertFalse((self.project/'reports').exists())

    def test_path_traversal_and_symlinked_archives_are_rejected(self):
        for value in ('../secret', '/tmp/secret', 'r-123'):
            with self.assertRaises(EvidenceError):
                archive.read_report(value, self.store)
        meta = self.scan()['archive']
        path = Path(meta['archive_path'])/'report.json'
        path.unlink()
        path.symlink_to(self.file)
        with self.assertRaises(EvidenceError):
            archive.verify(meta['report_id'], self.store)

    def test_cli_configuration_and_show_do_not_rescan(self):
        from contextlib import redirect_stdout
        import io
        with redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['reports','init','--store',str(self.store)]), 0)
            self.assertEqual(cli.main(['reports','scan',str(self.project),'--label','CLI test']), 0)
        meta = archive.list_reports()['items'][0]
        self.file.unlink()
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(cli.main(['reports','show',meta['report_id']]), 0)
        self.assertIn('effect-after-await', output.getvalue())
        self.assertEqual(archive.configuration()['store'], str(self.store.resolve()))


if __name__ == '__main__':
    unittest.main()
