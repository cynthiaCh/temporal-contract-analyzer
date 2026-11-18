"""Stage trusted benchmark scoring sources, without archives, runs or credentials."""
import argparse
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

REPO = Path(__file__).resolve().parents[2]
CASE_DIRECTORIES = {'base', 'oracle', 'reference', 'mutants', 'negative-controls',
                    'prompts', 'provenance', 'calibration', 'conditions'}
SKIP = {'.git', 'node_modules', '__pycache__', '.venv'}


def local_path(path):
    """Extended Windows paths preserve deeply nested upstream source files."""
    return Path('\\\\?\\' + str(path)) if os.name == 'nt' and not str(path).startswith('\\\\?\\') else path


def selection_ids(selection, locations):
    with Path(selection).open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    ids = [row['case_id'] for row in rows]
    if not ids or len(ids) != len(set(ids)) or not set(ids) <= locations.keys():
        raise ValueError('Selection must contain distinct registered cases')
    for row in rows:
        if row.get('manifest') and row['manifest'] != locations[row['case_id']]:
            raise ValueError('Selection manifest differs from central roster: ' + row['case_id'])
    return ids


def git_contents(benchmark, revision, sources):
    """Restore Git blobs, accepting only checkout newline conversion locally."""
    paths = sorted(p.relative_to(benchmark).as_posix() for p in sources)
    query = ''.join(revision + ':' + name + '\n' for name in paths).encode('utf-8')
    result = subprocess.check_output(['git', '--git-dir=' + str(benchmark / '.git'),
                                      'cat-file', '--batch'], input=query)
    offset, content, missing = 0, {}, []
    for name in paths:
        end = result.index(b'\n', offset)
        header = result[offset:end].decode('utf-8')
        offset = end + 1
        local = local_path(benchmark / name).read_bytes()
        if header.endswith(' missing'):
            # Public installers can be supplied alongside the frozen checkout.
            content[name] = local
            missing.append(name)
            continue
        _, kind, size = header.split()
        if kind != 'blob':
            raise ValueError('Expected a regular Git blob: ' + name)
        size = int(size)
        data = result[offset:offset + size]
        offset += size + 1
        if local != data and local.replace(b'\r\n', b'\n') != data:
            raise ValueError('Benchmark input has changes beyond checkout newlines: ' + name)
        content[name] = data
    return content, missing


def prepare(benchmark, output, selection=None):
    benchmark, output = Path(benchmark).resolve(), Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise ValueError('Use a new build context directory')
    if any(output.resolve() == root or root in output.resolve().parents for root in (benchmark, REPO)):
        raise ValueError('Build context must be outside both source repositories')
    roster = json.loads((benchmark / 'benchmark/swe-tempoc.json').read_text(encoding='utf8'))['cases']
    locations = {row['case_id']: row['manifest'] for row in roster}
    if len(locations) != len(roster):
        raise ValueError('Duplicate central roster identities')
    selection = Path(selection) if selection else REPO / 'examples/tempoevo-v4/case-selections/gpt61-sol-medium-hardest50-20261029/selected_50_cases.csv'
    scoring_ids = selection_ids(selection, locations)
    index = subprocess.check_output(['git', '-C', str(benchmark), 'ls-files', '-s', '-z']).decode('utf8')
    tracked = {row.split('\t', 1)[1]: row.split('\t', 1)[0].split()[0] for row in index.split('\0') if row}
    sources = set(benchmark.glob('*.py'))
    # The benchmark catalog validates every cluster arm, even if it is not in
    # the scoring roster. Metadata alone does not admit its hidden resources.
    sources.update(benchmark/name for name in tracked
        if Path(name).name in ('case.json','task.json','case-record.json')
        and (len(Path(name).parts)==3 and Path(name).parts[0]=='cases'
             or len(Path(name).parts)==5 and Path(name).parts[0]=='case-clusters' and Path(name).parts[2]=='arms'))
    sources.update([benchmark / 'benchmark/swe-tempoc.json', benchmark / 'benchmark/Dockerfile',
                    benchmark / 'tools/setup_swe_tempoc.py',
                    benchmark / 'experiments/temporal-diagnostics-v1/corpus.json'])
    for cluster in (benchmark / 'case-clusters').iterdir():
        if cluster.is_dir():
            sources.update(p for p in cluster.iterdir() if p.is_file() and p.suffix in ('.json', '.md'))
    # Native transfer bridges read frozen version receipts outside their arms.
    metadata = subprocess.check_output(['git', '--git-dir=' + str(benchmark / '.git'),
        'ls-files', '-z', '--', 'case-clusters/*/expansion/**/runtime-versions.json'])
    sources.update(benchmark / name.decode('utf-8') for name in metadata.split(b'\0') if name)
    for name in ['document-submit-ports', 'vanilla-js', 'vue2', 'vue3', 'react18']:
        sources.update(benchmark / 'runtimes' / name / p for p in ['package.json', 'package-lock.json'])
    for cid, relative in locations.items():
        # Keep catalogue metadata, but do not bundle other experiments' source
        # trees or controls. The explicit selection determines scoring scope.
        path = Path(relative)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Unsafe registered manifest')
        manifest_path = benchmark / path
        sources.add(manifest_path)
        if cid not in scoring_ids:
            continue
        case_root = manifest_path.parent
        prefix = case_root.relative_to(benchmark).as_posix() + '/'
        for name, mode in tracked.items():
            if not name.startswith(prefix):
                continue
            parts = Path(name[len(prefix):]).parts
            if (len(parts) == 1 or parts[0] in CASE_DIRECTORIES) and not set(parts) & SKIP:
                if mode not in ('100644', '100755'):
                    raise ValueError('Unsupported tracked file mode: ' + name)
                sources.add(benchmark / name)
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if manifest['id'] != cid:
            raise ValueError('Manifest identity mismatch')
        sources.update(case_root / p for p in manifest.get('files_sha256', {}))
        if manifest.get('calibration_receipt'):
            sources.add(benchmark / manifest['calibration_receipt'])
    extras = {
        'Dockerfile': REPO / 'containers/tempoevo/Dockerfile.grader',
        'install_grader_runtime.py': REPO / 'containers/tempoevo/install_grader_runtime.py',
    }
    files = {('benchmark-source/' + p.relative_to(benchmark).as_posix()): p for p in sources}
    files.update(extras)
    revision = subprocess.check_output(['git', '--git-dir=' + str(benchmark / '.git'), 'rev-parse', 'HEAD'], text=True).strip()
    canonical, untracked = git_contents(benchmark, revision, sources)
    output.mkdir(parents=True, exist_ok=False)
    hashes, total, checked_parents = {}, 0, set()
    # A tar context avoids the Windows MAX_PATH limit for nested case names.
    with tarfile.open(output / 'benchmark-source.tar', 'w') as archive:
        for name, source in sorted(files.items()):
            root = benchmark if name.startswith('benchmark-source/') else REPO
            physical = local_path(source)
            if not physical.is_file() or physical.is_symlink() or not source.absolute().is_relative_to(root):
                raise ValueError('Unsafe/missing grader input: ' + str(source))
            for parent in source.parents:
                if parent not in checked_parents:
                    if local_path(parent).is_symlink():
                        raise ValueError('Symlinked input parent: ' + str(source))
                    checked_parents.add(parent)
            if source.name.startswith('.env') or set(source.parts) & SKIP:
                raise ValueError('Excluded grader input: ' + str(source))
            content = canonical[name.removeprefix('benchmark-source/')] if name.startswith('benchmark-source/') else source.read_bytes()
            if name.startswith('benchmark-source/'):
                info = tarfile.TarInfo(name.removeprefix('benchmark-source/'))
                info.size, info.mode = len(content), 0o644
                archive.addfile(info, io.BytesIO(content))
            else:
                (output / name).write_bytes(content)
            hashes[name] = hashlib.sha256(content).hexdigest()
            total += len(content)
    record = dict(schema_version='tempoevo-trusted-grader-inputs-v1', benchmark_root=str(benchmark),
                  benchmark_revision=revision, catalogue_cases=len(locations), files=hashes,
                  scoring_case_ids=scoring_ids, selection_sha256=hashlib.sha256(selection.read_bytes()).hexdigest(),
                  selection_path=str(selection.resolve()),
                  case_manifests={cid: locations[cid] for cid in scoring_ids},
                  checkout_policy='Git blob bytes; working-tree-only inputs explicitly listed; non-newline edits rejected',
                  working_tree_only_inputs=untracked,
                  policy='Checked-in scoring sources and registered controls; no source archives, experiment runs, .git or credentials',
                  historical_image_equivalence=False, model_calls=0)
    (output / 'grader-inputs.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    return dict(status='staged_not_built', context=str(output), files=len(files), source_bytes=total,
                scoring_cases=len(scoring_ids), benchmark_revision=revision, model_calls=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--selection', type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.benchmark_root, args.output, args.selection), indent=2))
