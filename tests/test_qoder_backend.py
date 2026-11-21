"""Synthetic CLI events test the Qoder boundary without model requests or Credits."""
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from temporal_contract_analyzer.qoder_backend import QoderBackend, parse_events
from temporal_contract_analyzer._session_runtime.model_settings import resolve_profile, validate_settings
from temporal_contract_analyzer._session_runtime.read_policy import read_command


def events(turns=1):
    return [dict(type='system', subtype='init', model='DeepSeek-Flash', apiKeySource='none', mcp_servers=[], plugins=[]),
            dict(type='assistant', message=dict(id='fixture-message', stop_reason='end_turn')),
            dict(type='result', subtype='success', is_error=False, num_turns=turns,
                 result='{"ready":true}', total_credits=0.125, permission_denials=[])]


class Parsing(unittest.TestCase):
    def test_confirmed_model_and_bounded_turns(self):
        self.assertEqual(parse_events(events(), 'DeepSeek-Flash', 2)['num_turns'], 1)
        for data, model in [(events(3), 'DeepSeek-Flash'), (events(), 'Auto'),
                            (events()+[events()[-1]], 'DeepSeek-Flash'), (events()[:-1], 'DeepSeek-Flash')]:
            with self.subTest(data=data, model=model), self.assertRaises(ValueError):
                parse_events(data, model, 2)

    def test_custom_key_and_external_tools_are_rejected(self):
        for key, value in [('apiKeySource', 'custom'), ('mcp_servers', ['fixture']), ('plugins', ['fixture'])]:
            data = events()
            data[0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                parse_events(data, 'DeepSeek-Flash', 2)

    def test_credits_profile_cannot_be_redirected_to_byok(self):
        settings = resolve_profile()
        settings.update(model='DeepSeek-Flash', reasoning_effort='low', service_tier=None,
                        provider=dict(name='Qoder Credits', wire_api='qoder_cli', requires_openai_auth=False))
        self.assertEqual(validate_settings(settings)['model'], 'DeepSeek-Flash')
        settings['provider']['env_key'] = 'DEEPSEEK_API_KEY'
        with self.assertRaises(ValueError):
            validate_settings(settings)


class Execution(unittest.TestCase):
    def run_stage(self, timeout=False, invalid_json=False, ungated_tool=False, action=False):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'binary').touch()
            (root/'account/.auth').mkdir(parents=True)
            (root/'account/.auth/user').write_text('synthetic auth fixture, not a credential')
            stage = root/'stage'; stage.mkdir()
            data = events()
            if ungated_tool:
                data[1]['message']['content'] = [dict(type='tool_use', name='Bash', id='fixture-tool', input=dict(command='pwd'))]
            if invalid_json:
                data[-1]['result'] = 'not JSON'

            class Process:
                def __init__(self, *args, **kwargs):
                    self.stdin = io.StringIO()
                    self.stdout = iter(json.dumps(e)+'\n' for e in data)
                    self.returncode = None if timeout else 0
                    if action:
                        (stage/'public-input/main.py').write_text('value = 43\n')
                def wait(self, timeout=None):
                    if self.returncode is None:
                        raise subprocess.TimeoutExpired('synthetic CLI', timeout)
                    return self.returncode
                def poll(self):
                    return self.returncode
                def terminate(self):
                    self.returncode = -15

            protocol = dict(binary=str(root/'binary'), qoder_auth_dir=str(root/'account'),
                            backend=dict(kind='docker', solver_image='sha256:'+'a'*64))
            payload = dict(task='Synthetic fixture', sources={'main.py':'value = 42\n'},
                           schema=dict(type='object', properties=dict(ready=dict(type='boolean')), required=['ready']))
            with patch('temporal_contract_analyzer.tempoevo_docker.image_identity', side_effect=lambda x:x), \
                    patch('temporal_contract_analyzer._session_runtime.docker_transport.stop') as stop, \
                    patch('temporal_contract_analyzer.qoder_backend.subprocess.Popen', Process):
                result = QoderBackend(protocol).execute('action' if action else 'contract', payload,
                    dict(model='DeepSeek-Flash', reasoning_effort='low'), dict(requests=2, seconds=1), stage)
                self.assertTrue(stop.called)
                command = json.loads((stage/'command.json').read_text())
                self.assertEqual(command[command.index('--max-turns')+1], '2')
                self.assertEqual(command[command.index('--max-model-request-retries')+1], '0')
                self.assertEqual(command[command.index('--setting-sources')+1], 'user')
                self.assertNotIn('DEEPSEEK_API_KEY', ' '.join(command))
                self.assertNotIn('synthetic auth fixture', ' '.join(command))
                mounts = [command[i+1] for i, x in enumerate(command) if x == '--mount']
                self.assertEqual(any('dst=/workspace,readonly' in x for x in mounts), not action)
                self.assertFalse(any('docker.sock' in x or 'experience-memory' in x for x in mounts))
                return result

    def test_json_and_credits_are_measured_without_inventing_http_requests(self):
        result = self.run_stage()
        self.assertTrue(result['valid'], result)
        self.assertEqual(result['requests'], 1)
        self.assertEqual(result['output'], dict(ready=True))
        self.assertEqual(result['credits'], 0.125)
        self.assertIsNone(result['http_requests'])
        self.assertIsNone(result['tokens'])

    def test_timeout_stops_owned_container(self):
        result = self.run_stage(timeout=True)
        self.assertFalse(result['valid'])
        self.assertEqual(result['failure_type'], 'timeout')

    def test_invalid_json_is_retained_and_rejected(self):
        result = self.run_stage(invalid_json=True)
        self.assertFalse(result['valid'])
        self.assertEqual(result['failure_type'], 'invalid_output')

    def test_missing_tool_gate_fails_closed(self):
        result = self.run_stage(ungated_tool=True)
        self.assertFalse(result['valid'])
        self.assertIn('mandatory tool gate', result['error'])

    def test_action_delivers_actual_candidate_files_after_cleanup(self):
        result = self.run_stage(action=True)
        self.assertTrue(result['valid'], result)
        self.assertEqual(result['candidate_sources'], {'main.py':'value = 43\n'})


class ToolHook(unittest.TestCase):
    def test_workspace_prefix_preserves_closed_read_policy(self):
        hook = Path(__file__).resolve().parents[1]/'temporal_contract_analyzer/_session_runtime/qoder_hook.py'
        for command, denied in [('cd /workspace && cat main.py', False), ('cd /workspace && touch main.py', True),
                                ('cd /etc && cat passwd', True)]:
            event = dict(hook_event_name='PreToolUse', cwd='/workspace', tool_name='Bash', tool_input=dict(command=command))
            fake_client = SimpleNamespace(forward=lambda value:dict(deny=not read_command(value)))
            with self.subTest(command=command), patch.dict(sys.modules, {'guard_client':fake_client}), \
                    patch.object(sys, 'stdin', io.StringIO(json.dumps(event))), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                if denied:
                    with self.assertRaises(SystemExit) as error:
                        runpy.run_path(str(hook), run_name='__main__')
                    self.assertEqual(error.exception.code, 2)
                else:
                    runpy.run_path(str(hook), run_name='__main__')
