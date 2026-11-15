"""Public-source Contract review; model judgments are not execution verdicts."""
from . import taxonomy
from .core import EvidenceError

POLICY = 'public_contract_review_3_versions_v1'
MAX_VERSIONS = 3
CRITERIA = ('grounding', 'coverage', 'overconstraint', 'consistency', 'unknowns')


def schema(contract_schema):
    from .tempoevo_v4 import obj_schema, STR, STRINGS, EVIDENCE
    citation_list = dict(EVIDENCE, minItems=0)
    check = obj_schema(dict(
        criterion=dict(type='string', enum=list(CRITERIA)),
        status=dict(type='string', enum=['supported', 'issue', 'unknown']),
        explanation=STR, evidence=citation_list))
    change = obj_schema(dict(reason=STR, evidence=EVIDENCE))
    return obj_schema(dict(
        decision=dict(type='string', enum=['ready', 'revise', 'unresolved']),
        contract_after=contract_schema, analysis=taxonomy.analysis_schema(),
        checks=dict(type='array', minItems=5, maxItems=5, items=check),
        changes=dict(type='array', items=change),
        removed_obligations=dict(type='array', items=obj_schema(dict(
            id=STR, reason=STR, evidence=EVIDENCE))),
        remaining_unknowns=STRINGS))


def instruction(version):
    return f'''Review the Auto-Contract before code repair, using only the original
public task, source, available static evidence and applicable retrieved experience.
This is Contract version {version} of at most {MAX_VERSIONS}, including the draft.
Read public source files as needed to investigate missing evidence. Do not edit code.

Infer multiple obligation categories and mechanism premises from current sources;
categories are investigation directions, not mandatory requirement checklists.
Return source-grounded analysis using the supplied taxonomy. Exact label/fact citations
use original source lines or TASK; line numbers start at 1. Never use case IDs,
historical scores, hidden tests, reference repairs or Gold as evidence.

Check each of grounding, coverage, overconstraint, consistency and unknowns once:
- grounding: does each obligation follow from the task or existing source behaviour?
- coverage: are relevant triggers, ordering, identity, lifecycle and preservation missing?
- overconstraint: has a special-case experience become an unsupported requirement?
- consistency: are requirements compatible and their suggested checks meaningful?
- unknowns: are uncertain execution relationships explicitly unresolved?
Experience suggests checks; only the current task and source establish requirements.
Do not force every taxonomy category to apply. Static clues do not prove execution.
Report supported, issue or unknown with explanations and exact public quotations;
supported/issue checks require evidence. Never invent a test execution or claim Gold PASS.

Preserve original task obligations and source-supported behaviour, not every statement
in the fallible draft. A revision may add missing obligations or remove/rewrite an
unsupported draft obligation. Explain every changed version with public evidence;
list every removed or rewritten obligation ID with its own reason and evidence.
Return unchanged contract_after unless decision is revise. Choose revise only for an
evidence-backed, actionable correction; unknowns alone do not justify new requirements.
Choose ready if no supported actionable issue remains, or unresolved when evidence
cannot settle remaining issues. ready is a review conclusion, not verified correctness.
Retain remaining_unknowns explicitly. At version {MAX_VERSIONS}, no further revision is
allowed: return ready or unresolved with an unchanged Contract.
'''


def validate_review(review, before, task, sources, version):
    from .tempoevo_v4 import CONTRACT_SCHEMA, check_contract, evidence_valid
    from ._session_runtime.schema_validator import validate
    from .experience_routing import validate_analysis
    validate(review, schema(CONTRACT_SCHEMA))
    check_contract(review['contract_after'], task, sources)
    validate_analysis(review['analysis'], task, sources, text_grounding=True)
    if sorted(c['criterion'] for c in review['checks']) != sorted(CRITERIA):
        raise EvidenceError('Contract review must check each criterion once')
    for check in review['checks']:
        evidence_valid(check['evidence'], task, sources)
        if check['status'] != 'unknown' and not check['evidence']:
            raise EvidenceError('Contract review claims require public evidence')
    if review['decision'] == 'ready' and any(c['status'] == 'issue' for c in review['checks']):
        raise EvidenceError('Unresolved Contract issues cannot be marked ready')
    for change in review['changes'] + review['removed_obligations']:
        evidence_valid(change['evidence'], task, sources)
    after = review['contract_after']
    changed = after != before
    if (review['decision'] == 'revise') != changed:
        raise EvidenceError('Contract review decision and revision disagree')
    if changed and (version >= MAX_VERSIONS or not review['changes']):
        raise EvidenceError('Contract revision requires evidence and an available version')
    if changed and not any(c['status'] == 'issue' for c in review['checks']):
        raise EvidenceError('Contract revision requires an identified issue, not uncertainty alone')
    retained = {o['id']: o['text'] for o in after['obligations']}
    removed = {o['id'] for o in before['obligations'] if retained.get(o['id']) != o['text']}
    rows = review['removed_obligations']
    if len(rows) != len({r['id'] for r in rows}) or {r['id'] for r in rows} != removed:
        raise EvidenceError('Every deleted or rewritten draft obligation requires evidence')
    return changed
