"""Host-owned ledger using the unchanged request guard; no archive mount in CLI."""
import json,secrets,socket,threading
from pathlib import Path
from request_guard import account

class GuardServer:
    def __init__(self,socket_dir,meter,call,cap,mode,*,docker_desktop=False):
        self.directory=Path(socket_dir);self.meter=Path(meter);self.call=call;self.cap=cap;self.mode=mode;self.errors=[]
        self.stop_event=threading.Event();self.thread=None;self.socket=None
        self.docker_desktop=docker_desktop;self.token=secrets.token_hex(32) if docker_desktop else None
    def __enter__(self):
        self.directory.mkdir(parents=True,exist_ok=False);self.directory.chmod(0o700)
        self.meter.mkdir(parents=True,exist_ok=True)
        (self.meter/'config.json').write_text(json.dumps({'global_cap':self.cap,'calls':{self.call:{'cap':self.cap,'mode':self.mode}}}))
        self.socket=socket.socket(socket.AF_INET if self.docker_desktop else socket.AF_UNIX)
        self.socket.bind(('127.0.0.1',0) if self.docker_desktop else str(self.directory/'hook.sock'))
        if self.docker_desktop:
            endpoint=self.directory/'endpoint.json'
            endpoint.write_text(json.dumps(dict(host='host.docker.internal',port=self.socket.getsockname()[1],token=self.token)))
            endpoint.chmod(0o600)
        self.socket.listen(16);self.socket.settimeout(.1)
        self.thread=threading.Thread(target=self._serve,daemon=True);self.thread.start();return self
    def _serve(self):
        while not self.stop_event.is_set():
            try:conn,_=self.socket.accept()
            except socket.timeout:continue
            except OSError:break
            with conn:
                conn.settimeout(10)
                try:
                    data=b''
                    while not data.endswith(b'\n'):
                        part=conn.recv(65536)
                        if not part:raise ValueError('incomplete hook event')
                        data+=part
                        if len(data)>8*1024*1024:raise ValueError('oversized hook event')
                    event=json.loads(data)
                    if self.docker_desktop:
                        if not isinstance(event,dict) or not isinstance(event.get('token'),str) or not secrets.compare_digest(event['token'],self.token):
                            conn.sendall(b'{"deny":true}\n');continue
                        event=event['event']
                    denied=account(event,self.meter,self.call,terminate=False)
                    conn.sendall(json.dumps({'deny':denied}).encode()+b'\n')
                except Exception as exc:
                    self.errors.append(repr(exc))
                    try:conn.sendall(b'{"deny":true,"collector_error":true}\n')
                    except OSError:pass
    def __exit__(self,*exc):
        self.stop_event.set();self.socket.close();self.thread.join(timeout=11)
        (self.directory/'hook.sock').unlink(missing_ok=True)
