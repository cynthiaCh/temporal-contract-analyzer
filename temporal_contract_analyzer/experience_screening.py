"""Development qualification, separate from content review and active pointers."""
import json
import fcntl
from pathlib import Path

from .core import EvidenceError
from .case_evaluation import relation_states, VERDICTS
from . import archive

VERSION = 'cross-source-development-screen-v2'


def critical_check(before, after, keys):
    """Compare preregistered obligations; missing observations remain unknown."""
    left = [relation_states(v) for v in before]
    right = [relation_states(v) for v in after]
    unknown = [k for k in keys if any(v.get(k) is None for v in left + right)]
    lost = [k for k in keys if any(v.get(k) is True for v in left)
            and any(v.get(k) is False for v in right)]
    return dict(lost=lost, unknown=unknown)


def evaluate(report):
    """Recompute the engineering gate from complete outcomes, never assertion counts."""
    reasons = []
    pending = []
    if not isinstance(report,dict) or report.get('schema_version') != VERSION:
        return dict(status='pending', reasons=['No v2 cross-source screening evidence'])
    source = report.get('source', {})
    transfers = report.get('transfers', [])
    if not isinstance(source,dict) or not isinstance(transfers,list) or any(not isinstance(r,dict) for r in transfers):
        return dict(status='pending',reasons=['Malformed screening groups'])
    units = [source.get('source_unit')] + [r.get('source_unit') for r in transfers]
    if len(transfers) != 2 or any(not isinstance(u, str) or not u.strip() for u in units) \
            or len(set(units)) != 3:
        return dict(status='pending', reasons=['Two distinct other source units are required'])
    budget = report.get('budget', {})
    if not isinstance(budget,dict):return dict(status='pending',reasons=['Malformed budget evidence'])
    if budget.get('within') is not True or budget.get('complete') is not True \
            or type(budget.get('requests')) is not int or type(budget.get('cap')) is not int \
            or not 0 <= budget['requests'] <= budget['cap'] or budget.get('unknown_requests') != 0:
        pending.append('Budget or accounting is incomplete or exceeded')
    groups = [source] + transfers
    comparisons = []
    for index, group in enumerate(groups):
        old = group.get('old', [])
        new = group.get('new', [])
        keys = group.get('critical_relations')
        if not isinstance(keys, list) or not keys or any(not isinstance(k,str) or not k for k in keys) or len(keys) != len(set(keys)):
            pending.append('Missing preregistered critical obligations')
            continue
        if not isinstance(old,list) or not isinstance(new,list) or len(old) != 2 or len(new) != 2 or any(not isinstance(v, dict) or v.get('verdict') not in VERDICTS
                for v in old + new):
            pending.append('Every required arm needs two valid scores')
            continue
        try:
            vectors = [relation_states(v) for v in old + new]
            if any(set(v) != set(vectors[0]) for v in vectors):
                raise EvidenceError('Behavior vector mismatch')
            if any(not isinstance(v.get('schedules',{}),dict) for v in old+new):
                raise EvidenceError('Malformed schedule evidence')
            if any(v.get('runtime_errors') or any(isinstance(r,dict) and r.get('runtimeError')
                    for r in v.get('schedules',{}).values()) for v in old + new):
                raise EvidenceError('Runtime errors are not valid screening scores')
            if any(any(state is None for state in vector.values()) or
                   ((outcome['verdict'] == 'PASS') != all(state is True for state in vector.values()))
                   for outcome, vector in zip(old + new, vectors)):
                raise EvidenceError('Unknown or contradictory score')
            critical = critical_check(old + ([group['original']] if 'original' in group else []), new, keys)
            if critical['lost']:
                reasons.append('Critical preservation loss: '+', '.join(critical['lost']))
            if critical['unknown']:
                pending.append('Unknown critical behavior: '+', '.join(critical['unknown']))
        except (EvidenceError, TypeError, KeyError):
            pending.append('Invalid or incomplete behavior evidence')
            continue
        counts = dict(source_unit=group['source_unit'], old=sum(v['verdict'] == 'PASS' for v in old),
                      new=sum(v['verdict'] == 'PASS' for v in new), critical=critical)
        if index:
            identical=group.get('prompts_identical')
            if type(identical) is not bool:
                pending.append('Missing frozen prompt-difference check')
            elif identical and counts['old']!=counts['new']:
                pending.append('Identical prompts cannot support attributing random pass differences to experience')
            counts['prompts_identical']=identical
            comparisons.append(counts)
    if len(comparisons) == 2:
        if any(c['new'] < c['old'] for c in comparisons):
            pending.append('A transfer source has fewer whole-task passes')
        if sum(c['new'] - c['old'] for c in comparisons) < 2:
            pending.append('Transfer gain is below two additional whole-task passes')
    else:
        pending.append('Cross-source comparisons are incomplete')
    return dict(status='blocked' if reasons else 'pending' if pending else 'qualified',
                reasons=reasons + pending, comparisons=comparisons,
                claim='Development screening only; not statistical significance or final-test benefit')


def read(store, code):
    if not isinstance(code,str) or len(code)!=64 or any(c not in '0123456789abcdef' for c in code):
        raise EvidenceError('Invalid screened version ID')
    path = Path(store)/'screening'/(code+'.json')
    from .experience_lifecycle import metadata
    version=metadata(store,code)
    if version and version.get('origin_root'):
        task=version.get('validation_job')
        if not task:return None
        if task!='validation-'+code:raise EvidenceError('Validation job does not bind this exact candidate')
        path=Path(store)/'workflow/screens'/code/(task+'.json')
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value,dict) or value.get('candidate_sha256') != code:
        raise EvidenceError('Screening evidence belongs to another version')
    return value


def qualified(store, code):
    report = read(store, code)
    return report is not None and evaluate(report)['status'] == 'qualified'


def require(store, code):
    if not qualified(store, code):
        raise EvidenceError('Default activation requires complete passing cross-source development screening')


def save(store, report):
    code = report['candidate_sha256']
    if not isinstance(code, str) or len(code) != 64 or any(c not in '0123456789abcdef' for c in code):
        raise EvidenceError('Invalid candidate version')
    path = Path(store)/'screening'/(code+'.json')
    if report.get('workflow_task_id'):
        from .experience_lifecycle import metadata
        version=metadata(store,code) or {}
        if version.get('validation_job')!=report['workflow_task_id']:raise EvidenceError('Validation task/version binding mismatch')
        path=Path(store)/'workflow/screens'/code/(report['workflow_task_id']+'.json')
    with (Path(store)/'decision.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if path.exists():
            raise EvidenceError('Screening record exists; do not overwrite historical results')
        result = dict(report, gate=evaluate(report))
        archive.atomic_json(path, result)
    return result
