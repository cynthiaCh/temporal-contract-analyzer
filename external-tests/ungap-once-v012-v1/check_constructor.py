#!/usr/bin/env python3
"""Supplemental construction probe on the two exact saved source inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--run', type=Path, required=True)
p.add_argument('--node', default='/Applications/Visual Studio Code.app/Contents/MacOS/Code')
args = p.parse_args()
rows = []
for name, expected in [('original', 1), ('synthetic_late_flag', 2)]:
    folder = args.run/name
    source = (folder/'source.js').read_bytes()
    with tempfile.TemporaryDirectory(prefix='tca-construct-reentry-') as directory:
        module = Path(directory)/'once.mjs'
        module.write_bytes(source)
        result = subprocess.run([args.node, str(HERE/'construct-reentry.mjs'), str(module)],
            env=dict(os.environ, ELECTRON_RUN_AS_NODE='1'), text=True, capture_output=True, timeout=30)
    observation = json.loads(result.stdout)
    assert observation['constructorCalls'] == expected and observation['itemIsItem']
    assert result.returncode == (0 if expected == 1 else 1)
    for filename, content in [('constructor.stdout', result.stdout), ('constructor.stderr', result.stderr)]:
        with (folder/filename).open('x') as target:
            target.write(content)
    rows.append(dict(name=name, source_sha256=hashlib.sha256(source).hexdigest(), observation=observation,
                     exit_code=result.returncode))
record = dict(rows=rows, probes={name: hashlib.sha256((HERE/name).read_bytes()).hexdigest()
    for name in ['check_constructor.py', 'construct-reentry.mjs']},
    limits='Supplemental researcher probe of the same labeled synthetic ordering mutation, not another independent defect.')
with (args.run/'constructor_verification.json').open('x') as target:
    target.write(json.dumps(record, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(record, ensure_ascii=False, indent=2))
