"""Execute the exact historical safe-read tools inside the production namespace."""
import json,sys,tempfile,subprocess
from pathlib import Path
A=Path(__file__).resolve().parent
from archive import Archive,save,inventory
from guard_server import GuardServer
import runner
from test_read_policy_real import corpus

def main():
 case=json.loads((A/'cohort.json').read_text())[0];candidate=A/'materials/D1/candidate'
 commands=[e['tool_input']['command'] for name,slot,e in corpus() if name.endswith('v2r1-20261108_215007')]
 assert len(commands)==3
 out=A/'offline/read-policy-replay';out.mkdir(parents=True,exist_ok=False)
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);ar=Archive(root/'run').prepare(candidate,A/'materials/D1/task.md','Offline actual tool replay, no model.',{})
  with GuardServer(root/'ipc',ar.root/'meter','safe-read-fixture',12,'extraction') as guard:
   cmd=runner.command('safe-read-fixture',ar.run_dir,'extract',case,runtime=root/'runtime',socket_dir=guard.directory,copy_auth=False);prefix=cmd[:cmd.index('--')+1]
   body='''import json,socket,subprocess
from pathlib import Path
commands=COMMANDS
for command in commands:
 s=socket.socket(socket.AF_UNIX);s.connect('/hook-control/hook.sock');s.sendall(json.dumps({'hook_event_name':'PreToolUse','tool_name':'Bash','tool_input':{'command':command}}).encode()+b'\\n');decision=json.loads(s.recv(4096));s.close();assert not decision['deny'],(command,decision)
 r=subprocess.run(['/bin/bash','-lc',command],capture_output=True,text=True)
 print(json.dumps({'command':command,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}))
assert not Path('/archive').exists() and not Path('/home/sribd').exists()
'''.replace('COMMANDS',repr(commands))
   r=subprocess.run(prefix+['/usr/bin/python3','-B','-c',body],capture_output=True,text=True,timeout=30)
   (out/'stdout.jsonl').write_text(r.stdout);(out/'stderr.txt').write_text(r.stderr)
   assert r.returncode==0,r.stderr
   ledger=json.loads((ar.root/'meter/ledger.json').read_text());assert all(not e['denied'] for e in ledger['events'])
   save(out/'ledger.json',ledger)
  assert inventory(candidate)==inventory(ar.workspace)
  save(out/'receipt.json',{'status':'PASS','exact_real_tools_replayed':len(commands),'tool_denials':0,'model_requests':0,'candidate_unchanged':True,'namespace':'unchanged production bwrap prefix','note':'Missing docs may return shell exit2; that is a normal read result, not infrastructure failure.'})
 print('PASS exact three formerly interrupted read tools in isolated namespace; zero model requests')
if __name__=='__main__':main()
