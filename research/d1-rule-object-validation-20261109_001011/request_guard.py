"""Synchronous model-request cap and candidate-read-only tool gate."""
import fcntl,json,os,re,shlex,signal,sys,time
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

from read_policy import read_command

def account(e,root,call,terminate=True):
 root=Path(root);cfg=json.loads((root/'config.json').read_text());p=root/'ledger.json';deny=False;reason=None;k=e.get('hook_event_name')
 with (root/'lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  s=json.loads(p.read_text()) if p.exists() else dict(started=0,completed=0,blocked_requests=0,tool_attempts=0,sessions={},events=[])
  r=s['sessions'].setdefault(call,dict(started=0,completed=0,blocked_requests=0,tool_attempts=0,blocked_tools=0));limit=cfg['calls'][call]
  if k=='PreModelRequest':
   posts=[x['event'] for x in s['events'] if x['call_id']==call and x['event'].get('hook_event_name')=='PostModelRequest']
   if s['started']>=cfg['global_cap'] or r['started']>=limit['cap'] or r['started']!=r['completed'] or (posts and posts[-1].get('status')!='completed'):
    deny=True;reason='request cap or retry prohibited';s['blocked_requests']+=1;r['blocked_requests']+=1
   else:s['started']+=1;r['started']+=1
  elif k=='PostModelRequest':s['completed']+=1;r['completed']+=1
  elif k in ['PreToolUse','PermissionRequest']:
   s['tool_attempts']+=1;r['tool_attempts']+=1
   if limit['mode']=='reflection' or (limit['mode']!='maintenance' and not read_command(e)):deny=True;reason='reflection no tools / extraction candidate read commands only';r['blocked_tools']+=1
  item=dict(at=time.time(),call_id=call,event=e,denied=deny,reason=reason);s['events'].append(item);p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
  with (root/'events.jsonl').open('a') as f:f.write(json.dumps(item,ensure_ascii=False)+'\n')
 if deny and terminate:kill_cli()
 return deny
if __name__=='__main__':account(json.load(sys.stdin),Path('/meter'),os.environ['DIAG_CALL_ID']);print('{}')
