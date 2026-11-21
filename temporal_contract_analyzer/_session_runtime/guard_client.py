"""CLI hook client. Only decision travels back; host archive path stays unmounted."""
import json,socket,sys
from pathlib import Path
from request_guard import kill_cli

def forward(event,endpoint='/hook-control/hook.sock'):
    settings=Path(endpoint).with_name('endpoint.json')
    if settings.is_file():
        config=json.loads(settings.read_text())
        address=(config['host'],config['port']);family=socket.AF_INET
        event=dict(token=config['token'],event=event)
    else:address=endpoint;family=socket.AF_UNIX
    with socket.socket(family) as conn:
        conn.settimeout(10);conn.connect(address);conn.sendall(json.dumps(event).encode()+b'\n');data=b''
        while not data.endswith(b'\n'):
            part=conn.recv(1024)
            if not part:raise RuntimeError('hook collector closed without decision')
            data+=part
        return json.loads(data)

if __name__=='__main__':
    try:decision=forward(json.load(sys.stdin))
    except Exception:kill_cli();raise
    if decision.get('deny'):kill_cli()
    print('{}')
