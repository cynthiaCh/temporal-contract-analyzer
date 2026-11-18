"""Reuse hash-matched public dependencies; invoke the unchanged benchmark setup."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('/opt/swe-tempoc')
PUBLIC = Path('/opt/solver-build')
inputs = json.loads((PUBLIC / 'public-inputs.json').read_text())['files']
for name, digest in inputs.items():
    if name.startswith(('tools/', 'runtimes/')):
        original = (PUBLIC / name).read_bytes()
        staged = (ROOT / name).read_bytes()
        if hashlib.sha256(original).hexdigest() != digest:
            raise ValueError('Public runtime provenance changed: ' + name)
        if staged != original and staged != original.replace(b'\r\n', b'\n'):
            raise ValueError('Public runtime input differs from the solver build: ' + name)

# Keep all oracle, candidate, reference and manifest bytes unchanged. Only the
# dependency layout is reconstructed here, using the benchmark's own installer.
sys.path.insert(0, str(ROOT / 'tools'))
import setup_swe_tempoc as setup

for version, short in [('16.20.2', '16'), ('18.17.0', '18'), ('24.8.0', '24')]:
    setup.link('/runtime/node' + short,
               ROOT / '.swe-tempoc/toolchains' / ('node-v' + version + '-linux-x64'))

shared = ROOT / '.swe-tempoc/js'
shared.mkdir(parents=True)
for name in ['package.json', 'package-lock.json']:
    (shared / name).write_bytes((ROOT / 'runtimes/document-submit-ports' / name).read_bytes())
setup.link('/runtime/frameworks/node_modules', shared / 'node_modules')
# npm ci is intentionally retained: the upstream installer verifies unchanged
# lockfiles and creates all historical runtime aliases used by the probes.
subprocess.run([sys.executable, '-B', str(ROOT / 'tools/setup_swe_tempoc.py'),
                '--node', '16.20.2', '--node', '18.17.0', '--node', '24.8.0',
                '--js', '--native'], check=True)
