"""Regression for external isolation and pause settlement, no provider calls."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parents[1]/'temporal_contract_analyzer/_session_runtime'
sys.path.insert(0,str(R))
import request_guard

class AuditTests(unittest.TestCase):
    def test_pause_settles_inflight_and_denies_next_without_counting(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);stop=p/'STOP';(p/'config.json').write_text(json.dumps(dict(global_cap=12,calls={'x':dict(cap=12,mode='extraction')},stop_file=str(stop))))
            self.assertFalse(request_guard.account(dict(hook_event_name='PreModelRequest'),p,'x',False))
            stop.touch()
            self.assertFalse(request_guard.account(dict(hook_event_name='PostModelRequest',status='completed'),p,'x',False))
            self.assertTrue(request_guard.account(dict(hook_event_name='PreModelRequest'),p,'x',False))
            v=json.loads((p/'ledger.json').read_text())
            self.assertEqual((v['started'],v['completed'],v['blocked_requests']),(1,1,1))
            self.assertEqual(v['events'][-1]['reason'],'user_requested_pause')

    def test_external_namespace_does_not_change_workspace_or_guard(self):
        spec=importlib.util.spec_from_file_location('audit_runner',R/'runner.py')
        runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        folder=Path('/fixture')
        base=['bwrap','--ro-bind',str(folder/'workspace'),'/workspace','--sandbox','read-only','--chdir','/workspace']
        with patch.object(runner.backend,'command',return_value=base.copy()) as factory:
            cmd=runner.command('x',folder,'analysis',dict(node='/node',external_container_isolation=True),runtime=Path('/runtime'),socket_dir=Path('/guard'))
            self.assertEqual(cmd[cmd.index('--sandbox')+1],'danger-full-access')
            self.assertEqual(cmd[cmd.index(str(folder/'workspace'))-1],'--ro-bind')
            self.assertTrue(factory.call_args.kwargs['readonly_tools'])
            self.assertEqual(factory.call_args.kwargs['socket_dir'],Path('/guard'))
        with patch.object(runner.backend,'command',return_value=base.copy()):
            cmd=runner.command('x',folder,'analysis',dict(node='/node'),runtime=Path('/runtime'),socket_dir=Path('/guard'))
            self.assertEqual(cmd[cmd.index('--sandbox')+1],'read-only')

if __name__=='__main__':unittest.main()
