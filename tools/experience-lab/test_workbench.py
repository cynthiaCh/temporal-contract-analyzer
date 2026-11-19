"""Offline controller checks. Fixtures are synthetic; no models or scorers run."""
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import runner
import records
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


if __name__ == '__main__':
    unittest.main()
