"""Six report-only independent Codex sessions; no continuation/retry/scoring."""
import hashlib,importlib.util,json,os,shutil,signal,subprocess,time
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent.parent
HELPER=ROOT/'research/development-feedback-mechanism-v1-20261106/run.py'
spec=importlib.util.spec_from_file_location('namespace_helper',HELPER);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper);helper.OUT=OUT
BINARY=helper.BINARY
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def command(call,folder,copy_auth=True,meter=None):
 work=folder/'workspace';output=folder/'cli-output';profile=OUT/'.runtime'/call
 for p in [work,output,profile]:p.mkdir(parents=True,exist_ok=True)
 profile.chmod(0o700)
 if copy_auth:
  for name in ['auth.json','config.toml','models_cache.json']:
   f=Path.home()/'.codex'/name
   if f.is_file():shutil.copyfile(f,profile/name);(profile/name).chmod(0o600)
 hooks={'hooks':{e:[{'hooks':[{'type':'command','command':'/usr/bin/python3 /request_guard.py','timeout':10}]}] for e in ['PreModelRequest','PostModelRequest','PreToolUse','PermissionRequest']}}
 save(profile/'hooks.json',hooks);save(folder/'hooks.json',hooks)
 cmd=helper.base_namespace(work,output,profile,meter or folder/'request-meter',call)
 cmd[cmd.index('/format.json')-1]=str(OUT/'report.schema.json')
 cmd+=['/opt/codex','exec','--ignore-rules','--ephemeral','--json','--color','never','--skip-git-repo-check','--sandbox','read-only','-c','approval_policy="never"','-m','gpt-6-sol','-c','model_reasoning_effort="low"','-c','web_search="disabled"','--dangerously-bypass-hook-trust','--output-schema','/format.json']
 for name in ['apps','plugins','multi_agent','browser_use','computer_use','sleep_tool','tool_suggest']:cmd+=['--disable',name]
 return cmd+['-C','/workspace','-o','/output/answer.json','-']
def frozen():
 p=read(OUT/'protocol.json');assert sha(OUT/'protocol.json')==(OUT/'protocol.sha256').read_text().strip()
 for name,h in p['files'].items():assert sha(name)==h,name
 return p

def main():
 frozen();assert read(OUT/'offline-validation.json')['status']=='PASS'
 assert not (OUT/'requests.json').exists(),'No resume/replay allowed'
 save(OUT/'requests.json',[])
 for slot in read(OUT/'schedule.json')['order']:
  frozen();rows=read(OUT/'requests.json');assert len(rows)<6
  folder=OUT/'runs'/slot['call_id'];folder.mkdir(parents=True)
  material=OUT/'materials'/slot['case'];shutil.copytree(material/'candidate',folder/'workspace')
  shutil.copyfile(material/'prompt.md',folder/'actual-prompt.md')
  save(folder/'request-meter/config.json',dict(call_id=slot['call_id'],request_cap=12))
  cmd=command(slot['call_id'],folder);start=time.monotonic()
  rec=dict(**slot,model='gpt-6-sol',effort='low',timeout_seconds=600,request_cap=12,prompt_sha256=sha(folder/'actual-prompt.md'),status='launched',started_at=time.time(),command=cmd)
  rows.append(rec);save(OUT/'requests.json',rows)
  try:
   with (folder/'actual-prompt.md').open('rb') as inp,(folder/'events.jsonl').open('wb') as stdout,(folder/'stderr.log').open('wb') as stderr:
    proc=subprocess.Popen(cmd,stdin=inp,stdout=stdout,stderr=stderr,cwd=folder/'workspace',start_new_session=True)
    try:proc.wait(timeout=600)
    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait();rec['timed_out']=True
   events=[];malformed=[]
   for n,line in enumerate((folder/'events.jsonl').read_text().splitlines(),1):
    try:events.append((n,json.loads(line)))
    except ValueError:malformed.append(n)
   turns=[e for n,e in events if e.get('type')=='turn.completed']
   tools=[dict(line=n,item=e['item']) for n,e in events if e.get('type')=='item.completed' and e.get('item',{}).get('type') not in [None,'reasoning','agent_message','error']]
   native=read(folder/'request-meter/ledger.json') if (folder/'request-meter/ledger.json').exists() else {}
   answer=folder/'cli-output/answer.json';raw=answer.read_text() if answer.exists() else '';(folder/'raw-answer.txt').write_text(raw)
   errors=[]
   try:
    obj=json.loads(raw);assert set(obj)=={'report'} and isinstance(obj['report'],str)
    report=obj['report'];(folder/'report.md').write_text(report)
    rec.update(report_characters=len(report),over_length=len(report)>6000,archive_truncated=False)
    if len(report)>6000:errors.append('report_over_6000_characters')
   except (ValueError,AssertionError,TypeError):errors.append('invalid_report_format')
   actual={str(f.relative_to(folder/'workspace')):sha(f) for f in (folder/'workspace').rglob('*') if f.is_file()}
   expected=next(c['candidate_files'] for c in read(OUT/'source-verification.json')['cases'] if c['case']==slot['case'])
   if actual!=expected:errors.append('candidate_source_changed')
   rec.update(exit_code=proc.returncode,seconds=time.monotonic()-start,completed_at=time.time(),usage={k:sum(e.get('usage',{}).get(k,0) or 0 for e in turns) for k in ['input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens']},tools=len(tools),tool_index=tools,native_requests=native.get('started'),native_completed=native.get('completed'),blocked_requests=native.get('blocked_requests'),blocked_tools=native.get('blocked_tools'),completed_turns=len(turns),malformed_event_lines=malformed,format_errors=errors,candidate_unchanged=actual==expected,raw_answer_sha256=sha(folder/'raw-answer.txt'))
   rec['status']='completed' if proc.returncode==0 and len(turns)==1 and native.get('started',0)>0 and native.get('started')==native.get('completed') and not native.get('blocked_requests') and not native.get('blocked_tools') and not errors and not malformed else 'failed'
   save(folder/'receipt.json',rec);rows=read(OUT/'requests.json');rows[-1]=rec;save(OUT/'requests.json',rows)
   print(json.dumps({k:rec.get(k) for k in ['call_id','case','repeat','status','native_requests','report_characters','seconds']}),flush=True)
   if not native.get('started'):raise RuntimeError('Counter unavailable or zero dispatch: stop remaining slots, no retries')
   assert sum(r.get('native_requests',0) or 0 for r in rows)<=72
  finally:shutil.rmtree(OUT/'.runtime'/slot['call_id'],ignore_errors=True)
 save(OUT/'execution-complete.json',dict(status='ALL_SIX_SLOTS_FINISHED',at=time.time(),no_retries=True))
if __name__=='__main__':main()
