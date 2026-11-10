"""Synthetic IPC peer; no CLI model/provider requests or expert claims."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from temporal_contract_analyzer._session_runtime.code_host_probe import probe


class CodeHostProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)

    def helper(self,mode):
        source='#!'+sys.executable+'\n'+'''import json,struct,sys,time
mode=MODE
def read():
 n=struct.unpack('<I',sys.stdin.buffer.read(4))[0]
 return json.loads(sys.stdin.buffer.read(n))
def send(value):
 b=json.dumps(value).encode();sys.stdout.buffer.write(struct.pack('<I',len(b))+b);sys.stdout.buffer.flush()
assert read()['type']=='connection/hello'
send(dict(type='connection/ready',selectedVersion=2 if mode=='version' else 1,capabilities=[]))
if mode=='version':sys.exit(0)
assert read()['request']['method']=='session/open'
send(dict(type='operation/response',id=1,result=dict(status='ok',value=dict(type='session/ready'))))
r=read()['request']['request'];assert r['enabled_tools']==[] and '6 * 7' in r['source']
send(dict(type='operation/response',id=2,result=dict(status='ok',value=dict(type='execution/started'))))
result=dict(cell_id='1',error_text='SYNTHETIC_ENGINE_FAILURE' if mode=='error' else None)
if mode=='missing':result.pop('error_text')
send(dict(type='execute/initialResponse',id=2,result=dict(status='ok',value=dict(Result=result))))
time.sleep(30)
'''.replace('MODE',repr(mode))
        path=self.root/'fixture-host';path.write_text(source);path.chmod(0o755);return path

    def test_execution_probe_and_process_cleanup(self):
        original=subprocess.Popen;processes=[]
        def start(*args,**kwargs):
            result=original(*args,**kwargs);processes.append(result);return result
        with patch('temporal_contract_analyzer._session_runtime.code_host_probe.subprocess.Popen',side_effect=start):
            result=probe(self.helper('complete'))
        self.assertTrue(result['handshake']);self.assertTrue(result['javascript_execution'])
        self.assertFalse(result['delegated_tools_tested']);self.assertEqual(result['model_calls'],0)
        self.assertTrue(all(p.poll() is not None for p in processes))

    def test_javascript_failure_is_not_readiness(self):
        with self.assertRaisesRegex(RuntimeError,'JavaScript execution failed'):probe(self.helper('error'))

    def test_missing_result_evidence_is_not_readiness(self):
        with self.assertRaisesRegex(RuntimeError,'JavaScript execution failed'):probe(self.helper('missing'))

    def test_unknown_wire_version_fails_before_any_model(self):
        with self.assertRaisesRegex(RuntimeError,'Unsupported code host handshake'):probe(self.helper('version'))


if __name__=='__main__':unittest.main()
