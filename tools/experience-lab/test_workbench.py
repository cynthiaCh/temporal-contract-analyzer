"""Offline controller checks. Fixtures are synthetic; no models or scorers run."""
import json
import io
import os
import subprocess
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import runner
import records

import serve
from serve import Server


class Commands(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'bench').mkdir()
        (self.root/'store').mkdir()
        (self.root/'profiles.json').write_text(json.dumps(dict(profiles={'test':dict(model='fixture', reasoning_effort='medium')})))
        self.config = dict(mode='testing', workers=2, start=1, count=1, condition='structured',
                           benchmark=str(self.root/'bench'), store=str(self.root/'store'), model_config=str(self.root/'profiles.json'),
                           model_profile='test', solver_image='sha256:'+'a'*64, grader_image='sha256:'+'b'*64,
                           public_checks=str(self.root/'missing.json'))

    def test_testing_preparation_has_no_training_inputs(self):
        command, env, model = runner.prepare_command(self.config, self.root/'new')
        self.assertEqual(command[command.index('--mode')+1], 'testing')
        self.assertEqual(command[command.index('--swe-tempoc-root')+1], str((self.root/'bench').resolve()))
        self.assertNotIn('--training-recipe', command)
        self.assertNotIn('--public-checks-docs', command)
        self.assertNotIn('--execute', command)
        self.assertEqual(env['TCA_BENCH_ROOT'], str((self.root/'bench').resolve()))

    def test_case_details_load_on_the_launcher_python(self):
        trajectory = self.root/'trajectory'
        trajectory.mkdir()
        protocol = dict(mode='testing', max_attempts=1, model={}, condition='structured', task='Public task',
                        original_inventory={}, memory_snapshot={'entries':[]}, limits={},
                        learning_policy='frozen', memory_snapshot_sha256='fixture')
        (trajectory/'protocol.json').write_text(json.dumps(protocol))
        (trajectory/'state.json').write_text(json.dumps(dict(status='prepared', attempts=[], stages=[])))
        with patch.object(records, 'job_list', return_value=[dict(case_id='fixture', trajectory=trajectory)]):
            detail = records.case_detail(None, 'run-fixture', 'fixture')
        self.assertEqual(detail['source'], str(trajectory))
        self.assertEqual(detail['case']['status'], 'prepared')

    def test_default_benchmark_uses_existing_checkout_and_respects_override(self):
        repository = self.root/'analyzer'
        fallback = self.root/'temporal-contract-bench-git'
        index = fallback/'experiments/temporal-diagnostics-v1/corpus.json'
        index.parent.mkdir(parents=True)
        index.write_text('{}')
        with patch.object(runner, 'REPO', repository), patch.dict(os.environ, {}, clear=True):
            self.assertEqual(runner.default_benchmark(), str(fallback))
            with patch.dict(os.environ, {'TCA_BENCH_ROOT': str(self.root/'explicit')}):
                self.assertEqual(runner.default_benchmark(), str(self.root/'explicit'))
            preferred = self.root/'temporal-contract-bench'
            (preferred/'experiments/temporal-diagnostics-v1').mkdir(parents=True)
            (preferred/'experiments/temporal-diagnostics-v1/corpus.json').write_text('{}')
            self.assertEqual(runner.default_benchmark(), str(preferred))

    def test_host_image_configuration_overrides_historical_defaults(self):
        config = self.root/'.tempoevo/docker-images.json'
        config.parent.mkdir()
        images = {key: self.config[key] for key in ('solver_image', 'grader_image')}
        with patch.object(runner, 'REPO', self.root):
            self.assertEqual(runner.default_images()['solver_image'], runner.DEFAULT_SOLVER)
            config.write_text(json.dumps(images))
            self.assertEqual(runner.default_images(), images)

    def test_macos_preparation_uses_provisioned_linux_binary(self):
        binary = self.root/'.tempoevo/bin/linux-x64/codex'
        binary.parent.mkdir(parents=True)
        binary.touch()
        with patch.object(runner, 'REPO', self.root), patch.object(runner.sys, 'platform', 'darwin'):
            command, _, _ = runner.prepare_command(self.config, self.root/'new')
        self.assertEqual(command[command.index('--binary')+1], str(binary))

    def test_qoder_profile_selects_linux_cli_and_turn_measurement(self):
        profiles = runner.read(self.root/'profiles.json')
        profiles['profiles']['test']['provider'] = dict(name='Qoder Credits', wire_api='qoder_cli', requires_openai_auth=False)
        (self.root/'profiles.json').write_text(json.dumps(profiles))
        binary = self.root/'.tempoevo/qoder/linux/qoder'
        login = self.root/'.tempoevo/qoder/account/.auth/user'
        for file in (binary, login):
            file.parent.mkdir(parents=True, exist_ok=True)
            file.touch()
        with patch.object(runner, 'REPO', self.root):
            command, _, model = runner.prepare_command(self.config, self.root/'new')
        self.assertEqual(command[command.index('--binary')+1], str(binary.resolve()))
        self.assertEqual(model['request_unit'], 'model turns')

    def test_training_requires_actual_check_descriptions(self):
        self.config['mode'] = 'learning'
        with self.assertRaisesRegex(ValueError, 'Public check descriptions'):
            runner.prepare_command(self.config, self.root/'new')

    def test_worker_and_dataset_limits(self):
        for field, value in [('workers', 0), ('workers', 9), ('count', 31), ('start', 0), ('mode', 'unknown')]:
            with self.subTest(field=field, value=value):
                config = dict(self.config, **{field:value})
                with self.assertRaises(ValueError):
                    runner.prepare_command(config, self.root/'new')

    def test_mutable_image_tags_rejected(self):
        self.config['solver_image'] = 'latest'
        with self.assertRaisesRegex(ValueError, 'immutable'):
            runner.prepare_command(self.config, self.root/'new')

    def test_missing_host_never_creates_a_run(self):
        c = runner.Controller(self.root/'runs')
        with patch.object(runner, 'environment', return_value={'docker':{'ok':False, 'detail':'fixture unavailable'}, 'codex':{'ok':True}}):
            with self.assertRaisesRegex(ValueError, 'not ready'):
                c.prepare(self.config)
        self.assertFalse(list(c.root.iterdir()))

    def test_finder_path_discovers_codex_and_passes_it_to_preparation(self):
        binary = self.root/'.vscode/extensions/openai.chatgpt-fixture/bin/macos-x86_64/codex'
        binary.parent.mkdir(parents=True)
        binary.write_text('#!/bin/sh\nexit 0\n')
        binary.chmod(0o755)
        with patch.dict(os.environ, {'PATH': '/usr/bin:/bin'}), \
             patch.object(runner.sys, 'platform', 'darwin'), \
             patch.object(runner.platform, 'machine', return_value='x86_64'), \
             patch.object(runner.Path, 'home', return_value=self.root):
            self.assertEqual(runner.configure_codex_path(), str(binary))
            _, env, _ = runner.prepare_command(self.config, self.root/'new')
            self.assertEqual(env['PATH'].split(os.pathsep)[0], str(binary.parent))
            self.assertEqual(runner.shutil.which('codex', path=env['PATH']), str(binary))

    def test_existing_codex_path_is_preserved(self):
        before = os.environ.get('PATH')
        with patch.object(runner.shutil, 'which', return_value='/configured/codex'):
            self.assertEqual(runner.configure_codex_path(), '/configured/codex')
        self.assertEqual(os.environ.get('PATH'), before)

    def test_codex_failure_does_not_report_docker_as_broken(self):
        c = runner.Controller(self.root/'runs')
        with patch.object(runner, 'environment', return_value={
                'docker': {'ok': True, 'detail': '29.9.3'},
                'codex': {'ok': False, 'detail': 'Codex executable was not found'}}):
            with self.assertRaisesRegex(ValueError, 'not ready: Codex executable was not found'):
                c.prepare(self.config)
        self.assertFalse(list(c.root.iterdir()))

    def test_cli_arguments_are_not_shell_commands(self):
        command = runner.run_command(self.root/'name with spaces; echo fixture')
        self.assertEqual(command[-1], '--execute')
        self.assertEqual(command[command.index('--root')+1], str(self.root/'name with spaces; echo fixture'))
        self.assertEqual(command[1:5], ['-B', '-m', 'temporal_contract_analyzer', 'tempoevo'])

    def test_prepare_then_explicit_start_uses_public_cli(self):
        c = runner.Controller(self.root/'runs')
        ready = {'docker': {'ok': True}, 'codex': {'ok': True}}
        with patch.object(runner, 'environment', return_value=ready), \
             patch.object(runner, 'command_output', return_value={'ok': True}), \
             patch.object(runner.threading.Thread, 'start'):
            ident = c.prepare(self.config)
        batch = c.directory(ident)
        trajectory = batch/'batch/fixture/trajectory'
        trajectory.mkdir(parents=True)
        rows = [dict(root=str(trajectory.parent), case_id='fixture', status='prepared')]
        (batch/'batch/progress.json').write_text(json.dumps(rows))
        (trajectory/'state.json').write_text(json.dumps(dict(status='prepared', stages=[], attempts=[])))
        protocol = dict(mode='testing', max_attempts=1, learning_policy='frozen')
        with patch.object(runner.subprocess, 'run') as process, \
             patch.object(runner.Trajectory, 'verify', return_value=protocol):
            process.return_value.returncode = 0
            command, env, _ = runner.prepare_command(self.config, batch/'batch')
            c._prepare(batch, command, env)
            self.assertEqual(process.call_count, 1)
            self.assertNotIn('--execute', process.call_args.args[0])
        self.assertEqual(runner.read(batch/'lab.json')['status'], 'prepared')
        self.assertIsNone(c.active)
        with patch.object(runner.Trajectory, 'verify', return_value=protocol), \
             patch.object(runner.threading.Thread, 'start'):
            c.start(ident)
        with patch.object(runner.subprocess, 'run') as process:
            process.return_value.returncode = 0
            c._execute(batch, rows)
            self.assertEqual(process.call_count, 1)
            self.assertEqual(process.call_args.args[0], runner.run_command(trajectory))
        self.assertEqual(runner.read(batch/'lab.json')['status'], 'finished')
        self.assertIsNone(c.active)

    def test_profile_metadata_does_not_expose_credentials(self):
        (self.root/'profiles.json').write_text(json.dumps(dict(profiles={'test':dict(model='fixture', api_key='fixture-secret')})))
        self.assertNotIn('api_key', runner.public_profiles(self.root/'profiles.json')['test'])

    def test_testing_start_refuses_more_than_one_action(self):
        c = runner.Controller(self.root/'runs')
        root = c.root/'run-fixture';root.mkdir()
        job = root/'case/trajectory';job.mkdir(parents=True)
        (root/'batch').mkdir()
        (root/'lab.json').write_text(json.dumps(dict(id='run-fixture', status='prepared', config=self.config)))
        (root/'batch/progress.json').write_text(json.dumps([dict(root=str(job.parent), case_id='fixture')]))
        (job/'state.json').write_text(json.dumps(dict(stages=[],attempts=[])))
        with patch.object(runner.Trajectory, 'verify', return_value=dict(mode='testing', max_attempts=3, learning_policy='frozen')):
            with self.assertRaisesRegex(ValueError, 'one Action'):
                c.start('run-fixture')
        self.assertIsNone(c.active)

    def test_started_trajectory_cannot_be_replayed(self):
        c = runner.Controller(self.root/'runs')
        root = c.root/'run-fixture';root.mkdir()
        job = root/'case/trajectory';job.mkdir(parents=True)
        (root/'batch').mkdir()
        (root/'lab.json').write_text(json.dumps(dict(id='run-fixture', status='prepared', config=self.config)))
        (root/'batch/progress.json').write_text(json.dumps([dict(root=str(job.parent), case_id='fixture')]))
        (job/'state.json').write_text(json.dumps(dict(stages=[{'status':'started'}],attempts=[])))
        with patch.object(runner.Trajectory, 'verify', return_value=dict(mode='testing', max_attempts=1, learning_policy='frozen')):
            with self.assertRaisesRegex(ValueError, 'fresh'):
                c.start('run-fixture')


class HTTP(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.server = Server(0, Path(self.temp.name)/'runs')
        thread = threading.Thread(target=self.server.serve_forever, daemon=True);thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def test_cross_origin_start_is_forbidden(self):
        request = Request(self.server.url+'/api/start', data=b'{"id":"run-fixture"}', headers={
            'Content-Type':'application/json', 'Origin':'https://example.invalid', 'X-TempoEvo-Token':self.server.token})
        with self.assertRaises(HTTPError) as error:
            urlopen(request)
        self.assertEqual(error.exception.code, 403)
        self.assertIsNone(self.server.controller.active)

    def test_shutdown_requires_local_token(self):
        request = Request(self.server.url+'/api/shutdown', data=b'{}', headers={'Content-Type':'application/json'})
        with self.assertRaises(HTTPError) as error:
            urlopen(request)
        self.assertEqual(error.exception.code, 403)
        self.assertFalse(self.server.closing)

    def test_shutdown_preserves_active_run(self):
        self.server.controller.active = 'run-fixture'
        request = Request(self.server.url+'/api/shutdown', data=b'{}', headers={
            'Content-Type':'application/json', 'Origin':self.server.url, 'X-TempoEvo-Token':self.server.token})
        with self.assertRaises(HTTPError) as error:
            urlopen(request)
        self.assertEqual(error.exception.code, 400)
        self.assertIn('A run is active', json.loads(error.exception.read())['error'])
        self.assertFalse(self.server.closing)
        self.assertEqual(self.server.controller.active, 'run-fixture')

    def test_relaunch_reuses_existing_workspace_and_preserves_active_run(self):
        self.server.controller.active = 'run-fixture'
        token = self.server.token
        output = io.StringIO()
        with patch.object(serve.sys, 'argv', ['serve.py', '--port', str(self.server.server_port),
                         '--runs', str(self.server.controller.root), '--open']), \
                patch.object(serve.webbrowser, 'open') as open_browser, redirect_stdout(output):
            serve.main()
        self.assertIn('already running', output.getvalue())
        open_browser.assert_called_once_with(self.server.url)
        self.assertEqual(self.server.token, token)
        self.assertEqual(self.server.controller.active, 'run-fixture')
        self.assertEqual(urlopen(self.server.url+'/api/identity').status, 200)

    def test_other_workspace_conflict_is_clear_and_does_not_open_browser(self):
        output = io.StringIO()
        with patch.object(serve.sys, 'argv', ['serve.py', '--port', str(self.server.server_port),
                         '--runs', str(Path(self.temp.name)/'other-runs'), '--open']), \
                patch.object(serve.webbrowser, 'open') as open_browser, redirect_stderr(output):
            with self.assertRaises(SystemExit) as error:
                serve.main()
        self.assertEqual(error.exception.code, 1)
        self.assertIn('occupied by another service or workspace', output.getvalue())
        self.assertNotIn('Traceback', output.getvalue())
        open_browser.assert_not_called()

    def test_unrelated_service_is_not_reused(self):
        with patch.object(serve, 'build_opener') as opener:
            response = opener.return_value.open.return_value.__enter__.return_value
            response.geturl.return_value = self.server.url+'/api/identity'
            response.read.return_value = b'{"application":"other-service"}'
            self.assertFalse(serve.existing_workspace(self.server.url, self.server.controller.root))

    def test_redirected_identity_is_not_reused(self):
        with patch.object(serve, 'build_opener') as opener:
            response = opener.return_value.open.return_value.__enter__.return_value
            response.geturl.return_value = 'https://example.invalid/api/identity'
            self.assertFalse(serve.existing_workspace(self.server.url, self.server.controller.root))

    def test_archives_are_readonly_and_path_traversal_is_rejected(self):
        for ident in ['archive-training', '../elsewhere', 'run-fixture/../../elsewhere']:
            request = Request(self.server.url+'/api/start', data=json.dumps(dict(id=ident)).encode(), headers={
                'Content-Type':'application/json', 'Origin':self.server.url, 'X-TempoEvo-Token':self.server.token})
            with self.assertRaises(HTTPError) as error:
                urlopen(request)
            self.assertEqual(error.exception.code, 400)
        self.assertIsNone(self.server.controller.active)

    def test_unknown_route_does_not_serve_local_files(self):
        with self.assertRaises(HTTPError) as error:
            urlopen(self.server.url+'/../runner.py')
        self.assertEqual(error.exception.code, 404)

    def test_unrecognized_host_is_rejected(self):
        request = Request(self.server.url+'/api/bootstrap', headers={'Host': 'example.invalid'})
        with self.assertRaises(HTTPError) as error:
            urlopen(request)
        self.assertEqual(error.exception.code, 403)


class CloseLauncher(unittest.TestCase):
    def test_stop_closes_only_matching_server_and_preserves_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)/'runs'
            script = str(Path(serve.__file__).resolve())
            process = subprocess.Popen([serve.sys.executable, '-B', script, '--port', '0', '--runs', str(root)],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                address = json.loads(process.stdout.readline())['url']
                port = address.rsplit(':', 1)[1]
                record = root/'retained-record.txt'
                record.write_text('fixture')
                mismatch = subprocess.run([serve.sys.executable, '-B', script, '--port', port,
                                           '--runs', str(root/'other'), '--stop'], capture_output=True, text=True, timeout=10)
                self.assertEqual(mismatch.returncode, 1)
                self.assertIn('No process was stopped', mismatch.stderr)
                self.assertIsNone(process.poll())
                result = subprocess.run([serve.sys.executable, '-B', script, '--port', port,
                                         '--runs', str(root), '--stop'], capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('Workspace closed', result.stdout)
                self.assertEqual(process.wait(timeout=5), 0)
                self.assertEqual(record.read_text(), 'fixture')
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
                process.stdout.close()
                process.stderr.close()


if __name__ == '__main__':
    unittest.main()
