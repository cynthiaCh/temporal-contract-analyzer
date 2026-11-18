"""Reused native CLI namespace; host archives are never mounted into the actor."""
import json,hashlib,os,shutil,subprocess,time,signal,sys
from pathlib import Path
from model_settings import resolve_profile, validate_settings
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent.parent
BINARY=None  # Supplied explicitly by the prepared, hash-bound protocol.
DISABLE=['code_mode','apps','plugins','multi_agent','browser_use','computer_use','sleep_tool','tool_suggest',
 'goals','view_image','multi_agent_v2','request_permissions_tool','runtime_agent_instances','default_mode_request_user_input']
def read(p):return json.loads(Path(p).read_text())
def save(p,d):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(b):return hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
def hashes(root):return {str(p.relative_to(root)):sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
def provider_catalog(settings,readonly_no_tools=False,readonly_tools=False):
 if settings['model']!='deepseek-flash' or settings['provider'].get('name')!='DeepSeek':return None
 # Official DeepSeek catalog snapshot; capability reductions match this sandbox.
 data=read(OUT/'deepseek-model-catalog.json')
 model=next(m for m in data['models'] if m['slug']==settings['model'])
 model.update(input_modalities=['text'],supports_image_detail_original=False,multi_agent_version=None,
              experimental_supported_tools=[],supports_search_tool=False)
 if readonly_no_tools or readonly_tools:model['apply_patch_tool_type']=None
 return dict(models=[model])

def command(call,folder,mode,copy_auth=True,meter=None,*,runtime=None,socket_dir=None,settings=None,readonly_no_tools=False,readonly_tools=False):
 settings=validate_settings(settings or resolve_profile());provider=settings['provider']
 if BINARY is None:raise ValueError('explicit prepared Codex binary required')
 if runtime is None or socket_dir is None:raise ValueError('explicit external runtime and hook endpoint required')
 work=folder/'workspace';archive=folder/'archive';profile=Path(runtime)/'.runtime'/call
 for p in [work,profile]:p.mkdir(parents=True,exist_ok=True)
 profile.chmod(0o700)
 if copy_auth and provider['requires_openai_auth']:
  for n in ['auth.json']:
   p=Path.home()/'.codex'/n
   if p.is_file():shutil.copyfile(p,profile/n);(profile/n).chmod(0o600)
 shutil.copyfile(OUT/'research-config.toml',profile/'config.toml')
 if (OUT/'models-cache.snapshot.json').exists():shutil.copyfile(OUT/'models-cache.snapshot.json',profile/'models_cache.json')
 catalog=provider_catalog(settings,readonly_no_tools,readonly_tools)
 if readonly_no_tools and not catalog:raise ValueError('No-tool model catalog has not been verified for this provider')
 if catalog:save(profile/'models.json',catalog)
 catalog_path=profile/('models.json' if catalog else 'models_cache.json')
 save(archive/'configuration-before.json',{'research_config_sha256':sha((profile/'config.toml').read_bytes()),'research_config_text':(profile/'config.toml').read_text(),'global_config':global_snapshot(),'model_catalog_sha256':sha(catalog_path.read_bytes()) if catalog_path.exists() else None})
 hooks={'hooks':{e:[{'hooks':[{'type':'command','command':'/usr/bin/python3 -B /guard_client.py','timeout':10}]}] for e in ['PreModelRequest','PostModelRequest','PreToolUse','PermissionRequest']}}
 save(profile/'hooks.json',hooks);save(archive/'hooks.json',hooks)
 ns=['bwrap','--die-with-parent','--new-session','--unshare-user','--unshare-pid','--unshare-ipc','--unshare-uts','--cap-drop','ALL','--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--symlink','usr/bin','/bin','--symlink','usr/sbin','/sbin','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/home/agent','--dir','/etc','--ro-bind','/etc/resolv.conf','/etc/resolv.conf','--ro-bind','/etc/ssl','/etc/ssl','--ro-bind',str(BINARY.parent),'/opt','--bind',str(profile),'/home/agent/.codex','--ro-bind',str(work),'/workspace','--ro-bind',str(OUT/'request_guard.py'),'/request_guard.py','--ro-bind',str(OUT/('reflection.schema.json' if mode=='reflection' else 'extraction.schema.json')),'/format.json','--ro-bind',str(socket_dir),'/hook-control','--ro-bind',str(OUT/'guard_client.py'),'/guard_client.py','--ro-bind',str(OUT/'read_policy.py'),'/read_policy.py','--chdir','/workspace','--setenv','HOME','/home/agent','--setenv','CODEX_HOME','/home/agent/.codex','--setenv','PATH','/usr/bin:/bin:/opt','--setenv','LANG','C.UTF-8']
 for k in sorted(os.environ):
  if k not in ['HOME','CODEX_HOME','PATH','LANG',provider.get('env_key')]:ns+=['--unsetenv',k]
 for k in ['HTTP_PROXY','HTTPS_PROXY','NO_PROXY','http_proxy','https_proxy','no_proxy']:
  if k in os.environ:ns+=['--setenv',k,os.environ[k]]
 ns+=['--setenv','DIAG_CALL_ID',call,'--']
 cmd=ns+['/opt/codex','exec','--ignore-rules','--ephemeral','--json','--color','never','--skip-git-repo-check','--sandbox','read-only','-c','approval_policy="never"','-m',settings['model'],'-c','web_search="disabled"','-c','model_provider="tempoevo_configured"','--dangerously-bypass-hook-trust','--output-schema','/format.json']
 if catalog:cmd+=['-c','model_catalog_json="/home/agent/.codex/models.json"']
 cmd+=['-c','tools.update_plan.enabled=false','-c','tools.experimental_request_user_input.enabled=false']
 for key in ['reasoning_effort','service_tier']:
  if settings[key] is not None:cmd+=['-c',('model_reasoning_effort' if key=='reasoning_effort' else key)+'='+json.dumps(settings[key])]
 for key,value in dict(provider,request_max_retries=0,stream_max_retries=0).items():
  cmd+=['-c','model_providers.tempoevo_configured.'+key+'='+json.dumps(value)]
 disabled=DISABLE+(['shell_tool','code_mode_host'] if mode=='reflection' else [])
 if readonly_no_tools:
  disabled+=['shell_tool','code_mode_host']
 for feature in dict.fromkeys(disabled):cmd+=['--disable',feature]
 if mode=='extraction' and not readonly_no_tools:cmd+=['--enable','code_mode_host','--enable','shell_tool']
 return cmd+['-C','/workspace','-']

def global_snapshot():
 p=Path.home()/'.codex/config.toml'
 if not p.is_file():return {'sha256':None,'mtime':None,'fields':[]}
 return {'sha256':sha(p.read_bytes()),'mtime':p.stat().st_mtime,'fields':[x for x in p.read_text().splitlines() if x.startswith(('model =','model_reasoning_effort','service_tier'))]}
