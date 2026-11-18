"""Zero-model image smoke test. This does not certify a case or Codex binary."""
import json
import os
from pathlib import Path
import platform
import subprocess
import sys


def check(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()


def main():
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'amd64'):
        raise SystemExit('The solver must be Linux amd64')
    for path in ('/opt/swe-tempoc', '/evaluation', '/var/run/docker.sock', '/run/docker.sock'):
        if Path(path).exists():
            raise RuntimeError('Forbidden solver path: ' + path)
    import fcntl  # Linux file-locking primitive used by the real runtime.
    observed = {}
    for major, expected in [('16', 'v16.20.2'), ('18', 'v18.17.0'), ('24', 'v24.8.0')]:
        actual = check('/runtime/node' + major + '/bin/node', '--version')
        if actual != expected:
            raise RuntimeError('Wrong Node version: ' + actual)
        observed['node' + major] = actual
    env = dict(os.environ, NODE_PATH='/runtime/frontend/node_modules')
    script = '''const assert=require('assert');
const expected={'@babel/parser':'7.29.8','@vue/compiler-sfc':'3.5.13',
react:'18.3.1','react-dom':'18.3.1',vue2:'2.7.16',vue3:'3.4.38',jquery:'3.7.1',jsdom:'22.1.0',esbuild:'0.21.5'};
for(const [name,version] of Object.entries(expected)){
  assert.strictEqual(require(name+'/package.json').version,version,name);
  require(name);
}
assert.ok(require('@babel/parser').parse('const value: number = 1',{plugins:['typescript']}));
assert.strictEqual(require('@vue/compiler-sfc').parse('<script>export default {}</script>').errors.length,0);
console.log(JSON.stringify(expected));'''
    observed['packages'] = json.loads(subprocess.check_output(
        ['/runtime/node16/bin/node', '-e', script], text=True, env=env))
    for name, command in {'go': ['/opt/go1.13.8/bin/go', 'version'],
                          'ruby': ['ruby', '--version'], 'php': ['php', '--version'],
                          'java': ['java', '-version'], 'javac': ['javac', '-version'],
                          'git': ['git', '--version'], 'rg': ['rg', '--version']}.items():
        observed[name] = check(*command).splitlines()[0]
    if not observed['go'].startswith('go version go1.13.8 '):
        raise RuntimeError('Wrong Go version')
    print(json.dumps(dict(valid=True, model_calls=0, python=sys.version.split()[0],
                         runtimes=observed, codex_binary_tested=False, case_calibration_tested=False)))


if __name__ == '__main__':
    main()
