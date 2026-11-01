#!/usr/bin/env python3
"""Reproduce the small pinned-project pilot without installing dependencies."""
import argparse
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import urllib.request

BASE = Path(__file__).resolve().parent
ANALYZER = BASE.parents[1]
SOURCE = json.loads((BASE / 'SOURCE.json').read_text())


def runtime(explicit):
    candidates = [explicit] if explicit else [shutil.which('node'), '/Applications/Visual Studio Code.app/Contents/MacOS/Code']
    for candidate in candidates:
        if not candidate or not Path(candidate).exists():
            continue
        env = dict(os.environ)
        if Path(candidate).name == 'Code':
            env['ELECTRON_RUN_AS_NODE'] = '1'
        version = subprocess.run([candidate, '--version'], env=env, capture_output=True, text=True, timeout=10)
        if version.returncode == 0 and version.stdout.startswith('v') and int(version.stdout[1:].split('.')[0]) >= 22:
            return candidate, env, version.stdout.strip()
    raise SystemExit('Need an existing Node 22+ runtime; pass --node PATH. No runtime will be installed.')


def fetch_if_missing():
    target = BASE / 'upstream'
    if (target / 'index.js').exists():
        return
    if target.exists() and any(target.iterdir()):
        raise SystemExit('Refusing to overwrite a partial upstream directory.')
    request = urllib.request.Request(SOURCE['archive'], headers={'User-Agent': 'temporal-contract-analyzer-pilot'})
    with urllib.request.urlopen(request, timeout=40) as response:
        data = response.read(2_000_001)
    if len(data) > 2_000_000:
        raise SystemExit('Unexpected archive size')
    target.mkdir(exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        for member in archive.getmembers():
            parts = PurePosixPath(member.name).parts[1:]
            if not parts or '..' in parts or member.issym() or member.islnk():
                continue
            destination = target.joinpath(*parts)
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(archive.extractfile(member).read())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', help='Existing Node 22+ executable')
    args = parser.parse_args()
    node, env, version = runtime(args.node)
    fetch_if_missing()
    from datetime import datetime, timezone
    output = BASE / 'reruns' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output.mkdir(parents=True)
    scan_command = [sys.executable, '-B', '-m', 'temporal_contract_analyzer', 'reports', 'scan',
                    str(BASE / 'upstream/index.js'), '--store', str(BASE / 'reports'),
                    '--project', 'p-debounce', '--label', 'v6.0.0 reproducibility run', '--node', node]
    scan = subprocess.run(scan_command, cwd=ANALYZER, env=env, capture_output=True, text=True, timeout=60)
    (output / 'scan.log').write_text(scan.stdout + scan.stderr)
    if scan.returncode:
        raise SystemExit('Scan failed; see ' + str(output / 'scan.log'))
    metadata = json.loads(scan.stdout)
    (output / 'SCAN.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    statuses = {}
    for name, command in [('upstream-tests', [node, '--test', 'test.js']), ('behavior-probes', [node, str(BASE / 'probe.mjs')])]:
        result = subprocess.run(command, cwd=BASE / 'upstream', env=env, capture_output=True, text=True, timeout=90)
        (output / (name + '.log')).write_text(result.stdout + result.stderr)
        statuses[name] = result.returncode
    (output / 'RUN.json').write_text(json.dumps({'node': node, 'version': version, 'exitCodes': statuses,
                                               'reportId': metadata['report_id'], 'modelCalls': 0,
                                               'qualification': 'Exploratory source and behavior probe; xo and tsd not run.'}, indent=2) + '\n')
    print(json.dumps({'output': str(output), 'reportId': metadata['report_id'], 'exitCodes': statuses}, ensure_ascii=False, indent=2))
    return 0 if not any(statuses.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
