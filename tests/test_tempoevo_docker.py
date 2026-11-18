"""V4 Docker dispatch and evaluation boundaries; no model requests."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from temporal_contract_analyzer.tempoevo_backend import NativeV4Backend
from temporal_contract_analyzer.tempoevo_docker import evaluate,evaluator_inputs,image_identity
from temporal_contract_analyzer.tempoevo_v4 import MODEL
from temporal_contract_analyzer.core import EvidenceError

IMAGE='sha256:'+'a'*64
class DockerV4Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
 def test_image_must_be_immutable(self):
  with self.assertRaises(EvidenceError):image_identity('mutable:tag')
 def test_mounts_cannot_replace_submission_or_runtime(self):
  file=self.root/'check.py';file.write_text('pass')
  for target in ['/','/submission/check.py','/runtime/node','relative','/checks/../submission']:
   with self.subTest(target=target),self.assertRaises(EvidenceError):evaluator_inputs(dict(inputs={str(file):target}))
 def test_evaluation_readonly_offline_and_cleanup(self):
  candidate=self.root/'candidate';candidate.mkdir();script=self.root/'check.py';script.write_text('pass')
  payload=dict(candidate=str(candidate),evaluator=dict(image=IMAGE,inputs={str(script):'/checks/check.py'},command=['python3','/checks/check.py']))
  with patch('temporal_contract_analyzer.tempoevo_docker.image_identity'),patch('temporal_contract_analyzer.tempoevo_docker.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout='{"passed": false}',stderr='')) as run,patch('temporal_contract_analyzer._session_runtime.docker_transport.stop') as stop:
   result=evaluate(payload,self.root);self.assertTrue(result['valid']);self.assertFalse(result['passed']);self.assertEqual(stop.call_count,1)
  command=run.call_args[0][0];self.assertEqual(command[command.index('--network')+1],'none');self.assertIn('--read-only',command);self.assertEqual(command[-1],'/submission');self.assertNotIn('auth.json',' '.join(command))
  temporary=[command[i+1].split(':',1)[0] for i,arg in enumerate(command) if arg=='--tmpfs']
  runtime='/opt/swe-tempoc/results/transfer-v4-window-runtime'
  self.assertNotIn(runtime,temporary,'Mounting the whole runtime hides installed JS dependencies')
  self.assertIn(runtime+'/builds',temporary)
  self.assertIn(runtime+'/native-launch-receipts',temporary)
  self.assertIn('/opt/swe-tempoc/results/multi-family-expansion-20261005/rxjs-executions',temporary)
  self.assertNotIn('/opt/swe-tempoc/results/multi-family-expansion-20261005/rxjs-cache',temporary)
 def test_container_command_on_windows_without_unix_user_ids(self):
  from temporal_contract_analyzer.docker_backend import container_command
  with patch('temporal_contract_analyzer.docker_backend.os',SimpleNamespace()):
   command,_=container_command(IMAGE,'test')
  self.assertEqual(command[command.index('--user')+1],'1000:1000')
 def test_public_runtime_can_opt_out_of_only_gold_specific_tmpfs(self):
  candidate=self.root/'candidate';candidate.mkdir()
  payload=dict(candidate=str(candidate),purpose='auxiliary_public_check',
      evaluator=dict(image=IMAGE,command=['python3','/checks/public.py'],trusted_gold_runtime=False))
  with patch('temporal_contract_analyzer.tempoevo_docker.image_identity'),patch('temporal_contract_analyzer.tempoevo_docker.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout='{"passed": null}',stderr='')) as run,patch('temporal_contract_analyzer._session_runtime.docker_transport.stop'):
   result=evaluate(payload,self.root)
  self.assertTrue(result['valid']);self.assertIsNone(result['passed'])
  command=run.call_args.args[0]
  temporary=[command[i+1].split(':',1)[0] for i,arg in enumerate(command) if arg=='--tmpfs']
  self.assertIn('/tmp',temporary)
  self.assertFalse(any(path.startswith('/opt/swe-tempoc/') for path in temporary))
 def test_v12_gold_purposes_preserve_behavior_failure_and_public_boundary(self):
  candidate=self.root/'candidate';candidate.mkdir()
  for purpose,valid in [('training_acceptance',True),('final_scoring',True),
                        ('auxiliary_public_check',False),('independent_testing',False)]:
   with self.subTest(purpose=purpose),patch('temporal_contract_analyzer.tempoevo_docker.image_identity'),patch('temporal_contract_analyzer.tempoevo_docker.subprocess.run',return_value=SimpleNamespace(returncode=1,stdout='{"verdict":"UNDERREACH"}',stderr='')),patch('temporal_contract_analyzer._session_runtime.docker_transport.stop'):
    result=evaluate(dict(candidate=str(candidate),purpose=purpose,
        evaluator=dict(image=IMAGE,command=['python3','/checks/check.py'])),self.root)
   self.assertIs(result['valid'],valid)
   if valid:self.assertEqual(result['verdict'],'UNDERREACH')
 def test_stage_dispatches_to_existing_docker_runner(self):
  directory=self.root/'stage';directory.mkdir()
  backend=NativeV4Backend(dict(binary='/public/codex',backend=dict(kind='docker',solver_image=IMAGE)))
  result=dict(completed=True,infrastructure_valid=True,output={},usage=dict(requests_started=1,total_usage=dict(total_tokens=2)))
  with patch('temporal_contract_analyzer.docker_backend.DockerBackend.execute',return_value=result) as call,patch('temporal_contract_analyzer.execution_backend.NativeBackend.execute',side_effect=AssertionError('No native execution')):
   out=backend.execute('contract',dict(task='Public task',sources={'main.go':'package main\n'}),MODEL,dict(requests=12,seconds=600),directory)
  self.assertTrue(out['valid']);protocol=call.call_args[0][0];self.assertEqual(protocol['backend']['solver_image'],IMAGE);self.assertEqual(protocol['node'],'/runtime/node16/bin/node')
