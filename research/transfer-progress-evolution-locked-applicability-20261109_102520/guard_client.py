"""CLI hook client. Only decision travels back; host archive path stays unmounted."""
import json,socket,sys
from request_guard import kill_cli

def forward(event,endpoint='/hook-control/hook.sock'):
    with socket.socket(socket.AF_UNIX) as conn:
        conn.settimeout(10);conn.connect(endpoint);conn.sendall(json.dumps(event).encode()+b'\n');data=b''
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
