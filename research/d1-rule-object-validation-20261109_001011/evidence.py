"""Offline, training-only reflection handoff. No model, runner, or registry writes.

Evidence pointers prove provenance, not natural-language entailment. Admission
also requires a hash-bound execution-agent review and development observations.
"""
import hashlib
import json
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def object_digest(value):
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')).encode())


def pointer(document, path):
    if path == '':
        return document
    if not path.startswith('/'):
        raise ValueError('JSON pointer must start with /')
    for part in path[1:].split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        document = document[int(part)] if isinstance(document, list) else document[part]
    return document


ALLOWED_ROLES = {'training_task', 'training_source', 'training_document',
                 'training_contract', 'training_standard', 'training_score',
                 'training_patch', 'training_public_delivery', 'training_rejection_review'}
KINDS = {'documented_requirement', 'source_fact', 'observed_result',
         'preservation_inference', 'hypothesis', 'unknown'}


def verify_ledger(root, ledger):
    root = Path(root).resolve()
    files = ledger['files']
    for name, record in files.items():
        path = (root / name).resolve()
        if root not in path.parents or record['role'] not in ALLOWED_ROLES:
            raise ValueError('untrusted provenance: ' + name)
        if digest(path.read_bytes()) != record['sha256']:
            raise ValueError('input digest mismatch: ' + name)
    entries = ledger['entries']
    if len({e['id'] for e in entries}) != len(entries):
        raise ValueError('duplicate evidence ID')
    by_id = {e['id']: e for e in entries}
    for e in entries:
        if e['kind'] not in KINDS or not e['author']:
            raise ValueError('untyped evidence')
        if e['kind'] not in {'unknown', 'hypothesis'} and not e['anchors']:
            raise ValueError('unsupported evidence')
        for anchor in e['anchors']:
            name = anchor['file']
            if name not in files:
                raise ValueError('unlisted evidence file')
            content = (root / name).read_text()
            if anchor['type'] == 'lines':
                start, end = anchor['start'], anchor['end']
                if not 1 <= start <= end <= len(content.splitlines()):
                    raise ValueError('line bounds')
                actual = '\n'.join(content.splitlines()[start - 1:end])
                if actual != anchor['quote']:
                    raise ValueError('source quotation mismatch')
            elif anchor['type'] == 'json':
                if pointer(json.loads(content), anchor['pointer']) != anchor['value']:
                    raise ValueError('observation mismatch')
            else:
                raise ValueError('unknown anchor type')
        if any(x not in by_id for x in e.get('related', [])):
            raise ValueError('unknown related evidence')
    for constraint in ledger['constraints']:
        if not constraint['evidence'] or any(x not in by_id for x in constraint['evidence']):
            raise ValueError('unsupported preservation constraint')
    return by_id


def assemble_payload(root, ledger, feedback):
    """Only explicitly role-tagged, hash-pinned training files enter payload."""
    verify_ledger(root, ledger)
    if feedback != rebuild_feedback(root, ledger):
        raise ValueError('feedback differs from frozen training observations')
    materials = []
    for name, record in ledger['files'].items():
        materials.append({'role': record['role'], 'content': (Path(root) / name).read_text(),
                          'artifact': name, 'sha256': record['sha256']})
    return {'schema': 'training-reflection-handoff-3', 'materials': materials,
            'feedback': feedback, 'evidence': ledger['entries'],
            'constraints': ledger['constraints'],
            'causality': 'No independently verified cause. Outcomes and multi-hunk patches do not isolate causation.',
            'public_delivery_status': 'Unverified model claims, not observations.'}


def rebuild_feedback(root, ledger):
    from feedback import feedback
    spec = ledger['feedback_inputs']
    def read(name, role):
        if ledger['files'][name]['role'] != role:
            raise ValueError('feedback input role mismatch')
        return json.loads((Path(root) / name).read_text())
    result = feedback(read(spec['original'], 'training_score'),
                      [read(name, 'training_score') for name in spec['repairs']],
                      read(spec['standards'], 'training_standard'))
    result['causal_status'] = 'No cause independently verified; see evidence ledger for separately authored source reasoning.'
    return result

