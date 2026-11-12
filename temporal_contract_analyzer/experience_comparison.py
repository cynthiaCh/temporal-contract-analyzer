"""Typed, evidence-addressed comparisons; semantic novelty is never a text metric."""
from .core import EvidenceError

VERSION = 'experience-increment-comparison-v1'
TEXT = dict(type='string', minLength=1)


def obj(fields):
    return dict(type='object', properties=fields, required=list(fields), additionalProperties=False)


def choices(values):
    values = list(values)
    return dict(type='string', enum=values) if values else dict(type='string')


def schema(priors, target, targets):
    match = obj(dict(experience_sha256=choices(priors),
        rule_id=choices(sorted({r['id'] for b in priors.values() for r in b['rules']})),
        covered=TEXT))
    matches = dict(type='array', items=match)
    versions = dict(type='array', items=choices(priors))
    if not priors:
        matches['maxItems'] = 0
        versions['maxItems'] = 0
    return obj(dict(compared_versions=versions, comparisons=dict(type='array', items=obj({
        target: dict(type=['integer', 'null'], minimum=0) if target=='change_index' else choices(targets),
        'matches': matches,
        'uncovered_increment': dict(type='string'),
        'classification': dict(type='string', enum=['duplicate', 'local_revision', 'independent_new', 'unchanged', 'insufficient_evidence']),
        'reason': TEXT}))))


def check(value, priors, target, targets):
    """Validate addressability and coverage, not whether an AI explanation is true."""
    from ._session_runtime.schema_validator import validate
    try:
        validate(value, schema(priors, target, targets))
    except (ValueError, KeyError, TypeError) as error:
        raise EvidenceError('Invalid increment comparison: '+str(error)) from error
    versions = value['compared_versions']
    if len(set(versions)) != len(versions) or set(versions) != set(priors):
        raise EvidenceError('Increment comparison must consider every supplied prior version exactly once')
    if [r[target] for r in value['comparisons']] != list(targets):
        raise EvidenceError('Increment comparison must cover every target exactly once in order')
    for row in value['comparisons']:
        seen = set()
        for match in row['matches']:
            pair = (match['experience_sha256'], match['rule_id'])
            if pair in seen or pair[0] not in priors or not any(r['id']==pair[1] for r in priors[pair[0]]['rules']):
                raise EvidenceError('Comparison references a duplicate or nonexistent prior rule/version')
            seen.add(pair)
        kind = row['classification']
        if kind in ('duplicate', 'local_revision', 'unchanged') and not row['matches']:
            raise EvidenceError('Covered or revised guidance must identify the corresponding prior rules')
        increment = row['uncovered_increment'].strip()
        if (kind in ('local_revision', 'independent_new')) != bool(increment):
            raise EvidenceError('Comparison classification disagrees with its stated uncovered increment')
    return value['comparisons']


INSTRUCTIONS = '''Compare meaning, including implications, not wording. Consider every supplied prior
version and identify all relevant old rules by exact version SHA and rule ID. For each target, record
what those rules already cover, the specific still-uncovered requirement (or an empty string), and
classify duplicate / local_revision / independent_new / unchanged / insufficient_evidence with a reason. A new formulation,
merged reminders, greater detail, or a successful patch alone is not a substantive increment.
Compare event admission, retirement before cleanup becomes available, retained delayed auditing,
and startup-before-return verification separately where present. If earlier rules already entail
per-event admission, naming that check does not establish novelty. Do not infer novelty from labels.
Use insufficient_evidence when no increment is established and duplication cannot be confirmed;
retain unknowns rather than claiming coverage or novelty. Missing evidence is uncertainty, not novelty.
Python checks references/coverage; AI and human review assess semantics.
'''
