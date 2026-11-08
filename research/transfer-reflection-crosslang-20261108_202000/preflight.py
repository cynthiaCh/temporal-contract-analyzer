import importlib.util,pathlib as P,json,subprocess,shutil,sys,hashlib,os,signal,time
sys.dont_write_bytecode=True
A=P.Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('current_runner',A/'runner.py');r=importlib.util.module_from_spec(sp);sp.loader.exec_module(r)
save=r.save;results=[]
for c in r.cases():
 d=A/'offline-final'/c['case'];shutil.copytree(A/'materials'/c['case']/'candidate',d/'workspace');call='offline-'+str(c['index']);cmd=r.command(call,d,'extract');prefix=cmd[:cmd.index('--')+1]
 body=r'''import subprocess,sys,re,json
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,'/')
from read_policy import allowed,read_command
import request_guard as guard
command='for f in /workspace/README.md /workspace/src/*; do echo "$f"; nl -ba "$f"; done'
e={'hook_event_name':'PreToolUse','tool_name':'Bash','tool_input':{'command':command}}
assert read_command(e) and not guard.account(e,'/meter',sys.argv[1],terminate=False)
p=subprocess.run(['/bin/bash','-lc',command],capture_output=True,text=True);assert p.returncode==0,p.stderr
normalized=[re.sub(r'^\s*\d+\s+','',x).strip() for x in p.stdout.splitlines()]
for f in Path('/workspace/src').glob('*'):
 if f.is_file():assert all(s.strip() in normalized for s in f.read_text().splitlines() if s.strip()),str(f)
assert all(not allowed(s) for s in ['cat /etc/passwd','cat /home/agent/.codex/auth.json','cat /meter/ledger.json','cat ../reference/a','echo x > src/a','for f in /etc/*; do cat "$f"; done','python3 -c "print(1)"'])
assert not Path('/home/sribd').exists() and not Path('/workspace/oracle').exists() and not Path('/workspace/reference').exists()
try:Path('/workspace/probe').write_text('x');raise AssertionError('writable')
except OSError:pass
print(p.stdout)
'''
 z=subprocess.run(prefix+['/usr/bin/python3','-B','-c',body,call],capture_output=True,text=True,timeout=25);(d/'body.stdout.txt').write_text(z.stdout);(d/'body.stderr.txt').write_text(z.stderr);assert z.returncode==0,z.stderr
 assert r.hashes(d/'workspace')==c['candidate_files']
 proofs=r.source_proof([{'type':'item.completed','item':{'type':'command_execution','exit_code':0,'aggregated_output':z.stdout}}],c);assert len(proofs)==sum(P.Path(k).suffix in ['.js','.py'] for k in c['candidate_files']);save(d/'source-body-proofs.json',proofs)
 results.append({'case':c['case'],'body_all_lines':True,'proof_files':len(proofs),'isolated_readonly':True,'ordinary_loop_guard':True})
 flags=[]
 for i,x in enumerate(cmd):
  if x in ['-c','--enable','--disable']:flags+=cmd[i:i+2]
 z=subprocess.run(prefix+['/opt/codex','features','list']+flags,capture_output=True,text=True,timeout=20);(d/'features.txt').write_text(z.stdout+z.stderr);assert z.returncode==0
 features={x.split()[0]:x.split()[-1]=='true' for x in z.stdout.splitlines() if x.strip()};assert features['code_mode_host'] and features['shell_tool'] and not any(features[k] for k in ['apps','plugins','multi_agent'])
 z=subprocess.run(prefix+['/opt/codex-code-mode-host','--help'],capture_output=True,text=True,timeout=20);(d/'host-help.txt').write_text(z.stdout+z.stderr);assert z.returncode==0
 shutil.rmtree(P.Path((A/'runtime-location.txt').read_text().strip())/'.runtime'/call)
# Recheck current hook cap, failed/cancelled request accounting; synthetic fixtures only.
sys.path.insert(0,str(A));import request_guard as g
for kind in ['cap','failure','cancelled']:
 d=A/'offline-final'/kind;save(d/'config.json',{'global_cap':24,'calls':{'fixture':{'cap':24,'mode':'maintenance'}}})
 for i in range(24 if kind=='cap' else 1):
  assert not g.account({'hook_event_name':'PreModelRequest'},d,'fixture',False)
  if kind!='cancelled':assert not g.account({'hook_event_name':'PostModelRequest','status':'completed' if kind=='cap' else 'failed','token_usage':{'input_tokens':10,'output_tokens':2}},d,'fixture',False)
 assert g.account({'hook_event_name':'PreModelRequest'},d,'fixture',False)
 s=r.read(d/'ledger.json');assert s['started']==(24 if kind=='cap' else 1)
# process group timeout local fixture
p=subprocess.Popen(['/bin/sleep','5'],start_new_session=True)
try:p.wait(timeout=.05);raise AssertionError('early exit')
except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
# maintenance namespace writable and readback only independent workspace
c=r.cases()[0];d=A/'offline-final/write';shutil.copytree(A/'materials'/c['case']/'candidate',d/'workspace');cmd=r.command('offline-write',d,'repair');prefix=cmd[:cmd.index('--')+1]
z=subprocess.run(prefix+['/usr/bin/python3','-B','-c',"from pathlib import Path; p=Path('/workspace/write-probe'); p.write_text('ok'); assert p.read_text()=='ok'; p.unlink(); assert not Path('/home/sribd').exists(); print('PASS')"],capture_output=True,text=True,timeout=20);(d/'namespace.txt').write_text(z.stdout+z.stderr);assert z.returncode==0
shutil.rmtree(P.Path((A/'runtime-location.txt').read_text().strip())/'.runtime/offline-write')
cli=r.backend.BINARY
models=r.read(A/'models-cache.snapshot.json');entries=models.get('models',[]) if isinstance(models,dict) else models
info=[]
for model in ['gpt-6-sol','gpt-5.6-terra']:
 found=[e for e in entries if e.get('slug',e.get('id'))==model];assert found,model;info.extend(found)
save(A/'catalog-role-metadata.json',info)
save(A/'frozen-config.json',{'extraction':{'model':'gpt-6-sol','effort':'low','requests':12},'maintenance':{'model':'gpt-5.6-terra','effort':'medium','requests':24},'reflection':{'model':'gpt-5.6-terra','effort':'medium','requests':12},'session_seconds':600,'global_cap':324,'sessions_max':15,'concurrency':1,'service_tier':'priority','CLI':str(cli),'CLI_sha256':r.sha(cli),'CLI_version':subprocess.check_output([str(cli),'--version'],text=True).strip(),'python_actual':subprocess.check_output(['python3','--version'],text=True).strip(),'node_actual':subprocess.check_output([c['node'],'--version'],text=True).strip(),'global_config':r.backend.global_snapshot(),'runtime':(A/'runtime-location.txt').read_text().strip(),'server_route_attested':False,'effort_observability':'CLI/config declaration; hook model checked; server effort and route not independently attested','models_catalog':'local cached catalog, not a live model probe','stdout_cap_bytes':16777216,'report_max_characters':6000,'unknown_usage':'null, never imputed zero; cached/reasoning are subsets'})
save(A/'offline-validation.json',{'status':'PASS','AI_assisted':True,'human_approval':False,'real_model_requests':0,'source_reading':results,'features':features,'code_mode_host_help':'PASS','synthetic_accounting_cap_failure_cancelled':'PASS','timeout_fixture':'PASS','maintenance_namespace':'PASS','scope':'filesystem namespace hides task standards/evaluation/reference/history/other sessions; cooperative CLI boundary, not adversarial proof','historical_read_loops':'unchanged read_policy hash and prior-offline-validation.json; current ordinary read loop also executed for both languages'})
print('M1 TOOL PREFLIGHT PASS; zero model calls')
