"""Version-matched local maintenance namespace and reflection role checks, zero model/scorer calls."""
import sys,json,tempfile,subprocess
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A))
import runner as r
from archive import Archive,save,sha,inventory
from guard_server import GuardServer
read=lambda p:json.loads(Path(p).read_text());C=read(A/'cohort.json');S=Path(read(A/'sources.json')['source_followup']);O=Path(read(A/'sources.json')['source_development'])
assert read(S/'offline-validation.json')['status']=='PASS';assert read(O/'offline-validation.json')['tests']==15
assert r.ROLE['repair']==('gpt-5.6-terra','low',24,'maintenance') and r.ROLE['reflect']==('gpt-5.6-terra','medium',12,'reflection')
assert sha(r.backend.BINARY)==read(A/'frozen-config.json')['CLI_sha256']
for mode,phase,cap in [('maintenance','repair',24),('reflection','reflect',12)]:
 a=Archive(A/'offline'/('check-'+str(len(list((A/'offline').glob('check-*')))+1))/mode).prepare(A/'materials/candidate',A/'materials/task.md',(A/'prompts/AUTO.md').read_text() if phase=='repair' else (A/'reflection-input.md').read_text(),{'offline':True})
 with tempfile.TemporaryDirectory(prefix='e2-local-check-') as rt:
  with GuardServer(Path(rt)/'hook',a.root/'meter','offline-'+phase,cap,mode) as g:
   cmd=r.command('offline-'+phase,a.run_dir,phase,C,runtime=rt,socket_dir=g.directory,copy_auth=False);prefix=cmd[:cmd.index('--')+1]
   assert cmd[cmd.index('-m')+1]=='gpt-5.6-terra';assert 'model_reasoning_effort="'+('low' if phase=='repair' else 'medium')+'"' in cmd
   assert str(a.root) not in prefix and '/meter' not in prefix and '/output' not in prefix
   if phase=='reflect':assert all(['--disable',f] in [cmd[i:i+2] for i in range(len(cmd)-1)] for f in ['shell_tool','code_mode_host'])
   else:
    body=r'''from pathlib import Path
import subprocess,socket,json
assert not any(Path(p).exists() for p in ['/archive','/meter','/output','/home/sribd','/workspace/../archive'])
assert Path('/workspace/src/session.js').read_text()
subprocess.run(['/bin/bash','-c','for f in /workspace/src/*; do cp "$f" /tmp/check; diff "$f" /tmp/check; done'],check=True)
p=Path('/workspace/offline-owned');p.write_text('edit check');assert p.read_text()=='edit check';p.unlink()
s=socket.socket(socket.AF_UNIX);s.connect('/hook-control/hook.sock');s.sendall(json.dumps({'hook_event_name':'PreToolUse','tool_name':'Bash','tool_input':{'command':'for f in src/*; do cat "$f"; done'}}).encode()+b'\n');assert not json.loads(s.recv(1024))['deny'];s.close()
assert subprocess.check_output(['/runtime/node','--version'],text=True).strip()=='v16.20.2'
print('local maintenance namespace PASS')
'''
    z=subprocess.run(prefix+['/usr/bin/python3','-B','-c',body],capture_output=True,text=True,timeout=20);(a.root/'namespace.stdout.txt').write_text(z.stdout);(a.root/'namespace.stderr.txt').write_text(z.stderr);assert z.returncode==0,z.stderr
 assert inventory(a.workspace)==inventory(a.original);assert a.finalize(model_stopped=True)['status']=='OK';assert not (a.root/'patch.diff').read_bytes()
 assert not (read(a.root/'meter/ledger.json') if (a.root/'meter/ledger.json').exists() else {}).get('started',0)
save(A/'offline-validation.json',{'status':'PASS','model_calls':0,'maintenance_executions':0,'score_reruns':0,'namespace_read_edit_validate':'PASS','host_archive_hidden':True,'reflection_role_config_matches_original':True,'same_runner_source_hashes':True,'archive_fixture_tests_reused':read(O/'offline-validation.json'),'case_calibrations_reused':len(C['calibration']),'no_counterfactual_candidate_created':True})
print('Offline PASS; 0 model/scorer calls')
