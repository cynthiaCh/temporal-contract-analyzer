"""Explicit operator decisions and frozen active research experience views."""
import json
import fcntl
from pathlib import Path
from copy import deepcopy

from . import archive, experience_memory as memory
from .core import EvidenceError, canonical

ACTIVE_VERSION = 'experience-active-index-v1'
UNSPECIFIED = object()


def empty_index():
    return dict(schema_version=ACTIVE_VERSION, versions={}, history=[])


def _descendant(bundles, candidate, ancestor):
    while candidate is not None:
        if candidate == ancestor:
            return True
        candidate = bundles[candidate]['parent_sha256']
    return False


def _acceptance(rows, code):
    final = [row for row in rows if row['candidate_sha256'] == code
             and row['decision'] in ('accept', 'reject')]
    if not final or final[-1]['decision'] != 'accept':
        raise EvidenceError('Activation requires an existing acceptance of this exact version')
    return final[-1]


def _index(store, bundles, rows):
    from .compact_experience import is_library
    if is_library(store):
        from .compact_experience import active_view
        current=set(active_view(store)['active_ids'])
        accepted = {r['candidate_sha256'] for r in rows if r['decision']=='accept'}
        return dict(schema_version=ACTIVE_VERSION, history=[],
                    versions={b['id']:code for code,b in bundles.items() if code in accepted and b['id'] in current})
    path = Path(store)/'active.json'
    if not path.is_file():
        raise EvidenceError('Explicit active.json is missing; migrate-active with an exact reviewed version mapping')
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        memory.object_fields(value, {'schema_version', 'versions', 'history'}, 'active index')
        if value['schema_version'] != ACTIVE_VERSION or not isinstance(value['versions'], dict) \
                or not isinstance(value['history'], list):
            raise EvidenceError('Invalid active index')
        replay = {}
        by_decision = {row['sha256']: row for row in rows}
        fields = {'sequence', 'action', 'id', 'previous_sha256', 'candidate_sha256',
                  'source_decision_sha256', 'actor', 'reason', 'at'}
        for sequence, event in enumerate(value['history'], 1):
            memory.object_fields(event, fields, 'activation event')
            if event['sequence'] != sequence or event['action'] not in ('migrate', 'activate', 'rollback', 'deactivate','withdraw_enable') \
                    or not memory.text(event['actor']) or not isinstance(event['reason'], str) \
                    or not memory.text(event['at']) or not isinstance(event['id'], str) \
                    or event['previous_sha256'] != replay.get(event['id']):
                raise EvidenceError('Invalid activation history or previous pointer')
            decision = by_decision[event['source_decision_sha256']]
            code = event['candidate_sha256']
            if event['action'] in ('deactivate','withdraw_enable'):
                if code is not None or event['previous_sha256'] is None or decision['decision'] != ('reject' if event['action']=='deactivate' else 'accept') \
                        or decision['candidate_sha256'] != event['previous_sha256']:
                    raise EvidenceError('Invalid deactivation evidence')
                if event['action']=='withdraw_enable':
                    from .experience_lifecycle import load
                    withdrawn=load(Path(store)/'workflow/revocations'/(decision['sha256']+'.json'))
                    if not withdrawn or withdrawn['actor']!=event['actor'] or withdrawn['candidate_sha256']!=event['previous_sha256']:
                        raise EvidenceError('Invalid enable withdrawal evidence')
                replay.pop(event['id'])
            else:
                bundle = bundles[code]
                previous = event['previous_sha256']
                if bundle['id'] != event['id'] or decision['decision'] != 'accept' \
                        or decision['candidate_sha256'] != code:
                    raise EvidenceError('Activation must reference exact acceptance evidence')
                if event['action'] == 'migrate' and previous is not None:
                    raise EvidenceError('Migration cannot replace an active pointer')
                if event['action'] == 'activate' and previous is not None and not _descendant(bundles, code, previous):
                    raise EvidenceError('An upgrade cannot silently select an ancestor or another branch')
                if event['action'] == 'rollback' and (previous is None or previous == code
                        or not _descendant(bundles, previous, code)):
                    raise EvidenceError('Rollback must explicitly select an accepted ancestor')
                replay[event['id']] = code
        if value['versions'] != replay:
            raise EvidenceError('Active pointers do not match their retained activation history')
        for identifier, code in value['versions'].items():
            bundle = bundles[code]
            if bundle['id'] != identifier:
                raise EvidenceError('Active pointer identity mismatch')
            _acceptance(rows, code)
        return value
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise EvidenceError('Invalid active index: '+str(error)) from error


def _change(store, index, bundle, decision, action, actor, reason):
    value = deepcopy(index)
    identifier = bundle['id']
    code = None if action in ('deactivate','withdraw_enable') else bundle['sha256']
    previous = value['versions'].get(identifier)
    if previous == code:
        return value
    value['history'].append(dict(sequence=len(value['history'])+1, action=action, id=identifier,
        previous_sha256=previous, candidate_sha256=code, source_decision_sha256=decision['sha256'],
        actor=actor, reason=reason, at=archive.now()))
    if code is None:
        value['versions'].pop(identifier, None)
    else:
        value['versions'][identifier] = code
    archive.atomic_json(Path(store)/'active.json', value)
    return value


def migrate_active(store, versions, actor, reason=''):
    """Explicit technical migration using existing decisions, never a new expert review."""
    store = Path(store)
    if not isinstance(versions, dict) or not memory.text(actor) or not isinstance(reason, str):
        raise EvidenceError('Migration needs an exact id-to-digest mapping and a named technical actor')
    with (store/'decision.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if (store/'active.json').exists():
            raise EvidenceError('Active index already exists; use explicit activate or rollback')
        bundles = {b['sha256']: b for b in memory.records(store)}
        rows = decisions(store)
        value = empty_index()
        for identifier, code in sorted(versions.items()):
            if not isinstance(identifier, str) or not isinstance(code, str) or code not in bundles \
                    or bundles[code]['id'] != identifier:
                raise EvidenceError('Migration mapping contains an unknown or unrelated version')
            decision = _acceptance(rows, code)
            value['versions'][identifier] = code
            value['history'].append(dict(sequence=len(value['history'])+1, action='migrate', id=identifier,
                previous_sha256=None, candidate_sha256=code, source_decision_sha256=decision['sha256'],
                actor=actor, reason=reason, at=archive.now()))
        archive.atomic_json(store/'active.json', value)
        return value


def activation_options(store, code):
    bundles = {b['sha256']: b for b in memory.records(store)}
    rows = decisions(store)
    index = _index(store, bundles, rows)
    if code not in bundles:
        raise EvidenceError('Unknown experience version')
    bundle = bundles[code]
    previous = index['versions'].get(bundle['id'])
    try:
        _acceptance(rows, code)
        accepted = True
    except EvidenceError:
        accepted = False
    eligible = any(entry['bundle']['sha256'] == code for entry in approved(store))
    return dict(current_sha256=previous, default_eligible=eligible,
        qualification='review_accepted' if eligible else 'awaiting_acceptance',
        can_activate=accepted and eligible and previous != code and (previous is None or _descendant(bundles, code, previous)),
        can_rollback=accepted and eligible and previous is not None and previous != code and _descendant(bundles, previous, code))


def activate(store, code, expected_current, actor, reason='', *, rollback=False):
    """Select an accepted exact version, with a stale-view check and an explicit rollback mode."""
    if not memory.text(actor) or not isinstance(reason, str):
        raise EvidenceError('Activation needs the actual operator name and a text reason')
    store = Path(store)
    with (store/'decision.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        bundles = {b['sha256']: b for b in memory.records(store)}
        rows = decisions(store)
        index = _index(store, bundles, rows)
        if code not in bundles:
            raise EvidenceError('Unknown experience version')
        bundle = bundles[code]
        decision = _acceptance(rows, code)
        previous = index['versions'].get(bundle['id'])
        if previous != expected_current:
            raise EvidenceError('Active version changed; reload before selecting a version')
        if rollback:
            if previous is None or previous == code or not _descendant(bundles, previous, code):
                raise EvidenceError('Rollback must select an accepted ancestor of the active version')
        elif previous is not None and not _descendant(bundles, code, previous):
            raise EvidenceError('Selecting an older version requires explicit rollback; unrelated branches cannot replace it')
        return _change(store, index, bundle, decision, 'rollback' if rollback else 'activate', actor, reason)


def decisions(store):
    store = Path(store)
    from .compact_experience import is_library, materialize
    if is_library(store):
        bundles, rows, _ = materialize(store)
        by_hash = {b['sha256']:b for b in bundles}
        for row in rows:
            validate_decision(row, by_hash[row['candidate_sha256']])
        return rows
    bundles = {b['sha256']:b for b in memory.records(store)}
    result = []
    for path in sorted((store/'decisions').glob('*.json')):
        row = json.loads(path.read_text(encoding='utf-8'))
        expected = memory.digest(canonical({k:v for k,v in row.items() if k!='sha256'}))
        if row.get('sha256') != expected or path.name != f"{row.get('sequence', 0):08d}-{expected}.json" \
                or row.get('sequence') != len(result)+1 or row.get('candidate_sha256') not in bundles:
            raise EvidenceError('Invalid expert decision history')
        validate_decision(row, bundles[row['candidate_sha256']], bundles, result)
        result.append(row)
    return result


def validate_decision(row, bundle, bundles=None, prior=None):
    if not memory.text(row.get('reviewer')):
        raise EvidenceError('A named operator is required')
    if not isinstance(row.get('reason'), str):
        raise EvidenceError('Review reason must be text; it may be empty')
    if row.get('decision') not in ('accept', 'reject', 'revise') or row.get('scope') not in ('research', 'exploratory'):
        raise EvidenceError('Invalid expert decision or research scope')
    findings = row.get('rules')
    if not isinstance(findings, list) or len(findings) != len(bundle['rules']):
        raise EvidenceError('Every rule needs a resolved explicit or verified inherited finding')
    expected = [r['id'] for r in bundle['rules']]
    if [r.get('rule_id') for r in findings if isinstance(r, dict)] != expected:
        raise EvidenceError('Expert rule findings must match the frozen candidate order')
    for finding in findings:
        fields = {'rule_id', 'supported', 'reason'}
        if row.get('schema_version') in ('experience-expert-decision-v2','experience-expert-decision-v3') and 'inherited_from' in finding:
            fields.add('inherited_from')
        if set(finding) != fields or type(finding['supported']) is not bool \
                or not isinstance(finding['reason'], str):
            raise EvidenceError('Each rule needs a support finding and a text reason, which may be empty')
    if row.get('schema_version') == 'experience-expert-decision-v2' or row.get('schema_version')=='experience-expert-decision-v3' and 'inherit_from' in row:
        if bundles is None or prior is None:
            raise EvidenceError('Inherited review findings require retained parent decision history')
        from .experience_review_delta import resolve
        explicit = [r for r in findings if 'inherited_from' not in r]
        expected_findings = resolve(bundle, bundles, prior, row.get('inherit_from'), explicit, row['scope'])
        if findings != expected_findings:
            raise EvidenceError('Inherited findings differ from the unchanged accepted parent rules')
    elif 'inherit_from' in row:
        raise EvidenceError('Review inheritance requires the v2 decision schema')
    if row.get('schema_version')=='experience-expert-decision-v3':
        intent=row.get('enable_authorization')
        if not isinstance(intent,dict) or set(intent)!={'authorized','expected_current','authorized_by','candidate_sha256'} \
                or type(intent['authorized']) is not bool or intent['authorized_by']!=row['reviewer'] \
                or intent['candidate_sha256']!=bundle['sha256'] or intent['authorized']!=(row['decision']=='accept' and row.get('auto_enable') is True):
            raise EvidenceError('Invalid exact-version automatic enable authorization')
        if intent['expected_current'] is not None and (not isinstance(intent['expected_current'],str) or len(intent['expected_current'])!=64):
            raise EvidenceError('Invalid expected active version in authorization')
        submitted=row.get('submitted_request',{})
        if any(submitted.get(k)!=row.get(k) for k in ('reviewer','decision','reason','scope','auto_enable','request_id')):
            raise EvidenceError('Human authorization differs from its original submitted request')
    if row['decision'] == 'accept' and (not all(r['supported'] for r in findings)
            or bundle['review']['status'] == 'rejected'):
        raise EvidenceError('Unsupported or rejected rules cannot be accepted')
    report = row.get('report_sha256')
    if report is not None and (not isinstance(report, str) or len(report) != 64):
        raise EvidenceError('Invalid review report digest')


def decide(store, candidate_sha256, request, report_sha256=None, *, activate_version=False,
           expected_current=UNSPECIFIED):
    """Operator entry point. Never called by automatic reflection or repair."""
    from .compact_experience import is_library
    if is_library(store):
        raise EvidenceError('Use the review page or edit review in the corresponding experience file')
    fields = {'reviewer', 'decision', 'reason', 'scope', 'rules'}
    if not isinstance(request, dict) or not fields<=set(request) or set(request)-fields-{'inherit_from','auto_enable','request_id'}:
        raise EvidenceError('Expert request must contain reviewer, decision, reason, scope and per-rule findings')
    store = Path(store)
    if type(activate_version) is not bool:
        raise EvidenceError('Activation choice must be boolean')
    with (store/'decision.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        bundles = {b['sha256']:b for b in memory.records(store)}
        if candidate_sha256 not in bundles:
            raise EvidenceError('Unknown expert-review candidate')
        prior = decisions(store)
        from . import experience_lifecycle as lifecycle
        if 'auto_enable' in request and type(request['auto_enable']) is not bool:raise EvidenceError('auto_enable must be an explicit boolean')
        if 'request_id' in request:
            lifecycle.nonce(request['request_id'])
            repeated=[r for r in prior if r.get('request_id')==request['request_id']]
            if repeated:
                row=repeated[0]
                if row['candidate_sha256']!=candidate_sha256 or row.get('submitted_request')!=request:
                    raise EvidenceError('Review request_id reused with different content')
                return row
        index = _index(store, bundles, prior)
        bundle = bundles[candidate_sha256]
        previous = index['versions'].get(bundle['id'])
        if expected_current is not UNSPECIFIED and previous != expected_current:
            raise EvidenceError('Active version changed; reload before submitting this review')
        # Content acceptance is sufficient; effect reports are optional.
        row = dict(deepcopy(request), schema_version='experience-expert-decision-v2' if 'inherit_from' in request else 'experience-expert-decision-v1',
                   actor='named_operator', candidate_sha256=candidate_sha256,
                   report_sha256=report_sha256, at=archive.now(), sequence=len(prior)+1)
        if 'auto_enable' in request or 'request_id' in request:
            row.update(schema_version='experience-expert-decision-v3',submitted_request=deepcopy(request),
                enable_authorization=dict(authorized=request['decision']=='accept' and request.get('auto_enable') is True,
                    expected_current=previous,authorized_by=request['reviewer'],candidate_sha256=candidate_sha256))
        if 'inherit_from' in request:
            from .experience_review_delta import resolve
            row['rules'] = resolve(bundle, bundles, prior, request['inherit_from'], request['rules'], request['scope'])
        validate_decision(row, bundles[candidate_sha256], bundles, prior)
        row['sha256'] = memory.digest(canonical(row))
        path = store/'decisions'/f"{row['sequence']:08d}-{row['sha256']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8') as target:
            target.write(json.dumps(row, ensure_ascii=False, indent=2)+'\n')
        if row['decision'] == 'reject' and previous == candidate_sha256:
            _change(store, index, bundle, row, 'deactivate', row['reviewer'], row['reason'])
        elif row['decision'] == 'accept' and activate_version \
                and (previous is None or _descendant(bundles, candidate_sha256, previous)):
            _change(store, index, bundle, row, 'activate', row['reviewer'], row['reason'])
        lifecycle.on_decision(store,row)
        return row


def active(store):
    bundles = {b['sha256']:b for b in memory.records(store)}
    rows = decisions(store)
    index = _index(store, bundles, rows)
    return [dict(bundle=bundles[code], expert_decision=_acceptance(rows, code))
            for identifier, code in sorted(index['versions'].items())]


def approved(store):
    """Accepted retrieval guidance, resolving compact revisions and merges."""
    bundles = {b['sha256']: b for b in memory.records(store)}
    latest = {}
    for row in decisions(store):
        latest[row['candidate_sha256']] = row
    accepted = [dict(bundle=bundles[row['candidate_sha256']], expert_decision=row)
            for row in sorted(latest.values(), key=lambda r: r['sequence'])
            if row['decision'] == 'accept' and not
            (Path(store)/'workflow/revocations'/(row['sha256']+'.json')).exists()]
    from .compact_experience import is_library,active_view
    if is_library(store):
        current=set(active_view(store)['active_ids'])
        return [entry for entry in accepted if entry['bundle']['id'] in current]
    # Explicitly reviewed merges consolidate exact source versions. The original
    # acceptance and frozen historical snapshots remain valid and readable.
    superseded=set()
    for entry in accepted:
        bundle=entry['bundle'];notes=bundle['audit']['notes']
        operation=next((n for n in reversed(notes) if n.startswith('Reflection operation: ')),None)
        targets=next((n.partition(': ')[2].split(',') for n in reversed(notes) if n.startswith('Reflection targets: ')),[])
        if operation=='Reflection operation: merge' and len(set(targets))>=2 and bundle['parent_sha256'] in targets and all(code in bundles for code in targets):
            superseded.update(targets)
    return [entry for entry in accepted if entry['bundle']['sha256'] not in superseded]


def review_plan(store, code):
    from .experience_review_delta import plan
    bundles = {b['sha256']:b for b in memory.records(store)}
    if code not in bundles:
        raise EvidenceError('Unknown review candidate')
    return plan(bundles[code], bundles, decisions(store))


def review_template(store, code, full=False):
    delta = review_plan(store, code)
    inherited = delta['mode'] == 'incremental' and not full
    result = dict(reviewer='', decision='revise', reason='',
        scope=delta['parent_decision']['scope'] if inherited else 'exploratory',
        rules=[dict(rule_id=r['rule_id'], supported=False, reason='') for r in delta['rules']
               if not inherited or not r['inheritable']])
    if inherited:
        result['inherit_from'] = delta['inherit_from']
    return result


def freeze(store, *, legacy=False):
    # The legacy argument remains for compatibility. Native active pointers do
    # not gate this bank; compact accepted replacements are resolved by approved().
    entries = approved(store)
    from .compact_experience import is_library, reviewed_summaries
    if is_library(store):
        summaries=reviewed_summaries(store)
        entries=[dict(entry, retrieval_summary=summaries[entry['bundle']['id']]) if entry['bundle']['id'] in summaries else entry for entry in entries]
    result = dict(schema_version='experience-active-snapshot-v1', scope='research_only',
                  entries=entries)
    result['sha256'] = memory.digest(canonical(result))
    return result


def validate_snapshot(store, snapshot):
    if not isinstance(snapshot, dict) or set(snapshot) != {'schema_version','scope','entries','sha256'} \
            or snapshot['schema_version'] != 'experience-active-snapshot-v1' or snapshot['scope'] != 'research_only' \
            or snapshot['sha256'] != memory.digest(canonical({k:v for k,v in snapshot.items() if k!='sha256'})):
        raise EvidenceError('Invalid frozen active snapshot')
    seen = set()
    history = None
    bundles = None
    for entry in snapshot['entries']:
        fields={'bundle','expert_decision'}
        if 'retrieval_summary' in entry:
            from .compact_experience import validate_summary
            fields.add('retrieval_summary')
            validate_summary(entry['retrieval_summary'])
            if entry['retrieval_summary']['review']['decision']!='accept' or entry['retrieval_summary']['source_record']!=entry['bundle']['sha256']:
                raise EvidenceError('Snapshot summary must be accepted for this exact experience')
        memory.object_fields(entry, fields, 'active snapshot entry')
        bundle, decision = entry['bundle'], entry['expert_decision']
        memory.validate(bundle, lambda code:memory.source_bytes(store, code))
        if history is None:
            history = decisions(store)
            bundles = {b['sha256']:b for b in memory.records(store)}
        position = next((i for i,r in enumerate(history) if r['sha256']==decision.get('sha256')), None)
        if position is None or history[position] != decision:
            raise EvidenceError('Snapshot decision needs its retained audited history')
        validate_decision(decision, bundle, bundles, history[:position])
        if decision['decision'] != 'accept' or decision['candidate_sha256'] != bundle['sha256'] \
                or decision['sha256'] != memory.digest(canonical({k:v for k,v in decision.items() if k!='sha256'})) \
                or bundle['sha256'] in seen:
            raise EvidenceError('Snapshot must bind unique expert-accepted records')
        seen.add(bundle['sha256'])
    return snapshot
