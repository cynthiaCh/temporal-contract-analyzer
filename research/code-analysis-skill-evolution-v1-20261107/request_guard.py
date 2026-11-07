"""Synchronous native request limits; read-only analysis tools, tool-free reflection."""
import fcntl,json,os,re,signal,sys,time
from pathlib import Path

def kill_cli():
 pid=os.getppid()
 while pid>1:
  try:
   args=(Path('/proc')/str(pid)/'cmdline').read_bytes().split(b'\0');parent=int((Path('/proc')/str(pid)/'status').read_text().split('PPid:\t')[1].splitlines()[0])
  except (OSError,ValueError,IndexError):break
  if args and args[0]==b'/opt/codex':os.kill(pid,signal.SIGKILL);return
  pid=parent
 os.killpg(os.getpgrp(),signal.SIGKILL)
def account(e,root,call,terminate=True):
 root=Path(root);cfg=json.loads((root/'config.json').read_text());path=root/'ledger.json';kind=e.get('hook_event_name');deny=False;reason=None
 with (root/'lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);s=json.loads(path.read_text()) if path.exists() else dict(started=0,completed=0,blocked_requests=0,tool_attempts=0,sessions={},events=[])
  r=s['sessions'].setdefault(call,dict(started=0,completed=0,blocked_requests=0,tool_attempts=0,blocked_tools=0));limit=cfg['calls'][call]
  if kind=='PreModelRequest':
   posts=[x['event'] for x in s['events'] if x['call_id']==call and x['event'].get('hook_event_name')=='PostModelRequest']
   retry=r['started']>r['completed'] or bool(posts and posts[-1].get('status')!='completed')
   if s['started']>=97 or r['started']>=limit['cap'] or retry:deny=True;reason='request cap or transport retry';s['blocked_requests']+=1;r['blocked_requests']+=1
   else:s['started']+=1;r['started']+=1
  elif kind=='PostModelRequest':s['completed']+=1;r['completed']+=1
  elif kind in ['PreToolUse','PermissionRequest']:
   s['tool_attempts']+=1;r['tool_attempts']+=1
   inp=e.get('tool_input',{});text=json.dumps(inp,ensure_ascii=False) if not isinstance(inp,str) else inp;name=e.get('tool_name','')
   if limit['mode']=='reflection' or re.search(r'apply_patch|write_file|edit_file',name,re.I) or re.search(r'\b(node|node16|python[0-9.]*|pytest|npm|npx|curl|wget)\b',text):deny=True;reason='analysis reads only; reflection has no tools';r['blocked_tools']+=1
  item=dict(at=time.time(),call_id=call,event=e,denied=deny,reason=reason);s['events'].append(item);path.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
  with (root/'events.jsonl').open('a') as f:f.write(json.dumps(item,ensure_ascii=False)+'\n')
 if deny and terminate:kill_cli()
 return deny
if __name__=='__main__':
 account(json.load(sys.stdin),Path('/meter'),os.environ['DIAG_CALL_ID']);print('{}')
