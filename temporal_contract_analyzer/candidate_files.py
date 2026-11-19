"""Bounded candidate snapshots shared by development and frozen evaluation."""
import os
from pathlib import Path

from .core import EvidenceError, sha

EXCLUDED = {'node_modules', '__pycache__', 'dist', 'build', 'coverage', 'vendor'}
LIMIT = 25 * 1024 * 1024


def capture(root):
    """Copyable candidate-visible files, including tests and documentation."""
    files, skipped = {}, []
    total = 0
    for current, dirs, names in os.walk(root, followlinks=False):
        base = Path(current)
        for name in list(dirs):
            path = base/name
            relative = path.relative_to(root).as_posix()
            if name.startswith('.') or name in EXCLUDED:
                dirs.remove(name)
                skipped.append(relative + '/')
            elif path.is_symlink():
                raise EvidenceError('Candidate directories do not support symbolic links: ' + relative)
        for name in sorted(names):
            path = base/name
            relative = path.relative_to(root).as_posix()
            if name.startswith('.'):
                skipped.append(relative)
                continue
            if path.is_symlink() or not path.is_file():
                raise EvidenceError('Candidate inputs must be regular files: ' + relative)
            if path.stat().st_size > LIMIT - total:
                raise EvidenceError('Candidate input exceeds 25 MiB')
            raw = path.read_bytes()
            total += len(raw)
            files[relative] = raw
            if len(files) > 1000 or total > LIMIT:
                raise EvidenceError('Candidate input exceeds 1000 files or 25 MiB')
    return files, sorted(skipped)

def inventory(files):
    return {name: sha(raw) for name, raw in sorted(files.items())}

def file_modes(root, files):
    return {name: 0o755 if (root/name).stat().st_mode & 0o111 else 0o644 for name in files}

def write_files(root, files, modes=None):
    root.mkdir(parents=True)
    for name, raw in files.items():
        path = root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        path.chmod((modes or {}).get(name, 0o644))
