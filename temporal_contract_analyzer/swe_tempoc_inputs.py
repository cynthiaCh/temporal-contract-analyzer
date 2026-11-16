"""Candidate-visible inputs from the frozen SWE-TempoC roster, never Gold."""
import json
from pathlib import Path
from .case_catalog import inside
from .core import EvidenceError, sha


def case_input(case_id, root, upstream_loader=None, public_destination=None):
    root = Path(root).resolve()
    rows = json.loads((root/'benchmark/swe-tempoc.json').read_text())['cases']
    matches = [r for r in rows if r['case_id'] == case_id]
    if len(matches) != 1:
        raise EvidenceError('Case must have one frozen SWE-TempoC roster entry')
    row = matches[0]
    manifest_path = inside(root, row['manifest'])
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('id') != case_id:
        raise EvidenceError('SWE-TempoC manifest identity mismatch')
    if manifest_path.name == 'task.json':
        if upstream_loader is not None:
            return upstream_loader(case_id, root, row, manifest_path, manifest)
        raise EvidenceError('Upstream repository task requires its source-archive adapter; no model started')
    relative = manifest['prompt'] if manifest.get('schema_version')=='python-pilot-0.1' else manifest['diagnostic_tasks']['maintenance']['core_prompt']
    prompt = inside(manifest_path.parent, relative)
    candidate = inside(manifest_path.parent, 'base')
    if not candidate.is_dir():
        raise EvidenceError('Missing public base candidate')
    projection=None
    if case_id.startswith('rxjs-asyncsubject-clear-latent-maintenance-port-') and public_destination is not None:
        candidate,projection=project_public_base(candidate,Path(public_destination))
    raw = prompt.read_bytes()
    result=dict(candidate=str(candidate), task=raw.decode('utf-8'), label=case_id,
        case_record=dict(id=case_id, manifest=row['manifest'], source='swe-tempoc',
            condition='latent-maintenance', authorization='ungranted',
            prompt_sha256=sha(raw), source_manifest_sha256=sha(manifest_path.read_bytes()),
            roster_sha256=sha((root/'benchmark/swe-tempoc.json').read_bytes())))
    if projection:result['case_record']['projection']=projection
    return result


def project_public_base(base,destination):
    """All product sources and selected ORIGINAL public tests; no trusted inputs."""
    from .candidate_files import write_files
    names={'README.md','package.json','dependencies.lock.json','rxjs/README.md','rxjs/package.json','rxjs/tsconfig.json',
           'rxjs/spec/subjects/AsyncSubject-spec.ts','rxjs/spec/Subject-spec.ts',
           'rxjs/spec/subjects/BehaviorSubject-spec.ts','rxjs/spec/subjects/ReplaySubject-spec.ts'}
    files={p.relative_to(base).as_posix():p.read_bytes() for p in base.rglob('*') if p.is_file() and
           (p.relative_to(base).as_posix().startswith(('src/','docs/','rxjs/src/')) or p.relative_to(base).as_posix() in names)}
    if 'rxjs/src/internal/AsyncSubject.ts' not in files:raise EvidenceError('Projection missing public product target')
    projection=dict(kind='frozen_base_public_projection_v1',paths=sorted(files),files_sha256={k:sha(v) for k,v in files.items()},
        scope='All original native and RxJS product src, original named public regression tests and public root documents. Unprojected original files restored only in trusted scorer.',
        local_dependency_limit='Full npm dependencies/build fixtures are only available in grader; public source projection is not a complete local installation.')
    files['PROJECTION.md']=(projection['scope']+'\n'+projection['local_dependency_limit']+'\n').encode()
    write_files(destination,files)
    return destination,projection
