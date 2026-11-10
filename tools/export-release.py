"""Export maintained source only. Never copy research records or run models."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
TREES = ('temporal_contract_analyzer', 'tests', 'case-clusters', 'templates',
         'examples', 'docs', 'tools', 'vscode-extension')
FILES = ('README.md', 'MASTER_PROMPT.md', 'pyproject.toml', 'setup.cfg',
         'setup.py', '.gitignore', 'experiments/local-cases.json',
         '启动Codex实验工作台.command', '启动边界审查工作台.command')
SKIP = {'.git', '__pycache__', 'node_modules', '.venv', '.vscode-test',
        'build', 'dist', 'runtime'}
PRIVATE_DOCS = {'docs/CLEANUP.md', 'docs/RELEASE_SCOPE.md'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources():
    paths = list(FILES)
    for tree in TREES:
        for folder, dirs, files in os.walk(str(ROOT / tree), followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in SKIP and not d.endswith('.egg-info'))
            if any((Path(folder) / d).is_symlink() for d in dirs):
                raise ValueError('Directory symlinks are not supported in the export')
            for name in sorted(files):
                path = Path(folder) / name
                relative = path.relative_to(ROOT).as_posix()
                if (relative in PRIVATE_DOCS or name.endswith(('.pyc', '.pyo', '.vsix'))
                        or name in {'.DS_Store', 'auth.json', '.env'}):
                    continue
                paths.append(relative)
    return sorted(set(paths))


def export(destination):
    destination = Path(destination).expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError('Export destination must not exist')
    if destination == ROOT or ROOT in destination.resolve().parents:
        raise ValueError('Export must be outside the source checkout')
    paths = sources()
    destination.mkdir(parents=True)
    manifest = []
    for relative in paths:
        source, target = ROOT / relative, destination / relative
        if not source.is_file():
            raise ValueError('Missing required source file: ' + relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        record = dict(path=relative, sha256=digest(source), bytes=source.stat().st_size)
        if source.is_symlink():
            link = os.readlink(str(source))
            if (Path(link).is_absolute() or source.resolve() != ROOT / 'temporal_contract_analyzer/prompts/MASTER_PROMPT.md'
                    or relative != 'MASTER_PROMPT.md'):
                raise ValueError('Unexpected source symlink: ' + relative)
            target.symlink_to(link)
            record['symlink'] = link
        else:
            shutil.copy2(str(source), str(target))
        manifest.append(record)
    for record in manifest:
        if digest(destination / record['path']) != record['sha256']:
            raise ValueError('Export verification failed: ' + record['path'])
    (destination / 'release-manifest.json').write_text(json.dumps(dict(
        schema_version='tca-source-export-1', files=manifest,
        research_memory_included=False, installed_dependencies_included=False,
        license_selected=False), indent=2) + '\n', encoding='utf-8')
    return dict(files=len(manifest), bytes=sum(r['bytes'] for r in manifest))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python3 -B tools/export-release.py /path/to/new-export')
    print(json.dumps(export(sys.argv[1])))
