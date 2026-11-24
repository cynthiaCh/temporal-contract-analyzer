import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from temporal_contract_analyzer.core import EvidenceError, ROOT
from temporal_contract_analyzer.mcp_server import Session
from temporal_contract_analyzer.personal_memory import PersonalMemory


class PersonalMemoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root/'project'
        self.other = self.root/'other'
        self.project.mkdir()
        self.other.mkdir()
        self.store = self.root/'personal'
        self.memory = PersonalMemory(self.store)

    def record(self, **kwargs):
        return self.memory.update(str(self.project), 'update' if kwargs.get('experience_id') else 'add', '关闭页面不能取消已提交的保存请求。',
                                    guidance='Preserve accepted saves after closing.', **kwargs)['experience']

    def test_empty_reads_do_not_create_store_and_projects_are_isolated(self):
        self.assertEqual(self.memory.recall(str(self.project), '')['items'], [])
        self.assertFalse(self.store.exists())
        row = self.record()
        self.assertEqual(self.memory.recall(str(self.other), '')['items'], [])
        with self.assertRaises(EvidenceError):
            self.memory.read(str(self.other), row['experience_id'])
        with self.assertRaises(EvidenceError):
            self.memory.recall('relative/path', '')

    def test_original_correction_and_revision_survive_new_client(self):
        old = self.record()
        revised = self.memory.update(str(self.project), 'update', '只适用于编辑页面。',
                                       experience_id=old['experience_id'], expected_version=1)['experience']
        new_client = PersonalMemory(self.store)
        row = new_client.read(str(self.project), old['experience_id'])
        self.assertEqual(row, revised)
        self.assertEqual(row['history'][0]['correction'], '关闭页面不能取消已提交的保存请求。')
        self.assertEqual(row['history'][1]['correction'], '只适用于编辑页面。')
        with self.assertRaises(EvidenceError):
            self.record(experience_id=old['experience_id'], expected_version=1)
        self.assertEqual(new_client.read(str(self.project), old['experience_id'])['version'], 2)

    def test_delete_restore_and_stale_writes(self):
        row = self.record()
        deleted = self.memory.update(str(self.project), 'delete', experience_id=row['experience_id'], expected_version=1)["experience"]
        self.assertTrue(deleted['deleted'])
        self.assertFalse(self.memory.recall(str(self.project), '')['items'])
        with self.assertRaises(EvidenceError):
            self.memory.update(str(self.project), 'restore', experience_id=row['experience_id'], expected_version=1)["experience"]
        restored = self.memory.update(str(self.project), 'restore', experience_id=row['experience_id'], expected_version=2)["experience"]
        self.assertEqual(restored['version'], 3)
        self.assertEqual(self.memory.recall(str(self.project), '保存')['items'][0]['experience_id'], row['experience_id'])

    def test_recall_uses_current_text_and_paginates_without_cross_project_matches(self):
        self.record()
        self.memory.update(str(self.project), 'add', '保存前检查请求身份。')['experience']
        self.memory.update(str(self.other), 'add', '保存 unrelated project')['experience']
        first = self.memory.recall(str(self.project), '保存', limit=1)
        second = self.memory.recall(str(self.project), '保存', limit=1, offset=first['next_offset'])
        self.assertEqual(first['total'], 2)
        self.assertIsNone(second['next_offset'])
        self.assertNotEqual(first['items'][0]['experience_id'], second['items'][0]['experience_id'])
        self.assertEqual(self.memory.recall(str(self.project), 'nonexistent')['items'], [])

    def test_invalid_ids_and_missing_version_cannot_mutate(self):
        row = self.record()
        for code in ('../outside', '', 'a'*33):
            with self.assertRaises(EvidenceError):
                self.memory.read(str(self.project), code)
        with self.assertRaises(EvidenceError):
            self.memory.update(str(self.project), 'delete', experience_id=row['experience_id'], expected_version=None)["experience"]
        with self.assertRaises(EvidenceError):
            self.memory.update(str(self.project), 'add', '   ')['experience']

    def test_mcp_instructions_and_validation(self):
        session = Session(self.root/'reports', personal_store=self.store)
        result = session.handle(dict(jsonrpc='2.0', id=1, method='initialize', params={}))
        self.assertIn('update_experience', result['result']['instructions'])
        session.handle(dict(jsonrpc='2.0', method='notifications/initialized'))
        for arguments in ({'project': str(self.project)},
                          {'project': str(self.project), 'correction': 'x', 'unexpected': 'x'}):
            result = session.handle(dict(jsonrpc='2.0', id=2, method='tools/call',
                                         params=dict(name='update_experience', arguments=arguments)))
            self.assertTrue(result['result']['isError'])
        self.assertFalse(self.store.exists())

    def test_stdio_records_and_second_process_recalls_without_model_or_project_execution(self):
        def run(tool, arguments):
            messages = [dict(jsonrpc='2.0', id=1, method='initialize', params={}),
                        dict(jsonrpc='2.0', method='notifications/initialized'),
                        dict(jsonrpc='2.0', id=2, method='tools/call', params=dict(name=tool, arguments=arguments))]
            process = subprocess.run([sys.executable, '-I', '-S', '-B',
                                      str(ROOT/'temporal_contract_analyzer/hub_entry.py'),
                                      'reports', 'mcp', '--store', str(self.root/'reports'),
                                      '--personal-store', str(self.store)],
                                     input='\n'.join(json.dumps(m) for m in messages)+'\n',
                                     text=True, capture_output=True, cwd=self.other, timeout=15)
            self.assertEqual(process.returncode, 0, process.stderr)
            result = json.loads(process.stdout.splitlines()[-1])['result']
            self.assertFalse(result['isError'], result)
            return json.loads(result['content'][0]['text'])
        saved = run('update_experience', dict(project=str(self.project), operation='add', correction='Do not cancel accepted saves.'))
        recalled = run('recall_experience', dict(project=str(self.project), query='accepted saves'))
        self.assertEqual(recalled['items'][0]['experience_id'], saved['experience']['experience_id'])
        self.assertFalse((self.root/'reports').exists())

    def test_concurrent_clients_cannot_overwrite_same_version(self):
        from concurrent.futures import ThreadPoolExecutor
        row = self.record()

        def revise(correction):
            try:
                PersonalMemory(self.store).update(str(self.project), 'update', correction,
                    experience_id=row['experience_id'], expected_version=1)['experience']
                return 'saved'
            except EvidenceError:
                return 'stale'

        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(revise, ['first correction', 'second correction']))
        self.assertEqual(sorted(results), ['saved', 'stale'])
        self.assertEqual(self.memory.read(str(self.project), row['experience_id'])['version'], 2)

    def test_restricted_session_cannot_access_personal_memory(self):
        with patch('temporal_contract_analyzer.archive.layer_text', return_value='frozen evidence'):
            session = Session(self.root/'reports', report_id='bound', layer='facts',
                              personal_store=self.store)
        self.assertEqual([tool['name'] for tool in session.definitions()], ['read_report'])
        for name in ('recall_experience', 'read_experience', 'update_experience'):
            with self.subTest(tool=name), self.assertRaises(EvidenceError):
                session.call(name, dict(project=str(self.project), correction='x'))
        self.assertFalse(self.store.exists())

    def test_noop_preserves_files_and_rejects_stale_or_deleted_coverage(self):
        empty = self.memory.update(str(self.project), 'noop')
        self.assertEqual(empty, dict(operation='noop', changed=False, experience=None))
        self.assertFalse(self.store.exists())
        row = self.record()
        (self.store/'.lock').unlink()
        before = {p.name: p.read_bytes() for p in self.store.iterdir()}
        result = self.memory.update(str(self.project), 'noop', experience_id=row['experience_id'], expected_version=1)
        self.assertFalse(result['changed'])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.store.iterdir()})
        self.memory.update(str(self.project), 'delete', experience_id=row['experience_id'], expected_version=1)
        for version in (1, 2):
            with self.subTest(version=version), self.assertRaises(EvidenceError):
                self.memory.update(str(self.project), 'noop', experience_id=row['experience_id'], expected_version=version)

    def test_invalid_operation_combinations_cannot_create_storage(self):
        cases = [dict(operation='unknown'), dict(operation='update', correction='New rule'),
                 dict(operation='add', correction='New rule', experience_id='a'*32),
                 dict(operation='delete', experience_id='a'*32, expected_version=1, correction='Ignored text'),
                 dict(operation='noop', guidance='Must not be silently ignored'),
                 dict(operation='restore', experience_id='a'*32, expected_version=True)]
        for arguments in cases:
            with self.subTest(arguments=arguments), self.assertRaises(EvidenceError):
                self.memory.update(str(self.project), **arguments)
        self.assertFalse(self.store.exists())

    def test_repeated_add_delete_restore_report_noop_without_extra_versions(self):
        arguments = dict(correction='Status 2 is pending.', guidance='Read the API enum.')
        added = self.memory.update(str(self.project), 'add', **arguments)
        self.assertTrue(added['changed'])
        repeated = self.memory.update(str(self.project), 'add', **arguments)
        self.assertEqual(repeated['operation'], 'noop')
        row = added['experience']
        for operation, first_version in (('delete', 1), ('restore', 2)):
            changed = self.memory.update(str(self.project), operation, experience_id=row['experience_id'], expected_version=first_version)
            unchanged = self.memory.update(str(self.project), operation, experience_id=row['experience_id'], expected_version=first_version+1)
            self.assertTrue(changed['changed'])
            self.assertFalse(unchanged['changed'])
            self.assertEqual(unchanged['experience']['version'], first_version+1)

    def test_environment_selects_personal_store(self):
        with patch.dict(os.environ, TCA_PERSONAL_MEMORY=str(self.store)):
            self.assertEqual(PersonalMemory().root, self.store.resolve())
