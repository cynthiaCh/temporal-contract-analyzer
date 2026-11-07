"""No-model checks and freeze; never invokes a model endpoint."""
import subprocess,json,shlex,shutil
from pathlib import Path
from run import OUT,ROOT,BINARY,command,read,save,sha
import request_guard as guard

def main():
 assert not (OUT/'requests.json').exists();d=OUT/'offline';d.mkdir(exist_ok=True)
 for mode,cap in [('extraction',12),('reflection',1)]:
  p=d/mode;save(p/'config.json',{'global_cap':cap,'calls':{'test':{'cap':cap,'mode':mode}}})
  for _ in range(cap):
   assert not guard.account({'hook_event_name':'PreModelRequest'},p,'test',False)
   assert not guard.account({'hook_event_name':'PostModelRequest','status':'completed'},p,'test',False)
  assert guard.account({'hook_event_name':'PreModelRequest'},p,'test',False)
 for mode,cmd,allow in [('extraction','pwd && rg --files | head -80',True),('extraction',"nl -ba src/usePreparation.js; sed -n '1,40p' src/preparation-api.js",True),('extraction','cat /home/agent/.codex/auth.json',False),('extraction','node src/usePreparation.js',False),('extraction',"sed '1e id' src/usePreparation.js",False),('extraction','cat /proc/1/root/home/sribd/file',False),('extraction','cat src/a > /output/stolen',False),('reflection','cat src/a',False)]:
  e={'hook_event_name':'PreToolUse','tool_name':'Bash','tool_input':{'command':cmd}}
  assert (guard.read_command(e) and mode!='reflection')==allow,(cmd,allow)
 p=d/'failed-request';save(p/'config.json',{'global_cap':3,'calls':{'test':{'cap':3,'mode':'extraction'}}});guard.account({'hook_event_name':'PreModelRequest'},p,'test',False);guard.account({'hook_event_name':'PostModelRequest','status':'failed'},p,'test',False);assert guard.account({'hook_event_name':'PreModelRequest'},p,'test',False)
 p=d/'namespace';work=p/'workspace';work.mkdir(parents=True,exist_ok=True);(work/'example.txt').write_text('frozen')
 meter=d/'fake';save(meter/'config.json',{'global_cap':1,'calls':{'offline':{'cap':1,'mode':'extraction'}}})
 cmd=command('offline',p,'extraction',False,meter);prefix=cmd[:cmd.index('--')+1]
 check=subprocess.run(prefix+['/bin/sh','-c','test ! -e /home/sribd && test ! -e /proc/1/root/home/sribd && cat /workspace/example.txt && if echo bad > /workspace/example.txt; then exit 9; fi'],capture_output=True,text=True,timeout=20);assert check.returncode==0,check.stderr
 fake="import subprocess,json; ev=lambda k:json.dumps({'hook_event_name':k,'status':'completed'});subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PreModelRequest'),text=True);subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PostModelRequest'),text=True);subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PreModelRequest'),text=True);open('/output/over-cap','w').write('bad')"
 killed=subprocess.run(prefix+['/bin/bash','-c','exec -a /opt/codex /usr/bin/python3 -c '+shlex.quote(fake)],capture_output=True,text=True,timeout=20);assert killed.returncode!=0 and not (p/'cli-output/over-cap').exists()
 # Offline config parse and features only; no exec/prompt/model run.
 feature=subprocess.run(prefix+['/opt/codex','features','list','-c','model_provider="experiment_no_retry"','-c','model_providers.experiment_no_retry.name="OpenAI"','-c','model_providers.experiment_no_retry.wire_api="responses"','-c','model_providers.experiment_no_retry.requires_openai_auth=true','-c','model_providers.experiment_no_retry.request_max_retries=0','-c','model_providers.experiment_no_retry.stream_max_retries=0'],capture_output=True,text=True,timeout=20)
 (d/'features.stdout.txt').write_text(feature.stdout);(d/'features.stderr.txt').write_text(feature.stderr);assert feature.returncode==0,feature.stderr
 version=subprocess.run([str(BINARY),'--version'],capture_output=True,text=True,timeout=10)
 shutil.rmtree(OUT/'.runtime/offline')
 save(OUT/'offline-validation.json',{'status':'PASS','model_calls':0,'candidate_readonly':True,'research_not_mounted':True,'per_session_and_global_caps_tested':True,'no_retry_after_failed_request':True,'restricted_read_commands':True,'reflection_tool_free':True,'over_cap_fake_provider_killed':killed.returncode,'configuration_offline_parse':feature.returncode,'cli_version':version.stdout.strip(),'namespace_readonly_error':check.stderr})
 files=[OUT/n for n in ['PLAN.md','evaluation-v1.csv','scope-and-sources.json','contract_extraction_K0.md','prompt-template.md','extraction.schema.json','reflection.schema.json','schedule.json','request-meter/config.json','run.py','request_guard.py','offline_check.py']]+[p for p in (OUT/'materials').rglob('*') if p.is_file()]
 files += [Path(p) for p in read(OUT/'scope-and-sources.json')['source_files']]
 save(OUT/'protocol.json',{'status':'FROZEN_BEFORE_MODEL_CALLS','model':'gpt-6-sol','effort':'low','timeout_seconds':600,'top_level_session_cap':5,'extraction_request_cap':12,'reflection_request_cap':1,'global_request_cap':49,'automatic_retry':False,'output_character_cap':6000,'files':{str(p):sha(p.read_bytes()) for p in files},'cli_binary_sha256':sha(BINARY.read_bytes())})
 (OUT/'protocol.sha256').write_text(sha((OUT/'protocol.json').read_bytes())+'\n');print('OFFLINE_PASS_ZERO_MODEL_CALLS',flush=True)
if __name__=='__main__':main()
