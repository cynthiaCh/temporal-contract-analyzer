"""Single-source rule output, ledger-derived schema, deterministic rendering.

Evidence entailment remains a separate, hash-bound AI-assisted review. No model
calls, business-policy synthesis, evidence completion, or registry writes here.
"""
import json
from pathlib import Path
from evidence import (verify_ledger, rebuild_feedback, assemble_payload,
                      object_digest, digest, pointer)
from schema_validator import validate

VERSION = 'single-source-rules-1'
CATEGORIES = {'applicability': '适用条件', 'event_relation': '事件关系',
              'verification': '验证动作', 'preservation': '保留行为', 'exclusion': '排除边界'}
GROUNDED = {'documented_requirement', 'source_fact', 'observed_result', 'preservation_inference'}
POLICY_SUPPORT = {'documented_requirement', 'source_fact', 'preservation_inference'}


def make_schema(ledger, predicates):
    """Only the backend's previously supported typed JSON-schema subset."""
    def obj(properties):
        return {'type': 'object', 'properties': properties, 'required': list(properties), 'additionalProperties': False}
    def enum(values):
        return {'type': 'string', 'enum': sorted(values)}
    def arr(item, minimum=0, maximum=30):
        return {'type': 'array', 'items': item, 'minItems': minimum, 'maxItems': maximum}
    def string(maximum):
        return {'type': 'string', 'minLength': 1, 'maxLength': maximum}
    grounded = [e['id'] for e in ledger['entries'] if e['kind'] in GROUNDED]
    known_conditions = grounded  # unknown/hypothesis IDs never establish applicability
    support = enum(grounded)
    constraints = enum([c['id'] for c in ledger['constraints']])
    rule = obj({'category': enum(CATEGORIES), 'body': string(480),
                'support': arr(support, 1), 'conditions': arr(enum(known_conditions), 1),
                'preserve': arr(constraints, 1), 'counterevidence': arr(enum(grounded)),
                'explanation': string(900),
                'causal_status': enum(['documented_relation', 'source_reasoning', 'hypothesis'])})
    applicability = obj({'predicate': enum(predicates), 'status': enum(['known', 'unknown', 'contradicted']),
                         'evidence': arr(enum(known_conditions)), 'explanation': string(700)})
    unresolved = obj({'statement': string(700), 'impact': enum(['scope_limit', 'policy', 'applicability'])})
    return obj({'version': enum([VERSION]), 'requires': arr(enum(predicates), 1, len(predicates)),
                'excludes': arr(enum(predicates), 0, len(predicates)),
                'applicability': arr(applicability, 1, len(predicates)),
                'rules': arr(rule, 5, 7), 'unresolved': arr(unresolved, 0, 12)})


def numbered_rules(candidate):
    """List order is authoritative; IDs are mechanical and never model-written."""
    return [{'id': 'R%02d' % (i + 1), **rule} for i, rule in enumerate(candidate['rules'])]


def render(candidate):
    """No rule paraphrase, inferred condition, or evidence metadata is delivered."""
    return '\n\n'.join(r['id'] + '【' + CATEGORIES[r['category']] + '】\n' + r['body']
                        for r in numbered_rules(candidate)) + '\n'


def validate_candidate(candidate, ledger, predicates):
    validate(candidate, make_schema(ledger, predicates))
    entries = {e['id']: e for e in ledger['entries']}
    constraints = {c['id'] for c in ledger['constraints']}
    if set(r['category'] for r in candidate['rules']) != set(CATEGORIES):
        raise ValueError('Missing required rule category')
    requires, excludes = set(candidate['requires']), set(candidate['excludes'])
    if len(requires) != len(candidate['requires']) or len(excludes) != len(candidate['excludes']) or requires & excludes:
        raise ValueError('Duplicate or conflicting mechanism predicates')
    app = {row['predicate']: row for row in candidate['applicability']}
    if len(app) != len(candidate['applicability']) or set(app) != requires | excludes:
        raise ValueError('Applicability rows must cover exactly selected mechanism predicates')
    for predicate, row in app.items():
        expected = 'known' if predicate in requires else 'contradicted'
        if row['status'] != expected or not row['evidence']:
            raise ValueError('Unknown/unmet mechanism prerequisite: ' + predicate)
    preserved, counter = set(), set()
    for rule in candidate['rules']:
        if not any(entries[e]['kind'] in POLICY_SUPPORT for e in rule['support']):
            raise ValueError('Observed outcome alone cannot authorize a normative rule')
        preserved.update(rule['preserve']); counter.update(rule['counterevidence'])
    if preserved != constraints:
        raise ValueError('Missing preservation obligations')
    if not set(ledger['mandatory_counterevidence']).issubset(counter):
        raise ValueError('Known counterexamples omitted')
    return {'structure_valid': True, 'mechanism_facts_claimed_not_verified': True,
            'semantic_status': 'pending_AI_assisted_review', 'admitted': False,
            'version': VERSION, 'candidate_sha256': object_digest(candidate),
            'rendered_sha256': digest(render(candidate).encode()),
            'rendering': 'program_derived_numbering_and_exact_body_concatenation'}


def semantic_gate(candidate, ledger, predicates, review):
    result = validate_candidate(candidate, ledger, predicates)
    expected = {'candidate_sha256': object_digest(candidate), 'ledger_sha256': object_digest(ledger),
                'rendered_sha256': digest(render(candidate).encode())}
    if any(review.get(key) != value for key, value in expected.items()):
        raise ValueError('Semantic review bound to different candidate/input/rendering')
    if review.get('reviewer') != 'execution_agent' or review.get('AI_assisted') is not True:
        raise ValueError('Explicit AI-assisted execution-agent review required')
    rows = review.get('rules', [])
    expected_rules = {r['id']: r for r in numbered_rules(candidate)}
    if len(rows) != len(expected_rules) or {r['id'] for r in rows} != set(expected_rules):
        raise ValueError('Incomplete rule review')
    for row in rows:
        allowed = set(expected_rules[row['id']]['support'] + expected_rules[row['id']]['conditions']
                      + expected_rules[row['id']]['counterevidence'])
        if not row.get('evidence') or not set(row['evidence']).issubset(allowed) or not row.get('reason'):
            raise ValueError('Rule review requires actual rule evidence and explanation')
    app_rows = review.get('applicability', [])
    selected = set(candidate['requires'] + candidate['excludes'])
    if len(app_rows) != len(selected) or {r['predicate'] for r in app_rows} != selected:
        raise ValueError('Incomplete mechanism applicability review')
    app = {r['predicate']: r for r in candidate['applicability']}
    for row in app_rows:
        if not row.get('evidence') or not set(row['evidence']).issubset(app[row['predicate']]['evidence']) or not row.get('reason'):
            raise ValueError('Mechanism review requires actual cited evidence')
    unresolved = review.get('unresolved', [])
    if len(unresolved) != len(candidate['unresolved']):
        raise ValueError('Unresolved issues require explicit review dispositions')
    accepted = (all(r.get('supported') is True for r in rows + app_rows)
                and all(r.get('blocking') is False and r.get('reason') for r in unresolved)
                and review.get('all_normative_rules_covered') is True
                and review.get('preservation_obligations_checked') is True
                and review.get('counterevidence_handled') is True)
    result['semantic_status'] = 'supported_by_execution_agent' if accepted else 'rejected_by_execution_agent'
    # Content eligibility only; development evidence is still needed for admission.
    result['development_eligible'] = accepted
    return result


INSTRUCTIONS = '''Produce ONE experience candidate, as a typed JSON object conforming
to the supplied single-source rule schema. No tools, no alternatives, no retry.
The ONLY delivered prose is rules[].body. Do NOT output a full text, quote,
rule ID or second copy of a rule. Python numbers rules in list order and joins
the exact bodies under fixed category labels; it does not repair their meaning.
Write 5-7 concise rules, each body at most 480 characters, covering all five
categories: applicability, event_relation, verification, preservation, exclusion.
Chinese is preferred. Bodies must jointly express the relevant conditions,
event relations, verification actions, preserved behavior and exclusion limits.
No case IDs, grading names, file paths, specialized code field names or copyable
patches in bodies. Bodies must be usable guidance, not a report of these scores.

requires/excludes are MECHANISM predicates from the full dictionary below.
Declare only evidenced relevant mechanisms. Do not confuse persistence-boundary
semantics with generic settlement or an entry snapshot with any previous-state
copy. For each selected predicate provide exactly one applicability row with
status, existing evidence IDs and explanation. A required mechanism must be
known and an excluded mechanism must be contradicted in current D1 evidence;
unknown never means applicable. Use empty excludes when no exclusion predicate
is established, and express justified narrower boundaries in exclusion bodies.

Per-rule conditions are EVIDENCE IDs supporting the rule's applicability, not
predicate names or condition prose. support/counterevidence are evidence IDs;
preserve contains constraint IDs. Put explanations only in explanation fields.
Every ID must belong to the field enum. Across rules cover every preservation
constraint and the mandatory counterevidence IDs listed below. Explain how the
relevant counterexamples limit rules instead of ignoring them.

Use the complete frozen training evidence: source/task/docs, actual patches,
all checks and event traces, original successes, retained successes, improvements,
regressions and unknowns. Public repair deliveries are unverified claims.
An assertion name or PASS/FAIL is not a business policy or a verified cause.
Distinguish source facts, documented requirements, preservation inferences,
observations, causal hypotheses and unknown causes. A multi-change patch does
not isolate causation. Mere absence of an already-proven complete repair or
isolated cause is a validation/scope limitation, not itself an unknown policy.
Do not preserve the reported defect as intended behavior. Resource ownership
does not establish the owner of another record. Keep cancellation, retry
suppression, entry eligibility, actual entry, settlement and cache writes distinct.
In particular check fresh uncached offline work before entry, lawful deferred
cached refresh, entered unconsumed background work and the current separate
record/resource ownership. Do not collapse them into observerless cancellation.
When evidence is insufficient, narrow a rule or record an unresolved issue;
never assume a missing prerequisite. No reference patch, old E2, test feedback
or expected category is supplied. Rejected-clause critique is not a seed.
Structural validity is not semantic support. Subsequent review is AI-assisted,
not independent human approval. No claim of experience benefit is established.
'''
