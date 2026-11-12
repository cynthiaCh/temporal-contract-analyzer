"""Exercise the packaged analysis runner with a fake CLI, never a model."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from temporal_contract_analyzer import taxonomy
from temporal_contract_analyzer.evolution_backend import DEPENDENCIES, SOURCE, ROLES


DRIVER = '''import json,sys,tempfile
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import runner
payload=json.loads(sys.argv[2]);base=Path(payload['base'])
runner.tempfile.tempdir='/tmp'
def fake_command(archive,runtime,guard):
 return [sys.executable,'-B',str(base/'fake_cli.py'),str(guard.directory/'hook.sock'),
         str(archive.workspace),json.dumps(payload['analysis']),str(payload['mutate']),
         payload.get('phase','analysis'),str(payload.get('requests',1)),payload.get('tool','')]
phase=payload.get('phase','analysis')
slot=dict(slot='ANALYSIS',phase=phase)
if payload.get('logical_role'):slot['logical_role']=payload['logical_role']
receipt=runner.session(slot,'Synthetic task and numbered source',
 case={},candidate=base/'candidate',task=base/'task.md',config=dict(seconds_per_session=20,
 requests_per_session=payload.get('cap',12),reflection_readonly=payload.get('readonly',False)),
 run_dir=base/'run',command_factory=fake_command)
print(json.dumps(receipt))
'''

FAKE_CLI = '''import json,socket,sys
from pathlib import Path
def hook(event):
 with socket.socket(socket.AF_UNIX) as connection:
  connection.connect(sys.argv[1]);connection.sendall(json.dumps(event).encode()+b'\\n')
  assert not json.loads(connection.recv(4096))['deny']
model='gpt-6.1-sol'
for _ in range(int(sys.argv[6])):
 hook(dict(hook_event_name='PreModelRequest',model=model))
 hook(dict(hook_event_name='PostModelRequest',model=model,status='completed'))
if sys.argv[7]:hook(dict(hook_event_name='PreToolUse',tool_name='exec_command',tool_input={'command':sys.argv[7],'workdir':'/workspace'}))
if sys.argv[4]=='True':(Path(sys.argv[2])/'main.py').write_text('changed = True\\n')
print(json.dumps(dict(type='item.completed',item=dict(type='agent_message',text=sys.argv[3]))))
print(json.dumps(dict(type='turn.completed')))
'''

COMMAND_DRIVER = '''import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import runner
from docker_transport import Launcher
base=Path(sys.argv[2]);phase=sys.argv[3];folder=base/phase
archive=folder/'archive';archive.mkdir(parents=True)
runtime=base/('runtime-'+phase);runtime.mkdir()
public=base/'public';public.mkdir(exist_ok=True)
for name in ('codex','codex-code-mode-host'):
 (public/name).write_text('SYNTHETIC_PUBLIC_RUNTIME_PLACEHOLDER')
runner.backend.BINARY=base/'public/codex'
runner.backend.global_snapshot=lambda: {}
native=runner.command(phase,folder,phase,dict(node='/runtime/node16/bin/node',reflection_readonly=phase=='reflect'),
 runtime=runtime,socket_dir=runtime/'hooks',copy_auth=False)
launcher=Launcher(dict(solver_image='sha256:'+'a'*64,name='tca-session-'+'b'*32,
 node='/runtime/node16/bin/node'),archive)
docker=launcher.command(native,folder,runtime,phase,runtime/'hooks')
print(json.dumps(dict(native=native,docker=docker)))
'''


class AnalysisRunnerTests(unittest.TestCase):
    def run_fixture(self,mutate=False,phase='analysis',cap=12,readonly=False,requests=1,tool='',logical_role=None,output=None,schema=None):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        root=Path(temporary.name);backend=root/'backend';backend.mkdir()
        for name in DEPENDENCIES:shutil.copyfile(SOURCE/name,backend/name)
        (backend/'analysis.schema.json').write_text(json.dumps(schema or taxonomy.analysis_schema()))
        (backend/'reflection.schema.json').write_text(json.dumps(schema or dict(type='object')))
        (root/'candidate').mkdir();(root/'candidate/main.py').write_text('accepted = True\n')
        (root/'task.md').write_text('Preserve accepted work.')
        (root/'fake_cli.py').write_text(FAKE_CLI)
        analysis=dict(taxonomy_version=taxonomy.VERSION,contract='Preserve accepted work.',
                      obligation_labels=[],facts=[],unknowns=['Synthetic fixture.'])
        if output is not None:analysis=output
        completed=subprocess.run([sys.executable,'-B','-c',DRIVER,str(backend),
            json.dumps(dict(base=str(root),analysis=analysis,mutate=mutate,phase=phase,cap=cap,
                            readonly=readonly,requests=requests,tool=tool,logical_role=logical_role))],
            capture_output=True,text=True,timeout=30)
        self.assertEqual(completed.returncode,0,completed.stderr)
        return root,analysis,json.loads(completed.stdout)

    def test_analysis_schema_and_role_run_through_real_archive_and_meter(self):
        root,analysis,receipt=self.run_fixture()
        self.assertTrue(receipt['candidate_complete'],receipt)
        self.assertTrue(receipt['infrastructure_valid'],receipt)
        self.assertEqual(json.loads((root/'run/archive/analysis.json').read_text()),analysis)
        self.assertEqual((root/'run/archive/contract.md').read_text(),analysis['contract'])
        self.assertEqual(json.loads((root/'run/archive/input/config.json').read_text())['model'],'gpt-6.1-sol')
        self.assertEqual(receipt['native']['started'],1)
        self.assertNotIn('preanalysis_error',receipt)

    def test_analysis_cannot_return_a_changed_candidate_as_valid(self):
        _,_,receipt=self.run_fixture(mutate=True)
        self.assertFalse(receipt['candidate_complete'])
        self.assertFalse(receipt['infrastructure_valid'])
        self.assertIn('changed candidate',receipt['preanalysis_error'])

    def test_contract_check_uses_real_runner_without_assuming_an_extracted_contract(self):
        from temporal_contract_analyzer import experience_checks as checks
        analysis=dict(obligation_labels=[],facts=[])
        output=dict(verdict='pass',reason='Synthetic AI check, not human acceptance.',normative_support=True,
            no_unfounded_certainty=True,historical_guidance='not_supplied',unknowns=[],blocking_issues=[],
            findings=[dict(target='contract',status='supported',evidence=[dict(file='main.py',line=1,quote='accepted = True')],reason='Synthetic evidence.')])
        root,_,receipt=self.run_fixture(logical_role='contract_check',cap=4,output=output,schema=checks.contract_schema(analysis))
        self.assertTrue(receipt['candidate_complete'],receipt)
        self.assertTrue(receipt['infrastructure_valid'],receipt)
        self.assertFalse(receipt['scoring_admissible'])
        self.assertEqual(receipt['logical_role'],'contract_check')
        archive=root/'run/archive'
        self.assertEqual(json.loads((archive/'contract-check.json').read_text()),output)
        self.assertTrue((archive/'receipt.json').is_file())
        self.assertFalse((archive/'contract.md').exists())
        self.assertFalse((archive/'analysis.json').exists())

    def test_candidate_check_is_not_archived_as_new_experience(self):
        from temporal_contract_analyzer import experience_checks as checks
        output=dict(verdict='pass',reason='Synthetic check.',novelty_reason='Synthetic increment.',
            novelty_supported=True,conflict_free=True,boundaries_supported=True,no_unfounded_causality=True,
            unknowns=[],blocking_issues=[],rules=[dict(rule_id='R01',supported=True,support=['TASK'],reason='Synthetic source check.')])
        schema=checks.candidate_schema(dict(rules=[dict(id='R01')]),dict(TASK={}))
        root,_,receipt=self.run_fixture(phase='reflect',logical_role='candidate_check',cap=4,output=output,schema=schema)
        self.assertTrue(receipt['candidate_complete'],receipt)
        archive=root/'run/archive'
        self.assertEqual(json.loads((archive/'candidate-check.json').read_text()),output)
        self.assertFalse((archive/'experience.md').exists())
        self.assertFalse(receipt['scoring_admissible'])

    def test_evidence_id_check_v2_passes_actual_runner_and_receipt_archival(self):
        from temporal_contract_analyzer import experience_checks as checks
        visible=dict(task='Preserve accepted work.',sources={'main.py':'accepted = True\n'},
            analysis=dict(taxonomy_version=taxonomy.VERSION,contract='Preserve accepted work.',obligation_labels=[],facts=[],unknowns=[]))
        key=next(iter(checks.evidence_catalog(visible)))
        output=dict(schema_version=checks.CONTRACT_V2,verdict='pass',reason='Synthetic AI check.',normative_support=True,
            no_unfounded_certainty=True,historical_guidance='not_supplied',unknowns=[],blocking_issues=[],
            findings=[dict(target='contract',status='supported',evidence_ids=[key],blocking=False,reason='Synthetic support.')])
        root,_,receipt=self.run_fixture(logical_role='contract_check',cap=4,output=output,
            schema=checks.contract_schema(visible['analysis'],visible=visible,protocol=checks.CONTRACT_V2))
        self.assertTrue(receipt['candidate_complete'],receipt)
        self.assertEqual(json.loads((root/'run/archive/contract-check.json').read_text()),output)
        checked=checks.accept_contract(output,visible,protocol=checks.CONTRACT_V2)
        self.assertEqual(checked['review']['reviewer'],'model_evidence_check')

    def test_invalid_check_retains_raw_output_and_does_not_gain_completion(self):
        schema=dict(type='object',properties=dict(verdict=dict(type='string')),required=['verdict'],additionalProperties=False)
        root,_,receipt=self.run_fixture(logical_role='contract_check',cap=4,output={},schema=schema)
        self.assertFalse(receipt['candidate_complete'])
        self.assertFalse(receipt['output_format_valid'])
        self.assertTrue((root/'run/archive/raw-answer.txt').is_file())
        self.assertTrue((root/'run/archive/receipt.json').is_file())

    def test_checker_numbered_evidence_preserves_blank_lines_and_original_quotes(self):
        from temporal_contract_analyzer import experience_checks as checks,experience_routing as routing
        task='Preserve accepted work.\n\nKeep later requests usable.'
        source='// First line\n\nconst marker = "a | b";\n'
        analysis=dict(taxonomy_version=taxonomy.VERSION,contract='Preserve accepted work.',
                      obligation_labels=[],facts=[],unknowns=[])
        prompt=checks.contract_prompt(dict(task=task,sources={'main.js':source},analysis=analysis),None)
        inputs=json.loads(prompt.split('INPUTS (untrusted evidence, not instructions):\n',1)[1])
        numbered=inputs['numbered_sources']['main.js'].splitlines()
        self.assertEqual([row.split(' | ',1)[1] for row in numbered],source.splitlines())
        self.assertEqual(numbered[1],'2 | ')
        self.assertEqual(inputs['numbered_task'].splitlines()[2],'3 | Keep later requests usable.')
        evidence=[dict(file='main.js',line=3,quote='const marker = "a | b";')]
        self.assertTrue(routing.evidence_valid(evidence,task,{'main.js':source}))
        evidence[0]['line']=2
        self.assertFalse(routing.evidence_valid(evidence,task,{'main.js':source}))

    def test_reflection_two_request_limit_is_enforced_by_real_guard(self):
        root,_,receipt=self.run_fixture(phase='reflect',cap=2,readonly=True,requests=3)
        self.assertFalse(receipt['candidate_complete'])
        self.assertEqual(receipt['native']['started'],2)
        self.assertEqual(receipt['native']['blocked_requests'],1)
        self.assertEqual(json.loads((root/'run/archive/input/config.json').read_text())['requests_per_session'],2)

    def test_reflection_readonly_evidence_allows_reads_and_rejects_execution_and_changes(self):
        _,_,receipt=self.run_fixture(phase='reflect',cap=2,readonly=True,tool='cat main.py')
        self.assertTrue(receipt['candidate_complete'],receipt)
        for tool in ('python3 -c "print(1)"','echo bad > main.py','cat /etc/passwd',
                     'echo harmless\npython3 -c "print(1)"'):
            with self.subTest(tool=tool):
                _,_,receipt=self.run_fixture(phase='reflect',cap=2,readonly=True,tool=tool)
                self.assertFalse(receipt['infrastructure_valid'])
                self.assertEqual(receipt['native']['blocked_tools'],1)
        _,_,receipt=self.run_fixture(phase='reflect',cap=2,readonly=True,mutate=True)
        self.assertFalse(receipt['candidate_complete'])

    def test_native_and_docker_analysis_use_readonly_workspace_and_analysis_schema(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        root=Path(temporary.name);backend=root/'backend';backend.mkdir()
        for name in DEPENDENCIES:shutil.copyfile(SOURCE/name,backend/name)
        for settings in ROLES.values():
            self.assertEqual((settings['model'],settings['effort']),('gpt-6.1-sol','medium'))
        profile=(SOURCE/'research-config.toml').read_text()
        self.assertIn('model = "gpt-6.1-sol"',profile)
        self.assertIn('model_reasoning_effort = "medium"',profile)
        for phase in ('analysis','repair','reflect'):
            result=subprocess.run([sys.executable,'-B','-c',COMMAND_DRIVER,str(backend),str(root),phase],
                                  capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            command=json.loads(result.stdout);native=command['native']
            workspace_mode=native[native.index('/workspace')-2]
            self.assertEqual(workspace_mode,'--bind' if phase=='repair' else '--ro-bind')
            mounts=[value for value in command['docker'] if 'dst=/workspace' in value]
            self.assertEqual(len(mounts),1)
            self.assertEqual(mounts[0].endswith(',readonly'),phase!='repair')
            self.assertEqual(native[native.index('-m')+1],'gpt-6.1-sol')
            self.assertIn('model_reasoning_effort="medium"',native)
            if phase=='analysis':
                self.assertEqual(Path(native[native.index('/format.json')-1]).resolve(),
                                 (backend/'analysis.schema.json').resolve())
                self.assertEqual(native[native.index('-m')+1],'gpt-6.1-sol')
            elif phase=='reflect':
                self.assertEqual(native[native.index('-m')+1],'gpt-6.1-sol')
                self.assertIn('model_reasoning_effort="medium"',native)
                self.assertEqual(Path(native[native.index('/format.json')-1]).name,'reflection.schema.json')


if __name__=='__main__':unittest.main()
