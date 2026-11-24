"""Exercise the packaged analysis runner with a fake CLI, never a model."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from temporal_contract_analyzer import taxonomy
from temporal_contract_analyzer.execution_backend import DEPENDENCIES, SOURCE, ROLES


DRIVER = '''import json,sys,tempfile
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import runner
payload=json.loads(sys.argv[2]);base=Path(payload['base'])
runner.tempfile.tempdir=str(base/('long-platform-temp-directory-'*5))
Path(runner.tempfile.tempdir).mkdir()
def fake_command(archive,runtime,guard):
 return [sys.executable,'-B',str(base/'fake_cli.py'),str(guard.directory/'hook.sock'),
         str(archive.workspace),json.dumps(payload['analysis']),str(payload['mutate']),
         payload.get('phase','analysis'),str(payload.get('requests',1)),payload.get('tool',''),
         (payload.get('model_settings') or {}).get('model','gpt-6.1-sol')]
phase=payload.get('phase','analysis')
slot=dict(slot='ANALYSIS',phase=phase)
if payload.get('logical_role'):slot['logical_role']=payload['logical_role']
if payload.get('audit_error'):
 def broken_audit(*args):raise ValueError('SYNTHETIC_AUDIT_FAILURE')
 runner.source_proof=broken_audit
if payload.get('archive_error'):
 original_finalize=runner.Archive.finalize
 def broken_archive(self,**kwargs):
  result=original_finalize(self,**kwargs);result['status']='ERROR';return result
 runner.Archive.finalize=broken_archive
def fake_score(candidate,directory):
 (directory/'called.json').write_text('true')
 return dict(verdict='PASS')
receipt=runner.session(slot,'Synthetic task and numbered source',
 case={},candidate=base/'candidate',task=base/'task.md',config=dict(seconds_per_session=20,
 requests_per_session=payload.get('cap',12),reflection_readonly=payload.get('readonly',False),model_settings=payload.get('model_settings')),
 run_dir=base/'run',command_factory=fake_command,score_fn=fake_score if payload.get('score') else None)
print(json.dumps(receipt))
'''

FAKE_CLI = '''import json,socket,sys
from pathlib import Path
def hook(event):
 with socket.socket(socket.AF_UNIX) as connection:
  connection.connect(sys.argv[1]);connection.sendall(json.dumps(event).encode()+b'\\n')
  assert not json.loads(connection.recv(4096))['deny']
model=sys.argv[8]
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

PROOF_DRIVER = '''import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import runner
print(json.dumps(runner.source_proof(json.load(sys.stdin),Path(sys.argv[2]))))
'''


class AnalysisRunnerTests(unittest.TestCase):
    def run_fixture(self,mutate=False,phase='analysis',cap=12,readonly=False,requests=1,tool='',logical_role=None,output=None,schema=None,model_settings=None,score=False,archive_error=False,audit_error=False):
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
                            readonly=readonly,requests=requests,tool=tool,logical_role=logical_role,model_settings=model_settings,
                            score=score,archive_error=archive_error,audit_error=audit_error))],
            capture_output=True,text=True,timeout=30)
        self.assertEqual(completed.returncode,0,completed.stderr)
        return root,analysis,json.loads(completed.stdout)

    def test_complete_repair_without_tool_read_proof_reaches_scorer(self):
        root,_,receipt=self.run_fixture(phase='repair',mutate=True,output=dict(report='Synthetic patch.'),score=True)
        self.assertEqual(receipt['source_body_proofs'],[])
        self.assertEqual(receipt['source_read_audit']['status'],'not_observed')
        self.assertFalse(receipt['source_read_audit']['required_for_scoring'])
        self.assertTrue(receipt['candidate_complete'],receipt)
        self.assertTrue(receipt['scoring_admissible'],receipt)
        self.assertEqual(receipt['scoring_status'],'COLLECTED')
        self.assertTrue((root/'run/archive/score/called.json').exists())
        self.assertTrue(receipt['scored_candidate_unchanged'])

    def test_optional_source_audit_failure_does_not_block_scoring(self):
        _,_,receipt=self.run_fixture(phase='repair',mutate=True,output=dict(report='Synthetic patch.'),score=True,audit_error=True)
        self.assertEqual(receipt['source_read_audit']['status'],'unavailable')
        self.assertIn('SYNTHETIC_AUDIT_FAILURE',receipt['source_read_audit']['error'])
        self.assertTrue(receipt['scoring_admissible'],receipt)
        self.assertEqual(receipt['scoring_status'],'COLLECTED')

    def test_missing_read_proof_does_not_bypass_invalid_output_or_archive(self):
        for changes in (dict(output=dict(wrong='Invalid repair schema')),dict(archive_error=True)):
            with self.subTest(changes=changes):
                config=dict(phase='repair',mutate=True,output=dict(report='Synthetic patch.'),score=True)
                config.update(changes);root,_,receipt=self.run_fixture(**config)
                self.assertEqual(receipt['source_body_proofs'],[])
                self.assertFalse(receipt['scoring_admissible'],receipt)
                self.assertFalse((root/'run/archive/score/called.json').exists())

    def test_nonzero_combined_read_retains_optional_source_audit(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        root=Path(temporary.name);backend=root/'backend';backend.mkdir()
        for name in DEPENDENCIES:shutil.copyfile(SOURCE/name,backend/name)
        original=root/'original';(original/'src').mkdir(parents=True)
        body="const acceptedDocumentIdentity = 'original';\nconst currentVisitIdentity = 'visit-one';\nconst retainedOperationResult = 'pending';\n"
        (original/'src/session.js').write_text(body)
        # The later rg failure must not erase successful cat output. Separators
        # belong to the shell grammar, not to the source filename.
        for separator in (';', '&&'):
            for output,expected in ((body,1),(body.splitlines()[0],0)):
                with self.subTest(separator=separator,complete_output=bool(expected)):
                    event=dict(type='item.completed',item=dict(type='command_execution',exit_code=1,
                        command="/bin/bash -lc 'cat src/session.js"+separator+" rg --files -g AGENTS.md'",
                        aggregated_output=output))
                    run=subprocess.run([sys.executable,'-B','-c',PROOF_DRIVER,str(backend),str(original)],
                        input=json.dumps([event]),capture_output=True,text=True,timeout=10)
                    self.assertEqual(run.returncode,0,run.stderr)
                    proofs=json.loads(run.stdout);self.assertEqual(len(proofs),expected)
                    if expected:
                        self.assertEqual(proofs[0]['source'],'src/session.js')
                        self.assertEqual(proofs[0]['proof_kind'],'complete_body_from_nonzero_read')

    def test_custom_model_hooks_match_frozen_session_profile(self):
        from temporal_contract_analyzer._session_runtime.model_settings import resolve_profile
        settings=resolve_profile();settings.update(model='synthetic-custom-model',reasoning_effort=None)
        root,_,receipt=self.run_fixture(model_settings=settings)
        self.assertTrue(receipt['candidate_complete'],receipt)
        config=json.loads((root/'run/archive/input/config.json').read_text())
        self.assertEqual(config['model'],'synthetic-custom-model');self.assertIsNone(config['effort'])

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

    def test_v4_stage_schemas_archive_without_a_markdown_contract_field(self):
        from temporal_contract_analyzer.tempoevo_v4 import CONTRACT_SCHEMA, DIAGNOSIS_SCHEMA, EXPERIENCE_SCHEMA, CONTRACT_FIELDS
        contract=dict({key:[] for key in CONTRACT_FIELDS},
            obligations=[dict(id='preserve',text='Preserve accepted work.')],
            supporting_evidence=[dict(file='TASK',quote='Preserve accepted work.')])
        diagnosis=dict(diagnosis='implementation_gap',contract_after=contract,
            structured_delta=[],supporting_evidence=contract['supporting_evidence'],
            remaining_unknowns=[],explanation='Retain the Contract.')
        experience=dict(labels=['I'],requires=['entry_snapshot'],excludes=[],
            rules=[dict(category='verification',body='Verify accepted identity.')],limitations=[])
        for output,schema in ((contract,CONTRACT_SCHEMA),(diagnosis,DIAGNOSIS_SCHEMA),(experience,EXPERIENCE_SCHEMA)):
            with self.subTest(schema=list(output)):
                root,_,receipt=self.run_fixture(output=output,schema=schema)
                self.assertTrue(receipt['candidate_complete'],receipt)
                self.assertTrue(receipt['infrastructure_valid'],receipt)
                self.assertEqual(receipt['native']['started'],1)
                self.assertEqual(json.loads((root/'run/archive/analysis.json').read_text()),output)
                self.assertTrue((root/'run/archive/receipt.json').is_file())
                self.assertFalse((root/'run/archive/contract.md').exists())

    def test_invalid_analysis_retains_raw_output_and_does_not_gain_completion(self):
        schema=dict(type='object',properties=dict(verdict=dict(type='string')),required=['verdict'],additionalProperties=False)
        root,_,receipt=self.run_fixture(cap=4,output={},schema=schema)
        self.assertFalse(receipt['candidate_complete'])
        self.assertFalse(receipt['output_format_valid'])
        self.assertTrue((root/'run/archive/raw-answer.txt').is_file())
        self.assertTrue((root/'run/archive/receipt.json').is_file())

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
        profiles=json.loads((SOURCE/'model-profiles.json').read_text())
        profile=profiles['profiles'][profiles['default_profile']]
        self.assertEqual(profile['model'],'gpt-6.1-sol')
        self.assertEqual(profile['reasoning_effort'],'medium')
        self.assertNotIn('model =',(SOURCE/'research-config.toml').read_text())
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
