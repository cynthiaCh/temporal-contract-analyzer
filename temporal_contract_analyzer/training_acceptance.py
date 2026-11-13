"""Deterministic verdict normalization and opt-in public behavioral projection.

Raw grader output is never a model input. Mapping descriptions are frozen public
configuration, not strings copied from hidden schedules or assertions.
"""
from .core import EvidenceError

FAILURES=('FAIL','UNDERREACH','OVERREACH','UNDERREACH_AND_OVERREACH')


def validate_mapping(mapping):
    if not isinstance(mapping,dict):raise EvidenceError('training_feedback must be a mapping')
    for key,row in mapping.items():
        if not isinstance(key,str) or not isinstance(row,dict) or set(row)!={'summary','expected'} \
                or not isinstance(row['summary'],str) or not row['summary'].strip() or type(row['expected']) is not bool:
            raise EvidenceError('Behavior mapping requires a public summary and boolean expected value')


def normalize(raw,mapping=None):
    mapping=mapping or {};validate_mapping(mapping)
    def invalid(message):return dict(valid=False,passed=None,error=message,failure_type=raw.get('failure_type','invalid_output') if isinstance(raw,dict) else 'invalid_output')
    if not isinstance(raw,dict):return invalid('Scorer output must be an object')
    if 'valid' in raw and type(raw['valid']) is not bool:return invalid('Invalid execution validity flag')
    if raw.get('valid') is False:return invalid(str(raw.get('error','Invalid scorer execution')))
    score=raw.get('full_score',raw)
    if not isinstance(score,dict):return invalid('Malformed scorer envelope')
    schedules=score.get('schedules',{})
    if not isinstance(schedules,dict):return invalid('Malformed scorer schedules')
    if score.get('runtime_errors') or score.get('runtimeError') or (isinstance(schedules,dict) and any(isinstance(x,dict) and x.get('runtimeError') for x in schedules.values())):
        return invalid('Scorer runtime error; consult separately archived raw result')
    if raw.get('verdict') is not None and score.get('verdict') is not None and raw['verdict']!=score['verdict']:return invalid('Conflicting scorer envelope verdicts')
    verdict=score.get('verdict',raw.get('verdict'))
    if verdict is not None:
        if verdict not in ('PASS',)+FAILURES:return invalid('Unknown scorer verdict')
        passed=verdict=='PASS'
        if 'passed' in raw and (type(raw['passed']) is not bool or raw['passed']!=passed):return invalid('Contradictory scorer verdict and passed flag')
    elif type(raw.get('passed')) is bool:
        passed=raw['passed'];verdict='PASS' if passed else 'FAIL'
    else:return invalid('No explicit behavioral verdict')
    effects=score.get('observed_effects',{})
    observations=[];unknowns=[]
    for key,row in mapping.items():
        actual=effects.get(key) if isinstance(effects,dict) else None
        if type(actual) is bool:
            observations.append(dict(summary=row['summary'],expected=row['expected'],actual=actual,passed=actual==row['expected']))
        else:unknowns.append(row['summary'])
    if not mapping:unknowns=['Only the acceptance verdict is available for feedback; no failure cause inferred.']
    return dict(valid=True,passed=passed,verdict=verdict,
        feedback=dict(passed=passed,observations=observations,regressions=[],unknowns=unknowns))
