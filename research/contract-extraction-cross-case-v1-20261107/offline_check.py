import json,shutil,subprocess,shlex
from pathlib import Path
from run import OUT,ROOT,BINARY,read,save,sha,hashes,command,global_snapshot
import request_guard as guard

def main():
 assert not (OUT/'requests.json').exists();d=OUT/'offline';d.mkdir();observations={}
 for case in ['C1','C3']:
  p=d/case;shutil.copytree(OUT/'materials'/case/'candidate',p/'workspace');meter=p/'fake-meter';call='offline-'+case;save(meter/'config.json',{'global_cap':1,'calls':{call:{'cap':1,'mode':'extraction'}}})
  cmd=command(call,p,'extraction',True,meter);prefix=cmd[:cmd.index('--')+1];args=[]
  for i,x in enumerate(cmd):
   if x in ['-c','--enable','--disable']:args+=cmd[i:i+2]
  feature=subprocess.run(prefix+['/opt/codex','features','list']+args,capture_output=True,text=True,timeout=20);assert feature.returncode==0,feature.stderr;(p/'effective-features.txt').write_text(feature.stdout)
  flags={x.split()[0]:x.split()[-1]=='true' for x in feature.stdout.splitlines() if x.strip()};assert flags['code_mode_host'] and flags['shell_tool'] and not flags['apps'] and not flags['plugins'] and not flags['multi_agent']
  host=subprocess.run(prefix+['/opt/codex-code-mode-host','--help'],capture_output=True,text=True,timeout=20);assert host.returncode==0
  source="import json,hashlib;from pathlib import Path;p=Path('/workspace');print(json.dumps({str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file()}));print(next((p/'src').glob('*.js')).read_text())"
  body=subprocess.run(prefix+['/usr/bin/python3','-c',source],capture_output=True,text=True,timeout=20);assert body.returncode==0;assert json.loads(body.stdout.splitlines()[0])==read(OUT/'source-and-exposure.json')['cases'][case]['candidate_files'];(p/'mounted-source-body.txt').write_text(body.stdout)
  test=subprocess.run(prefix+['/bin/sh','-c','test ! -e /home/sribd && test ! -e /proc/1/root/home/sribd && test ! -e /workspace/evaluation.csv && if echo bad > /workspace/package.json; then exit 9; fi'],capture_output=True,text=True,timeout=20);assert test.returncode==0
  fake="import subprocess,json;ev=lambda k:json.dumps({'hook_event_name':k,'status':'completed'});subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PreModelRequest'),text=True);subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PostModelRequest'),text=True);subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PreModelRequest'),text=True);open('/output/over-cap','w').write('bad')"
  kill=subprocess.run(prefix+['/bin/bash','-c','exec -a /opt/codex /usr/bin/python3 -c '+shlex.quote(fake)],capture_output=True,text=True,timeout=20);assert kill.returncode!=0 and not (p/'cli-output/over-cap').exists()
  observations[case]={'feature_flags':flags,'command':cmd,'research_config_sha256':sha((OUT/'.runtime'/call/'config.toml').read_bytes()),'model_catalog_sha256':sha((OUT/'.runtime'/call/'models_cache.json').read_bytes()),'hard_kill_exit':kill.returncode,'global_config':global_snapshot(),'limits':{'timeout':600,'per_slot_requests':12,'global_requests':49,'sessions':8,'report_characters':6000}}
  shutil.rmtree(OUT/'.runtime'/call)
 for label,cap in [('per-slot',12),('global',49)]:
  p=d/label;save(p/'config.json',{'global_cap':cap,'calls':{'test':{'cap':cap,'mode':'extraction'}}})
  for _ in range(cap):assert not guard.account({'hook_event_name':'PreModelRequest'},p,'test',False);assert not guard.account({'hook_event_name':'PostModelRequest','status':'completed'},p,'test',False)
  assert guard.account({'hook_event_name':'PreModelRequest'},p,'test',False)
 for cmd,expected in [('cat README.md',True),("sed -n '1,20p' README.md",True),('cat /home/agent/.codex/auth.json',False),('cat /proc/1/root/home/sribd/file',False),('node src/controller.js',False)]:assert guard.read_command({'tool_name':'Bash','tool_input':{'command':cmd}})==expected
 save(OUT/'environment-and-isolation.json',{'status':'PASS_OFFLINE_ONLY','observations':observations,'client_config_locked':True,'global_config_not_used_as_session_config':True,'server_routing_attested':False,'v2_historical_service_tier_origin':'unknown; previous mtime/copy-order evidence cannot establish causation','actual_model_read_proven':False,'first_formal_gate_required':True,'model_calls':0})
 save(OUT/'offline-validation.json',{'status':'PASS','model_calls':0,'read_backend_enabled':True,'read_only_and_research_unmounted':True,'request_time_output_limits_verified':True,'first_formal_gate_required':True})
 files=[p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'offline' not in p.parts and p.name!='initial-state.json']
 source=read(OUT/'source-and-exposure.json')['review_sources'];files+=[Path(p) for p in source]
 save(OUT/'protocol.json',{'model':'gpt-6-sol','effort':'low','service_tier':'priority','max_sessions':8,'per_slot_requests':12,'global_requests':49,'timeout_seconds':600,'report_character_limit':6000,'reflection_calls':0,'files':{str(p):sha(p.read_bytes()) for p in files},'cli_binary_sha256':sha(BINARY.read_bytes()),'host_binary_sha256':sha((BINARY.parent/'codex-code-mode-host').read_bytes()),'frozen_before_formal_calls':True})
 (OUT/'protocol.sha256').write_text(sha((OUT/'protocol.json').read_bytes())+'\n');print('OFFLINE_CONFIG_AND_SOURCE_PASS_ZERO_MODEL_CALLS')
if __name__=='__main__':main()
