"""Explicit submission of immutable candidates to a shared review store. No models."""
import fcntl
import json
import os
from pathlib import Path
import tempfile

from . import archive, experience_memory as memory, experience_screening as screening
from .core import EvidenceError


def publish(path, raw):
    """Publish a complete new file; callers hold the store's decision lock."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.submit-', dir=str(path.parent))
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def submit(source_store, target_store, code):
    """Copy one candidate, needed ancestors/evidence and screening; never approvals."""
    source, target = (Path(p).expanduser().resolve() for p in (source_store, target_store))
    if source == target:
        raise EvidenceError('Candidate is already in this store; open its content review directly')
    bundles = {b['sha256']: b for b in memory.records(source)}
    candidate = bundles.get(code)
    if candidate is None or candidate['review']['status'] != 'candidate':
        raise EvidenceError('Submit an existing immutable candidate record, not a review decision')
    chain = []
    current = candidate
    while current is not None:
        chain.append(current)
        current = bundles.get(current['parent_sha256'])
    chain.reverse()
    score_path = source/'screening'/(code+'.json')
    score = screening.read(source, code)
    if score is not None:
        if score.get('schema_version') != screening.VERSION or score.get('gate') != screening.evaluate(score):
            raise EvidenceError('Screening must retain its actual recomputed gate, including pending/blocked')
    usage_path = source/'development-usage.json'
    usage = json.loads(usage_path.read_text()) if usage_path.exists() else []
    if not isinstance(usage, list):
        raise EvidenceError('Malformed development exposure registry')
    usage = [row for row in usage if isinstance(row, dict) and row.get('batch_id') == candidate['version']]
    for row in usage:
        if not isinstance(row.get('cases'),dict) or not row['cases']:
            raise EvidenceError('Candidate development exposure is incomplete')
        for case in row['cases'].values():
            lineage=case.get('lineage',{}) if isinstance(case,dict) else {}
            if not memory.text(lineage.get('source_unit')):
                raise EvidenceError('Missing development source unit')
            memory.strings(lineage.get('derived_from'),'development source ancestry')
    # Validate everything before publishing even the first record. Read source
    # blobs once; all identities/digests are existing record IDs, not new chains.
    blobs = {s['sha256']:(source/'sources'/s['sha256']).read_bytes()
             for bundle in chain for s in bundle['audit']['sources']}
    record_bytes = {b['sha256']:(source/'records'/(b['sha256']+'.json')).read_bytes() for b in chain}
    memory.records(target)
    with (target/'decision.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        existing = {b['sha256']:b for b in memory.records(target)}
        identities = {(b['id'],b['version']):b['sha256'] for b in existing.values()}
        missing = []
        for bundle in chain:
            identity = (bundle['id'],bundle['version'])
            if identity in identities and identities[identity] != bundle['sha256']:
                raise EvidenceError('Immutable experience version conflicts with the review store')
            if bundle['sha256'] not in existing:
                same_id = any(b['id']==bundle['id'] for b in existing.values())
                parent = existing.get(bundle['parent_sha256'])
                if (same_id or bundle['parent_sha256'] is not None) and (parent is None or parent['id']!=bundle['id']):
                    raise EvidenceError('Submission has an unrelated or missing parent')
                missing.append(bundle)
                existing[bundle['sha256']] = bundle
            identities[identity] = bundle['sha256']
        for digest, raw in blobs.items():
            path = target/'sources'/digest
            if path.exists() and path.read_bytes() != raw:
                raise EvidenceError('Conflicting retained source; no submission was published')
        target_score = target/'screening'/(code+'.json')
        if score is not None and target_score.exists() and json.loads(target_score.read_text()) != score:
            raise EvidenceError('Screening already exists with different evidence; do not overwrite')
        target_usage = target/'development-usage.json'
        prior_usage = json.loads(target_usage.read_text()) if target_usage.exists() else []
        if not isinstance(prior_usage, list):
            raise EvidenceError('Malformed target development exposure registry')
        merged_usage = list(prior_usage)
        for row in usage:
            matches = [old for old in merged_usage if isinstance(old,dict) and old.get('batch_id')==row['batch_id']]
            if matches and matches != [row]:
                raise EvidenceError('Development exposure record conflicts; do not rewrite history')
            if not matches:
                merged_usage.append(row)
        for digest, raw in blobs.items():
            path = target/'sources'/digest
            if not path.exists():
                publish(path, raw)
        # Exposure precedes candidate visibility so final evaluation cannot lose
        # the development-source exclusion on a partial submission.
        if merged_usage != prior_usage:
            archive.atomic_json(target_usage, merged_usage)
        if score is not None and not target_score.exists():
            publish(target_score, score_path.read_bytes())
        for bundle in missing:
            publish(target/'records'/(bundle['sha256']+'.json'), record_bytes[bundle['sha256']])
    return dict(candidate_sha256=code, source_store=str(source), review_store=str(target),
        record_path=str(target/'records'/(code+'.json')),
        added_records=[b['sha256'] for b in missing], already_recorded=not missing,
        screening_status=None if score is None else screening.evaluate(score)['status'],
        decisions_copied=False, activation_changed=False,
        next_action='Open this exact version in the target store for named content review; submission is not acceptance or activation')
