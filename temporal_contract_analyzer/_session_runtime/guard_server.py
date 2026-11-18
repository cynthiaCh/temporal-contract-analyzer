"""Host-owned ledger using the unchanged request guard; no archive mount in CLI."""
import hashlib,json,re,socket,threading
from pathlib import Path
from request_guard import account

HOOK_EVENTS={'PreModelRequest','PostModelRequest','PreToolUse','PermissionRequest'}
TOOL_NAMES={'Bash','bash','shell','exec_command','shell_command','Read','read_file',
            'apply_patch','write_stdin','code_mode','code_mode_host'}

def error_context(event,exc):
    """Bounded metadata only; command_length counts Unicode characters.

    OSError.filename and exception messages may contain an entire command token.
    Neither belongs in a collector diagnostic. Known hook/tool identifiers are
    retained; arbitrary names are replaced rather than copied from the payload.
    """
    event=event if isinstance(event,dict) else {}
    hook=event.get('hook_event_name');tool=event.get('tool_name')
    hook=hook if isinstance(hook,str) and hook in HOOK_EVENTS else None
    if isinstance(tool,str):
        parts=tool.split('.')
        tool=tool if (len(parts)==1 and tool in TOOL_NAMES or len(parts)==2 and
                      parts[0]=='functions' and parts[1] in TOOL_NAMES) else 'unknown'
    else:tool=None
    inp=event.get('tool_input');command=inp.get('command',inp.get('cmd')) if isinstance(inp,dict) else None
    raw=command.encode('utf-8',errors='surrogatepass') if isinstance(command,str) else None
    name=type(exc).__name__
    name=name if re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]{0,63}',name) else 'Exception'
    number=getattr(exc,'errno',None)
    return dict(hook_event_name=hook,tool_name=tool,
                command_length=len(command) if raw is not None else None,
                command_sha256=hashlib.sha256(raw).hexdigest() if raw is not None else None,
                exception_type=name,errno=number if type(number) is int else None)

class GuardServer:
    def __init__(self,socket_dir,meter,call,cap,mode,stop_file=None):
        self.stop_file=stop_file
        self.directory=Path(socket_dir);self.meter=Path(meter);self.call=call;self.cap=cap;self.mode=mode;self.errors=[];self.error_contexts=[]
        self.stop_event=threading.Event();self.thread=None;self.socket=None
    def __enter__(self):
        self.directory.mkdir(parents=True,exist_ok=False);self.directory.chmod(0o700)
        self.meter.mkdir(parents=True,exist_ok=True)
        (self.meter/'config.json').write_text(json.dumps({'global_cap':self.cap,'calls':{self.call:{'cap':self.cap,'mode':self.mode}},'stop_file':self.stop_file}))
        self.socket=socket.socket(socket.AF_UNIX);self.socket.bind(str(self.directory/'hook.sock'));self.socket.listen(16);self.socket.settimeout(.1)
        self.thread=threading.Thread(target=self._serve,daemon=True);self.thread.start();return self
    def _serve(self):
        while not self.stop_event.is_set():
            try:conn,_=self.socket.accept()
            except socket.timeout:continue
            except OSError:break
            with conn:
                conn.settimeout(10)
                event=None
                try:
                    data=b''
                    while not data.endswith(b'\n'):
                        part=conn.recv(65536)
                        if not part:raise ValueError('incomplete hook event')
                        data+=part
                        if len(data)>8*1024*1024:raise ValueError('oversized hook event')
                    event=json.loads(data);denied=account(event,self.meter,self.call,terminate=False)
                    conn.sendall(json.dumps({'deny':denied}).encode()+b'\n')
                except Exception as exc:
                    context=error_context(event,exc);self.error_contexts.append(context)
                    self.errors.append(context['exception_type']+' (errno='+str(context['errno'])+')')
                    try:conn.sendall(b'{"deny":true,"collector_error":true}\n')
                    except OSError:pass
    def __exit__(self,*exc):
        self.stop_event.set();self.socket.close();self.thread.join(timeout=11)
        (self.directory/'hook.sock').unlink(missing_ok=True)
