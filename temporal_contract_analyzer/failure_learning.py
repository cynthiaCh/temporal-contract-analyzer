"""Carry unresolved execution evidence into later reflection, never repair policy."""
import fcntl
import json
from pathlib import Path

from . import archive
from .case_evaluation import relation_states
from .core import EvidenceError, canonical, sha

DIAGNOSES = ('retrieval_gap', 'execution_gap', 'rule_gap', 'unknown')
INSTRUCTIONS = (
    'For EVERY failure_observation return one failure_review row. Compare the actual '
    'delivered guidance with the actual patch and the scored execution; prior rules '
    'elsewhere in the bank were not necessarily delivered. Identify a retrieval gap, '
    'an execution gap, a rule gap, or unknown. A failed assertion name alone does not '
    'prove a cause. Cite the observation and task/source evidence; for an execution '
    'gap name a delivered rule and explain the concrete patch mismatch. When causes '
    'are unverified, say unknown and propose a distinguishing check. Give a concrete '
    'next_check and its expected observable behavior. "Already covered" is not a '
    'complete failure explanation. Compare PASS and failed patches when both exist. '
    'no_update means no rule delta, not that the failures are solved. Do not invent '
    'a new rule just to satisfy this review. Read previous_failed_attempts and their '
    'next checks; explain recurring mismatches rather than repeating an unsupported '
    '"already covered" conclusion. No outcome here establishes a verified '
    'cause or an improvement; Use the scored corrective repairs in this context to explain what was actually fixed. Do not claim that an executed repair is still only a proposed next step.\n'
)


def source_key(visible):
    return sha(canonical(dict(task=visible['task'], sources=visible['sources'])).encode())


def prior(store, visible):
    """Same-input observations are reflection material, not repair instructions."""
    key = source_key(visible)
    records = [json.loads(p.read_text()) for p in (Path(store)/'failure-learning').glob('*.json')]
    return sorted([r for r in records if r['source_key'] == key and r['failures']],
                  key=lambda r: r['at'])[-20:]


def observations(jobs):
    rows = []
    for job in jobs:
        if job['status'] != 'valid' or 'outcome' not in job:
            continue
        for relation, satisfied in relation_states(job['outcome']).items():
            if satisfied is not True:
                rows.append(dict(id=job['slot']+':'+relation, slot=job['slot'],
                                 relation=relation, observed=satisfied,
                                 observation_id='O-'+job['slot']))
        if job['outcome']['verdict'] != 'PASS' and not any(r['slot'] == job['slot'] for r in rows):
            rows.append(dict(id=job['slot']+':whole_task', slot=job['slot'],
                             relation='whole_task', observed=False,
                             observation_id='O-'+job['slot']))
    return rows


def _save(store, root, record):
    archive.atomic_json(Path(root)/'failure-learning.json', record)
    with (Path(store)/'decision.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        archive.atomic_json(Path(store)/'failure-learning'/(record['batch_id']+'.json'), record)


def capture(root, protocol, jobs, route, bundles):
    selected = next((b for b in bundles if b['sha256'] == route['selected_sha256']), None)
    artifacts = {}
    for job in jobs:
        if job['status'] != 'valid':
            continue
        artifacts[job['slot']] = {}
        for name in ('score.json', 'result.json'):
            path = Path(root)/'runs'/job['slot']/name
            if path.exists():
                artifacts[job['slot']][name] = dict(path=str(path), sha256=sha(path.read_bytes()))
    record = dict(batch_id=protocol['batch_id'], at=archive.now(), root=str(root),
                  source_key=source_key(protocol['cases']['source']['visible']),
                  roles=protocol.get('roles', {}), artifacts=artifacts,
                  failures=observations(jobs),
                  delivered=None if selected is None else dict(
                      sha256=selected['sha256'], id=selected['id'], rules=selected['rules']),
                  status='awaiting_reflection', review=None, candidate_action=None,
                  qualification='Observed failures only; diagnosis is unverified. Not approved repair guidance.')
    archive.atomic_json(Path(root)/'failure-observations.json', record)
    _save(protocol['store'], root, record)
    return record


def review_schema(record, ledger):
    rules = [] if record['delivered'] is None else [r['id'] for r in record['delivered']['rules']]
    ids = [r['id'] for r in record['failures']]
    fields = dict(failure_id=dict(type='string', **(dict(enum=ids) if ids else {})),
                  diagnosis=dict(type='string', enum=list(DIAGNOSES)),
                  evidence=dict(type='array', minItems=1, items=dict(type='string', enum=list(ledger))),
                  guidance_rule_ids=dict(type='array', items=dict(type='string', **(dict(enum=rules) if rules else {})),
                                         **({} if rules else dict(maxItems=0))),
                  explanation=dict(type='string', minLength=1),
                  next_check=dict(type='string', minLength=1))
    return dict(type='array', minItems=len(record['failures']), maxItems=len(record['failures']),
                items=dict(type='object', properties=fields, required=list(fields), additionalProperties=False))


def check(review, record, ledger):
    """Require coverage and traceability; never certify a model's causal judgment."""
    expected = {r['id']: r for r in record['failures']}
    if len({r['failure_id'] for r in review}) != len(review) or set(expected) != {r['failure_id'] for r in review}:
        raise EvidenceError('Failure review must cover every observed failure exactly once')
    for row in review:
        failure = expected[row['failure_id']]
        if failure['observation_id'] not in row['evidence']:
            raise EvidenceError('Failure diagnosis must cite its actual execution observation')
        if row['diagnosis'] != 'unknown' and not any(
                ledger[k]['kind'] in ('original_task', 'source_document') for k in row['evidence']):
            raise EvidenceError('Failure attribution requires task/source evidence, not assertion names alone')
        if row['diagnosis'] == 'execution_gap' and not row['guidance_rule_ids']:
            raise EvidenceError('An execution gap must identify actually delivered guidance')


def finish(root, protocol, value):
    path = Path(root)/'failure-learning.json'
    if not path.exists():
        return None
    record = json.loads(path.read_text())
    record.update(review=value['failure_review'], candidate_action=value['action'], status=fix_status(record))
    _save(protocol['store'], root, record)
    return record


def fix_status(record):
    if not record['failures']:
        return 'no_observed_failure'
    latest={row['source_slot']: row for row in record.get('repairs',[])}
    failed={row['slot'] for row in record['failures']}
    if all(slot in latest and latest[slot]['fixed'] for slot in failed):
        return 'fixed'
    return 'repair_exhausted' if 'repair_limit' in record else 'needs_followup'


def record_fix(root, protocol, source_slot, slot, candidate, outcome, original_delta, score_path, requests):
    path=Path(root)/'failure-learning.json'
    record=json.loads(path.read_text())
    states=relation_states(outcome)
    fixed=outcome['verdict']=='PASS' and bool(states) and all(v is True for v in states.values()) \
        and not outcome.get('runtime_errors') and not original_delta.get('lost')
    repair=dict(source_slot=source_slot,slot=slot,candidate=str(candidate),verdict=outcome['verdict'],
        fixed=fixed,states=states,original_delta=original_delta,requests=requests,
        score=dict(path=str(score_path),sha256=sha(Path(score_path).read_bytes())))
    previous=next((r for r in record.get('repairs',[]) if r['slot']==slot),None)
    if previous is not None:
        if previous!=repair:raise EvidenceError('Cannot replace a recorded bugfix attempt')
        return record
    record.setdefault('repairs',[]).append(repair)
    record['status']=fix_status(record)
    _save(protocol['store'],root,record)
    return record


def record_validation(root, protocol, candidate, outcomes, critical, prompt_changed):
    """Attach actual follow-up scores without converting recurrence into causality."""
    path = Path(root)/'failure-learning.json'
    if not path.exists():
        return
    record = json.loads(path.read_text())
    states = [relation_states(outcome) for outcome in outcomes]
    targets = sorted({r['relation'] for r in record['failures']})
    complete = len(states) == 2 and not critical['lost'] and not critical['unknown']
    observed = {key: [state.get(key) for state in states] for key in targets}
    record.setdefault('source_validation', {})[candidate] = dict(
        status='not_reproduced' if complete and all(
            len(values) == 2 and all(v is True for v in values) for values in observed.values())
        else 'unresolved',
        observed=observed, critical=critical, prompt_changed=prompt_changed,
        whole_task_passes=sum(outcome['verdict'] == 'PASS' for outcome in outcomes),
        actual_scores=len(outcomes), effect_attribution='not_established',
        qualification='Source revalidation observations only; not an experience effect estimate.')
    _save(protocol['store'], root, record)
