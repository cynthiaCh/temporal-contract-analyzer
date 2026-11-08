"""Offline, training-only reflection handoff. No model, runner, or registry writes.

Evidence pointers prove provenance, not natural-language entailment. Admission
also requires a hash-bound execution-agent review and development observations.
"""
import hashlib
import json
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def object_digest(value):
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')).encode())


def pointer(document, path):
    if path == '':
        return document
    if not path.startswith('/'):
        raise ValueError('JSON pointer must start with /')
    for part in path[1:].split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        document = document[int(part)] if isinstance(document, list) else document[part]
    return document


ALLOWED_ROLES = {'training_task', 'training_source', 'training_document',
                 'training_contract', 'training_standard', 'training_score',
                 'training_patch', 'training_public_delivery', 'training_rejection_review'}
KINDS = {'documented_requirement', 'source_fact', 'observed_result',
         'preservation_inference', 'hypothesis', 'unknown'}


def verify_ledger(root, ledger):
    root = Path(root).resolve()
    files = ledger['files']
    for name, record in files.items():
        path = (root / name).resolve()
        if root not in path.parents or record['role'] not in ALLOWED_ROLES:
            raise ValueError('untrusted provenance: ' + name)
        if digest(path.read_bytes()) != record['sha256']:
            raise ValueError('input digest mismatch: ' + name)
    entries = ledger['entries']
    if len({e['id'] for e in entries}) != len(entries):
        raise ValueError('duplicate evidence ID')
    by_id = {e['id']: e for e in entries}
    for e in entries:
        if e['kind'] not in KINDS or not e['author']:
            raise ValueError('untyped evidence')
        if e['kind'] not in {'unknown', 'hypothesis'} and not e['anchors']:
            raise ValueError('unsupported evidence')
        for anchor in e['anchors']:
            name = anchor['file']
            if name not in files:
                raise ValueError('unlisted evidence file')
            content = (root / name).read_text()
            if anchor['type'] == 'lines':
                start, end = anchor['start'], anchor['end']
                if not 1 <= start <= end <= len(content.splitlines()):
                    raise ValueError('line bounds')
                actual = '\n'.join(content.splitlines()[start - 1:end])
                if actual != anchor['quote']:
                    raise ValueError('source quotation mismatch')
            elif anchor['type'] == 'json':
                if pointer(json.loads(content), anchor['pointer']) != anchor['value']:
                    raise ValueError('observation mismatch')
            else:
                raise ValueError('unknown anchor type')
        if any(x not in by_id for x in e.get('related', [])):
            raise ValueError('unknown related evidence')
    for constraint in ledger['constraints']:
        if not constraint['evidence'] or any(x not in by_id for x in constraint['evidence']):
            raise ValueError('unsupported preservation constraint')
    return by_id


def assemble_payload(root, ledger, feedback):
    """Only explicitly role-tagged, hash-pinned training files enter payload."""
    verify_ledger(root, ledger)
    if feedback != rebuild_feedback(root, ledger):
        raise ValueError('feedback differs from frozen training observations')
    materials = []
    for name, record in ledger['files'].items():
        materials.append({'role': record['role'], 'content': (Path(root) / name).read_text(),
                          'artifact': name, 'sha256': record['sha256']})
    return {'schema': 'training-reflection-handoff-3', 'materials': materials,
            'feedback': feedback, 'evidence': ledger['entries'],
            'constraints': ledger['constraints'],
            'causality': 'No independently verified cause. Outcomes and multi-hunk patches do not isolate causation.',
            'public_delivery_status': 'Unverified model claims, not observations.'}


def rebuild_feedback(root, ledger):
    from feedback import feedback
    spec = ledger['feedback_inputs']
    def read(name, role):
        if ledger['files'][name]['role'] != role:
            raise ValueError('feedback input role mismatch')
        return json.loads((Path(root) / name).read_text())
    result = feedback(read(spec['original'], 'training_score'),
                      [read(name, 'training_score') for name in spec['repairs']],
                      read(spec['standards'], 'training_standard'))
    result['causal_status'] = 'No cause independently verified; see evidence ledger for separately authored source reasoning.'
    return result


INSTRUCTIONS = '''Produce one experience candidate using only this training payload.
Return a typed object matching reflection.schema.json; never encode an object as a report string.
Use full actual/expected checks, original successes, retained successes, improvements,
regressions, unknowns, original sources, and complete patches. An assertion name or
PASS/FAIL is not an explanation. Public deliveries are unverified claims.
Separate direct source facts, documented requirements, preservation inferences,
observed differences and hypotheses. Do not promote correlation to verified cause.
For every proposed normative rule, identify its exact quotation in text, support
evidence IDs, applicability evidence, preservation constraints and relevant
counterevidence. Explain how each counterexample narrows the rule. If support is
insufficient, report the gap in unresolved; do not invent a business policy.
Resource ownership does not imply ownership of another record. Check both against
the current source. Distinguish conditional retirement, retry suppression,
physical cancellation, settlement, history/cache writes and visible updates.
Generalize only within the evidenced conditions; retain successful behavior.
The text must contain applicability, event relationships, verification actions,
preserved behavior and exclusions. It must not contain case IDs, assertion names,
paths, specialized field names or copyable patches. Metadata may cite evidence IDs.
No reference patch, prior experience, test outcome or expected class is supplied.
Text is a raw model candidate, not admitted experience. Evidence linking is not
proof of semantic entailment; a subsequent execution-agent review is mandatory.
'''


def check_candidate(candidate, ledger, review=None):
    """Deterministic structural gate plus explicit, separately authored review.

No string matching claims to source semantics. A plausible citation cannot pass
the separate entailment review automatically. Missing development results never
count as successful validation.
"""
    from schema_validator import validate
    schema = json.loads(Path(__file__).with_name('reflection.schema.json').read_text())
    validate(candidate, schema)
    by_id = {e['id']: e for e in ledger['entries']}
    constraints = {c['id'] for c in ledger['constraints']}
    covered = set()
    counterevidence_covered = set()
    rule_ids = set()
    for rule in candidate['rules']:
        if rule['id'] in rule_ids:
            raise ValueError('duplicate rule')
        rule_ids.add(rule['id'])
        if rule['quote'] not in candidate['text']:
            raise ValueError('rule quotation is not verbatim candidate text')
        for key in ('support', 'conditions', 'counterevidence'):
            if any(x not in by_id for x in rule[key]):
                raise ValueError('unknown evidence ID')
        if not any(by_id[x]['kind'] in {'documented_requirement', 'source_fact', 'preservation_inference'}
                   for x in rule['support']):
            raise ValueError('outcome or hypothesis alone cannot support a policy')
        if any(by_id[x]['kind'] in {'hypothesis', 'unknown'} for x in rule['conditions']):
            raise ValueError('unresolved applicability')
        if any(x not in constraints for x in rule['preserve']):
            raise ValueError('unknown preservation constraint')
        covered.update(rule['preserve'])
        counterevidence_covered.update(rule['counterevidence'])
    if covered != constraints:
        raise ValueError('preservation constraints omitted')
    if not set(ledger['mandatory_counterevidence']).issubset(counterevidence_covered):
        raise ValueError('known counterevidence omitted')
    result = {'structural_support_valid': True, 'semantic_status': 'pending',
              'admitted': False, 'development_status': 'not_run',
              'reason': 'Requires evidence entailment review and development observations.'}
    if review is None:
        return result
    if (review.get('candidate_sha256') != object_digest(candidate)
            or review.get('ledger_sha256') != object_digest(ledger)
            or review.get('reviewer') != 'execution_agent'):
        raise ValueError('unbound semantic review')
    reviewed = review.get('rules', [])
    if len(reviewed) != len(rule_ids) or {r['id'] for r in reviewed} != rule_ids:
        raise ValueError('incomplete semantic review')
    accepted = (review.get('all_normative_rules_covered') is True
                and review.get('preservation_obligations_checked') is True
                and review.get('counterevidence_handled') is True
                and not any(u['impact'] in {'applicability', 'policy'} for u in candidate['unresolved'])
                and all(r.get('supported') is True and r.get('evidence') and r.get('reason')
                   and all(x in by_id for x in r['evidence']) for r in reviewed)
                )
    # Review is an agent judgment, explicitly not proof or human approval.
    result.update(semantic_status='supported_by_execution_agent' if accepted else 'rejected_by_execution_agent',
                  reason='Development observations still required.' if accepted else 'Unsupported rule; preserve raw output.')
    return result
