"""Collector failures retain bounded context without copying commands or secrets."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


SOURCE=Path(__file__).resolve().parents[1]/'temporal_contract_analyzer/_session_runtime'


def collector_fixture():
    spec=importlib.util.spec_from_file_location('safe_collector_fixture',SOURCE/'guard_server.py')
    module=importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules,{'request_guard':types.SimpleNamespace(account=lambda *a,**k:False)}):
        spec.loader.exec_module(module)
    return module


class Connection:
    def __init__(self,data):self.data=data;self.sent=[]
    def settimeout(self,*args):pass
    def recv(self,*args):value=self.data;self.data=b'';return value
    def sendall(self,value):self.sent.append(value)
    def __enter__(self):return self
    def __exit__(self,*args):pass


class Listener:
    def __init__(self,connections):self.connections=list(connections)
    def accept(self):
        if not self.connections:raise OSError('fixture listener complete')
        return self.connections.pop(0),None


class GuardCollectorDiagnosticTests(unittest.TestCase):
    def setUp(self):self.module=collector_fixture()

    def test_long_command_failure_is_denied_with_safe_fingerprint(self):
        secret='sk-DO-NOT-RECORD-THIS'
        command="rg -n '"+'x'*20000+secret+"' src/Main.java"
        event=dict(hook_event_name='PreToolUse',tool_name='Bash',tool_input=dict(command=command),
                   env={'SECRET':secret},Authorization='Bearer '+secret,prompt=secret)
        conn=Connection(json.dumps(event).encode()+b'\n')
        server=self.module.GuardServer('unused','unused','call',4,'extraction')
        server.socket=Listener([conn])
        self.module.account=Mock(side_effect=OSError(36,'sensitive '+secret,command))
        server._serve()
        self.assertEqual(json.loads(conn.sent[0]),dict(deny=True,collector_error=True))
        self.assertEqual(server.errors,['OSError (errno=36)'])
        self.assertEqual(server.error_contexts,[dict(hook_event_name='PreToolUse',tool_name='Bash',
            command_length=len(command),command_sha256=hashlib.sha256(command.encode()).hexdigest(),
            exception_type='OSError',errno=36)])
        serialized=json.dumps(dict(errors=server.errors,error_contexts=server.error_contexts))
        self.assertNotIn(secret,serialized);self.assertNotIn(command,serialized)
        self.assertNotIn('Authorization',serialized);self.assertLess(len(serialized),500)

    def test_malformed_next_event_does_not_reuse_previous_command_context(self):
        first=Connection(json.dumps(dict(hook_event_name='PreToolUse',tool_name='Bash',
                                        tool_input=dict(command='cat main.py'))).encode()+b'\n')
        second=Connection(b'{\n')
        server=self.module.GuardServer('unused','unused','call',4,'extraction')
        server.socket=Listener([first,second]);server._serve()
        self.assertEqual(json.loads(first.sent[0]),dict(deny=False))
        context=server.error_contexts[0]
        self.assertIsNone(context['hook_event_name']);self.assertIsNone(context['tool_name'])
        self.assertIsNone(context['command_length']);self.assertIsNone(context['command_sha256'])
        self.assertEqual(context['exception_type'],'JSONDecodeError')

    def test_arbitrary_payload_identifiers_are_not_diagnostic_text(self):
        event=dict(hook_event_name='Authorization: Bearer sk-secret',tool_name='echo sk-secret',
                   tool_input=dict(cmd='cat main.py'))
        context=self.module.error_context(event,ValueError('sk-secret'))
        self.assertIsNone(context['hook_event_name']);self.assertEqual(context['tool_name'],'unknown')
        self.assertNotIn('sk-secret',json.dumps(context))
        self.assertEqual(context['command_sha256'],hashlib.sha256(b'cat main.py').hexdigest())

    def test_surrogate_or_absent_command_cannot_break_error_reporting(self):
        context=self.module.error_context(dict(hook_event_name='PreToolUse',tool_name='functions.exec_command',
            tool_input=dict(cmd='cat \ud800')),OSError(36,'hidden filename'))
        self.assertEqual(context['command_length'],5)
        self.assertEqual(len(context['command_sha256']),64)
        other=self.module.error_context(dict(hook_event_name='PostModelRequest'),RuntimeError('secret'))
        self.assertIsNone(other['command_length']);self.assertIsNone(other['command_sha256'])

    @unittest.skipIf(os.name=='nt','packaged native runner uses Linux fcntl')
    def test_runner_archives_context_and_keeps_collector_error_invalid(self):
        from tests import test_analysis_runner as fixtures
        context=dict(hook_event_name='PreToolUse',tool_name='Bash',command_length=400,
                     command_sha256='a'*64,exception_type='OSError',errno=36)
        injection="""import runner
original_guard_init=runner.GuardServer.__init__
def fixture_guard_init(self,*args,**kwargs):
 original_guard_init(self,*args,**kwargs)
 self.errors=['OSError (errno=36)']
 self.error_contexts=[CONTEXT]
runner.GuardServer.__init__=fixture_guard_init""".replace('CONTEXT',repr(context))
        fixture=fixtures.AnalysisRunnerTests(methodName='test_analysis_schema_and_role_run_through_real_archive_and_meter')
        self.addCleanup(fixture.doCleanups)
        with patch.object(fixtures,'DRIVER',fixtures.DRIVER.replace('import runner',injection,1)):
            root,_,receipt=fixture.run_fixture()
        archived=json.loads((root/'run/archive/guard-collector-status.json').read_text())
        self.assertEqual(archived,dict(errors=['OSError (errno=36)'],error_contexts=[context]))
        self.assertFalse(receipt['infrastructure_valid'])


if __name__=='__main__':unittest.main()
