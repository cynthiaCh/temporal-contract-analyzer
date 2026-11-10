"""Synthetic protocol tests; real Docker checks are explicit offline actions."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_experience_evolution as fixtures
from temporal_contract_analyzer.docker_backend import (
    DockerBackend, validate_config, container_command, captured, project_score)
from temporal_contract_analyzer.experience_evolution import Evolution, load
from temporal_contract_analyzer.core import EvidenceError


CONFIG=dict(kind='docker',solver_image='sha256:'+'a'*64,grader_image='sha256:'+'b'*64,
            grader_node='/opt/swe-tempoc/.swe-tempoc/toolchains/node-v16.20.2/bin/node')


class DockerTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.EvolutionTests('test_complete_develop_review_activate_and_next_task_retrieval')
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.root=self.fixture.root

    def prepared(self):
        loop=Evolution(self.root/'docker-loop')
        loop.prepare('development',self.fixture.visible(),self.fixture.store,
            '/synthetic/codex','/runtime/node16/bin/node',dict(synthetic=True),
            source_relationship='Explicitly synthetic development fixture.',backend=CONFIG)
        return loop

    def test_mutable_images_unknown_fields_and_nonpublic_runtime_are_rejected(self):
        for bad in (dict(CONFIG,solver_image='solver:latest'),dict(CONFIG,privileged=True),
                    dict(CONFIG,grader_node='/tmp/arbitrary')):
            with self.subTest(config=bad),self.assertRaises(EvidenceError):validate_config(bad)

    def test_docker_selection_preserves_budgets_prompts_and_expert_pause(self):
        loop=self.prepared();protocol=load(loop.root/'protocol.json')
        self.assertEqual(protocol['total_request_cap'],108)
        self.assertEqual(protocol['backend'],CONFIG)
        self.assertEqual(len(protocol['slots']),5)
        prompt=loop.common(protocol)
        self.assertIn('/runtime/node16/bin/node',prompt)
        self.assertNotIn('sha256:',prompt)
        backend=fixtures.SyntheticBackend()
        with patch('temporal_contract_analyzer.docker_backend.DockerBackend',return_value=backend) as selected:
            result=loop.run(execute=True)
        self.assertEqual(selected.call_count,1)
        self.assertEqual(result['status'],'awaiting_expert')
        self.assertEqual(len(backend.calls),5)

    def test_backend_freeze_and_live_execution_gate(self):
        loop=self.prepared()
        with self.assertRaisesRegex(EvidenceError,'--execute'):loop.run()
        path=loop.root/'protocol.json';value=load(path);value['backend']['solver_image']='sha256:'+'c'*64
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(EvidenceError,'Frozen artifact'):loop.verify()

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
        protocol['binary']=__import__('sys').executable
        from temporal_contract_analyzer.core import sha
        protocol['executable_sha256']={protocol['binary']:sha(Path(protocol['binary']).read_bytes())}
        with patch('temporal_contract_analyzer.docker_backend.subprocess.check_output',
                   side_effect=[CONFIG['solver_image']+'\n',CONFIG['grader_image']+'\n']), \
             patch('temporal_contract_analyzer.docker_backend.captured',side_effect=[
                 dict(python='3.9.20',node='v16.20.2',codex='SYNTHETIC'),
                 dict(python='3.0.0',node='v16.20.2')]):
            with self.assertRaisesRegex(EvidenceError,'Grader Python'):DockerBackend().environment(protocol,self.root/'check')

    def test_unvalidated_frontend_dependencies_block_before_solver_dispatch(self):
        protocol=load(self.prepared().root/'protocol.json')
        import sys
        from temporal_contract_analyzer.core import sha
        protocol['binary']=sys.executable
        protocol['executable_sha256']={sys.executable:sha(Path(sys.executable).read_bytes())}
        protocol['case']['adapter']='legacy-js'
        backend=DockerBackend()
        with patch('temporal_contract_analyzer.docker_backend.scoring_inputs',return_value=protocol['scoring_inputs']), \
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
             patch('temporal_contract_analyzer.evolution_backend.subprocess.Popen',return_value=Process()), \
             patch('temporal_contract_analyzer.evolution_backend.stop_tree'):
            result=instance.execute(protocol,'repair','SYNTHETIC',None,directory)
        self.assertFalse(result['completed']);self.assertIsNone(result['usage'])
        stopped.assert_called_once()
        self.assertEqual((directory/'bridge-partial.stderr').read_text(),'SYNTHETIC_SERVICE_ERROR')
        self.assertEqual((directory/'bridge-partial.stdout').read_text(),'SYNTHETIC_PARTIAL')


if __name__=='__main__':unittest.main()
