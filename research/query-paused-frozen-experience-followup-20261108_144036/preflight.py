"""Local namespace/tool checks, no model/service request or case scoring."""
import sys,json,tempfile,subprocess
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A))
import runner as r
from archive import Archive,save,sha,inventory
from guard_server import GuardServer
C=json.loads((A/'cohort.json').read_text());results=[]
assert (A/'prompts/AUTO_EXP.md').read_bytes()==(A/'prompts/AUTO.md').read_bytes()+b'\n\n'+(A/'NEW_EXPERIENCE.md').read_bytes()
for arm in ['AUTO','AUTO_EXP']:
 a=Archive(A/'offline'/arm).prepare(A/'materials/candidate',A/'materials/task.md',(A/'prompts'/f'{arm}.md').read_text(),{'offline':True})
 original=inventory(a.workspace)
 with tempfile.TemporaryDirectory(prefix='frozen-followup-preflight-') as rt:
  with GuardServer(Path(rt)/'hook',a.root/'meter',f'offline-{arm}',24,'maintenance') as g:
   cmd=r.command(f'offline-{arm}',a.run_dir,'repair',C,runtime=rt,socket_dir=g.directory,copy_auth=False);prefix=cmd[:cmd.index('--')+1]
   assert str(a.root) not in prefix and '/meter' not in prefix and '/output' not in prefix
   assert cmd[cmd.index('-m')+1]=='gpt-5.6-terra' and 'model_reasoning_effort="low"' in cmd
   body=r'''from pathlib import Path
import subprocess,json,socket
assert not any(Path(p).exists() for p in ['/archive','/meter','/output','/home/sribd','/workspace/../archive'])
assert Path('/workspace/src/session.js').read_text().strip()
subprocess.run(['/bin/bash','-c','for f in /workspace/src/*; do cp "$f" /tmp/local-check; diff "$f" /tmp/local-check; done'],check=True)
p=Path('/workspace/offline-owned-fixture');p.write_text('local edit check');assert p.read_text()=='local edit check';p.unlink()
s=socket.socket(socket.AF_UNIX);s.connect('/hook-control/hook.sock');s.sendall(json.dumps({'hook_event_name':'PreToolUse','tool_name':'Bash','tool_input':{'command':'for f in src/*; do cat "$f"; done'}}).encode()+b'\n');assert not json.loads(s.recv(1024))['deny'];s.close()
assert subprocess.check_output(['/runtime/node','--version'],text=True).strip()=='v16.20.2'
print('PASS read/edit/validation, legal shell loops, hidden host archives, node16')
'''
   z=subprocess.run(prefix+['/usr/bin/python3','-B','-c',body],capture_output=True,text=True,timeout=20)
   (a.root/'namespace.stdout.txt').write_text(z.stdout);(a.root/'namespace.stderr.txt').write_text(z.stderr);assert z.returncode==0,z.stderr
   assert inventory(a.workspace)==original
   assert not json.loads((a.root/'meter/ledger.json').read_text()).get('started',0)
 state=a.finalize(model_stopped=True);assert state['status']=='OK';assert not (a.root/'patch.diff').read_bytes()
 results.append({'condition':arm,'status':'PASS','archive_outside_workspace':True,'model_requests':0,'candidate_unchanged':True})
modules=['runner.py','archive.py','native_backend.py','guard_server.py','guard_client.py','request_guard.py','read_policy.py','prompts.py','research-config.toml','models-cache.snapshot.json']
O=Path(json.loads((A/'sources.json').read_text())['source_batch'])
assert all(sha(A/f)==sha(O/f) for f in modules)
old=json.loads((A/'source-evidence/offline-validation.json').read_text());assert old['status']=='PASS' and old['tests']==15
save(A/'offline-validation.json',{'status':'PASS','namespace_checks':results,'byte_identical_modules':modules,'reused_archive_fixture_tests':old,'reused_case_calibration':len(C['calibration']),'prompt_difference_exact_experience_append':True,'experiment_model_calls':0,'maintenance_executions':0,'case_score_reruns':0,'no_network_probe':True,'service_route_independent_attestation':False})
print('PASS: two maintenance namespaces, exact prompts, byte-identical runner and existing 15 archive tests/10 calibrations reused; zero model calls')
