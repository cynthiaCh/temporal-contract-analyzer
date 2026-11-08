"""Research-only primitives; no case discovery, scoring or model execution here.

Taxonomy must be supplied from the missing authoritative specification. Tests
use synthetic classes, never claims about the real T1–T4 taxonomy.
"""
import hashlib
import json


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def visible_input(task, sources, ast):
    """Explicit whitelist; management metadata is deliberately not accepted."""
    return {'task': task, 'sources': sources, 'ast': ast}


def route(analysis, library, taxonomy, sources):
    """Fail closed on unresolved facts, exclusions, multiple matches or drift.

    Facts must point to a literal current source quote and its numbered line.
    This checks provenance, not the semantic truth of a model's interpretation.
    """
    def auto(reason):
        return {'condition': 'AUTO', 'selected': None, 'reason': reason}
    if set(analysis) - {'primary_class', 'facts', 'contract', 'evidence', 'secondary_tags'}:
        return auto('unexpected_analysis_metadata')
    primary = analysis.get('primary_class')
    if primary not in taxonomy:
        return auto('unknown_class')
    entries = [x for x in library if x['primary_class'] == primary]
    if not entries:
        return auto('empty_class')
    facts = {}
    for fact in analysis.get('facts', []):
        proof = fact.get('evidence', {})
        lines = sources.get(proof.get('file'), '').splitlines()
        line = proof.get('line', 0)
        if not isinstance(line, int) or not 1 <= line <= len(lines):
            return auto('unverified_fact')
        if not proof.get('quote') or proof['quote'] not in lines[line - 1]:
            return auto('unverified_fact')
        key, state = fact['predicate'], fact['state']
        if state not in ('known', 'unknown', 'contradicted'):
            return auto('invalid_fact_state')
        if key in facts and facts[key] != state:
            return auto('conflicting_facts')
        facts[key] = state
    eligible = []
    for entry in entries:
        # Bind text AND applicability: an unchanged text hash alone is insufficient.
        payload = {k: entry[k] for k in ('text', 'version', 'primary_class', 'requires', 'excludes')}
        expected = digest(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        if entry.get('sha256') != expected:
            return auto('digest_mismatch')
        if not entry['requires']:
            return auto('missing_applicability')
        if all(facts.get(k) == 'known' for k in entry['requires']) and all(
            facts.get(k) == 'contradicted' for k in entry['excludes']
        ):
            eligible.append(entry)
    if len(eligible) > 1:
        return auto('unresolved_conflict')
    if not eligible:
        return auto('insufficient_or_contradictory_premises')
    entry = eligible[0]
    return {'condition': 'ROUTED', 'selected': entry['sha256'], 'text': entry['text'], 'reason': 'verified_premises'}


def differences(before, after, standards, explanations=None):
    """Extract actual/standard deltas from generic behavioral booleans.

    Standards are evaluation-adapter data. Explanations are explicitly attributed
    execution-agent checks, never invented from assertion labels or file names.
    Missing effects stay unknown, never silently become failure or success.
    """
    result = {'differences': [], 'existing_successes': [], 'improvements': [],
              'regressions': [], 'unknown': [], 'explanations': explanations or []}
    for key, expected in standards.items():
        old, new = before.get(key), after.get(key)
        row = {'relation': key, 'expected': expected, 'before': old, 'after': new}
        if type(old) is not bool or type(new) is not bool:
            result['unknown'].append(row)
            continue
        if new != expected:
            result['differences'].append(row)
        if old == expected:
            result['existing_successes'].append(row)
        if old != expected and new == expected:
            result['improvements'].append(row)
        if old == expected and new != expected:
            result['regressions'].append(row)
    return result
