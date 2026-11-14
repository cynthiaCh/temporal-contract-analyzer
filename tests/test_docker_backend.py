"""Synthetic protocol tests; real Docker checks are explicit offline actions."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import evolution_fixtures as fixtures
import os
from types import SimpleNamespace
from temporal_contract_analyzer.docker_backend import (
    DockerBackend, validate_config, container_command, captured, project_score)
from temporal_contract_analyzer.case_catalog import case_input
from temporal_contract_analyzer.case_evaluation import scoring_inputs
from temporal_contract_analyzer.candidate_files import capture,inventory
load=lambda p:json.loads(Path(p).read_text())
from temporal_contract_analyzer.core import EvidenceError


CONFIG=dict(kind='docker',solver_image='sha256:'+'a'*64,grader_image='sha256:'+'b'*64,
            grader_node='/opt/swe-tempoc/.swe-tempoc/toolchains/node-v16.20.2/bin/node')


class DockerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        fixtures.synthetic_bench(self.root/'bench')
        env=patch.dict(os.environ,{'TCA_BENCH_ROOT':str(self.root/'bench')});env.start();self.addCleanup(env.stop)

    def prepared(self):
        data=case_input('development');case=data['case_record'];files,_=capture(Path(data['candidate']))
        protocol=dict(execution_policy='tempoevo-trajectory-v9',backend=CONFIG,case=case,binary='/synthetic/codex',
            node='/runtime/node16/bin/node',scoring_inputs=scoring_inputs(case),input_path=data['candidate'],
            candidate_files=inventory(files),visible=dict(task=data['task']),candidate_sha256='a'*64,
            calibration=dict(synthetic=True))
        root=self.root/'backend-input';root.mkdir(exist_ok=True);(root/'protocol.json').write_text(json.dumps(protocol))
        return SimpleNamespace(root=root)

    def test_mutable_images_unknown_fields_and_nonpublic_runtime_are_rejected(self):
        for bad in (dict(CONFIG,solver_image='solver:latest'),dict(CONFIG,privileged=True),
                    dict(CONFIG,grader_node='/tmp/arbitrary')):
            with self.subTest(config=bad),self.assertRaises(EvidenceError):validate_config(bad)

    def test_actor_metadata_excludes_case_identity_scores_and_calibration(self):
        protocol=load(self.prepared().root/'protocol.json')
        value=DockerBackend().session_options(protocol)['transport']
        self.assertEqual(set(value),{'solver_image','node','name'})
        self.assertTrue(value['name'].startswith('tca-session-'))

    def test_grader_has_offline_readonly_namespace_and_no_model_credentials(self):
        command,image=container_command(CONFIG['grader_image'],'synthetic-check',[(self.root,'/submission')])
        self.assertIn('-i',command)  # JSON payload/prompt must reach container stdin.
        self.assertEqual(command[command.index('--network')+1],'none')
        self.assertIn('--read-only',command)
        self.assertEqual(command[command.index('--cap-drop')+1],'ALL')
        self.assertIn('readonly',command[command.index('--mount')+1])
        self.assertNotIn('docker.sock',' '.join(command))
        self.assertNotIn('auth.json',' '.join(command))

    def test_docker_absence_blocks_without_dispatch(self):
        protocol=load(self.prepared().root/'protocol.json')
        with patch('temporal_contract_analyzer.docker_backend.shutil.which',return_value=None):
            with self.assertRaisesRegex(EvidenceError,'Docker CLI'):DockerBackend().environment(protocol,self.root/'check')

    def test_runtime_mismatch_cannot_be_credited_as_a_behavior_score(self):
        protocol=load(self.prepared().root/'protocol.json')
        public=self.root/'public-cli';public.mkdir()
        (public/'codex').write_text('SYNTHETIC_PUBLIC_CLI')
        (public/'codex-code-mode-host').write_text('SYNTHETIC_COMPANION')
        protocol['binary']=str(public/'codex')
        # Legacy version hashes are ignored; runtime mismatches still fail.
        protocol['executable_sha256']={protocol['binary']:'old-hash'}
        protocol['backend_sources']={'/old/runner.py':'old-hash'}
        with patch('temporal_contract_analyzer.docker_backend.shutil.which',return_value='/synthetic/docker'), \
             patch('temporal_contract_analyzer.docker_backend.subprocess.check_output',
                   side_effect=[CONFIG['solver_image']+'\n',CONFIG['grader_image']+'\n']), \
             patch('temporal_contract_analyzer.docker_backend.captured',side_effect=[
                 dict(python='3.9.20',node='v16.20.2',codex='SYNTHETIC',code_host=dict(javascript_execution=True)),
                 dict(python='3.0.0',node='v16.20.2')]):
            with self.assertRaisesRegex(EvidenceError,'Grader Python'):DockerBackend().environment(protocol,self.root/'check')

    def test_missing_companion_blocks_before_a_model_or_solver_launch(self):
        protocol=load(self.prepared().root/'protocol.json')
        public=self.root/'incomplete-cli';public.mkdir();(public/'codex').write_text('SYNTHETIC')
        protocol['binary']=str(public/'codex')
        with patch('temporal_contract_analyzer.docker_backend.shutil.which',return_value='/synthetic/docker'), \
             patch('temporal_contract_analyzer.docker_backend.subprocess.check_output',side_effect=[CONFIG['solver_image']+'\n',CONFIG['grader_image']+'\n']), \
             patch('temporal_contract_analyzer.docker_backend.captured') as launch:
            with self.assertRaisesRegex(EvidenceError,'companion is missing'):
                DockerBackend().environment(protocol,self.root/'blocked')
        launch.assert_not_called()

    def test_actor_projects_companion_to_the_cli_expected_sibling_path(self):
        from temporal_contract_analyzer._session_runtime.docker_transport import Launcher
        public=self.root/'cli';public.mkdir()
        for name in ('codex','codex-code-mode-host','rg'):(public/name).write_text('SYNTHETIC')
        runtime=self.root/'runtime';profile=runtime/'.runtime'/'slot';profile.mkdir(parents=True)
        (profile/'hooks.json').write_text('{"hooks":{}}')
        folder=self.root/'session';(folder/'workspace').mkdir(parents=True)
        schema=self.root/'schema.json';schema.write_text('{}')
        native=['bwrap','--ro-bind',str(public),'/opt','--bind',str(folder/'workspace'),'/workspace',
                '--ro-bind',str(schema),'/format.json','--','/opt/codex','exec']
        command=Launcher(dict(name='tca-session-'+'c'*32,solver_image=CONFIG['solver_image'],
                             node='/runtime/node16/bin/node'),self.root).command(native,folder,runtime,'slot',self.root)
        bindings=[command[i+1] for i,value in enumerate(command) if value=='--mount']
        self.assertIn('type=bind,src='+str(public/'codex-code-mode-host')+',dst=/opt/codex-code-mode-host,readonly',bindings)
        self.assertFalse(any('dst=/opt,' in b for b in bindings))

    def test_unvalidated_frontend_dependencies_block_before_solver_dispatch(self):
        protocol=load(self.prepared().root/'protocol.json')
        import sys
        protocol['binary']=sys.executable
        protocol['case']['adapter']='legacy-js'
        backend=DockerBackend()
        with patch('temporal_contract_analyzer.docker_backend.shutil.which',return_value='/synthetic/docker'), \
             patch('temporal_contract_analyzer.docker_backend.scoring_inputs',return_value=protocol['scoring_inputs']), \
             patch('temporal_contract_analyzer.docker_backend.subprocess.check_output',side_effect=[CONFIG['solver_image']+'\n',CONFIG['grader_image']+'\n']), \
             patch.object(backend,'_case',return_value=(dict(framework=dict(runtime='react18')),'/fixture',[])), \
             patch('temporal_contract_analyzer.docker_backend.captured') as launched:
            with self.assertRaisesRegex(EvidenceError,'frontend/upstream'):backend.environment(protocol,self.root/'frontend')
        launched.assert_not_called()

    def test_failed_check_retains_stderr_and_always_stops_container(self):
        class Process:
            returncode=1
            def communicate(self,*args,**kwargs):return 'SYNTHETIC_PARTIAL','SYNTHETIC_ORIGINAL_ERROR'
        with patch('temporal_contract_analyzer.docker_backend.subprocess.Popen',return_value=Process()), \
             patch('temporal_contract_analyzer.docker_backend.stop') as stopped:
            with self.assertRaises(EvidenceError):captured(['docker','SYNTHETIC'],self.root/'failed','owned-name')
        stopped.assert_called_once()
        self.assertEqual((self.root/'failed/stderr').read_text(),'SYNTHETIC_ORIGINAL_ERROR')
        self.assertEqual((self.root/'failed/stdout').read_text(),'SYNTHETIC_PARTIAL')

    def test_projection_preserves_raw_false_expectations_losses_and_unknowns(self):
        from temporal_contract_analyzer.case_evaluation import relation_states,delta
        raw=dict(verdict='UNDERREACH',missing_required_effects=['lost'],schedules=dict(
            false_expected=dict(actual=False,expected=False,passed=True),
            lost=dict(actual=['new'],expected=['old'],passed=False),
            unknown=dict(actual=None,expected=True)))
        before=deepcopy(raw);derived=project_score(raw,'a'*64)
        self.assertEqual(raw,before)
        self.assertEqual(derived['verdict'],raw['verdict'])
        self.assertEqual(relation_states(derived),dict(false_expected=True,lost=False,unknown=None))
        new=deepcopy(derived);new['behavior_states'].update(false_expected=False,lost=True)
        changes=delta(derived,new)
        self.assertEqual(changes['gained'],['lost'])
        self.assertEqual(changes['lost'],['false_expected'])
        self.assertEqual(changes['unknown'],['unknown'])

    def test_missing_or_malformed_schedule_result_is_not_success(self):
        from temporal_contract_analyzer.case_evaluation import relation_states
        self.assertEqual(relation_states(project_score(dict(schedules=dict(a={})), 'a'*64)),dict(a=None))
        with self.assertRaises(EvidenceError):project_score(dict(schedules=dict(a=dict(passed='PASS'))),'a'*64)

    def test_outer_bridge_timeout_preserves_partial_output_and_cleans_daemon_actor(self):
        import subprocess
        protocol=load(self.prepared().root/'protocol.json')
        directory=self.root/'timeout';directory.mkdir()
        class Process:
            def __init__(self):self.calls=0
            def communicate(self,*args,**kwargs):
                self.calls+=1
                if self.calls==1:raise subprocess.TimeoutExpired('SYNTHETIC',600)
                return 'SYNTHETIC_PARTIAL','SYNTHETIC_SERVICE_ERROR'
        instance=DockerBackend()
        with patch.object(instance,'preflight'),patch.object(instance,'stop_external') as stopped, \
             patch('temporal_contract_analyzer.execution_backend.subprocess.Popen',return_value=Process()), \
             patch('temporal_contract_analyzer.execution_backend.stop_tree'):
            result=instance.execute(protocol,'repair','SYNTHETIC',None,directory)
        self.assertFalse(result['completed']);self.assertIsNone(result['usage'])
        stopped.assert_called_once()
        self.assertEqual((directory/'bridge-partial.stderr').read_text(),'SYNTHETIC_SERVICE_ERROR')
        self.assertEqual((directory/'bridge-partial.stdout').read_text(),'SYNTHETIC_PARTIAL')


if __name__=='__main__':unittest.main()
