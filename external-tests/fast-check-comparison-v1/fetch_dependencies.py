#!/usr/bin/env python3
"""Fetch exact test-only published artifacts; never execute install scripts."""
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
import urllib.request

HERE = Path(__file__).resolve().parent
rows = []
for name, version in [('fast-check', '4.10.2'), ('pure-rand', '8.0.0')]:
    metadata = json.load(urllib.request.urlopen(f'https://registry.npmjs.org/{name}/{version}', timeout=30))
    dist = metadata['dist']
    data = urllib.request.urlopen(dist['tarball'], timeout=30).read()
    algorithm, expected = dist['integrity'].split('-', 1)
    assert base64.b64encode(hashlib.new(algorithm, data).digest()).decode() == expected
    destination = HERE/'dependencies'/name
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        for member in archive.getmembers():
            if not member.isfile(): continue
            path = PurePosixPath(member.name)
            assert path.parts[0] == 'package' and '..' not in path.parts and not path.is_absolute()
            target = destination/Path(*path.parts[1:])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.extractfile(member).read())
    rows.append(dict(name=name,version=version,tarball=dist['tarball'],integrity=dist['integrity']))
(HERE/'DEPENDENCIES.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
