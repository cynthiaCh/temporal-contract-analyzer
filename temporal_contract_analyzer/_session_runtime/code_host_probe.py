"""Offline IPC-v1 startup/execution probe for the installed public code host.

No Codex model client, credential profile, tools or provider connection is used.
Unknown protocol shapes fail before model dispatch rather than claiming readiness.
"""
import json
import os
from pathlib import Path
import select
import signal
import struct
import subprocess
import time


def probe(binary='/opt/codex-code-mode-host'):
    process=subprocess.Popen([str(binary),'--listen','stdio'],stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    deadline=time.monotonic()+8
    frames=[]
    def send(value):
        payload=json.dumps(value).encode()
        process.stdin.write(struct.pack('<I',len(payload))+payload);process.stdin.flush()
    def exact(size):
        value=b''
        while len(value)<size:
            remaining=deadline-time.monotonic()
            if remaining<=0 or not select.select([process.stdout],[],[],remaining)[0]:
                raise RuntimeError('Code host offline probe timed out')
            part=os.read(process.stdout.fileno(),size-len(value))
            if not part:raise RuntimeError('Code host exited before its IPC response')
            value+=part
        return value
    def receive():
        size=struct.unpack('<I',exact(4))[0]
        if not 0<size<=1024*1024:raise RuntimeError('Invalid code host probe frame length')
        value=json.loads(exact(size));frames.append(value);return value
    def response(value,ident):
        if value.get('id')!=ident or value.get('result',{}).get('status')!='ok':
            raise RuntimeError('Code host probe operation failed: '+json.dumps(value))
        return value['result']['value']
    try:
        send(dict(type='connection/hello',supportedVersions=[1],requiredCapabilities=[],optionalCapabilities=[]))
        hello=receive()
        if hello.get('type')!='connection/ready' or hello.get('selectedVersion')!=1:
            raise RuntimeError('Unsupported code host handshake')
        session='tca-offline-runtime-probe'
        send(dict(type='operation/request',id=1,request=dict(method='session/open',sessionId=session)))
        if response(receive(),1).get('type')!='session/ready':raise RuntimeError('Code host session did not start')
        send(dict(type='operation/request',id=2,request=dict(method='session/execute',sessionId=session,
            request=dict(tool_call_id='offline-probe',enabled_tools=[],
                source='if (6 * 7 !== 42) throw new Error("offline probe failed");',
                yield_time_ms=1000,max_output_tokens=128))))
        if response(receive(),2).get('type')!='execution/started':raise RuntimeError('Code host execution did not start')
        result=receive()
        if result.get('type')!='execute/initialResponse':raise RuntimeError('Missing code host execution result')
        value=response(result,2)
        if not isinstance(value.get('Result'),dict) or 'error_text' not in value['Result'] \
                or value['Result']['error_text'] is not None or not value['Result'].get('cell_id'):
            raise RuntimeError('Code host JavaScript execution failed: '+json.dumps(value))
        return dict(handshake=True,javascript_execution=True,protocol_version=1,
                    delegated_tools_tested=False,model_calls=0,frames=frames)
    finally:
        # The probe is owned, local, and deliberately independent of model sessions.
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        _,stderr=process.communicate(timeout=3)
        if stderr and process.returncode not in (0,-signal.SIGKILL):
            # Keep native diagnostics in the caller's captured stderr too.
            import sys
            sys.stderr.write(stderr.decode(errors='replace'))


if __name__=='__main__':
    print(json.dumps(probe()))
