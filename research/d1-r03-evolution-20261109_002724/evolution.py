"""R03-only object replacement using the unchanged parent rule protocol."""
import copy
import difflib
from handoff import make_schema, validate_candidate, render, object_digest
from schema_validator import validate


def revision_schema(ledger, predicates):
    schema = copy.deepcopy(make_schema(ledger, predicates)['properties']['rules']['items'])
    # Restrict the existing field to the parent's R03 category, not a new API.
    schema['properties']['category']['enum'] = ['verification']
    return schema


def scope_check(parent, candidate):
    if len(parent['rules']) != 5 or len(candidate['rules']) != 5:
        raise ValueError('Exactly five parent rules must be retained')
    unchanged = [0, 1, 3, 4]
    if any(parent['rules'][i] != candidate['rules'][i] for i in unchanged):
        raise ValueError('Rule outside R03 changed')
    if {k:v for k,v in parent.items() if k != 'rules'} != {k:v for k,v in candidate.items() if k != 'rules'}:
        raise ValueError('Mechanism fields, version or unresolved items changed')
    return {'only_rule_index_allowed': 2, 'unchanged_rules': ['R01','R02','R04','R05'],
            'other_rule_objects_unchanged': True, 'other_rule_bodies_unchanged': True,
            'requires_excludes_applicability_unchanged': True, 'unresolved_unchanged': True}


def synthesize(parent, revision, ledger, predicates):
    validate(revision, revision_schema(ledger, predicates))
    candidate = copy.deepcopy(parent)
    candidate['rules'][2] = copy.deepcopy(revision)
    check = scope_check(parent, candidate)
    validation = validate_candidate(candidate, ledger, predicates)
    return candidate, check, validation


def differences(parent, candidate):
    scope_check(parent, candidate)
    before, after = parent['rules'][2], candidate['rules'][2]
    fields = [{'field': k, 'before': before[k], 'after': after[k]} for k in before if before[k] != after[k]]
    text_diff = ''.join(difflib.unified_diff(render(parent).splitlines(True), render(candidate).splitlines(True),
                                          fromfile='parent/experience.md', tofile='derived/experience.md'))
    return {'rule': 'R03', 'changed_fields': fields, 'parent_object_sha256': object_digest(parent),
            'new_object_sha256': object_digest(candidate)}, text_diff
