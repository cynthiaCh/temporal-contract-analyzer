"""Explicit operator decisions and frozen active research experience views."""
import json
import fcntl
from pathlib import Path
from copy import deepcopy

from . import archive, experience_memory as memory
from .core import EvidenceError, canonical


def decisions(store):
    store = Path(store)
    bundles = {b['sha256']:b for b in memory.records(store)}
    result = []
    for path in sorted((store/'decisions').glob('*.json')):
        row = json.loads(path.read_text(encoding='utf-8'))
        expected = memory.digest(canonical({k:v for k,v in row.items() if k!='sha256'}))
        if row.get('sha256') != expected or path.name != f"{row.get('sequence', 0):08d}-{expected}.json" \
                or row.get('sequence') != len(result)+1 or row.get('candidate_sha256') not in bundles:
            raise EvidenceError('Invalid expert decision history')
        validate_decision(row, bundles[row['candidate_sha256']])
        result.append(row)
    return result


def validate_decision(row, bundle):
    if not memory.text(row.get('reviewer')):
        raise EvidenceError('A named operator is required')
    if not isinstance(row.get('reason'), str):
        raise EvidenceError('Review reason must be text; it may be empty')
    if row.get('decision') not in ('accept', 'reject', 'revise') or row.get('scope') not in ('research', 'exploratory'):
        raise EvidenceError('Invalid expert decision or research scope')
    findings = row.get('rules')
    if not isinstance(findings, list) or len(findings) != len(bundle['rules']):
        raise EvidenceError('Expert must review every rule')
    expected = [r['id'] for r in bundle['rules']]
    if [r.get('rule_id') for r in findings if isinstance(r, dict)] != expected:
        raise EvidenceError('Expert rule findings must match the frozen candidate order')
    for finding in findings:
        if set(finding) != {'rule_id', 'supported', 'reason'} or type(finding['supported']) is not bool \
                or not isinstance(finding['reason'], str):
            raise EvidenceError('Each rule needs a support finding and a text reason, which may be empty')
    if row['decision'] == 'accept' and (not all(r['supported'] for r in findings)
            or bundle['review']['status'] == 'rejected'):
        raise EvidenceError('Unsupported or rejected rules cannot be activated')
    report = row.get('report_sha256')
    if report is not None and (not isinstance(report, str) or len(report) != 64):
        raise EvidenceError('Invalid review report digest')


def decide(store, candidate_sha256, request, report_sha256=None):
    """Operator entry point. Never called by automatic reflection or repair."""
    if not isinstance(request, dict) or set(request) != {'reviewer', 'decision', 'reason', 'scope', 'rules'}:
        raise EvidenceError('Expert request must contain reviewer, decision, reason, scope and per-rule findings')
    store = Path(store)
    with (store/'decision.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        bundles = {b['sha256']:b for b in memory.records(store)}
        if candidate_sha256 not in bundles:
            raise EvidenceError('Unknown expert-review candidate')
        prior = decisions(store)
        row = dict(deepcopy(request), schema_version='experience-expert-decision-v1',
                   actor='named_operator', candidate_sha256=candidate_sha256,
                   report_sha256=report_sha256, at=archive.now(), sequence=len(prior)+1)
        validate_decision(row, bundles[candidate_sha256])
        row['sha256'] = memory.digest(canonical(row))
        path = store/'decisions'/f"{row['sequence']:08d}-{row['sha256']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8') as target:
            target.write(json.dumps(row, ensure_ascii=False, indent=2)+'\n')
        return row


def active(store):
    bundles = {b['sha256']:b for b in memory.records(store)}
    selected = {}
    for row in decisions(store):
        bundle = bundles[row['candidate_sha256']]
        if row['decision'] == 'accept':
            selected[bundle['id']] = dict(bundle=bundle, expert_decision=row)
        elif row['decision']=='reject' and bundle['id'] in selected \
                and selected[bundle['id']]['bundle']['sha256']==bundle['sha256']:
            del selected[bundle['id']]
    return [selected[key] for key in sorted(selected)]


def freeze(store):
    result = dict(schema_version='experience-active-snapshot-v1', scope='research_only',
                  entries=active(store))
    result['sha256'] = memory.digest(canonical(result))
    return result


def validate_snapshot(store, snapshot):
    if not isinstance(snapshot, dict) or set(snapshot) != {'schema_version','scope','entries','sha256'} \
            or snapshot['schema_version'] != 'experience-active-snapshot-v1' or snapshot['scope'] != 'research_only' \
            or snapshot['sha256'] != memory.digest(canonical({k:v for k,v in snapshot.items() if k!='sha256'})):
        raise EvidenceError('Invalid frozen active snapshot')
    seen = set()
    for entry in snapshot['entries']:
        memory.object_fields(entry, {'bundle', 'expert_decision'}, 'active snapshot entry')
        bundle, decision = entry['bundle'], entry['expert_decision']
        memory.validate(bundle, lambda code:(Path(store)/'sources'/code).read_bytes())
        validate_decision(decision, bundle)
        if decision['decision'] != 'accept' or decision['candidate_sha256'] != bundle['sha256'] \
                or decision['sha256'] != memory.digest(canonical({k:v for k,v in decision.items() if k!='sha256'})) \
                or bundle['id'] in seen:
            raise EvidenceError('Snapshot must bind one expert-accepted version per identity')
        seen.add(bundle['id'])
    return snapshot
