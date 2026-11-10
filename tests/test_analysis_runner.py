"""Exercise the packaged analysis runner with a fake CLI, never a model."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from temporal_contract_analyzer import taxonomy
from temporal_contract_analyzer.evolution_backend import DEPENDENCIES, SOURCE


DRIVER = '''import json,sys,tempfile
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import runner
payload=json.loads(sys.argv[2]);base=Path(payload['base'])
runner.tempfile.tempdir='/tmp'
def fake_command(archive,runtime,guard):
 return [sys.executable,'-B',str(base/'fake_cli.py'),str(guard.directory/'hook.sock'),
         str(archive.workspace),json.dumps(payload['analysis']),str(payload['mutate'])]
receipt=runner.session(dict(slot='ANALYSIS',phase='analysis'),'Synthetic task and numbered source',
 case={},candidate=base/'candidate',task=base/'task.md',config=dict(seconds_per_session=20),
 run_dir=base/'run',command_factory=fake_command)
print(json.dumps(receipt))
'''

FAKE_CLI = '''import json,socket,sys
from pathlib import Path
def hook(event):
 with socket.socket(socket.AF_UNIX) as connection:
  connection.connect(sys.argv[1]);connection.sendall(json.dumps(event).encode()+b'\\n')
  assert not json.loads(connection.recv(4096))['deny']
hook(dict(hook_event_name='PreModelRequest',model='gpt-6-sol'))
hook(dict(hook_event_name='PostModelRequest',model='gpt-6-sol',status='completed'))
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
runner.backend.BINARY=base/'public/codex'
runner.backend.global_snapshot=lambda: {}
native=runner.command(phase,folder,phase,dict(node='/runtime/node16/bin/node'),
 runtime=runtime,socket_dir=runtime/'hooks',copy_auth=False)
launcher=Launcher(dict(solver_image='sha256:'+'a'*64,name='tca-session-'+'b'*32,
 node='/runtime/node16/bin/node'),archive)
docker=launcher.command(native,folder,runtime,phase,runtime/'hooks')
print(json.dumps(dict(native=native,docker=docker)))
'''


class AnalysisRunnerTests(unittest.TestCase):
    def run_fixture(self,mutate=False):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        root=Path(temporary.name);backend=root/'backend';backend.mkdir()
        for name in DEPENDENCIES:shutil.copyfile(SOURCE/name,backend/name)
        (backend/'analysis.schema.json').write_text(json.dumps(taxonomy.analysis_schema()))
        (root/'candidate').mkdir();(root/'candidate/main.py').write_text('accepted = True\n')
        (root/'task.md').write_text('Preserve accepted work.')
        (root/'fake_cli.py').write_text(FAKE_CLI)
        analysis=dict(taxonomy_version=taxonomy.VERSION,contract='Preserve accepted work.',
                      obligation_labels=[],facts=[],unknowns=['Synthetic fixture.'])
        completed=subprocess.run([sys.executable,'-B','-c',DRIVER,str(backend),
            json.dumps(dict(base=str(root),analysis=analysis,mutate=mutate))],
            capture_output=True,text=True,timeout=30)
        self.assertEqual(completed.returncode,0,completed.stderr)
        return root,analysis,json.loads(completed.stdout)

    def test_analysis_schema_and_role_run_through_real_archive_and_meter(self):
        root,analysis,receipt=self.run_fixture()
        self.assertTrue(receipt['candidate_complete'],receipt)
        self.assertTrue(receipt['infrastructure_valid'],receipt)
        self.assertEqual(json.loads((root/'run/archive/analysis.json').read_text()),analysis)
        self.assertEqual((root/'run/archive/contract.md').read_text(),analysis['contract'])
        self.assertEqual(json.loads((root/'run/archive/input/config.json').read_text())['model'],'gpt-6-sol')
        self.assertEqual(receipt['native']['started'],1)
        self.assertNotIn('preanalysis_error',receipt)

    def test_analysis_cannot_return_a_changed_candidate_as_valid(self):
        _,_,receipt=self.run_fixture(mutate=True)
        self.assertFalse(receipt['candidate_complete'])
        self.assertFalse(receipt['infrastructure_valid'])
        self.assertIn('changed candidate',receipt['preanalysis_error'])

    def test_native_and_docker_analysis_use_readonly_workspace_and_analysis_schema(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        root=Path(temporary.name);backend=root/'backend';backend.mkdir()
        for name in DEPENDENCIES:shutil.copyfile(SOURCE/name,backend/name)
        for phase in ('analysis','repair'):
            result=subprocess.run([sys.executable,'-B','-c',COMMAND_DRIVER,str(backend),str(root),phase],
                                  capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            command=json.loads(result.stdout);native=command['native']
            workspace_mode=native[native.index('/workspace')-2]
            self.assertEqual(workspace_mode,'--ro-bind' if phase=='analysis' else '--bind')
            mounts=[value for value in command['docker'] if 'dst=/workspace' in value]
            self.assertEqual(len(mounts),1)
            self.assertEqual(mounts[0].endswith(',readonly'),phase=='analysis')
            if phase=='analysis':
                self.assertEqual(Path(native[native.index('/format.json')-1]).resolve(),
                                 (backend/'analysis.schema.json').resolve())
                self.assertEqual(native[native.index('-m')+1],'gpt-6-sol')


if __name__=='__main__':unittest.main()
