"""Independent report-only CLI sessions. No maintenance, scorer, GEPA or retry."""
import json,hashlib,importlib.util,os,shutil,signal,subprocess,time
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent.parent
spec=importlib.util.spec_from_file_location('namespace_only',ROOT/'research/development-feedback-mechanism-v1-20261106/run.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);old.OUT=OUT
BINARY=old.BINARY
read=lambda p:json.loads(Path(p).read_text())
def save(p,v):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
sha=lambda b:hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
def command(call,folder,mode,copy_auth=True,meter=None):
 work=folder/'workspace';output=folder/'cli-output';profile=OUT/'.runtime'/call
 for p in [work,output,profile]:p.mkdir(parents=True,exist_ok=True)
 profile.chmod(0o700)
 if copy_auth:
  for name in ['auth.json','config.toml','models_cache.json']:
   p=Path.home()/'.codex'/name
   if p.exists():shutil.copyfile(p,profile/name);(profile/name).chmod(0o600)
 hooks={'hooks':{e:[{'hooks':[{'type':'command','command':'/usr/bin/python3 /request_guard.py','timeout':10}]}] for e in ['PreModelRequest','PostModelRequest','PreToolUse','PermissionRequest']}};save(profile/'hooks.json',hooks);save(folder/'hooks.json',hooks)
 ns=old.base_namespace(work,output,profile,meter or OUT/'request-meter',call)
 idx=ns.index('/format.json');ns[idx-1]=str(OUT/('report.schema.json' if mode=='analysis' else 'reflection.schema.json'))
 cmd=ns+['/opt/codex','exec','--ignore-rules','--ephemeral','--json','--color','never','--skip-git-repo-check','--sandbox','read-only','-c','approval_policy="never"','-m','gpt-6-sol','-c','model_reasoning_effort="low"','-c','web_search="disabled"','--dangerously-bypass-hook-trust','--output-schema','/format.json']
 features=old.FEATURES if mode=='reflection' else ['apps','plugins','multi_agent','browser_use','computer_use','sleep_tool','tool_suggest']
 for name in features:cmd+=['--disable',name]
 return cmd+['-C','/workspace','-o','/output/answer.json','-']
def frozen():
 p=read(OUT/'protocol.json');assert sha((OUT/'protocol.json').read_bytes())==(OUT/'protocol.sha256').read_text().strip()
 for n,h in p['files'].items():assert sha(Path(n).read_bytes())==h,n
 return p

def one(slot,prompt,skill=None):
 frozen();rows=read(OUT/'requests.json') if (OUT/'requests.json').exists() else [];assert len(rows)<9 and slot['call_id'] not in [r['call_id'] for r in rows]
 folder=OUT/'runs'/slot['call_id'];folder.mkdir(parents=True,exist_ok=True)
 mode='reflection' if slot['phase']=='reflection' else 'analysis'
 if mode=='analysis':
  shutil.copytree(OUT/'materials'/slot['unit']/'candidate',folder/'workspace')
  assert skill is not None
  # The common fixed K0 prompt is updated only inside its single skill block.
  original=(OUT/'materials'/slot['unit']/'K0.prompt.md').read_text();K0=(OUT/'analysis_skill_K0.md').read_text();assert original.count(K0)==1
  assert prompt==original.replace(K0,skill,1)
 (folder/'actual-prompt.md').write_text(prompt);cmd=command(slot['call_id'],folder,mode)
 record=dict(**slot,path=str(folder),mode=mode,prompt_sha256=sha(prompt),model='gpt-6-sol',effort='low',timeout=600,started_at=time.time(),status='launched',command=cmd);rows.append(record);save(OUT/'requests.json',rows)
 try:
  with (folder/'actual-prompt.md').open('rb') as inp,(folder/'events.jsonl').open('wb') as out,(folder/'stderr.log').open('wb') as err:
   proc=subprocess.Popen(cmd,stdin=inp,stdout=out,stderr=err,cwd=folder/'workspace',start_new_session=True)
   try:proc.wait(timeout=600)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait();record['timed_out']=True
  events=[json.loads(l) for l in (folder/'events.jsonl').read_text().splitlines()];turns=[e for e in events if e.get('type')=='turn.completed'];tools=[dict(line=i,item=e['item']) for i,e in enumerate(events,1) if e.get('type')=='item.completed' and e.get('item',{}).get('type') not in [None,'error','agent_message','reasoning']]
  meter=read(OUT/'request-meter/ledger.json');native=meter['sessions'].get(slot['call_id'],{});rawpath=folder/'cli-output/answer.json';raw=rawpath.read_text() if rawpath.exists() else '';(folder/'raw-answer.txt').write_text(raw)
  record.update(exit_code=proc.returncode,completed_at=time.time(),seconds=time.time()-record['started_at'],native=native,usage={k:sum(t.get('usage',{}).get(k,0) or 0 for t in turns) for k in ['input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens']},tools=len(tools),tool_index=tools,completed_turns=len(turns),raw_sha256=sha(raw))
  errors=[]
  try:
   obj=json.loads(raw)
   if mode=='analysis':
    assert set(obj)=={'report'} and isinstance(obj['report'],str);assert len(obj['report'])<=6000;record['report_characters']=len(obj['report']);(folder/'report.md').write_text(obj['report'])
   else:
    assert set(obj)=={'skill','changes'} and isinstance(obj['skill'],str) and len(obj['skill'])<=6000 and isinstance(obj['changes'],list)
  except (ValueError,AssertionError,TypeError):errors.append('invalid_format_or_length')
  if mode=='analysis':
   actual={str(f.relative_to(folder/'workspace')):sha(f.read_bytes()) for f in (folder/'workspace').rglob('*') if f.is_file()};expected=read(OUT/'source-verification.json')['inputs'];expected=next(x['candidate_files'] for x in expected if x['unit']==slot['unit']);assert actual==expected,'read-only candidate changed'
  record['format_errors']=errors;record['status']='completed' if proc.returncode==0 and len(turns)==1 and native.get('started')==native.get('completed') and native.get('started',0)>0 and not native.get('blocked_requests') and not native.get('blocked_tools') and not errors else 'failed'
  save(folder/'receipt.json',record);rows=read(OUT/'requests.json');rows[-1]=record;save(OUT/'requests.json',rows);print(json.dumps(dict(call=slot['call_id'],status=record['status'],native=native.get('started'),chars=record.get('report_characters'))),flush=True)
  if not native.get('started'):raise RuntimeError('Native accounting unavailable; stop')
  return record
 finally:shutil.rmtree(OUT/'.runtime'/slot['call_id'],ignore_errors=True)

def phase(name):
 p=frozen();assert read(OUT/'runtime-preflight.json')['status']=='PASS';schedule=read(OUT/'schedule.json')['order'];skill=(OUT/('analysis_skill_K0.md' if name=='K0' else 'analysis_skill_K1.md')).read_text()
 if name=='K1':
  f=read(OUT/'K1.freeze.json');assert sha(skill)==f['skill_sha256'] and f['allow_execution']
 for slot in schedule:
  if slot['phase']!=name:continue
  prompt=(OUT/'materials'/slot['unit']/'K0.prompt.md').read_text().replace((OUT/'analysis_skill_K0.md').read_text(),skill,1);one(slot,prompt,skill)
 save(OUT/(name+'-complete.json'),dict(at=time.time(),phase=name))
if __name__=='__main__':
 import sys;phase(sys.argv[1])
