"""Deterministic review deltas. Unchanged findings may be referenced, never invented."""
from copy import deepcopy

from .core import EvidenceError


def links(bundle, rule_id):
    return sorted((r['source_sha256'], r['pointer']) for r in bundle['audit']['rule_links']
                  if r['rule_id'] == rule_id)


def plan(bundle, bundles, prior):
    parent = bundles.get(bundle['parent_sha256'])
    parent_rows = [r for r in prior if parent and r['candidate_sha256'] == parent['sha256']]
    accepted = parent_rows[-1] if parent_rows and parent_rows[-1]['decision'] == 'accept' else None
    changes = []
    if parent:
        changes = [k for k in ('taxonomy_version', 'labels', 'requires', 'excludes') if bundle[k] != parent[k]]
        if bundle['audit']['outcome_refs'] != parent['audit']['outcome_refs']:
            changes.append('global_outcome_evidence')
        old_boundaries = [r for r in parent['rules'] if r['category'] in ('applicability', 'exclusion')]
        new_boundaries = [r for r in bundle['rules'] if r['category'] in ('applicability', 'exclusion')]
        if old_boundaries != new_boundaries:
            changes.append('applicability_or_exclusion_rule')
        if any(links(parent,r['id']) != links(bundle,r['id']) for r in old_boundaries):
            changes.append('applicability_or_exclusion_evidence')
    previous_child_review = any(r['candidate_sha256'] == bundle['sha256'] for r in prior)
    old_rules = {r['id']:r for r in parent['rules']} if parent else {}
    old_findings = {r['rule_id']:r for r in accepted['rules']} if accepted else {}
    reference = None if accepted is None else dict(parent_sha256=parent['sha256'], decision_sha256=accepted['sha256'])
    rows = []
    for rule in bundle['rules']:
        old = old_rules.get(rule['id'])
        evidence_changed = old is not None and links(bundle, rule['id']) != links(parent, rule['id'])
        finding = old_findings.get(rule['id'])
        inherited = bool(old == rule and not evidence_changed and not changes and not previous_child_review
                         and finding and finding['supported'] is True and parent['review']['status'] != 'rejected')
        reasons = []
        if old is None: reasons.append('added_rule')
        elif old != rule: reasons.append('rule_changed')
        if evidence_changed: reasons.append('rule_evidence_changed')
        if changes: reasons.append('shared_context_changed')
        if not accepted: reasons.append('no_current_parent_acceptance')
        if previous_child_review: reasons.append('explicit_rereview')
        if finding and finding['supported'] is not True: reasons.append('parent_finding_not_supported')
        rows.append(dict(rule_id=rule['id'], before=deepcopy(old), after=deepcopy(rule),
            evidence_changed=evidence_changed, inheritable=inherited, reasons=reasons,
            before_evidence=[] if old is None else deepcopy([r for r in parent['audit']['rule_links'] if r['rule_id']==rule['id']]),
            inherited_finding=None if not inherited else dict(rule_id=rule['id'],
                supported=finding['supported'], reason=finding['reason'],
                inherited_from=dict(reference, rule_id=rule['id']))))
    inherited_ids = [r['rule_id'] for r in rows if r['inheritable']]
    return dict(candidate_sha256=bundle['sha256'], parent_sha256=bundle['parent_sha256'],
        mode='incremental' if inherited_ids else 'full', inherit_from=reference if inherited_ids else None,
        parent_decision=None if not accepted else {k:accepted[k] for k in ('sha256', 'reviewer', 'at', 'scope')},
        shared_context_changes=changes, inherited_rule_ids=inherited_ids,
        required_rule_ids=[r['rule_id'] for r in rows if not r['inheritable']], rules=rows,
        removed_rules=[deepcopy(r) for r in (parent['rules'] if parent else [])
                       if r['id'] not in {r['id'] for r in bundle['rules']}])


def resolve(bundle, bundles, prior, reference, explicit, scope):
    """Recheck under the decision lock; caller supplies only explicit findings."""
    current = plan(bundle, bundles, prior)
    if not isinstance(reference, dict) or current['inherit_from'] is None or reference != current['inherit_from']:
        raise EvidenceError('Parent acceptance or incremental review eligibility changed; reload or review in full')
    if scope != current['parent_decision']['scope']:
        raise EvidenceError('Changing the review scope requires a full review')
    if not isinstance(explicit, list) or any(not isinstance(r, dict) or
            set(r) != {'rule_id', 'supported', 'reason'} or type(r['supported']) is not bool
            or not isinstance(r['rule_id'], str) or not isinstance(r['reason'], str) for r in explicit):
        raise EvidenceError('Explicit findings need rule_id, supported and reason; inheritance is server-owned')
    supplied = {r['rule_id']:r for r in explicit}
    known = [r['id'] for r in bundle['rules']]
    if len(supplied) != len(explicit) or any(k not in known for k in supplied):
        raise EvidenceError('Duplicate or unknown explicit review rule')
    results = []
    for row in current['rules']:
        if row['rule_id'] in supplied:
            results.append(deepcopy(supplied[row['rule_id']]))
        elif row['inheritable']:
            results.append(deepcopy(row['inherited_finding']))
        else:
            raise EvidenceError('Explicit review required for '+row['rule_id'])
    return results
