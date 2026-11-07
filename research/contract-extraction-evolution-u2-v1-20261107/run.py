"""Five fixed slots; no pre-run, retry, scorer, maintenance or optimizer."""
import json,hashlib,os,shutil,subprocess,time,signal,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent.parent
BINARY=Path('/home/sribd/.vscode/extensions/openai.chatgpt-26.51021.22027-linux-x64/bin/linux-x86_64/codex')
DISABLE=['code_mode_host','code_mode','apps','plugins','multi_agent','browser_use','computer_use','sleep_tool','tool_suggest']
def read(p):return json.loads(Path(p).read_text())
def save(p,d):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(b):return hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
def hashes(root):return {str(p.relative_to(root)):sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
def command(call,folder,mode,copy_auth=True,meter=None):
 work=folder/'workspace';out=folder/'cli-output';profile=OUT/'.runtime'/call
 for p in [work,out,profile]:p.mkdir(parents=True,exist_ok=True)
 profile.chmod(0o700)
 if copy_auth:
  for n in ['auth.json','config.toml','models_cache.json']:
   p=Path.home()/'.codex'/n
   if p.is_file():shutil.copyfile(p,profile/n);(profile/n).chmod(0o600)
 hooks={'hooks':{e:[{'hooks':[{'type':'command','command':'/usr/bin/python3 /request_guard.py','timeout':10}]}] for e in ['PreModelRequest','PostModelRequest','PreToolUse','PermissionRequest']}}
 save(profile/'hooks.json',hooks);save(folder/'hooks.json',hooks)
 ns=['bwrap','--die-with-parent','--new-session','--unshare-user','--unshare-pid','--unshare-ipc','--unshare-uts','--cap-drop','ALL','--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--symlink','usr/bin','/bin','--symlink','usr/sbin','/sbin','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/home/agent','--dir','/etc','--ro-bind','/etc/resolv.conf','/etc/resolv.conf','--ro-bind','/etc/ssl','/etc/ssl','--ro-bind',str(BINARY.parent),'/opt','--bind',str(profile),'/home/agent/.codex','--ro-bind',str(work),'/workspace','--bind',str(out),'/output','--ro-bind',str(OUT/'request_guard.py'),'/request_guard.py','--ro-bind',str(OUT/('reflection.schema.json' if mode=='reflection' else 'extraction.schema.json')),'/format.json','--bind',str(meter or OUT/'request-meter'),'/meter','--chdir','/workspace','--setenv','HOME','/home/agent','--setenv','CODEX_HOME','/home/agent/.codex','--setenv','PATH','/usr/bin:/bin:/opt','--setenv','LANG','C.UTF-8']
 for k in sorted(os.environ):
  if k not in ['HOME','CODEX_HOME','PATH','LANG']:ns+=['--unsetenv',k]
 for k in ['HTTP_PROXY','HTTPS_PROXY','NO_PROXY','http_proxy','https_proxy','no_proxy']:
  if k in os.environ:ns+=['--setenv',k,os.environ[k]]
 ns+=['--setenv','DIAG_CALL_ID',call,'--']
 cmd=ns+['/opt/codex','exec','--ignore-rules','--ephemeral','--json','--color','never','--skip-git-repo-check','--sandbox','read-only','-c','approval_policy="never"','-m','gpt-6-sol','-c','model_reasoning_effort="low"','-c','web_search="disabled"','-c','model_provider="experiment_no_retry"','-c','model_providers.experiment_no_retry.name="OpenAI"','-c','model_providers.experiment_no_retry.wire_api="responses"','-c','model_providers.experiment_no_retry.requires_openai_auth=true','-c','model_providers.experiment_no_retry.request_max_retries=0','-c','model_providers.experiment_no_retry.stream_max_retries=0','--dangerously-bypass-hook-trust','--output-schema','/format.json']
 for feature in DISABLE+(['shell_tool'] if mode=='reflection' else []):cmd+=['--disable',feature]
 return cmd+['-C','/workspace','-o','/output/answer.json','-']
def frozen():
 p=read(OUT/'protocol.json');assert sha((OUT/'protocol.json').read_bytes())==(OUT/'protocol.sha256').read_text().strip()
 for n,h in p['files'].items():assert sha(Path(n).read_bytes())==h,n
 return p
def prompt_for(skill):return (OUT/'prompt-template.md').read_text().replace('{{TASK}}',(OUT/'materials/task.md').read_text()).replace('{{SKILL}}',skill)
def one(slot,prompt):
 frozen();rows=read(OUT/'requests.json') if (OUT/'requests.json').exists() else [];assert len(rows)<5 and slot['call_id'] not in [r['call_id'] for r in rows]
 folder=OUT/'runs'/slot['call_id'];folder.mkdir(parents=True,exist_ok=False);mode='reflection' if slot['phase']=='reflection' else 'extraction'
 if mode=='extraction':shutil.copytree(OUT/'materials/candidate',folder/'workspace')
 (folder/'actual-prompt.md').write_text(prompt);cmd=command(slot['call_id'],folder,mode)
 rec=dict(**slot,path=str(folder),mode=mode,model='gpt-6-sol',effort='low',timeout=600,prompt_sha256=sha(prompt),started_at=time.time(),status='launched',command=cmd);rows.append(rec);save(OUT/'requests.json',rows)
 try:
  with (folder/'actual-prompt.md').open('rb') as inp,(folder/'events.jsonl').open('wb') as out,(folder/'stderr.log').open('wb') as err:
   proc=subprocess.Popen(cmd,stdin=inp,stdout=out,stderr=err,cwd=folder/'workspace',start_new_session=True)
   try:proc.wait(timeout=600)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait();rec['timed_out']=True
  events=[];errors=[]
  for n,line in enumerate((folder/'events.jsonl').read_text().splitlines(),1):
   try:events.append(json.loads(line))
   except ValueError:errors.append('malformed_event:'+str(n))
  turns=[e for e in events if e.get('type')=='turn.completed'];tools=[dict(line=n,item=e['item']) for n,e in enumerate(events,1) if e.get('type')=='item.completed' and e.get('item',{}).get('type') not in [None,'agent_message','reasoning','error']]
  meter=read(OUT/'request-meter/ledger.json') if (OUT/'request-meter/ledger.json').exists() else {};native=meter.get('sessions',{}).get(slot['call_id'],{})
  rawpath=folder/'cli-output/answer.json';raw=rawpath.read_text() if rawpath.exists() else '';(folder/'raw-answer.txt').write_text(raw)
  rec.update(exit_code=proc.returncode,completed_at=time.time(),seconds=time.time()-rec['started_at'],native=native,usage={k:sum(t.get('usage',{}).get(k,0) or 0 for t in turns) for k in ['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens']},tools=len(tools),completed_turns=len(turns),raw_sha256=sha(raw))
  try:
   obj=json.loads(raw)
   if mode=='extraction':
    assert set(obj)=={'report'} and isinstance(obj['report'],str) and len(obj['report'])<=6000
    (folder/'contract.md').write_text(obj['report']);rec['report_characters']=len(obj['report'])
   else:assert set(obj)=={'skill','changes'} and isinstance(obj['skill'],str) and len(obj['skill'])<=4000 and isinstance(obj['changes'],list)
  except (ValueError,AssertionError,TypeError):errors.append('invalid_output_format')
  if mode=='extraction':assert hashes(folder/'workspace')==read(OUT/'scope-and-sources.json')['candidate_files'],'input changed'
  save(folder/'read-trace.json',{'completed_tool_items':tools,'hook_tool_attempts':[x for x in meter.get('events',[]) if x['call_id']==slot['call_id'] and x['event'].get('hook_event_name') in ['PreToolUse','PermissionRequest']]})
  rec['format_errors']=errors;rec['status']='completed' if proc.returncode==0 and len(turns)==1 and native.get('started',0)>0 and native.get('started')==native.get('completed') and not native.get('blocked_requests') and not native.get('blocked_tools') and not errors else 'failed'
  save(folder/'receipt.json',rec);rows=read(OUT/'requests.json');rows[-1]=rec;save(OUT/'requests.json',rows);print(json.dumps({'slot':slot['call_id'],'status':rec['status'],'requests':native.get('started'),'tools':len(tools),'seconds':rec['seconds']}),flush=True)
  if not native.get('started'):raise RuntimeError('No native request accounting, stop remaining schedule')
  return rec
 finally:shutil.rmtree(OUT/'.runtime'/slot['call_id'],ignore_errors=True)
def phase(name):
 frozen();assert read(OUT/'offline-validation.json')['status']=='PASS'
 if name=='K1':
  f=read(OUT/'K1.freeze.json');assert f['allow_execution'] and sha((OUT/'contract_extraction_K1.md').read_bytes())==f['skill_sha256']
 skill=(OUT/('contract_extraction_K0.md' if name=='K0' else 'contract_extraction_K1.md')).read_text()
 for slot in read(OUT/'schedule.json')['order']:
  if slot['phase']==name:one(slot,prompt_for(skill))
 save(OUT/(name+'-complete.json'),dict(phase=name,at=time.time()))
if __name__=='__main__':
 if sys.argv[1]=='reflection':
  assert (OUT/'K0-complete.json').exists();assert not (OUT/'runs/reflect-1').exists()
  save(OUT/'reflection.freeze.json',{'files':{str(OUT/n):sha((OUT/n).read_bytes()) for n in ['reflection.prompt.md','difference-feedback.json','baseline-review.csv']},'before_request':True})
  one(next(x for x in read(OUT/'schedule.json')['order'] if x['phase']=='reflection'),(OUT/'reflection.prompt.md').read_text())
 else:phase(sys.argv[1])
