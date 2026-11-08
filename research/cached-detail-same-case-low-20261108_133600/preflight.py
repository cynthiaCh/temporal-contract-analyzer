import sys,json,shutil,subprocess,tempfile
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A))
import runner as r
from archive import Archive,save,sha,inventory
from guard_server import GuardServer
C=json.loads((A/'cohort.json').read_text())
a=Archive(A/'offline/current-case-v2').prepare(A/'materials/candidate',A/'materials/task.md',(A/'prompts/extraction.md').read_text(),{'offline':True})
with tempfile.TemporaryDirectory(prefix='detail-preflight-') as rt:
 with GuardServer(Path(rt)/'hook',a.root/'meter','offline-case',12,'extraction') as g:
  cmd=r.command('offline-case',a.run_dir,'extract',C,runtime=rt,socket_dir=g.directory,copy_auth=False);prefix=cmd[:cmd.index('--')+1]
  body=r'''from pathlib import Path
import sys,subprocess,json,re,socket
sys.dont_write_bytecode=True;sys.path.insert(0,'/')
from read_policy import allowed
command='for f in /workspace/README.md /workspace/src/*; do echo "$f"; nl -ba "$f"; done'
assert allowed(command)
s=socket.socket(socket.AF_UNIX);s.connect('/hook-control/hook.sock');s.sendall(json.dumps({'hook_event_name':'PreToolUse','tool_name':'Bash','tool_input':{'command':command}}).encode()+b'\n');assert not json.loads(s.recv(1024))['deny'];s.close()
p=subprocess.run(['/bin/bash','-lc',command],capture_output=True,text=True);assert p.returncode==0
normalized=[re.sub(r'^\s*\d+\s+','',s).strip() for s in p.stdout.splitlines()]
for f in Path('/workspace').rglob('*'):
 if f.suffix in ['.md','.js'] and f.is_file():assert all(s.strip() in normalized for s in f.read_text().splitlines() if s.strip())
assert not Path('/archive').exists() and not Path('/meter').exists() and not Path('/output').exists() and not Path('/home/sribd').exists()
try:Path('/workspace/probe').write_text('x');raise AssertionError('writable extraction')
except OSError:pass
print(p.stdout)
'''
  z=subprocess.run(prefix+['/usr/bin/python3','-B','-c',body],capture_output=True,text=True,timeout=20);(a.root/'body.stdout.txt').write_text(z.stdout);(a.root/'body.stderr.txt').write_text(z.stderr);assert z.returncode==0,z.stderr
  proofs=r.source_proof([{'type':'item.completed','item':{'type':'command_execution','exit_code':0,'aggregated_output':z.stdout}}],a.original);assert len(proofs)==len(list(a.original.rglob('*.js')))
  save(a.root/'source-body-proofs.json',proofs)
  flags=[]
  for i,x in enumerate(cmd):
   if x in ['-c','--enable','--disable']:flags+=cmd[i:i+2]
  z=subprocess.run(prefix+['/opt/codex','features','list']+flags,capture_output=True,text=True,timeout=20);(a.root/'features.txt').write_text(z.stdout+z.stderr);assert z.returncode==0
  features={x.split()[0]:x.split()[-1]=='true' for x in z.stdout.splitlines() if x.strip()};assert features['code_mode_host'] and features['shell_tool'] and not any(features[x] for x in ['apps','plugins','multi_agent'])
  z=subprocess.run(prefix+['/opt/codex-code-mode-host','--help'],capture_output=True,text=True,timeout=20);assert z.returncode==0
  shutil.rmtree(Path(rt)/'.runtime')
# Frozen local catalog metadata: no service request/probe.
models=json.loads((A/'models-cache.snapshot.json').read_text())['models']
for model,effort in [('gpt-6-sol','low'),('gpt-5.6-terra','low'),('gpt-5.6-terra','medium')]:assert any(m['slug']==model and effort in [q['effort'] for q in m['supported_reasoning_levels']] for m in models)
save(A/'current-case-preflight.json',{'status':'PASS','AI_assisted':True,'independent_human_approval':False,'model_requests':0,'body_all_source_lines_verified':True,'source_proof_files':len(proofs),'extraction_readonly':True,'host_archive_hidden':True,'hook_RPC_body_read':'PASS','features':features,'native_code_mode_host_help':'PASS','maintenance_low_command_verified_by':'test_offline.py','policy_basis':'policy-review.md'})
save(A/'frozen-config.json',{'roles':r.ROLE,'session_seconds':600,'max_sessions':12,'max_underlying_requests':264,'concurrency':1,'service_tier':'priority','CLI_binary':str(r.backend.BINARY),'CLI_sha256':sha(r.backend.BINARY),'CLI_version':subprocess.check_output([str(r.backend.BINARY),'--version'],text=True).strip(),'node_actual':subprocess.check_output([C['node'],'--version'],text=True).strip(),'node_declared_in_manifest':'v16.20.2','global_config':r.backend.global_snapshot(),'server_model_route_independently_attested':False,'effort_observed':'CLI/config declarations only; hook model will be checked on actual requests','artifact_ownership':'fixed Python runner, outside actor workspace','max_stdout_bytes':16777216,'max_report_characters':6000,'same_case_development':True,'independent_generalization':False})
print('Current-case zero-model preflight PASS')
