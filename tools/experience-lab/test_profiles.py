"""Offline profile persistence and execution-boundary checks."""
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen

import runner
from model_profiles import Profiles, revision
from serve import Server


class ProfileEditing(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'model-profiles.json'
        self.store = Profiles(self.path)

    def payload(self):
        config = self.store.snapshot()
        return dict(path=config['path'], revision=config['revision'], workspace_revision=config['workspace_revision'],
                    base_id='sol56-medium', create=True, id='custom-medium', model='fixture-model',
                    reasoning_effort='medium', service_tier='priority')

    def test_seed_includes_codex_and_qoder_credits_presets(self):
        profiles = self.store.snapshot()['profiles']
        self.assertEqual(len(profiles), 10)
        self.assertEqual(profiles['qoder-deepseek-flash-low']['request_unit'], 'model turns')
        self.assertEqual(profiles['sol56-medium']['model'], 'gpt-5.6-sol')
        self.assertEqual(profiles['sol56-medium']['reasoning_effort'], 'medium')
        self.assertEqual(profiles['qoder-efficient'], dict(model='Efficient', reasoning_effort=None, service_tier=None, request_unit='model turns'))

    def test_existing_workspace_gets_efficient_without_replacing_profiles(self):
        data = runner.read(self.path)
        data['profiles'].pop('qoder-efficient')
        data['profiles']['qoder-deepseek-flash-low']['reasoning_effort'] = 'max'
        self.path.write_text(json.dumps(data))
        Profiles(self.path)
        updated = runner.read(self.path)
        self.assertIn('qoder-efficient', updated['profiles'])
        self.assertEqual(updated['profiles']['qoder-deepseek-flash-low']['reasoning_effort'], 'max')
        self.assertEqual(updated['default_profile'], data['default_profile'])

    def test_add_edit_restart_and_frozen_runtime(self):
        runtime = runner.REPO/'temporal_contract_analyzer/_session_runtime/model-profiles.json'
        frozen = revision(runtime)
        provider = runner.read(self.path)['profiles']['sol56-medium']['provider']
        self.assertEqual(self.store.save(self.payload())['selected'], 'custom-medium')
        self.store.save(dict(self.payload(), create=False, base_id='custom-medium', model='fixture-edited', reasoning_effort=None, service_tier=None))
        loaded = Profiles(self.path).snapshot()['profiles']['custom-medium']
        self.assertEqual(loaded, dict(model='fixture-edited', reasoning_effort=None, service_tier=None))
        self.assertEqual(runner.read(self.path)['profiles']['custom-medium']['provider'], provider)
        self.assertEqual(revision(runtime), frozen)

    def test_stale_editor_and_duplicate_ids_do_not_overwrite(self):
        stale = self.payload()
        self.store.save(self.payload())
        before = revision(self.path)
        with self.assertRaisesRegex(ValueError, 'changed since loading'):
            self.store.save(stale)
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.store.save(self.payload())
        self.assertEqual(revision(self.path), before)

    def test_invalid_values_leave_file_intact(self):
        before = revision(self.path)
        for fields in [dict(id='../bad'), dict(model=' '), dict(reasoning_effort='bad setting'), dict(service_tier=42)]:
            with self.subTest(fields=fields):
                with self.assertRaises(ValueError):
                    self.store.save(dict(self.payload(), **fields))
                self.assertEqual(revision(self.path), before)

    def test_external_profile_copied_without_modifying_source(self):
        source = Path(self.temp.name)/'external.json'
        source.write_text(self.path.read_text())
        before = revision(source)
        config = self.store.snapshot(str(source))
        self.store.save(dict(self.payload(), path=str(source), revision=config['revision']))
        self.assertEqual(revision(source), before)
        self.assertIn('custom-medium', self.store.snapshot()['profiles'])

    def test_save_endpoint_persists_without_execution(self):
        server = Server(0, Path(self.temp.name)/'runs')
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        config = server.profiles.snapshot()
        body = dict(self.payload(), path=config['path'], revision=config['revision'], workspace_revision=config['workspace_revision'])
        request = Request(server.url+'/api/profiles/save', data=json.dumps(body).encode(), headers={
            'Content-Type':'application/json', 'Origin':server.url, 'X-TempoEvo-Token':server.token})
        with patch.object(runner.subprocess, 'run') as execution:
            with urlopen(request) as response:
                saved = json.load(response)
            execution.assert_not_called()
        self.assertEqual(saved['selected'], 'custom-medium')
        self.assertIsNone(server.controller.active)
