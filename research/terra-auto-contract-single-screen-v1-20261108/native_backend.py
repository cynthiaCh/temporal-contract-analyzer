"""Five fixed slots; no pre-run, retry, scorer, maintenance or optimizer."""
import json,hashlib,os,shutil,subprocess,time,signal,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent.parent
BINARY=Path('/home/sribd/.vscode/extensions/openai.chatgpt-26.51021.22027-linux-x64/bin/linux-x86_64/codex')
DISABLE=['code_mode','apps','plugins','multi_agent','browser_use','computer_use','sleep_tool','tool_suggest']
def read(p):return json.loads(Path(p).read_text())
def save(p,d):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(b):return hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
def hashes(root):return {str(p.relative_to(root)):sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
def command(call,folder,mode,copy_auth=True,meter=None):
 work=folder/'workspace';out=folder/'cli-output';profile=OUT/'.runtime'/call
 for p in [work,out,profile]:p.mkdir(parents=True,exist_ok=True)
 profile.chmod(0o700)
 if copy_auth:
  for n in ['auth.json']:
   p=Path.home()/'.codex'/n
   if p.is_file():shutil.copyfile(p,profile/n);(profile/n).chmod(0o600)
 shutil.copyfile(OUT/'research-config.toml',profile/'config.toml')
 if (OUT/'models-cache.snapshot.json').exists():shutil.copyfile(OUT/'models-cache.snapshot.json',profile/'models_cache.json')
 save(folder/'configuration-before.json',{'research_config_sha256':sha((profile/'config.toml').read_bytes()),'research_config_text':(profile/'config.toml').read_text(),'global_config':global_snapshot(),'model_catalog_sha256':sha((profile/'models_cache.json').read_bytes()) if (profile/'models_cache.json').exists() else None})
 hooks={'hooks':{e:[{'hooks':[{'type':'command','command':'/usr/bin/python3 /request_guard.py','timeout':10}]}] for e in ['PreModelRequest','PostModelRequest','PreToolUse','PermissionRequest']}}
 save(profile/'hooks.json',hooks);save(folder/'hooks.json',hooks)
 ns=['bwrap','--die-with-parent','--new-session','--unshare-user','--unshare-pid','--unshare-ipc','--unshare-uts','--cap-drop','ALL','--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--symlink','usr/bin','/bin','--symlink','usr/sbin','/sbin','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/home/agent','--dir','/etc','--ro-bind','/etc/resolv.conf','/etc/resolv.conf','--ro-bind','/etc/ssl','/etc/ssl','--ro-bind',str(BINARY.parent),'/opt','--bind',str(profile),'/home/agent/.codex','--ro-bind',str(work),'/workspace','--bind',str(out),'/output','--ro-bind',str(OUT/'request_guard.py'),'/request_guard.py','--ro-bind',str(OUT/('reflection.schema.json' if mode=='reflection' else 'extraction.schema.json')),'/format.json','--bind',str(meter or OUT/'request-meter'),'/meter','--chdir','/workspace','--setenv','HOME','/home/agent','--setenv','CODEX_HOME','/home/agent/.codex','--setenv','PATH','/usr/bin:/bin:/opt','--setenv','LANG','C.UTF-8']
 for k in sorted(os.environ):
  if k not in ['HOME','CODEX_HOME','PATH','LANG']:ns+=['--unsetenv',k]
 for k in ['HTTP_PROXY','HTTPS_PROXY','NO_PROXY','http_proxy','https_proxy','no_proxy']:
  if k in os.environ:ns+=['--setenv',k,os.environ[k]]
 ns+=['--setenv','DIAG_CALL_ID',call,'--']
 cmd=ns+['/opt/codex','exec','--ignore-rules','--ephemeral','--json','--color','never','--skip-git-repo-check','--sandbox','read-only','-c','approval_policy="never"','-m','gpt-6-sol','-c','model_reasoning_effort="low"','-c','web_search="disabled"','-c','service_tier="priority"','-c','model_provider="experiment_no_retry"','-c','model_providers.experiment_no_retry.name="OpenAI"','-c','model_providers.experiment_no_retry.wire_api="responses"','-c','model_providers.experiment_no_retry.requires_openai_auth=true','-c','model_providers.experiment_no_retry.request_max_retries=0','-c','model_providers.experiment_no_retry.stream_max_retries=0','--dangerously-bypass-hook-trust','--output-schema','/format.json']
 for feature in DISABLE+(['shell_tool','code_mode_host'] if mode=='reflection' else []):cmd+=['--disable',feature]
 if mode=='extraction':cmd+=['--enable','code_mode_host','--enable','shell_tool']
 return cmd+['-C','/workspace','-o','/output/answer.json','-']

def global_snapshot():
 p=Path.home()/'.codex/config.toml'
 return {'sha256':sha(p.read_bytes()),'mtime':p.stat().st_mtime,'fields':[x for x in p.read_text().splitlines() if x.startswith(('model =','model_reasoning_effort','service_tier'))]}
