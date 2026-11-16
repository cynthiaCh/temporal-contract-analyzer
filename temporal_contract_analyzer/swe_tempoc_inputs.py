"""Candidate-visible inputs from the frozen SWE-TempoC roster, never Gold."""
import json
from pathlib import Path
from .case_catalog import inside
from .core import EvidenceError, sha


def case_input(case_id, root, upstream_loader=None):
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
    prompt = inside(manifest_path.parent, manifest['diagnostic_tasks']['maintenance']['core_prompt'])
    candidate = inside(manifest_path.parent, 'base')
    if not candidate.is_dir():
        raise EvidenceError('Missing public base candidate')
    raw = prompt.read_bytes()
    return dict(candidate=str(candidate), task=raw.decode('utf-8'), label=case_id,
        case_record=dict(id=case_id, manifest=row['manifest'], source='swe-tempoc',
            condition='latent-maintenance', authorization='ungranted',
            prompt_sha256=sha(raw), source_manifest_sha256=sha(manifest_path.read_bytes()),
            roster_sha256=sha((root/'benchmark/swe-tempoc.json').read_bytes())))
