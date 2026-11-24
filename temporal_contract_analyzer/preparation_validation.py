"""Advisory preparation validation; never manufactures evidence or approvals."""
from copy import deepcopy
from .core import EvidenceError
from . import taxonomy

POLICY = 'advisory-source-validation-v1'
ROLES = ('routing', 'selection', 'contract', 'diagnosis')


class OutputError(EvidenceError):
    """A bounded, correctly attributed preparation call returned unusable output."""


def analysis(value, task, sources):
    """Remove unsupported routing claims; unknown never satisfies a premise."""
    from ._session_runtime.schema_validator import validate
    from .experience_routing import evidence_valid, validate_analysis
    schema=deepcopy(taxonomy.analysis_schema())
    # Missing support is advisory, while the surrounding output structure remains checked.
    schema['properties']['obligation_labels']['items']['properties']['evidence']['minItems']=0
    validate(value, schema)
    result = deepcopy(value)
    warnings = []
    labels = []
    for label in result['obligation_labels']:
        if evidence_valid(label['evidence'], task, sources, text_grounding=True):
            labels.append(label)
        else:
            warnings.append(dict(code='unsupported_label_omitted', label=label['code']))
    result['obligation_labels'] = labels
    for fact in result['facts']:
        if fact['state'] == 'unknown' and not fact['evidence']:
            continue
        if not evidence_valid(fact['evidence'], task, sources, text_grounding=True):
            warnings.append(dict(code='unsupported_fact_unknown', predicate=fact['predicate'], previous_state=fact['state']))
            fact.update(state='unknown', evidence=[])
            note='Unsupported mechanism premise remains unknown: '+fact['predicate']
            if note not in result['unknowns'] and len(result['unknowns']) < 20:
                result['unknowns'].append(note)
    validate_analysis(result, task, sources, text_grounding=True)
    return result, warnings
