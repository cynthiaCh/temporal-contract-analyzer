"""Real command replay and isolation/accounting probes. Zero model requests."""
import importlib.util,json,shlex,shutil,subprocess,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parent.parent;OLD=R/'research/contract-repair-frozen-batch-v1-20261108'
spec=importlib.util.spec_from_file_location('small_runner',O/'runner.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
save=runner.save
def main():
 assert not (O/'offline-validation.json').exists()
 results=[]
 # Replay both *exact* previously rejected commands against their original file versions.
 for old_slot,cid in [('x01','download-polling-restoration-explicit-react18'),('x02','audit-commit-attribution-vanilla')]:
  folder=O/'offline-v3'/('legacy-'+old_slot);shutil.copytree(OLD/'materials'/cid/'candidate',folder/'workspace')
  (folder/'workspace/outside-link').symlink_to('/etc/resolv.conf')
  call='legacy-'+old_slot;cmd=runner.command(call,folder,'extract');prefix=cmd[:cmd.index('--')+1]
  ledger=json.loads((OLD/'runs'/old_slot/'meter/ledger.json').read_text());event=next(e['event'] for e in ledger['events'] if e.get('denied'));actual_command=event['tool_input']['command']
  (folder/'replayed-command.txt').write_text(actual_command+'\n')
  body="""import json,subprocess,sys,hashlib
from pathlib import Path
sys.path.insert(0,'/')
from read_policy import allowed,read_command
import request_guard as guard
command=json.loads(sys.argv[1]);event={'hook_event_name':'PreToolUse','tool_name':'Bash','tool_input':{'command':command}}
assert read_command(event)
assert guard.account(event,Path('/meter'),sys.argv[2],terminate=False) is False
p=subprocess.run(['/bin/bash','-lc',command],capture_output=True,text=True,timeout=10)
assert p.returncode==0,p.stderr
sources=list(Path('/workspace/src').glob('*'))+[Path('/workspace/package.json')]
for source in sources:
 if source.is_file():
  lines=[x.strip() for x in source.read_text().splitlines() if len(x.strip())>=20]
  normalized=[__import__('re').sub(r'^\\s*\\d+\\s+','',x).strip() for x in p.stdout.splitlines()]
  assert all(x in normalized for x in lines),(source,lines)
assert not Path('/home/sribd').exists()
assert not Path('/workspace/oracle').exists()
assert not Path('/workspace/reference').exists()
assert not Path('/workspace/H.md').exists()
assert not Path('/workspace/../runs').exists()
negative=['cat /home/agent/.codex/auth.json','cat /meter/ledger.json','cat /output/answer.json','cat /workspace/../etc/resolv.conf','cat /etc/resolv.conf','cat /proc/1/root/etc/resolv.conf','cat outside-link','sed -i 1p src/controller.js','echo bad > src/controller.js','cat $(pwd)/README.md','for f in /etc/*; do nl -ba "$f"; done','for f in src/*; do rm "$f"; done','rg --pre python README.md','python3 -c "print(1)"']
assert all(not allowed(s) for s in negative),[(s,allowed(s)) for s in negative]
positive=['pwd && rg --files | head -200','for f in src/*.js; do printf "--- %s ---\\n" "$f"; sed -n 1,200p "$f"; done','nl -ba /workspace/package.json']
assert all(allowed(s) for s in positive),[(s,allowed(s)) for s in positive]
try:Path('/workspace/write-probe').write_text('bad');raise AssertionError('read-only failed')
except OSError:pass
print(json.dumps({'command':command,'source_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources if p.is_file()},'source_body_complete':True,'negative_tests':negative,'positive_tests':positive,'namespace_hidden_sources':True,'candidate_read_only':True,'source_output':p.stdout if False else ''}))
print(subprocess.check_output(['/bin/bash','-lc',command],text=True))
"""
  check=subprocess.run(prefix+['/usr/bin/python3','-c',body,json.dumps(actual_command),call],capture_output=True,text=True,timeout=20)
  (folder/'replay.stdout.txt').write_text(check.stdout);(folder/'replay.stderr.txt').write_text(check.stderr);assert check.returncode==0,check.stderr
  source_hashes=runner.hashes(folder/'workspace');source_hashes.pop('outside-link')
  assert source_hashes==runner.hashes(OLD/'materials'/cid/'candidate')
  results.append({'label':call,'exact_old_command':actual_command,'exit_code':check.returncode,'all_original_body_lines_verified':True,'source_file_hashes_match':True,'out_of_bounds_and_mutation_rejected':True,'read_only_candidate':True})
  shutil.rmtree(O/'.runtime'/call)
 # Maintenance write scope and model/tool/runtime metadata, no API calls.
 folder=O/'offline-v3/repair';shutil.copytree(O/'materials'/runner.cases()[0]['case']/'candidate',folder/'workspace');cmd=runner.command('repair-probe',folder,'repair');prefix=cmd[:cmd.index('--')+1]
 body="from pathlib import Path\nimport subprocess\np=Path('/workspace/probe');p.write_text('ok');assert p.read_text()=='ok';p.unlink()\nassert not Path('/home/sribd').exists() and not Path('/workspace/oracle').exists()\nassert subprocess.check_output(['/runtime/node','--version'],text=True).strip()=='v16.20.2'\nprint('writable isolated candidate, immutable system, unavailable research/reference/other-slot paths: PASS')\n"
 check=subprocess.run(prefix+['/usr/bin/python3','-c',body],capture_output=True,text=True,timeout=20);(folder/'namespace.txt').write_text(check.stdout+check.stderr);assert check.returncode==0
 flags=[]
 for i,x in enumerate(cmd):
  if x in ['-c','--enable','--disable']:flags+=cmd[i:i+2]
 check=subprocess.run(prefix+['/opt/codex','features','list']+flags,capture_output=True,text=True,timeout=20);assert check.returncode==0;(folder/'features.txt').write_text(check.stdout)
 features={x.split()[0]:x.split()[-1]=='true' for x in check.stdout.splitlines() if x.strip()};assert features['code_mode_host'] and features['shell_tool'] and not any(features[k] for k in ['apps','plugins','multi_agent'])
 check=subprocess.run(prefix+['/opt/codex-code-mode-host','--help'],capture_output=True,text=True,timeout=20);assert check.returncode==0
 shutil.rmtree(O/'.runtime/repair-probe')
 # Synthetic requests, usage and failures: guard semantics preserved, full 24 cap tested.
 folder=O/'offline-v3/accounting';shutil.copytree(O/'materials'/runner.cases()[0]['case']/'candidate',folder/'workspace');cmd=runner.command('cap-test',folder,'repair');prefix=cmd[:cmd.index('--')+1]
 fake="""import json,subprocess
for i in range(24):
 subprocess.run(['/usr/bin/python3','/request_guard.py'],input=json.dumps({'hook_event_name':'PreModelRequest'}),text=True,check=True)
 subprocess.run(['/usr/bin/python3','/request_guard.py'],input=json.dumps({'hook_event_name':'PostModelRequest','status':'completed','token_usage':{'input_tokens':10,'output_tokens':2}}),text=True,check=True)
subprocess.run(['/usr/bin/python3','/request_guard.py'],input=json.dumps({'hook_event_name':'PreModelRequest'}),text=True)
open('/output/overcap','w').write('bad')
"""
 check=subprocess.run(prefix+['/bin/bash','-c','exec -a /opt/codex /usr/bin/python3 -c '+shlex.quote(fake)],capture_output=True,text=True,timeout=20)
 assert check.returncode!=0 and not (folder/'cli-output/overcap').exists();meter=runner.read(folder/'meter/ledger.json');assert meter['started']==meter['completed']==24 and meter['blocked_requests']==1
 posts=[e['event'] for e in meter['events'] if e['event'].get('hook_event_name')=='PostModelRequest'];assert sum(e['token_usage']['input_tokens'] for e in posts)==240
 shutil.rmtree(O/'.runtime/cap-test')
 # Real process-group timeout termination, using a local sleep fixture (not a model).
 start=time.monotonic();proc=subprocess.Popen(['/bin/sleep','5'],start_new_session=True)
 try:proc.wait(timeout=.1);raise AssertionError('fixture unexpectedly exited')
 except subprocess.TimeoutExpired:
  import os,signal
  os.killpg(proc.pid,signal.SIGKILL);proc.wait()
 assert proc.returncode!=0 and time.monotonic()-start<2
 save(O/'offline-validation.json',{'status':'PASS','model_calls':0,'exact_command_replays':results,'maintenance_namespace':'PASS','features':features,'backend_help':'PASS','request_cap_24_hard_kill_exit':check.returncode,'synthetic_accounting':{'started':24,'completed':24,'blocked':1,'input_tokens':240,'output_tokens':48,'not_real_usage':True},'timeout_process_group_fixture':'PASS','scope':'Filesystem namespace hides host research, scorer, reference patches and other runs. Extraction tool parser supports constrained read loops; extraction candidate is read-only. Administrative CLI profile/output/meter are per-slot, not shared. Cooperative execution boundary, not a proof against arbitrary adversarial code.'})
 print('Offline PASS: both exact old loops, source bytes, denied escapes/writes, tool backend, 24-request hard cap, usage and timeout. Model calls 0.')
if __name__=='__main__':main()
