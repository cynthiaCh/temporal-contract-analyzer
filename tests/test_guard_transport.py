"""Exercise real hook accounting across local Unix and authenticated TCP transport."""
from pathlib import Path
import subprocess
import sys
import unittest


SCRIPT = '''
import json,socket,sys,tempfile
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from guard_server import GuardServer
from guard_client import forward
tcp=sys.argv[2]=='tcp'
with tempfile.TemporaryDirectory(prefix='tca-test-',dir='/tmp') as root:
 root=Path(root)
 with GuardServer(root/'hooks',root/'meter','fixture',1,'extraction',docker_desktop=tcp) as guard:
  endpoint=guard.directory/'hook.sock'
  if tcp:
   config=json.loads((guard.directory/'endpoint.json').read_text())
   config['host']='127.0.0.1'
   (guard.directory/'endpoint.json').write_text(json.dumps(config))
   with socket.create_connection((config['host'],config['port']),timeout=3) as conn:
    conn.sendall(json.dumps(dict(token='wrong',event=dict(hook_event_name='PreModelRequest'))).encode()+b'\\n')
    assert json.loads(conn.recv(4096))['deny'] is True
   assert not (root/'meter/ledger.json').exists()
  assert forward(dict(hook_event_name='PreModelRequest'),str(endpoint))['deny'] is False
  assert forward(dict(hook_event_name='PostModelRequest',status='completed'),str(endpoint))['deny'] is False
  assert forward(dict(hook_event_name='PreModelRequest'),str(endpoint))['deny'] is True
  ledger=json.loads((root/'meter/ledger.json').read_text())
  assert ledger['started']==1 and ledger['completed']==1 and ledger['blocked_requests']==1
  assert guard.errors==[]
 assert not endpoint.exists()
'''


class GuardTransport(unittest.TestCase):
    def test_accounting_and_caps(self):
        source = Path(__file__).resolve().parents[1]/'temporal_contract_analyzer/_session_runtime'
        for transport in ('unix', 'tcp'):
            with self.subTest(transport=transport):
                result = subprocess.run([sys.executable, '-B', '-c', SCRIPT, str(source), transport],
                                        capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr)
