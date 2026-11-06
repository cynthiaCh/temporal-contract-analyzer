"""Synchronous hooks: global8, per-session1; all tools denied. No feedback injection."""
import fcntl,json,os,signal,sys,time
from pathlib import Path

def kill_cli():
    pid=os.getppid()
    while pid>=1:
        try:
            args=(Path('/proc')/str(pid)/'cmdline').read_bytes().split(b'\0');parent=int((Path('/proc')/str(pid)/'status').read_text().split('PPid:\t')[1].splitlines()[0])
        except (OSError,ValueError,IndexError):break
        if args and args[0]==b'/opt/codex':os.kill(pid,signal.SIGKILL);return
        if parent<=0 or parent==pid:break
        pid=parent
    os.killpg(os.getpgrp(),signal.SIGKILL)

def account(event,root,call_id,terminate=True):
    root=Path(root);root.mkdir(exist_ok=True);cfg=json.loads((root/'config.json').read_text());path=root/'ledger.json';kind=event.get('hook_event_name');denied=False
    with (root/'lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);s=json.loads(path.read_text()) if path.exists() else dict(started=0,completed=0,blocked_requests=0,tool_attempts=0,sessions={},events=[])
        r=s['sessions'].setdefault(call_id,dict(started=0,completed=0,blocked_requests=0,tool_attempts=0))
        if kind=='PreModelRequest':
            if s['started']>=cfg['global_cap'] or r['started']>=cfg['per_session_cap']:s['blocked_requests']+=1;r['blocked_requests']+=1;denied=True
            else:s['started']+=1;r['started']+=1
        elif kind=='PostModelRequest':s['completed']+=1;r['completed']+=1
        elif kind in ['PreToolUse','PermissionRequest']:s['tool_attempts']+=1;r['tool_attempts']+=1;denied=True
        item=dict(at=time.time(),call_id=call_id,denied=denied,event=event);s['events'].append(item);path.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
        with (root/'events.jsonl').open('a') as f:f.write(json.dumps(item,ensure_ascii=False)+'\n')
    if denied and terminate:kill_cli()
    return denied
if __name__=='__main__':
    denied=account(json.load(sys.stdin),os.environ.get('DIAG_METER_ROOT','/meter'),os.environ['DIAG_CALL_ID'])
    print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':'Reflection-only experiment; tools forbidden.'}}) if denied else '{}')
