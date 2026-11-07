"""Zero-model config/isolation/counting checks; actual read proof is formal slot 1."""
import subprocess,shutil,json,shlex
from pathlib import Path
from run import OUT,ROOT,BINARY,read,save,sha,hashes,command
import request_guard as guard

def options(cmd):
 out=[];i=cmd.index('/opt/codex')+2
 while i<len(cmd):
  if cmd[i] in ['-c','--enable','--disable']:out+=cmd[i:i+2];i+=2
  else:i+=1
 return out

def main():
 assert not (OUT/'requests.json').exists();d=OUT/'offline';d.mkdir()
 for mode,cap in [('extraction',12),('reflection',1)]:
  p=d/mode;save(p/'config.json',{'global_cap':cap,'calls':{'test':{'cap':cap,'mode':mode}}})
  for _ in range(cap):
   assert not guard.account({'hook_event_name':'PreModelRequest'},p,'test',False);assert not guard.account({'hook_event_name':'PostModelRequest','status':'completed'},p,'test',False)
  assert guard.account({'hook_event_name':'PreModelRequest'},p,'test',False)
 p=d/'global';save(p/'config.json',{'global_cap':1,'calls':{x:{'cap':12,'mode':'extraction'} for x in ['a','b']}});assert not guard.account({'hook_event_name':'PreModelRequest'},p,'a',False);assert not guard.account({'hook_event_name':'PostModelRequest','status':'completed'},p,'a',False);assert guard.account({'hook_event_name':'PreModelRequest'},p,'b',False)
 p=d/'no-retry';save(p/'config.json',{'global_cap':3,'calls':{'test':{'cap':3,'mode':'extraction'}}});guard.account({'hook_event_name':'PreModelRequest'},p,'test',False);guard.account({'hook_event_name':'PostModelRequest','status':'failed'},p,'test',False);assert guard.account({'hook_event_name':'PreModelRequest'},p,'test',False)
 for cmd,ok in [('pwd && rg --files | head -80',True),("nl -ba src/usePreparation.js; sed -n '1,40p' src/preparation-api.js",True),('cat /home/agent/.codex/auth.json',False),('cat /proc/1/root/home/sribd/file',False),('node src/usePreparation.js',False)]:assert guard.read_command({'tool_name':'Bash','tool_input':{'command':cmd}})==ok
 effective={};checks={}
 for mode in ['extraction','reflection']:
  call='offline-'+mode;p=d/mode/'namespace';p.mkdir(parents=True)
  if mode=='extraction':shutil.copytree(OUT/'materials/candidate',p/'workspace')
  meter=d/mode/'fake-meter';save(meter/'config.json',{'global_cap':1,'calls':{call:{'cap':1,'mode':mode}}})
  cmd=command(call,p,mode,True,meter);prefix=cmd[:cmd.index('--')+1]
  f=subprocess.run(prefix+['/opt/codex','features','list']+options(cmd),capture_output=True,text=True,timeout=20)
  (p/'effective-features.txt').write_text(f.stdout);(p/'effective-features.stderr.txt').write_text(f.stderr);assert f.returncode==0,f.stderr
  features={x.split()[0]:x.split()[-1]=='true' for x in f.stdout.splitlines() if x.strip()}
  assert features['code_mode_host']==(mode=='extraction') and features['shell_tool']==(mode=='extraction')
  assert not features['code_mode'] and not features['apps'] and not features['plugins'] and not features['multi_agent']
  host=subprocess.run(prefix+['/opt/codex-code-mode-host','--help'],capture_output=True,text=True,timeout=20);assert host.returncode==0; (p/'host-help.txt').write_text(host.stdout)
  if mode=='extraction':
   script="import hashlib,json;from pathlib import Path;r=Path('/workspace');print(json.dumps({str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in r.rglob('*') if p.is_file()},sort_keys=True));print((r/'src/usePreparation.js').read_text())"
   mounted=subprocess.run(prefix+['/usr/bin/python3','-c',script],capture_output=True,text=True,timeout=20);assert mounted.returncode==0
   assert json.loads(mounted.stdout.splitlines()[0])==read(OUT/'scope-and-sources.json')['candidate_files'];(p/'offline-mounted-source.txt').write_text(mounted.stdout)
   isolate=subprocess.run(prefix+['/bin/sh','-c','test ! -e /home/sribd && test ! -e /proc/1/root/home/sribd && test ! -e /workspace/evaluation-v1.csv && if echo bad > /workspace/src/usePreparation.js; then exit 9; fi'],capture_output=True,text=True,timeout=20);assert isolate.returncode==0
   (p/'readonly.stderr.txt').write_text(isolate.stderr)
   fake="import subprocess,json;ev=lambda k:json.dumps({'hook_event_name':k,'status':'completed'});subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PreModelRequest'),text=True);subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PostModelRequest'),text=True);subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PreModelRequest'),text=True);open('/output/over-cap','w').write('bad')"
   killed=subprocess.run(prefix+['/bin/bash','-c','exec -a /opt/codex /usr/bin/python3 -c '+shlex.quote(fake)],capture_output=True,text=True,timeout=20);assert killed.returncode!=0 and not (p/'cli-output/over-cap').exists()
   checks['hard_cap_kill']=killed.returncode
  else:
   deny={'hook_event_name':'PreToolUse','tool_name':'Bash','tool_input':{'command':'cat src/x'}};assert guard.account(deny,meter,call,False)
  effective[mode]={'features':features,'argv':cmd,'configuration_sha256':sha((OUT/'.runtime'/call/'config.toml').read_bytes()),'host_sha256':sha((BINARY.parent/'codex-code-mode-host').read_bytes())}
  shutil.rmtree(OUT/'.runtime'/call)
 v1=OUT.parent/'contract-extraction-evolution-u2-v1-20261107'
 unchanged=['evaluation-v1.csv','scope-and-sources.json','contract_extraction_K0.md','prompt-template.md','extraction.schema.json','reflection.schema.json','request_guard.py','request-meter/config.json']
 for n in unchanged:assert (OUT/n).read_bytes()==(v1/n).read_bytes(),n
 assert hashes(OUT/'materials/candidate')==hashes(v1/'materials/candidate')
 save(OUT/'environment-check.json',{'model_calls':0,'exact_cli_config_effective':effective,'candidate_readonly':True,'mounted_source_hashes_match':True,'research_not_mounted':True,'v1_reused_files_byte_identical':unchanged,'timeout_seconds':600,'global_request_cap':49,'checks':checks,'limitation':'offline checks prove mount/config/binary and counter properties only, not model tool success; formal k0-1 execution gate required','configuration_reference':'https://learn.chatgpt.com/docs/config-file/config-reference'})
 save(OUT/'offline-validation.json',{'status':'PASS','model_calls':0,'code_mode_host_enabled_for_extraction':True,'shell_tool_enabled_for_extraction':True,'other_tools_not_expanded':True,'reflection_no_tools':True,'source_mount_and_boundaries_checked':True,'actual_model_reading_proven':False,'first_formal_slot_gate_required':True})
 files=[OUT/n for n in ['PLAN.md','evaluation-v1.csv','scope-and-sources.json','contract_extraction_K0.md','prompt-template.md','extraction.schema.json','reflection.schema.json','schedule.json','request-meter/config.json','run.py','request_guard.py','offline_check.py','execution_gate.py','config-v1-v2.diff','config-changes.json']]+[p for p in (OUT/'materials').rglob('*') if p.is_file()]
 files += [Path(n) for n in read(OUT/'scope-and-sources.json')['source_files']]
 save(OUT/'protocol.json',{'status':'FROZEN_BEFORE_MODEL_CALLS','model':'gpt-6-sol','effort':'low','timeout_seconds':600,'top_level_session_cap':5,'extraction_request_cap':12,'reflection_request_cap':1,'global_request_cap':49,'automatic_retry':False,'output_character_cap':6000,'files':{str(p):sha(p.read_bytes()) for p in files},'cli_binary_sha256':sha(BINARY.read_bytes()),'host_binary_sha256':sha((BINARY.parent/'codex-code-mode-host').read_bytes())})
 (OUT/'protocol.sha256').write_text(sha((OUT/'protocol.json').read_bytes())+'\n');print('OFFLINE_PASS_NO_MODEL_REQUESTS')
if __name__=='__main__':main()
