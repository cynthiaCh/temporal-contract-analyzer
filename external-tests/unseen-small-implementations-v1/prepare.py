#!/usr/bin/env python3
"""Freeze a selected convenience sample before running any candidate analysis."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
import urllib.request
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CLONES = Path('/tmp/tca-unseen-20261102')


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def main():
    assert not (HERE/'CASES.json').exists()
    discovery = json.loads((HERE/'discovery/api-snapshots.json').read_text())
    api = discovery['files']
    fixes = {x['id']: x['commit'] for x in discovery['fix_commits']}
    cases = []

    def add(id, implementation, repository, commit, entry, files, label, family, witness, provenance):
        folder = HERE/'snapshots'/id
        folder.mkdir(parents=True, exist_ok=False)
        for path, content in files.items():
            assert not content.startswith('{"message":"Moved Permanently"'), (id, path)
            destination = folder/path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content)
        assert len(files[entry].splitlines()) <= 600
        cases.append(dict(id=id, implementation=implementation, repository=repository, commit=commit,
                          entry=entry, sources=[entry], label=label, family=family, witness=witness,
                          provenance=provenance, source_lines=len(files[entry].splitlines()),
                          source_url=f'https://github.com/{repository}/blob/{commit}/{entry}'))

    for id, repository, entry, family, witness in [
        ('eventemitter3', 'primus/eventemitter3', 'index.js', 'once_listener_reentry', 'event-once'),
        ('mitt', 'developit/mitt', 'src/index.js', 'listener_iteration_mutation', 'mitt-removal'),
        ('memoize-one', 'alexreardon/memoize-one', 'src/index.js', 'cache_exception_state', 'memo-exception-cache'),
        ('p-memoize', 'sindresorhus/p-memoize', 'index.js', 'pending_cache_publication', 'promise-cache')]:
        fix = fixes[id]
        for side, commit, label in [('before', fix['parents'][0]['sha'], 'upstream_bug'),
                                     ('fixed', fix['sha'], 'upstream_fix')]:
            api_id = ('eventemitter3' if side == 'fixed' else 'eventemitter3-before') if id == 'eventemitter3' else id+'-'+side
            files = {entry: api[api_id+'/'+entry]}
            add(id+'-'+side, id, repository, commit, entry, files, label, family, witness,
                dict(fix_url=fix['html_url'], fix_message=fix['commit']['message'],
                     runtime_oracle='Upstream regression/patch behavior, ported to bounded dependency-free assertions.'))

    for side, commit, label in [('before', '422ef6381ae02826e63bcaf9a7c0b299d2187081', 'upstream_bug'),
                                 ('fixed', '1365152d6eade38fe1f4568943d772cc1237f1ef', 'upstream_fix')]:
        add('inflight-'+side, 'inflight', 'isaacs/inflight-DEPRECATED-DO-NOT-USE', commit, 'inflight.js',
            {'inflight.js': api['inflight-'+side+'/inflight.js']}, label, 'callback_exception_cleanup', 'inflight',
            dict(fix_url='https://github.com/isaacs/inflight-DEPRECATED-DO-NOT-USE/commit/1365152d6eade38fe1f4568943d772cc1237f1ef',
                 fix_message='cleanup even if a callback throws (fixes #1)',
                 runtime_oracle='After callback failure, a later request for the same key can start again. This does not require all queued callbacks to run after failure.'))

    once_spec = next(x for x in discovery['specs'] if x['id'] == 'once')
    once_files = {key.removeprefix('once/'): value for key, value in api.items() if key.startswith('once/')}
    add('once-control', 'once', 'isaacs/once', once_spec['ref'], 'once.js', once_files,
        'behavior_control', 'once_listener_reentry', 'strict-once', dict(runtime_oracle='README only-once and once.strict contracts.'))

    for id, clone, repository, entry, files, family, witness in [
        ('memoize-one-control', 'alexreardon--memoize-one', 'alexreardon/memoize-one', 'src/memoize-one.ts',
         ['src/memoize-one.ts', 'src/are-inputs-equal.ts', 'README.md', 'LICENSE', 'package.json'], 'cache_exception_state', 'memo-retry'),
        ('mitt-control', 'developit--mitt', 'developit/mitt', 'src/index.ts',
         ['src/index.ts', 'README.md', 'LICENSE', 'package.json'], 'listener_iteration_mutation', 'mitt-removal'),
        ('memoize-control', 'sindresorhus--mem', 'sindresorhus/memoize', 'index.ts',
         ['index.ts', 'readme.md', 'license', 'package.json'], 'cache_exception_state', 'memo-retry')]:
        directory = CLONES/clone
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=directory, text=True).strip()
        copied = {path: (directory/path).read_text() for path in files if (directory/path).is_file()}
        add(id, id.removesuffix('-control'), repository, commit, entry, copied, 'behavior_control', family, witness,
            dict(runtime_oracle='Published README behavior and independently authored bounded runtime assertions.'))
        if id == 'memoize-one-control':
            cases[-1]['sources'].append('src/are-inputs-equal.ts')

    # Actual published dependencies; no npm install and no lifecycle scripts.
    dependencies = []
    for name, version in [('once', '1.4.0'), ('wrappy', '1.0.2'), ('mimic-fn', '3.1.0'),
                          ('map-age-cleaner', '0.1.3'), ('p-defer', '1.0.0'), ('mimic-function', '5.0.1')]:
        metadata = json.load(urllib.request.urlopen(f'https://registry.npmjs.org/{name}/{version}', timeout=30))
        dist = metadata['dist']
        archive = urllib.request.urlopen(dist['tarball'], timeout=30).read()
        assert hashlib.sha1(archive).hexdigest() == dist['shasum']
        algorithm, expected = dist['integrity'].split('-', 1)
        assert base64.b64encode(hashlib.new(algorithm, archive).digest()).decode() == expected
        folder = HERE/'dependencies'/name
        folder.mkdir(parents=True, exist_ok=False)
        with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as tar:
            for member in tar.getmembers():
                if not member.isfile():
                    continue
                path = PurePosixPath(member.name)
                assert path.parts[0] == 'package' and '..' not in path.parts and not path.is_absolute()
                destination = folder/Path(*path.parts[1:])
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(tar.extractfile(member).read())
        dependencies.append(dict(name=name, version=version, tarball=dist['tarball'], integrity=dist['integrity'],
                                 archive_sha256=hashlib.sha256(archive).hexdigest()))
        print('dependency', name, version, flush=True)

    evidence = HERE/'upstream-evidence'
    evidence.mkdir()
    for key, value in api.items():
        if key.endswith(('.md', 'LICENSE', 'package.json', 'emitter.test.js', 'test.js')):
            p = evidence/key; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(value)
    for id, fix in fixes.items():
        dump(evidence/(id+'-fix.json'), fix)

    # Include the analyzer source snapshot, and verify live source identity at run time.
    frozen = HERE/'frozen-tool'; frozen.mkdir()
    paths = [*sorted((ROOT/'temporal_contract_analyzer').glob('*.py')),
             ROOT/'tools/temporal-contract-analyzer/parse.cjs', ROOT/'tools/temporal-contract-analyzer/package.json',
             ROOT/'tools/temporal-contract-analyzer/package-lock.json']
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    dump(frozen/'FILES.json', hashes)
    with zipfile.ZipFile(frozen/'source.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path, str(path.relative_to(ROOT)))
    dump(HERE/'CASES.json', dict(cases=cases, dependencies=dependencies,
        amendment='Before analysis: include a fifth real fix pair found in the original inflight candidate history; include modern TS controls for the two Flow implementations. 14 snapshots, 7 implementations, 5 correlated historical pairs, 4 current behavior controls.',
        acquisition_notes=['GitHub search API secondary rate limit; public commit/file APIs and local git metadata used.',
                           'Two git clones failed HTTP/2; exact files fetched through the GitHub connector.',
                           'mem is now sindresorhus/memoize; inflight was renamed and deprecated.',
                           'Historical eventemitter3 declares MIT in package.json/README without a standalone license file at this revision.',
                           'Historical Flow sources remain original static inputs; a documented type-only runtime adapter is permitted, never fed to the analyzer.']))
    immutable = [HERE/'PROTOCOL.json', HERE/'CASES.json', *sorted((HERE/'snapshots').rglob('*')),
                 *sorted((HERE/'dependencies').rglob('*')), *sorted(evidence.rglob('*')), *sorted(frozen.rglob('*'))]
    dump(HERE/'INPUT_HASHES.json', {str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in immutable if p.is_file()})
    print([(c['id'], c['source_lines']) for c in cases])


if __name__ == '__main__':
    main()
