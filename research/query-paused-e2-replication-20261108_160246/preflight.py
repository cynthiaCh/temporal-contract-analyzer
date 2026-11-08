"""Temporary tiny candidates, fake model events, explicit fake score callback; no model or case scorer."""
import sys,json,tempfile,subprocess,shutil,time
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A))
import runner as r
from archive import Archive,inventory,digest,save,sha
from guard_server import GuardServer
from guard_client import forward
read=lambda p:json.loads(Path(p).read_text())
C=read(A/'cohort.json');S=Path(read(A/'sources.json')['sole_source']);checks=[]
assert (A/'prompts/AUTO_EXP.md').read_bytes()==(A/'prompts/AUTO.md').read_bytes()+b'\n\n'+(A/'NEW_EXPERIENCE.md').read_bytes()
assert sha(A/'NEW_EXPERIENCE.md')=='85c058e4065322155ac3ae3a8486df020da62745c3c64f25db5fd1b7570904c1'
assert r.ROLE['repair']==('gpt-5.6-terra','low',24,'maintenance')
for n,meta in read(A/'sources.json')['reuse'].items():assert sha(A/n)==meta['sha256']
assert read(S/'offline-validation.json')['status']=='PASS';assert read(S/'offline-validation.json')['archive_fixture_tests_reused']['tests']==15
start=time.monotonic()
with tempfile.TemporaryDirectory(prefix='e2-replication-offline-') as tmp:
 root=Path(tmp);cand=root/'tiny';(cand/'src').mkdir(parents=True);(cand/'src/main.js').write_text('export const value = 1;\n');(cand/'remove.txt').write_text('old\n');task=root/'task.md';task.write_text('local fixture, not an experiment task\n');original=inventory(cand)
 def build(body,post=True):
  def factory(a,runtime,guard):
   sock=str(guard.directory/'hook.sock')
   assert not forward({'hook_event_name':'PreModelRequest','model':'gpt-5.6-terra'},sock)['deny']
   if post:assert not forward({'hook_event_name':'PostModelRequest','model':'gpt-5.6-terra','status':'completed','token_usage':{'input_tokens':2,'output_tokens':1}},sock)['deny']
   return [sys.executable,'-B','-u','-c',body]
  return factory
 end="\nimport json\nprint(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':json.dumps({'report':'LOCAL FAKE EVENT ONLY'})}}))\nprint(json.dumps({'type':'turn.completed'}))\n"
 def fake_score(final,out):
  assert final.name=='final-candidate' and 'archive' in final.parts
  save(out/'fake-score.json',{'fixture_only':True,'verdict':'FAKE_NOT_A_CASE_SCORE'});return {'fixture_only':True,'verdict':'FAKE_NOT_A_CASE_SCORE'}
 for name,body in [('unchanged',''),('change_add_delete',"from pathlib import Path\nPath('src/main.js').write_text('export const value = 2;\\n')\nPath('remove.txt').unlink()\nPath('new.txt').write_text('new\\n')\n")]:
  rec=r.session({'slot':name,'phase':'repair','condition':'AUTO'},'FAKE LOCAL FIXTURE',case={'node':C['node']},candidate=cand,task=task,config={'seconds_per_session':2},run_dir=root/name,command_factory=build(body+end),score_fn=fake_score)
  p=root/name/'archive';assert rec['offline_fixture'] and rec['archive_status']['status']=='OK' and rec['scored_candidate_unchanged']
  assert inventory(cand)==original==inventory(p/'input/original');assert inventory(p/'final-candidate')==inventory(root/name/'workspace')
  diff=read(p/'diff-result.json');assert diff['exit_code']==(0 if name=='unchanged' else 1)
  if name=='unchanged':assert not (p/'patch.diff').read_bytes()
  else:
   changes=read(p/'file-changes.json');assert changes['added']==['new.txt'] and changes['deleted']==['remove.txt'] and changes['changed']==['src/main.js']
   applied=root/'apply';shutil.copytree(cand,applied);z=subprocess.run(['patch','--batch','-p1','-d',str(applied),'-i',str(p/'patch.diff')],capture_output=True,text=True);assert z.returncode==0,z.stderr;assert inventory(applied)==inventory(p/'final-candidate')
  checks.append(name+' snapshot/diff/fake-score handoff PASS')
 rec=r.session({'slot':'timeout','phase':'repair'},'FAKE',case={'node':C['node']},candidate=cand,task=task,config={'seconds_per_session':.25},run_dir=root/'timeout',command_factory=build("from pathlib import Path\nimport time,json,sys\nPath('src/main.js').write_text('export const value = 3;\\n')\nprint(json.dumps({'type':'item.completed','item':{'type':'command_execution','exit_code':0,'aggregated_output':'partial fake tool output'}}),flush=True)\nprint('fixture stderr',file=sys.stderr,flush=True)\ntime.sleep(3)",post=False))
 p=root/'timeout/archive';assert rec['failure_class']=='model_resource_limit' and rec['archive_status']['status']=='OK';assert (p/'patch.diff').stat().st_size and 'partial fake tool output' in (p/'events.jsonl').read_text();assert not read(p/'collection.json')['answer_present'];checks.append('timeout preserves partial traces/final candidate/diff PASS')
 def fail_diff(cmd,**kw):kw['stderr'].write(b'LOCAL FAKE DIFF FAILURE');return subprocess.CompletedProcess(cmd,2)
 rec=r.session({'slot':'diff-error','phase':'repair'},'FAKE',case={'node':C['node']},candidate=cand,task=task,config={'seconds_per_session':2},run_dir=root/'diff-error',command_factory=build("from pathlib import Path\nimport sys\nPath('src/main.js').write_text('export const value = 4;\\n')\nsys.exit(7)"),diff_runner=fail_diff)
 assert rec['exit_code']==7 and rec['failure_class']=='model_or_cli_abnormal_exit' and rec['archive_status']['status']=='ERROR';assert Path(rec['final_candidate']).exists();assert read(root/'diff-error/archive/diff-result.json')['exit_code']==2;checks.append('diff error retained without masking original exit/no model repair PASS')
 with GuardServer(root/'meter-ipc',root/'meter-data','fake-counter',2,'maintenance') as g:
  for i in range(2):
   assert not forward({'hook_event_name':'PreModelRequest','model':'gpt-5.6-terra'},str(g.directory/'hook.sock'))['deny'];assert not forward({'hook_event_name':'PostModelRequest','model':'gpt-5.6-terra','status':'completed','token_usage':{'input_tokens':1,'output_tokens':1}},str(g.directory/'hook.sock'))['deny']
  assert forward({'hook_event_name':'PreModelRequest','model':'gpt-5.6-terra'},str(g.directory/'hook.sock'))['deny']
  assert read(g.meter/'ledger.json')['started']==2 and read(g.meter/'ledger.json')['blocked_requests']==1
 checks.append('fake request counter exact cap and blocked dispatch PASS')
 a=Archive(root/'namespace').prepare(cand,task,'LOCAL',{'offline':True});before=inventory(a.workspace)
 with tempfile.TemporaryDirectory(prefix='e2-replication-namespace-') as rt:
  with GuardServer(Path(rt)/'hook',a.root/'meter','local-namespace',24,'maintenance') as g:
   cmd=r.command('local-namespace',a.run_dir,'repair',C,runtime=rt,socket_dir=g.directory,copy_auth=False);prefix=cmd[:cmd.index('--')+1]
   assert str(a.root) not in prefix and '/meter' not in prefix and '/output' not in prefix
   source_cmd=read(S/'runs/block-1-A/archive/command.json');assert cmd[cmd.index('--')+1:]==source_cmd[source_cmd.index('--')+1:]
   assert read(a.root/'configuration-before.json')['research_config_sha256']==read(S/'runs/block-1-A/archive/configuration-before.json')['research_config_sha256']
   assert cmd[cmd.index('-m')+1]=='gpt-5.6-terra' and 'model_reasoning_effort="low"' in cmd and 'model_providers.experiment_no_retry.request_max_retries=0' in cmd
   body=r'''from pathlib import Path
import subprocess,json,socket,hashlib
assert hashlib.sha256(Path('/home/agent/.codex/config.toml').read_bytes()).hexdigest()==EXPECTED_PROFILE_SHA
assert not Path('/home/sribd/.codex/config.toml').exists()
assert not any(Path(x).exists() for x in ['/archive','/output','/meter','/home/sribd','/workspace/../archive'])
assert Path('/workspace/src/main.js').read_text()
subprocess.run(['/bin/bash','-c','for f in /workspace/src/*; do cp "$f" /tmp/check; diff "$f" /tmp/check; done'],check=True)
p=Path('/workspace/local-owned');p.write_text('write check');assert p.read_text()=='write check';p.unlink()
s=socket.socket(socket.AF_UNIX);s.connect('/hook-control/hook.sock');s.sendall(json.dumps({'hook_event_name':'PreToolUse','tool_name':'Bash','tool_input':{'command':'for f in src/*; do cat "$f"; done'}}).encode()+b'\n');assert not json.loads(s.recv(1024))['deny'];s.close()
assert subprocess.check_output(['/runtime/node','--version'],text=True).strip()=='v16.20.2'
print('namespace read/edit/validate; archives hidden; legal shell tools PASS')
'''
   body=body.replace('EXPECTED_PROFILE_SHA',repr(sha(A/'research-config.toml')))
   z=subprocess.run(prefix+['/usr/bin/python3','-B','-c',body],capture_output=True,text=True,timeout=20);assert z.returncode==0,z.stderr
   assert inventory(a.workspace)==before;assert not read(a.root/'meter/ledger.json').get('started',0)
 assert a.finalize(model_stopped=True)['status']=='OK';checks.append('native maintenance namespace/read/edit/node/host archive isolation PASS')
assert all(sha(A/n)==meta['sha256'] for n,meta in read(A/'sources.json')['reuse'].items())
host=read(A/'host-config-isolation.json');host.update(proof_pending=False,offline_proof='PASS',isolated_profile_matches_source=True,complete_CLI_tail_matches_source=True,host_global_config_inaccessible=True,all_other_historical_protected_hashes_match=True);save(A/'host-config-isolation.json',host)
save(A/'offline-validation.json',{'status':'PASS','checks':checks,'seconds':time.monotonic()-start,'experiment_model_calls':0,'maintenance_executions':0,'real_case_score_calls':0,'real_case_score_reruns':0,'local_fake_events_not_real_model_usage':True,'fake_score_callback_not_oracle':True,'temporary_tiny_candidates_outside_repository':True,'source_archive_tests_reused':read(S/'offline-validation.json')['archive_fixture_tests_reused'],'source_case_calibrations_reused':len(C['calibration']),'prompt_append_byte_exact':True,'E2_unmodified':True,'source_runner_modules_byte_identical':True,'native_service_preprobe':False})
print('PASS',len(checks),'offline checks; 0 real model/scorer calls')
