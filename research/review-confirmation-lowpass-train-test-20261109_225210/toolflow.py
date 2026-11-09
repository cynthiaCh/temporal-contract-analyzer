"""Case-blind experience routing, shared prompts, and generic score differences."""
import hashlib
import json
from pathlib import PurePosixPath

PREDICATES = {'shared_lifetime': 'The target shared state or work can outlive an individual consumer.',
 'observer_lifetime': 'Multiple consumers share the same work through distinct subscription or '
                      'observer identities.',
 'attempt_resource': 'Each execution attempt has its own cancellation resource or completion '
                     'identity.',
 'lazy_consumption': 'Accessing a cancellation capability synchronously records actual '
                     'consumption, and current evidence can establish ownership of that record.',
 'async_resume': 'Paused or retrying work can resume through an asynchronous continuation.',
 'deferred_batch': 'The repair target coalesces consecutive inputs into deferred work that can '
                   'remain pending.',
 'boundary_persistence': 'Current documentation requires accepted persistence obligations to '
                         'settle before a departure or submission boundary returns.',
 'entry_snapshot': 'An accepted operation is bound to the selection or data at entry; subsequent '
                   'reentry must not rewrite its established obligations.',
 'inline_reentry': 'Settlement or notification synchronously calls callbacks that can reenter '
                   'navigation or editing.',
 'effect_lifetimes': 'Persistent results and current UI feedback have distinguishable ownership '
                     'and validity periods.',
 'different_ownership_policy': 'The current task explicitly requires an ownership policy that '
                               'contradicts separating shared state from individual attempts.',
 'discard_boundary_policy': 'The current task explicitly permits discarding the target accepted '
                            'persistence obligation instead of settling it.',
 'no_lazy_shared_mechanism': 'Current evidence explicitly establishes that the repair target lacks '
                             'a shared-state and lazy-consumption mechanism.'}

POLICY = 'Original snapshots, final source, diffs, logs and scores are archived automatically by external Python code. Only repair business code and perform necessary validation. Do not create experiment backups, archived patches or result-summary files. Return a JSON object whose only field is report. In English, briefly describe the actual changes, validation and uncovered scope, using no more than 6000 Unicode characters.'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def public_material(task, sources, ast, taxonomy):
    # No **metadata argument: case identity and evaluation data have no entry.
    return {'task': task, 'sources': sources, 'AST': ast, 'taxonomy': taxonomy,
            'predicates': PREDICATES}


def extraction_prompt(material):
    return """Read only the current source and README/docs in /workspace. In one response, produce the candidate automatic Contract, primary mechanism class, premises and semantic self-check. Write all generated prose in English; retain exact source quotations and opaque identifiers.
Return the top-level typed JSON object required by the CLI schema. Do not wrap it in report, encode JSON as a string, or use Markdown.
Actually read source bodies first. AST is only a clue: no AST match does not imply that a mechanism is absent. Only candidate-reading commands are allowed; do not edit code, run tests or access the network. Allowed commands are pwd, ls, rg, cat, nl, head, tail, wc, echo, printf, and sed -n with numeric line ranges ending in p. You may use 2>/dev/null and || true for missing documentation. Do not use find, python, scripts, cd or general output redirection.
Use only the original task, current source/docs and public material below. Do not classify from directory or package names, case/cluster identity, historical scores or evaluators.
Semantic checks:
1. Text after Repair/Fix may describe a defect to remove. Do not convert it into a preservation requirement. Distinguish reported_defect, requirement, source_fact and preservation_inference.
2. Preserve the source conditions, negation and event order of supported behavior. Do not broaden cancellation or completion obligations.
3. For each source_fact, identify the object/lifetime actually read or written (record_owner) and its source owner_expression. Check record ownership separately from physical resource ownership. Do not relocate an active record because another object has a similarly named or unused field. Correspondence to an attempt alone does not establish where a record is stored.
4. Distinguish retained history from current display eligibility, and cancellation requests from settlement. Contract and source_fact must be compatible. Record a core conflict in consistency rather than claiming it was checked.
Emit each predicate exactly once as known, unknown or contradicted. known/contradicted require one current evidence item; unknown may have none.
TASK is the original task as virtual numbered text, with line numbers starting at 1. Use local relative file paths and exact contiguous single-line quotations of at most 80 characters. For compressed long lines, quote only the relevant substring, never the whole line. Use one evidence item per fact or claim.
Keep Contract within 1400 characters, claims within four items, and top-level evidence within three items. Use unknown honestly for unknown ownership.
Do not make a separate classification-model call. Do not output patches or task answers.
Public material:
""" + canonical({k:v for k,v in material.items() if k!='sources'})


def maintenance_prompt(task, contract, experience=None):
    common = task + '\n\nThe following automatic Contract is auxiliary material. Check it against the current task and source; do not follow unsupported policies blindly:\n' + contract
    common += '\n\nLocate, repair and validate autonomously within /workspace. Modify product source only; preserve interfaces, dependencies, and build/test configuration. Do not install dependencies or access the network or research materials. For JavaScript use /runtime/node; for Python use /usr/bin/python3 -B. Write your final report in English.\n' + POLICY
    return common if experience is None else common + '\n\nThe following is the frozen English experience translation. Check its applicability against current evidence:\n' + experience


def valid_evidence(evidence, sources):
    if not isinstance(evidence, list) or not evidence:
        return False
    for item in evidence:
        if not isinstance(item, dict) or set(item) != {'file', 'line', 'quote'}:
            return False
        name, line, quote = item['file'], item['line'], item['quote']
        if not isinstance(name, str) or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:
            return False
        lines = sources.get(name, '').splitlines()
        if type(line) is not int or not 1 <= line <= len(lines) or not quote or quote not in lines[line - 1]:
            return False
    return True


def validate_analysis(analysis, sources):
    if not isinstance(analysis,dict):return 'non_object_analysis'
    extra={k:analysis[k] for k in ['claims','consistency'] if k in analysis}
    analysis={k:v for k,v in analysis.items() if k not in extra}
    if extra:
        if set(extra)!={'claims','consistency'}:return 'incomplete_semantic_structure'
        if not isinstance(extra['claims'],list) or not isinstance(extra['consistency'],dict):return 'invalid_semantic_types'
        for claim in extra['claims']:
            if set(claim) not in [{'kind','statement','evidence'},{'kind','statement','evidence','record_owner','owner_expression'}] or claim['kind'] not in ['reported_defect','requirement','source_fact','preservation_inference']:return 'invalid_semantic_claim'
            if not valid_evidence(claim['evidence'],sources):return 'unbound_semantic_claim'
        if set(extra['consistency'])!={'conflicts','unknowns','checked_dimensions'}:return 'invalid_semantic_review'
        # Self-reported tensions are preserved evidence, not a policy verdict.
        # The mandatory source-bound semantic review decides actual core conflicts.
        # Unknowns can be scope limits. The source-bound semantic veto must
        # distinguish unresolved policy from honest non-exhaustiveness.
    if set(analysis) != {'contract', 'primary_class', 'secondary_tags', 'evidence', 'facts'}:
        return 'invalid_or_invisible_analysis_fields'
    if not isinstance(analysis['contract'], str) or not isinstance(analysis['facts'], list):
        return 'invalid_analysis_types'
    if analysis['primary_class'] not in ['T1', 'T2', 'T3', 'T4', 'unknown']:
        return 'invalid_primary_class'
    if analysis['primary_class'] != 'unknown' and not valid_evidence(analysis['evidence'], sources):
        return 'primary_class_without_source_evidence'
    seen = set()
    for fact in analysis['facts']:
        if set(fact) != {'predicate', 'state', 'evidence'} or fact['predicate'] not in PREDICATES:
            return 'invalid_fact_or_invisible_fields'
        if fact['predicate'] in seen:
            return 'duplicate_or_conflicting_fact'
        seen.add(fact['predicate'])
        if fact['state'] not in ['known', 'unknown', 'contradicted']:
            return 'invalid_fact_state'
        if fact['state'] != 'unknown' and not valid_evidence(fact['evidence'], sources):
            return 'fact_without_source_evidence'
    return None


def freeze_entry(candidate, primary):
    if set(candidate) != {'text', 'requires', 'excludes'}:
        raise ValueError('reflection candidate schema')
    if not candidate['text'].strip() or not candidate['requires']:
        raise ValueError('empty text or applicability')
    for key in ['requires', 'excludes']:
        if not isinstance(candidate[key], list) or any(x not in PREDICATES for x in candidate[key]):
            raise ValueError('unknown applicability predicate')
    if set(candidate['requires']) & set(candidate['excludes']):
        raise ValueError('applicability conflict')
    entry = {**candidate, 'version': 'pilot-v2r4-1', 'primary_class': primary,
             'text_sha256': digest(candidate['text'])}
    entry['sha256'] = digest(canonical(entry))
    return entry


def route(analysis, sources, library, *, task=None, review=None):
    # Only data used below is accepted. No case/cluster/history/oracle arguments.
    def fallback(reason, checks=None):
        return {'condition': 'AUTO', 'reason': reason, 'selected': None,
                'checks': checks or [], 'primary_class': analysis.get('primary_class', 'unknown')}
    invalid = validate_analysis(analysis, sources)
    if invalid:return fallback(invalid)
    if task is None:return fallback('missing_task_semantic_inputs')
    issue=semantic_gate(task,sources,analysis,review)
    if issue:return fallback(issue)
    if invalid:
        return fallback(invalid)
    if analysis['primary_class'] == 'unknown':
        return fallback('unknown_class')
    if not library:
        return fallback('empty_library')
    allowed = {'text', 'requires', 'excludes', 'version', 'primary_class', 'text_sha256', 'sha256'}
    if any(set(e) != allowed for e in library):
        return fallback('invisible_or_invalid_registry_fields')
    entries = [e for e in library if e['primary_class'] == analysis['primary_class']]
    if not entries:
        return fallback('no_experience_for_class')
    facts = {x['predicate']: x for x in analysis['facts']}
    eligible, checks = [], []
    for entry in entries:
        check = {'sha256': entry['sha256'], 'premises': [], 'exclusions': []}
        copy = {k: v for k, v in entry.items() if k != 'sha256'}
        if entry['sha256'] != digest(canonical(copy)) or entry['text_sha256'] != digest(entry['text']):
            return fallback('digest_tampering', checks + [check])
        if not entry['requires']:
            return fallback('empty_applicability')
        for kind, field, expected in [('premises', 'requires', 'known'), ('exclusions', 'excludes', 'contradicted')]:
            for key in entry[field]:
                fact = facts.get(key, {'state': 'unknown', 'evidence': []})
                check[kind].append({'predicate': key, 'state': fact['state'], 'evidence': fact['evidence'],
                                    'satisfied': fact['state'] == expected})
        check['eligible'] = all(x['satisfied'] for x in check['premises'] + check['exclusions'])
        checks.append(check)
        if check['eligible']:
            eligible.append(entry)
    if len(eligible) > 1:
        return fallback('unresolved_multiple_experience_conflict', checks)
    if not eligible:
        return fallback('insufficient_or_contradictory_premises', checks)
    chosen = eligible[0]
    return {'condition': 'ROUTED', 'primary_class': analysis['primary_class'], 'reason': 'source_bound_premises',
            'selected': {'version': chosen['version'], 'sha256': chosen['sha256'],
                         'text_sha256': chosen['text_sha256']}, 'checks': checks}


from feedback_v2 import feedback


def reflection_prompt(payload):
    return """Reflect once using only the following training feedback from this batch. Do not use tools. Generate one transferable experience candidate without reading or borrowing old experience. Materials include the original candidate, task/docs requirements, two actual repairs/scores and public deliveries. No reference implementation or patch is included.
Preserve established successes. Distinguish actual differences, regressions and unknown causes. Never infer business policy or root cause from assertion names. actual_successes lists what that repair passed; original_successes lists what the original candidate passed; regressions lists established behaviors lost. all_checks retains raw actual/expected checks and assertions. Public repair deliveries are unverified model claims, not score facts. Check every repaired/preserved/regressed claim against actual results. Multiple code changes support a causal hypothesis, not independent causal isolation. Do not narrate which training patch succeeded in the experience body; state general applicability boundaries and verification actions. The execution-agent provenance of standard interpretations is recorded.
Include applicability, event relations, verification, preserved behavior and exclusions. The body must not contain case IDs, scoring assertion names, file paths, specialized field/function names or directly copyable patches. Use ordinary English to describe general temporal mechanisms. Do not name training cases or promise unobserved outcomes.
requires/excludes may contain only fixed predicate keys. At least one requires entry is mandatory. Add an exclusion only with evidence. An exclusion permits routing only when current evidence explicitly contradicts that predicate; unknown causes fallback. Do not apply an adjacent object's policy to the repair target or require the candidate to be already repaired.
Return the top-level JSON object required by this compatibility schema, with no report wrapper, string-encoded JSON or Markdown:
{"text":"Complete experience body in English", "requires":["predicate_key"], "excludes":[]}
Keep text within 3600 characters. Produce one candidate, with no alternative revision. requires/excludes must agree with the body. Do not assert an applicability policy that cannot be checked.
Fixed predicate dictionary:
""" + canonical(PREDICATES) + '\nTraining material for this batch:\n' + canonical(payload)


def semantic_gate(task, sources, analysis, review):
    """A source-bound veto record; never changes category, Contract or experience."""
    required={'contract_sha256','task_sha256','sources_sha256','reviewer','approved','conflicts','unknowns','evidence','findings'}
    if not isinstance(review,dict) or set(review)!=required:return 'missing_or_invalid_semantic_veto_record'
    if review['contract_sha256']!=digest(analysis['contract']) or review['task_sha256']!=digest(task) or review['sources_sha256']!=digest(canonical(sources)):return 'semantic_review_input_drift'
    if review['reviewer']!='execution_agent_visible_input_only':return 'invalid_semantic_review_provenance'
    if not review['approved'] or review['conflicts'] or review['unknowns']:return 'unresolved_semantic_conflict'
    if not valid_evidence(review['evidence'],sources):return 'unbound_semantic_review'
    return None

