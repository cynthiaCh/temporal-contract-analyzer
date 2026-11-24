import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from temporal_contract_analyzer.core import EvidenceError, ROOT
from temporal_contract_analyzer.general_memory import DEFAULT_PACK, GeneralMemory, SECTIONS, VERSION, export_pack
from temporal_contract_analyzer.mcp_server import Session
from temporal_contract_analyzer.personal_memory import PersonalMemory


def pack_entry(code='general-save'):
    return dict(experience_id=code, title='Save lifecycle', summary='Preserve accepted saves after close.',
                labels=['L', 'A'], requires=[], excludes=[], reviewed_by='fixture', reviewed_at='2026-11-24',
                applicability='An accepted save outlives its editor.', event_relation='Stop UI updates after close.',
                preservation='Finish accepted saves.', exclusion='Not a rollback request.',
                verification='Check completion after closing the editor.')


class CombinedMemoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root/'project'
        self.project.mkdir()
        self.pack = self.root/'general.json'
        self.value = dict(schema_version=VERSION, domain='temporal_contracts', version='fixture-v1',
                          entries=[pack_entry()])
        self.pack.write_text(json.dumps(self.value))
        self.personal = self.root/'personal'
        self.session = Session(self.root/'reports', personal_store=self.personal, general_store=self.pack)

    def call(self, name, **arguments):
        result = self.session.call(name, dict(project=str(self.project), **arguments))
        return result['experience'] if name == 'update_experience' else result

    def test_perspective_and_modification_are_searchable_versioned_and_preserved(self):
        original = self.call('update_experience', operation='add', correction='This interpretation is incorrect.',
                             perspective='Treat the repository enum as a business contract, not a guessed label.',
                             modification='Use the explicit mapping and render a yellow badge for pending.',
                             applicability='Order list only.')
        for query in ('enum', 'yellow'):
            result = self.call('recall_experience', source='personal', query=query)
            self.assertEqual(result['items'][0]['experience_id'], original['experience_id'])
            self.assertEqual(result['items'][0]['perspective'], original['history'][0]['perspective'])
            self.assertEqual(result['items'][0]['modification'], original['history'][0]['modification'])
        updated = self.call('update_experience', operation='update', correction='Also preserve the empty-state display.',
                            experience_id=original['experience_id'], expected_version=1,
                            modification=original['history'][0]['modification']+' Preserve the empty-state display.')
        self.assertEqual(updated['history'][-1]['perspective'], original['history'][0]['perspective'])
        self.assertEqual(updated['history'][0]['correction'], 'This interpretation is incorrect.')
        self.assertIn('empty-state', updated['history'][-1]['modification'])
        self.assertEqual(updated['history'][-1]['applicability'], 'Order list only.')
        cleared = self.call('update_experience', operation='update', correction='Do not infer the cause yet.',
                            experience_id=original['experience_id'], expected_version=2, perspective='')
        self.assertEqual(cleared['history'][-1]['perspective'], '')
        self.assertEqual(self.call('recall_experience', source='personal', query='enum')['total'], 0)
        self.call('update_experience', operation='delete', experience_id=original['experience_id'], expected_version=3)
        restored = self.call('update_experience', operation='restore', experience_id=original['experience_id'], expected_version=4)
        self.assertEqual(restored['history'][-1]['modification'], cleared['history'][-1]['modification'])
        self.assertEqual(self.call('read_experience', experience_id=original['experience_id'])['history'][0], original['history'][0])

    def test_structured_content_is_text_and_cannot_be_silently_ignored(self):
        for arguments in (dict(operation='add', correction='User correction', modification=['step']),
                          dict(operation='noop', perspective='Would be silently lost')):
            with self.subTest(arguments=arguments), self.assertRaises(EvidenceError):
                self.call('update_experience', **arguments)
        self.assertFalse(self.personal.exists())

    def test_mem0_style_recall_update_and_noop_preserve_scope_and_quotes(self):
        first = self.call('update_experience', operation='add', correction='Status 2 means pending.',
                          guidance='For orders, status 2 means pending; read the API enum.', applicability='Orders only.')
        for i in range(6):
            self.call('update_experience', operation='add', correction='Order rule '+str(i))
        self.pack.write_text('{}')
        candidates = self.call('recall_experience', source='personal', limit=5, query='Order status pending')
        self.assertEqual(len(candidates['items']), 5)
        self.assertEqual(candidates['total'], 7)
        self.assertTrue(all(row['source']=='personal' for row in candidates['items']))
        candidate = next(row for row in candidates['items'] if row['experience_id']==first['experience_id'])
        history = self.call('read_experience', experience_id=candidate['experience_id'])
        self.assertEqual(history['history'][0]['correction'], 'Status 2 means pending.')
        updated = self.call('update_experience', operation='update', correction='Pending needs a yellow badge.',
                            experience_id=candidate['experience_id'], expected_version=candidate['version'],
                            guidance=candidate['guidance']+' Pending needs a yellow badge.')
        self.assertEqual(updated['history'][-1]['applicability'], 'Orders only.')
        self.assertIn('status 2 means pending', updated['history'][-1]['guidance'])
        self.assertEqual(updated['history'][0]['correction'], 'Status 2 means pending.')
        result = self.session.call('update_experience', dict(project=str(self.project), operation='noop',
                                  experience_id=first['experience_id'], expected_version=2))
        self.assertFalse(result['changed'])
        self.assertEqual(result['experience']['version'], 2)
        with self.assertRaises(EvidenceError):
            self.call('update_experience', operation='update', correction='Stale update',
                      experience_id=candidate['experience_id'], expected_version=candidate['version'])

    def test_read_general_is_readonly_and_update_cannot_target_it(self):
        before = self.pack.read_bytes()
        row = self.call('read_experience', source='general', experience_id='general-save')
        self.assertEqual(row['source'], 'general')
        self.assertTrue(row['read_only'])
        self.assertEqual(row['version'], 'fixture-v1')
        with self.assertRaises(EvidenceError):
            self.call('update_experience', source='general', operation='delete',
                      experience_id='general-save', expected_version=1)
        self.assertEqual(self.pack.read_bytes(), before)
        self.assertFalse(self.personal.exists())

    def test_combined_candidates_keep_sources_and_full_boundaries(self):
        self.call('update_experience', operation='add', correction='Accepted saves must finish after close.',
                  applicability='Only the edit page.', related_general_id='general-save')
        result = self.call('recall_experience', query='save close')
        self.assertEqual([x['source'] for x in result['items']], ['personal', 'general'])
        self.assertEqual(result['items'][0]['related_general_id'], 'general-save')
        general = result['items'][1]
        self.assertTrue(general['read_only'])
        self.assertEqual(general['version'], 'fixture-v1')
        for key in SECTIONS:
            self.assertEqual(general[key], self.value['entries'][0][key])
        self.assertEqual(result['sources']['general']['bank_count'], 1)
        self.assertFalse((self.root/'reports').exists())

    def test_pagination_and_source_filter_do_not_starve_either_pool(self):
        for i in range(3):
            self.call('update_experience', operation='add', correction='Save rule '+str(i))
        first = self.call('recall_experience', query='save', limit=2)
        self.assertEqual([x['source'] for x in first['items']], ['personal', 'general'])
        next_page = self.call('recall_experience', query='save', limit=2, offset=first['next_offset'])
        self.assertEqual(len(next_page['items']), 2)
        self.assertIsNone(next_page['next_offset'])
        self.assertEqual(len(self.call('recall_experience', query='', source='personal')['items']), 3)
        self.assertEqual(len(self.call('recall_experience', query='', source='general')['items']), 1)
        self.assertEqual(self.call('recall_experience', query='no_matches')['total'], 0)

    def test_non_temporal_corrections_and_local_revisions_preserve_omitted_fields(self):
        saved = self.call('update_experience', operation='add', correction='Status 2 means pending confirmation.',
                          guidance='Read the API enum instead of guessing.', context='Order badge',
                          mistake='Treated 2 as completed.', applicability='Order endpoint only.',
                          exclusions='Not the payment status.')
        revised = self.call('update_experience', operation='update', correction='Status 2 also needs a yellow badge.',
                            experience_id=saved['experience_id'], expected_version=1)
        for key in ('guidance', 'context', 'mistake', 'applicability', 'exclusions'):
            self.assertEqual(revised['history'][-1][key], saved['history'][-1][key])
        matches = self.call('recall_experience', query='endpoint', source='personal')['items']
        self.assertEqual(matches[0]['experience_id'], saved['experience_id'])
        deleted = self.call('update_experience', experience_id=saved['experience_id'], operation='delete', expected_version=2)
        restored = self.call('update_experience', experience_id=saved['experience_id'], operation='restore', expected_version=3)
        self.assertTrue(deleted['deleted'])
        self.assertEqual(restored['history'][-1]['exclusions'], 'Not the payment status.')
        self.assertEqual(restored['history'][0]['correction'], 'Status 2 means pending confirmation.')

    def test_exact_duplicate_is_noop_and_general_content_is_never_written(self):
        before = self.pack.read_bytes()
        args = dict(correction='Save correction', guidance='Preserve accepted saves.', related_general_id='general-save')
        first = self.call('update_experience', operation='add', **args)
        repeated = self.call('update_experience', operation='add', **args)
        self.assertEqual(first, repeated)
        self.assertEqual(len(list(self.personal.glob('*.json'))), 1)
        same = self.call('update_experience', operation='update', **args, experience_id=first['experience_id'], expected_version=1)
        self.assertEqual(same['version'], 1)
        with self.assertRaises(EvidenceError):
            self.call('update_experience', experience_id='general-save', operation='delete', expected_version=1)
        self.assertEqual(self.pack.read_bytes(), before)

    def test_legacy_personal_files_remain_readable_and_explicit_empty_clears(self):
        memory = PersonalMemory(self.personal)
        row = memory.update(str(self.project), 'add', 'Old correction', guidance='Old guidance')['experience']
        path = self.personal/(row['experience_id']+'.json')
        legacy = copy.deepcopy(row)
        for key in ('context', 'mistake', 'applicability', 'exclusions', 'related_general_id', 'perspective', 'modification'):
            legacy['history'][0].pop(key)
        path.write_text(json.dumps(legacy))
        self.assertEqual(self.call('recall_experience', query='Old', source='personal')['total'], 1)
        revised = self.call('update_experience', operation='update', correction='New correction', guidance='',
                            experience_id=row['experience_id'], expected_version=1)
        self.assertEqual(revised['history'][-1]['guidance'], '')
        self.assertEqual(revised['history'][0], legacy['history'][0])

    def test_personal_store_cannot_contain_general_pack(self):
        before = self.pack.read_bytes()
        with self.assertRaises(EvidenceError):
            Session(self.root/'reports', personal_store=self.root, general_store=self.pack)
        self.assertEqual(self.pack.read_bytes(), before)
        self.assertFalse((self.root/'.lock').exists())

    def test_export_cli_refuses_overwrite_and_keeps_input_library(self):
        output = self.root/'existing.json'
        output.write_text('keep existing output')
        result = subprocess.run([sys.executable, '-B', '-m', 'temporal_contract_analyzer',
            'experience-memory', 'export-general', '--store', str(self.root/'library'),
            '--version', 'fixture-v1', '--output', str(output)],
            text=True, capture_output=True, cwd=ROOT, timeout=15)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_text(), 'keep existing output')
        self.assertFalse((self.root/'library').exists())

    def test_invalid_general_pack_is_visible_and_personal_only_still_works(self):
        self.pack.write_text('{}')
        with self.assertRaises(EvidenceError):
            self.call('recall_experience', query='save')
        self.assertEqual(self.call('recall_experience', query='', source='personal')['total'], 0)
        self.assertFalse(self.personal.exists())
        self.value['entries'].append(pack_entry())
        self.pack.write_text(json.dumps(self.value))
        with self.assertRaises(EvidenceError):
            GeneralMemory(self.pack).recall('')

    def test_export_includes_only_current_approved_guidance_and_retains_text(self):
        from temporal_contract_analyzer import compact_experience as compact
        approved = dict(id='accepted', title='Accepted rule', labels=['L'], requires=[], excludes=[],
                        **{key: 'Verbatim '+key for key in SECTIONS})
        document = dict(schema_version=compact.VERSION, experiences=[approved,
                        dict(approved, id='pending'), dict(approved, id='superseded')])
        review = dict(reviewer='human', decision='accept', at='2026-11-24')
        with patch('temporal_contract_analyzer.experience_approval.approved', return_value=[dict(bundle=dict(id='accepted'))]), \
             patch.object(compact, 'reviewed_summaries', return_value={'accepted': {'text': 'Reviewed Abstract'}}), \
             patch.object(compact, 'documents', return_value=[(self.pack, document)]), \
             patch.object(compact, 'review_for', return_value=review):
            packed = export_pack(self.root, 'fixture-v1')
            self.assertEqual(len(packed['entries']), 1)
            for key in SECTIONS:
                self.assertEqual(packed['entries'][0][key], approved[key])
        text = json.dumps(packed)
        self.assertNotIn('sha256', text)
        self.assertNotIn('trajectory', text)

    def test_shipped_pack_is_reproducible_and_has_current_accepted_abstracts(self):
        if not (ROOT/'experience-memory/library').exists():
            self.skipTest('Research source library is excluded from clean source exports')
        shipped = json.loads(DEFAULT_PACK.read_text())
        rebuilt = export_pack(ROOT/'experience-memory/library', shipped['version'])
        self.assertEqual(shipped, rebuilt)
        self.assertEqual(len(GeneralMemory().recall('')['items']), len(shipped['entries']))

    def test_stdio_new_session_uses_general_and_personal_sources(self):
        messages = [dict(jsonrpc='2.0', id=1, method='initialize', params={}),
                    dict(jsonrpc='2.0', method='notifications/initialized'),
                    dict(jsonrpc='2.0', id=2, method='tools/call', params=dict(name='update_experience',
                         arguments=dict(project=str(self.project), operation='add', correction='Save project exception'))),
                    dict(jsonrpc='2.0', id=3, method='tools/call', params=dict(name='recall_experience',
                         arguments=dict(project=str(self.project), query='Save project exception', source='personal', limit=5))),
                    dict(jsonrpc='2.0', id=4, method='tools/call', params=dict(name='recall_experience',
                         arguments=dict(project=str(self.project), query='save')))]
        process = subprocess.run([sys.executable, '-I', '-S', '-B', str(ROOT/'temporal_contract_analyzer/hub_entry.py'),
                                  'reports', 'mcp', '--personal-store', str(self.personal), '--general-store', str(self.pack)],
                                 input='\n'.join(json.dumps(x) for x in messages)+'\n', text=True,
                                 capture_output=True, cwd=self.root, timeout=15)
        self.assertEqual(process.returncode, 0, process.stderr)
        responses = [json.loads(x) for x in process.stdout.splitlines()]
        prepared = json.loads(responses[-2]['result']['content'][0]['text'])
        self.assertEqual(len(prepared['items']), 1)
        recalled = json.loads(responses[-1]['result']['content'][0]['text'])
        self.assertEqual([x['source'] for x in recalled['items']], ['personal', 'general'])
        self.assertIn('update_experience', responses[0]['result']['instructions'])
