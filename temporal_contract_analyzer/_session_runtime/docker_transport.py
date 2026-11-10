"""Docker namespace for the existing guarded CLI; no models on import."""
import json
import os
from pathlib import Path
import re
import subprocess


def stop(name, receipt=None):
    """Stop descendants through the daemon before any candidate snapshot."""
    result = subprocess.run(['docker', 'container', 'inspect', name],
                            capture_output=True, text=True, timeout=20)
    if result.returncode:
        if 'no such' in result.stderr.lower():
            return
        raise RuntimeError('Cannot establish Docker container state: ' + result.stderr)
    data = json.loads(result.stdout)[0]
    if receipt:
        Path(receipt).write_text(json.dumps(dict(
            id=data['Id'], image=data['Image'], state=data['State'],
            mounts=[dict(destination=m['Destination'], writable=m['RW']) for m in data['Mounts']],
            network=data['HostConfig']['NetworkMode']), indent=2) + '\n')
    removed = subprocess.run(['docker', 'rm', '--force', name],
                             capture_output=True, text=True, timeout=30)
    if removed.returncode:
        raise RuntimeError('Docker cleanup failed: ' + removed.stderr)


class Launcher:
    def __init__(self, config, archive):
        self.config, self.archive, self.stopped = config, Path(archive), False
        if not re.fullmatch(r'tca-session-[0-9a-f]{32}', config['name']):
            raise ValueError('Invalid owned container name')
        if not re.fullmatch(r'sha256:[0-9a-f]{64}', config['solver_image']):
            raise ValueError('Require an immutable local solver image ID')

    def command(self, native, folder, runtime, call, socket_dir):
        # Construct the existing CLI/profile first; replace its bwrap envelope.
        namespace, cli = native[:native.index('--')], native[native.index('--') + 1:]
        profile = Path(runtime)/'.runtime'/call
        home = Path(runtime)/'login-home'
        (home/'.codex').mkdir(parents=True)
        node = self.config['node']
        if not re.fullmatch(r'/runtime/node(?:16|18|24)/bin/node', node):
            raise ValueError('Require a public solver Node runtime')
        path = str(Path(node).parent) + ':/runtime/bin:/public-cli:/usr/local/bin:/usr/bin:/bin:/opt'
        for name in ('.bash_profile', '.profile'):
            (home/name).write_text('export PATH="' + path + '"\n')
        hooks = json.loads((profile/'hooks.json').read_text())
        for group in hooks['hooks'].values():
            for rule in group:
                for hook in rule['hooks']:
                    hook['command'] = '/usr/local/bin/python3 -B /guard_client.py'
        (profile/'hooks.json').write_text(json.dumps(hooks))
        (self.archive/'hooks.json').write_text(json.dumps(hooks, indent=2) + '\n')
        args = ['docker', 'run', '-i', '--pull=never', '--name', self.config['name'],
                '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                '--network', 'host', '--user', str(os.getuid()) + ':' + str(os.getgid()),
                '--memory', '8g', '--cpus', '4', '--pids-limit', '512', '--init',
                '--tmpfs', '/tmp:rw,exec,mode=1777,size=4g', '--workdir', '/workspace']
        def mount(source, target, readonly=True):
            if ',' in str(source):
                raise ValueError('Commas in Docker bind paths are unsupported')
            args.extend(['--mount', 'type=bind,src=' + str(source) + ',dst=' + target +
                         (',readonly' if readonly else '')])
        public=Path(namespace[namespace.index('/opt') - 1])
        mount(public, '/public-cli')
        mount(public/'codex', '/opt/codex')
        if (public/'rg').is_file():mount(public/'rg', '/opt/rg')
        mount(home, '/home/agent')
        mount(profile, '/home/agent/.codex', False)
        mount(Path(folder)/'workspace', '/workspace', False)
        mount(namespace[namespace.index('/format.json') - 1], '/format.json')
        for name in ('guard_client.py', 'request_guard.py', 'read_policy.py'):
            mount(Path(__file__).parent/name, '/' + name)
        mount(socket_dir, '/hook-control')
        for key, value in dict(HOME='/home/agent', CODEX_HOME='/home/agent/.codex',
                              PATH=path, LANG='C.UTF-8', DIAG_CALL_ID=call,
                              NODE_PATH='/runtime/frontend/node_modules',
                              PYTHONDONTWRITEBYTECODE='1').items():
            args.extend(['--env', key + '=' + value])
        # Forward proxy values by name, without embedding credentials in command logs.
        for key in ('HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY', 'http_proxy', 'https_proxy', 'no_proxy'):
            if key in os.environ:
                args.extend(['--env', key])
        return args + ['--entrypoint', cli[0], self.config['solver_image']] + cli[1:]

    def close(self):
        if not self.stopped:
            stop(self.config['name'], self.archive/'container.json')
            self.stopped = True
