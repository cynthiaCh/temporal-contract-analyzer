"""Eight independent single-request CLI reflections. No maintenance or optimizer path."""
import json,hashlib,os,shutil,subprocess,time,signal
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
BINARY=Path('/home/sribd/.vscode/extensions/openai.chatgpt-26.51021.22027-linux-x64/bin/linux-x86_64/codex')
FEATURES=['shell_tool','code_mode_host','code_mode','apps','plugins','multi_agent','browser_use','computer_use','sleep_tool','tool_suggest']
def read(p):return json.loads(Path(p).read_text())
def save(p,d):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(b):return hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
def base_namespace(work,out,profile,meter,call_id):
    cmd=['bwrap','--die-with-parent','--new-session','--unshare-user','--unshare-pid','--unshare-ipc','--unshare-uts','--cap-drop','ALL','--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--symlink','usr/bin','/bin','--symlink','usr/sbin','/sbin','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/home/agent','--dir','/etc','--ro-bind','/etc/resolv.conf','/etc/resolv.conf','--ro-bind','/etc/ssl','/etc/ssl','--ro-bind',str(BINARY.parent),'/opt','--bind',str(profile),'/home/agent/.codex','--ro-bind',str(work),'/workspace','--bind',str(out),'/output','--ro-bind',str(OUT/'request_guard.py'),'/request_guard.py','--ro-bind',str(OUT/'response.schema.json'),'/format.json','--bind',str(meter),'/meter','--chdir','/workspace','--setenv','HOME','/home/agent','--setenv','CODEX_HOME','/home/agent/.codex','--setenv','PATH','/usr/bin:/bin:/opt','--setenv','LANG','C.UTF-8']
    for key in sorted(os.environ):
        if key not in ['HOME','CODEX_HOME','PATH','LANG']:cmd+=['--unsetenv',key]
    for key in ['HTTP_PROXY','HTTPS_PROXY','NO_PROXY','http_proxy','https_proxy','no_proxy']:
        if key in os.environ:cmd+=['--setenv',key,os.environ[key]]
    return cmd+['--setenv','DIAG_CALL_ID',call_id,'--']
def command(call_id,folder,meter=None,copy_auth=True):
    work=folder/'workspace';out=folder/'cli-output';profile=OUT/'.runtime'/call_id
    for p in [work,out,profile]:p.mkdir(parents=True,exist_ok=True)
    profile.chmod(0o700)
    if copy_auth:
        for name in ['auth.json','config.toml','models_cache.json']:
            p=Path.home()/'.codex'/name
            if p.is_file():shutil.copyfile(p,profile/name);(profile/name).chmod(0o600)
    hooks=dict(hooks={e:[dict(hooks=[dict(type='command',command='/usr/bin/python3 /request_guard.py',timeout=10)])] for e in ['PreModelRequest','PostModelRequest','PreToolUse','PermissionRequest']})
    save(profile/'hooks.json',hooks);save(folder/'hooks.json',hooks)
    cmd=base_namespace(work,out,profile,meter or OUT/'request-meter',call_id)
    cmd+=['/opt/codex','exec','--ignore-rules','--ephemeral','--json','--color','never','--skip-git-repo-check','--sandbox','read-only','-c','approval_policy="never"','-m','gpt-6-sol','-c','model_reasoning_effort="low"','-c','web_search="disabled"','--dangerously-bypass-hook-trust','--output-schema','/format.json']
    for name in FEATURES:cmd+=['--disable',name]
    cmd+=['-C','/workspace','-o','/output/answer.json','-']
    return cmd

def parse_events(path):
    events=[];usage=[];tools=[];errors=[]
    if not Path(path).exists():return dict(usage={},events=[],tools=[],errors=[])
    for n,line in enumerate(Path(path).read_text().splitlines(),1):
        try:e=json.loads(line)
        except ValueError:errors.append(dict(line=n,malformed_event=True));continue
        events.append(e)
        if e.get('type')=='turn.completed':usage.append(e.get('usage',{}))
        if e.get('type') in ['turn.failed','error']:errors.append(dict(line=n,event=e))
        item=e.get('item',{})
        if e.get('type')=='item.completed' and item.get('type') not in [None,'reasoning','agent_message']:tools.append(dict(line=n,item=item))
    return dict(usage={k:sum(x.get(k,0) for x in usage) for k in ['input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens']},events=events,tools=tools,errors=errors,completed_turns=len(usage))
def freeze_check():
    p=read(OUT/'protocol.json');assert sha((OUT/'protocol.json').read_bytes())==(OUT/'protocol.sha256').read_text().strip()
    for name,h in p['frozen_files'].items():assert sha(Path(name).read_bytes())==h,name
    return p

def main():
    freeze_check();assert read(OUT/'offline-validation.json')['status']=='PASS'
    if (OUT/'requests.json').exists():raise RuntimeError('No formal resume/replay/retry allowed')
    save(OUT/'requests.json',[]);save(OUT/'request-meter/config.json',dict(global_cap=8,per_session_cap=1));schedule=read(OUT/'schedule.json')['order']
    for slot in schedule:
        freeze_check();rows=read(OUT/'requests.json');assert len(rows)<8;folder=OUT/'runs'/slot['call_id'];folder.mkdir(parents=True,exist_ok=True);prompt=Path(slot['prompt']);shutil.copyfile(prompt,folder/'actual-prompt.md');cmd=command(slot['call_id'],folder)
        rec=dict(**slot,model='gpt-6-sol',effort='low',timeout=600,started_at=time.time(),path=str(folder),command=cmd,prompt_sha256=sha(prompt.read_bytes()),status='launched');rows.append(rec);save(OUT/'requests.json',rows);start=time.monotonic();process=None
        try:
            with prompt.open('rb') as inp,(folder/'events.jsonl').open('wb') as stdout,(folder/'stderr.log').open('wb') as stderr:
                process=subprocess.Popen(cmd,stdin=inp,stdout=stdout,stderr=stderr,cwd=folder/'workspace',start_new_session=True)
                try:process.wait(timeout=600)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait();rec['timed_out']=True
            tr=parse_events(folder/'events.jsonl');meter=read(OUT/'request-meter/ledger.json') if (OUT/'request-meter/ledger.json').exists() else {};session=meter.get('sessions',{}).get(slot['call_id'],{});answer=folder/'cli-output/answer.json';raw=answer.read_text() if answer.exists() else '';(folder/'raw-answer.txt').write_text(raw)
            rec.update(exit_code=process.returncode,seconds=time.monotonic()-start,usage=tr['usage'],completed_turns=tr.get('completed_turns',0),tool_items=tr['tools'],errors=tr['errors'],native_request_account=session,answer_sha256=sha(raw),completed_at=time.time())
            rec['status']='completed' if process.returncode==0 and tr.get('completed_turns')==1 and raw.strip() and session.get('started')==1 and not tr['tools'] and not session.get('tool_attempts') and not session.get('blocked_requests') else 'generation_failure'
            rec['counter_reliable']=session.get('started')==1
            save(folder/'receipt.json',rec);rows=read(OUT/'requests.json');rows[-1]=rec;save(OUT/'requests.json',rows)
            print(json.dumps(dict(event='generation_done',call_id=slot['call_id'],status=rec['status'],native_requests=session.get('started'),seconds=rec['seconds'])),flush=True)
            if not rec['counter_reliable']:raise RuntimeError('Native request counting unavailable; stop remaining schedule')
            assert meter['started']<=8
        finally:shutil.rmtree(OUT/'.runtime'/slot['call_id'],ignore_errors=True)
    save(OUT/'generation-complete.json',dict(status='COMPLETE',cli_sessions=len(read(OUT/'requests.json')),native_requests=read(OUT/'request-meter/ledger.json')['started'],at=time.time(),no_retries=True))
if __name__=='__main__':main()
