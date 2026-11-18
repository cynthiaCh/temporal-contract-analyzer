"""Real nested Docker/Unix-socket/CLI startup check; never creates a model client."""
import fcntl
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading


def main():
    repo=Path(__file__).resolve().parents[2]
    runtime=json.loads((repo/'examples/tempoevo-v4/docker-runtime.local.json').read_text())
    public=Path(os.environ['TCA_PUBLIC_CLI'])
    folder=Path(tempfile.mkdtemp(prefix='probe-',dir=os.environ['TMPDIR']))
    server=socket.socket(socket.AF_UNIX);server.bind(str(folder/'hook.sock'));server.listen(1);server.settimeout(30)
    errors=[]
    def reply():
        try:
            conn,_=server.accept()
            with conn:
                if conn.recv(100)!=b'offline-probe':raise ValueError('Unexpected probe message')
                conn.sendall(b'OK')
        except Exception as error:errors.append(repr(error))
    thread=threading.Thread(target=reply);thread.start()
    script="""import json,pathlib,socket,subprocess,sys
assert not any(pathlib.Path(p).exists() for p in ['/opt/swe-tempoc','/evaluation','/var/run/docker.sock'])
assert pathlib.Path('/project/pyproject.toml').is_file()
s=socket.socket(socket.AF_UNIX);s.connect('/hook-control/hook.sock');s.sendall(b'offline-probe');assert s.recv(100)==b'OK';s.close()
sys.path.insert(0,'/probe');from code_host_probe import probe
cli=subprocess.check_output(['/opt/codex','--version'],text=True).strip()
help=subprocess.run(['/opt/codex','exec','--ignore-rules','--dangerously-bypass-hook-trust','--ephemeral','--json','--help'],capture_output=True,text=True)
assert help.returncode==0,help.stderr
print(json.dumps(dict(codex=cli,code_host=probe(),nested_bind=True,unix_hook_socket=True,actor_has_no_docker_socket=True,model_calls=0)))
"""
    command=['docker','run','--rm','--pull=never','--network','none','--read-only','--cap-drop','ALL',
        '--security-opt','no-new-privileges','--tmpfs','/tmp:rw,exec,mode=1777',
        '--mount','type=bind,src='+str(repo)+',dst=/project,readonly',
        '--mount','type=bind,src='+str(repo/'temporal_contract_analyzer/_session_runtime')+',dst=/probe,readonly',
        '--mount','type=bind,src='+str(public)+',dst=/opt,readonly',
        '--mount','type=bind,src='+str(folder)+',dst=/hook-control,readonly',
        '--entrypoint','python3',runtime['backend']['solver_image'],'-B','-c',script]
    done=subprocess.run(command,capture_output=True,text=True,timeout=50)
    thread.join(timeout=2);server.close()
    if done.returncode:raise RuntimeError(done.stderr)
    if errors:raise RuntimeError(str(errors))
    result=json.loads(done.stdout)
    with (folder/'fcntl.lock').open('w') as stream:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
    import hashlib
    result.update(linux_store_lock=True,javascript_execution=result['code_host']['javascript_execution'],
                  controller_python=sys.version.split()[0],model_calls=0,
                  solver_image=runtime['backend']['solver_image'],
                  cli_sha256=hashlib.sha256((public/'codex').read_bytes()).hexdigest())
    print(json.dumps(result))
    return result


if __name__=='__main__':main()
