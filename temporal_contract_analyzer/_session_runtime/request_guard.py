"""Synchronous model-request cap and candidate-read-only tool gate."""
import fcntl,hashlib,json,os,re,shlex,signal,sys,time
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
  if not p.exists() and (root/'events.jsonl').exists():raise ValueError('Request ledger missing after initialization')
  s=json.loads(p.read_text()) if p.exists() else dict(started=0,completed=0,blocked_requests=0,tool_attempts=0,sessions={},events=[])
  r=s['sessions'].setdefault(call,dict(started=0,completed=0,blocked_requests=0,tool_attempts=0,blocked_tools=0));limit=cfg['calls'][call]
  if k=='PreModelRequest':
   posts=[x['event'] for x in s['events'] if x['call_id']==call and x['event'].get('hook_event_name')=='PostModelRequest']
   if cfg.get('stop_file') and Path(cfg['stop_file']).exists():
    deny=True;reason='user_requested_pause';s['blocked_requests']+=1;r['blocked_requests']+=1
   elif s['started']>=cfg['global_cap'] or r['started']>=limit['cap'] or r['started']!=r['completed'] or (posts and posts[-1].get('status')!='completed'):
    deny=True;reason='request cap or retry prohibited';s['blocked_requests']+=1;r['blocked_requests']+=1
   else:s['started']+=1;r['started']+=1
  elif k=='PostModelRequest':s['completed']+=1;r['completed']+=1
  elif k in ['PreToolUse','PermissionRequest']:
   s['tool_attempts']+=1;r['tool_attempts']+=1
   read_ok=read_command(e) if limit['mode']!='maintenance' else True
   if limit['mode']=='evidence_readonly':
    inp=e.get('tool_input',{});command=inp.get('command',inp.get('cmd','')) if isinstance(inp,dict) else ''
    # Shell newlines are command separators, not ordinary reader arguments.
    read_ok=read_ok and not any(ch in command for ch in ['\n','\r'])
   if limit['mode']=='reflection' or not read_ok:deny=True;reason='role permits no tools or only closed-grammar workspace evidence reads';r['blocked_tools']+=1
  item=dict(at=time.time(),call_id=call,event=e,denied=deny,reason=reason,
            sequence=len(s['events'])+1,
            request_id=hashlib.sha256(str(root.resolve()).encode()).hexdigest()+':'+call+':'+str(r['started']) if k in ('PreModelRequest','PostModelRequest') and not deny else None)
  s['events'].append(item)
  temporary=p.with_suffix('.tmp')
  with temporary.open('w',encoding='utf8') as f:
   f.write(json.dumps(s,ensure_ascii=False,indent=2)+'\n');f.flush();os.fsync(f.fileno())
  os.replace(temporary,p)
  with (root/'events.jsonl').open('a',encoding='utf8') as f:
   f.write(json.dumps(item,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
  descriptor=os.open(root,os.O_RDONLY)
  try:os.fsync(descriptor)
  finally:os.close(descriptor)
 if deny and terminate:kill_cli()
 return deny
if __name__=='__main__':account(json.load(sys.stdin),Path('/meter'),os.environ['DIAG_CALL_ID']);print('{}')
