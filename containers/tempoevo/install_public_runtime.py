"""Build public toolchains only. Executed inside Docker, never on the host."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys


ROOT = Path('/opt/solver-build')
RUNTIME = Path('/runtime')
VERSIONS = {'16': '16.20.2', '18': '18.17.0', '24': '24.8.0'}


def run(*args, **kwargs):
    subprocess.run([str(arg) for arg in args], check=True, **kwargs)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'amd64') or not ROOT.is_dir():
        raise SystemExit('Run this installer only inside the Linux amd64 solver build')
    manifest = json.loads((ROOT / 'public-inputs.json').read_text())
    # Verify each staged source before executing the benchmark's public installer.
    for relative, expected in manifest['files'].items():
        relative_path = Path(relative)
        if relative_path.is_absolute() or '..' in relative_path.parts:
            raise ValueError('Invalid public input path')
        if relative.startswith('parser/'):
            target = RUNTIME / 'frontend' / relative.removeprefix('parser/')
        elif relative in ('install_public_runtime.py', 'smoke_public_runtime.py'):
            target = ROOT / relative
        elif relative == 'Dockerfile':
            continue  # Build definition: recorded in provenance, not copied into the image.
        else:
            target = ROOT / relative
        if digest(target) != expected:
            raise ValueError('Changed public build input: ' + relative)

    run(sys.executable, '-B', ROOT / 'tools/setup_swe_tempoc.py',
        '--node', VERSIONS['16'], '--node', VERSIONS['18'],
        '--node', VERSIONS['24'], '--js')
    RUNTIME.mkdir(exist_ok=True)
    for major, version in VERSIONS.items():
        source = ROOT / '.swe-tempoc/toolchains' / ('node-v' + version + '-linux-x64')
        source.rename(RUNTIME / ('node' + major))
    (RUNTIME / 'node').symlink_to(RUNTIME / 'node16/bin/node')
    (RUNTIME / 'bin').mkdir(exist_ok=True)

    # Keep framework dependency resolution inside its own frozen tree. Use the
    # analyzer's parser lock at NODE_PATH's root, instead of replacing its pinned
    # parser/compiler with similarly named framework transitive dependencies.
    frameworks = RUNTIME / 'frameworks'
    (ROOT / '.swe-tempoc/js').rename(frameworks)
    frontend = RUNTIME / 'frontend'
    frozen_lock = digest(frontend / 'package-lock.json')
    node = RUNTIME / 'node16/bin/node'
    npm = RUNTIME / 'node16/lib/node_modules/npm/bin/npm-cli.js'
    env = dict(os.environ, PATH=str(node.parent) + ':' + os.environ.get('PATH', ''))
    run(node, npm, 'ci', '--ignore-scripts', '--no-audit', '--no-fund',
        '--registry=https://registry.npmjs.org', cwd=frontend, env=env)
    if digest(frontend / 'package-lock.json') != frozen_lock:
        raise ValueError('Parser installation changed its frozen lockfile')
    for source in sorted((frameworks / 'node_modules').iterdir()):
        if source.name.startswith('.'):
            continue
        target = frontend / 'node_modules' / source.name
        if source.name.startswith('@'):
            target.mkdir(exist_ok=True)
            for package in source.iterdir():
                destination = target / package.name
                if not destination.exists() and not destination.is_symlink():
                    destination.symlink_to(package)
        elif not target.exists() and not target.is_symlink():
            target.symlink_to(source)
    (RUNTIME / 'rebuild-provenance.json').write_text(json.dumps(dict(
        schema_version='tempoevo-public-solver-rebuild-v1',
        historical_image_equivalence=False, public_inputs=manifest,
        node_archive_sha256={major: (RUNTIME / ('node' + major) / 'ARCHIVE-SHA256').read_text().strip()
                            for major in VERSIONS},
        readiness='Requires image inspection, offline Codex/code-host probe and case calibration before model execution',
    ), indent=2) + '\n')


if __name__ == '__main__':
    main()
