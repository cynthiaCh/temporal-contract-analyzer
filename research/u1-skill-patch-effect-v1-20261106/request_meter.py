"""Request accounting only: no tool observations, state phases or Stop continuations."""
import fcntl,json,os,signal,sys,time
from pathlib import Path


def process_budget_exit():
    # Runs inside a dedicated bwrap PID namespace. Kill the CLI ancestor before
    # the next provider request; do not pretend hook JSON can veto requests.
    pid=os.getppid()
    while pid>1:
        try:
            args=(Path('/proc')/str(pid)/'cmdline').read_bytes().split(b'\0')
            parent=int((Path('/proc')/str(pid)/'status').read_text().split('PPid:\t')[1].splitlines()[0])
        except (OSError,ValueError,IndexError):break
        if args and args[0]==b'/opt/codex':
            os.kill(pid,signal.SIGKILL)
            return
        pid=parent
    # Defensive process-group termination; all study CLI jobs use a new session.
    os.killpg(os.getpgrp(),signal.SIGKILL)


def account(event,root,kill=True):
    root=Path(root);root.mkdir(exist_ok=True);config=json.loads((root/'config.json').read_text());path=root/'ledger.json'
    with (root/'lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        state=json.loads(path.read_text()) if path.exists() else dict(started=0,denied=0,completed=0,events=[])
        deny=False;kind=event.get('hook_event_name')
        if kind=='PreModelRequest':
            previous_posts=[x['event'] for x in state['events'] if x['event'].get('hook_event_name')=='PostModelRequest']
            retry=state['started']>state['completed'] or bool(previous_posts and previous_posts[-1].get('status')!='completed')
            if (config.get('reject_transport_retries',True) and retry) or (config.get('max_requests') is not None and state['started']>=config['max_requests']):
                state['denied']+=1;deny=True
            else:state['started']+=1
        elif kind=='PostModelRequest':state['completed']+=1
        item=dict(at=time.time(),denied=deny,event=event);state['events'].append(item);path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
        with (root/'events.jsonl').open('a') as out:out.write(json.dumps(item,ensure_ascii=False)+'\n')
    if deny and kill:process_budget_exit()
    return deny


if __name__=='__main__':
    account(json.load(sys.stdin),os.environ.get('TCA_METER_ROOT','/meter'))
    print('{}')
