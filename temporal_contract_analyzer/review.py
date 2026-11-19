"""Read-only, evidence-gated presentation; never a defect or utility verdict."""
from collections import Counter


NOTICE = ('Only state-publication candidates with complete evidence chains are shown; this filter supports reentrant-state-publication only. '
          'Other rules are hidden by default. Omission does not establish safety or a repair benefit from hints.')
PROTOCOL_NOTICE = ('Only state publication, listener removal ordering and argument-cache candidates with complete evidence chains are shown. '
                   'Other rules are hidden by default. Review hints against API contracts and runtime validation; omission does not establish safety or repair benefit.')


def _protocol_projection(finding, events, parsed, relations):
    """Validate each specialized relation instead of reusing a state-write label."""
    listener = finding['rule'] == 'reentrant-listener-detach'
    data = finding.get('listener_detach' if listener else 'cache_publication', {})
    if listener and data.get('status') == 'detach_before_call':
        return data, [], 'detach_before_call'
    if listener:
        ids = [data.get(k) for k in ('registration', 'receiver_capture', 'wrapper',
                                    'register_definition', 'remove_definition', 'callback', 'detach')]
        pairs = [('callback_before_listener_detach', data.get('callback'), data.get('detach'))]
        status = 'detach_after_call'
    else:
        ids = [data.get(k) for k in ('guard', 'callback', 'result_write', 'result_return')]
        ids += data.get('initializers', []) + data.get('key_writes', [])
        pairs = [('cache_key_before_compute', key, data.get('callback')) for key in data.get('key_writes', [])]
        pairs.append(('compute_before_cache_result', data.get('callback'), data.get('result_write')))
        status = 'key_before_result'
    if (data.get('status') != status or not data.get('state') or data.get('uncertainties') or
            finding['path'] not in parsed or not ids or
            any(eid not in events or events[eid]['path'] != finding['path'] or eid not in finding['evidence'] for eid in ids) or
            any(pair not in relations for pair in pairs) or
            not listener and (len(data.get('key_writes', [])) != 2 or len(data.get('initializers', [])) != 3)):
        return data, ids, 'incomplete_evidence'
    return data, ids, None


def focused_review(report):
    """Project raw facts into compact cards without mutating the source report."""
    events = {e['id']: e for f in report['files'] for e in f['events']}
    parsed = {f['path'] for f in report['files'] if f['status'] == 'parsed'}
    relations = {(r['before'], r['after']) for r in report['relations']
                 if r['kind'] == 'external_call_before_state_write'}
    clears = {(r['before'], r['after']) for r in report['relations']
              if r['kind'] in {'external_call_before_callback_clear', 'external_call_before_conditional_callback_clear'}}
    suppressed = Counter()
    grouped = {}
    context = []
    has_protocols = any(f['rule'] in {'reentrant-listener-detach', 'argument-cache-publication'} for f in report['findings'])
    protocol_relations = {(r['kind'], r['before'], r['after']) for r in report['relations']}
    for finding in report['findings']:
        if finding['rule'] in {'reentrant-listener-detach', 'argument-cache-publication'}:
            data, ids, reason = _protocol_projection(finding, events, parsed, protocol_relations)
            if reason:
                suppressed[reason] += 1
                continue
            key = (finding['rule'], finding['path'], finding['scope'], data['state'])
            if key not in grouped:
                grouped[key] = dict(rule=finding['rule'], path=finding['path'], scope=finding['scope'],
                    state=data['state'], finding_ids=[], message=finding['message'], condition=finding['condition'],
                    review_question=finding['review_question'], evidence=[])
            card = grouped[key]
            card['finding_ids'].append(finding['id'])
            known = {e['id'] for e in card['evidence']}
            for eid in ids:
                if eid not in known:
                    e = events[eid]
                    card['evidence'].append(dict(id=eid, path=e['path'], line=e['line'], kind=e['kind'],
                        text=e['text'][:240], truncated=len(e['text']) > 240))
                    known.add(eid)
            continue
        publication = finding.get('state_publication', {})
        reason = None
        if finding['rule'] != 'reentrant-state-publication':
            reason = 'exploratory_rule'
        elif publication.get('status') != 'write_after_call':
            reason = publication.get('status', 'not_established')
        else:
            ids = [publication.get(k) for k in ('guard', 'callback', 'write')]
            ids += publication.get('execution_path', [])
            if publication.get('callback_cleanup'):
                ids.append(publication['callback_cleanup']['write'])
                if publication['callback_cleanup'].get('guard'):
                    ids.append(publication['callback_cleanup']['guard'])
            if (finding['path'] not in parsed or publication.get('uncertainties') or
                    any(eid not in events or events[eid]['path'] != finding['path'] for eid in ids) or
                    (publication.get('callback'), publication.get('write')) not in relations or
                    publication.get('callback_cleanup') and
                    (publication.get('callback'), publication['callback_cleanup'].get('write')) not in clears):
                reason = 'incomplete_evidence'
        if reason:
            if reason == 'write_before_call':
                ids = [publication.get(k) for k in ('guard', 'callback', 'write')]
                if all(eid in events for eid in ids):
                    context.append(dict(path=finding['path'], state=publication['state'],
                        status=reason, write_line=events[publication['write']]['line'],
                        callback_line=events[publication['callback']]['line']))
            suppressed[reason] += 1
            continue
        key = (finding['path'], finding['scope'], publication['binding_scope'],
               publication['state'], publication['guard'], publication['write'])
        if key not in grouped:
            grouped[key] = dict(rule=finding['rule'], path=finding['path'], scope=finding['scope'],
                state=publication['state'], finding_ids=[], message=finding['message'],
                condition=finding['condition'], review_question=finding['review_question'], evidence=[])
        card = grouped[key]
        card['finding_ids'].append(finding['id'])
        if publication.get('callback_cleanup'):
            note = 'The post-call binding clear provides provenance and ordering evidence only; this card reviews entry-state writes relative to the call and does not classify the cleanup statement itself as defective.'
            if note not in card.setdefault('notes', []):
                card['notes'].append(note)
            condition = publication['callback_cleanup'].get('condition')
            if condition:
                conditional_note = 'Clearing occurs only when condition ' + condition + ' holds; it cannot be treated as an action on every path.'
                if conditional_note not in card['notes']:
                    card['notes'].append(conditional_note)
        known = {e['id'] for e in card['evidence']}
        for eid in ids:
            if eid not in known:
                e = events[eid]
                card['evidence'].append(dict(id=eid, path=e['path'], line=e['line'], kind=e['kind'],
                    text=e['text'][:240], truncated=len(e['text']) > 240))
                if (publication.get('callback_cleanup', {}).get('write') == eid and
                        publication.get('write') != eid):
                    card['evidence'][-1]['role'] = ('Binding cleared after call when condition holds (ordering fact)'
                        if publication['callback_cleanup'].get('condition') else 'Binding cleared after call (ordering fact)')
                known.add(eid)
    cards = list(grouped.values())
    return dict(schema_version='temporal-contract-focused-review-1',
        policy='source-protocol-evidence-v2' if has_protocols else 'state-publication-evidence-v1',
        notice=PROTOCOL_NOTICE if has_protocols else NOTICE,
        status=report['status'], tool_version=report['tool_version'],
        input_sha256=report['input_sha256'], tool_sha256=report['tool_sha256'],
        cards=cards, context=context, summary=dict(raw_findings=len(report['findings']), cards=len(cards),
            suppressed_findings=sum(suppressed.values()), suppressed_by_reason=dict(sorted(suppressed.items())),
            merged_findings=sum(len(c['finding_ids']) - 1 for c in cards)),
        coverage=[dict(path=f['path'], status=f['status'], analysis_scope=f.get('analysis_scope'),
                       error=f.get('error')) for f in report['files']],
        skipped=report['skipped'], limitations=report['limitations'])


def focused_markdown(report):
    if report['schema_version'] == 'temporal-contract-analysis-comparison-1':
        return '\n'.join(['# TempoEvo · Temporal relation comparison (low noise)', '', report['interpretation'],
            'Comparable parsing: ' + str(report['comparable']), 'Changed files: ' + ', '.join(report['changed_files']),
            'Each side is filtered separately; fewer cards do not establish a repair.', '', '## Before', focused_markdown(report['before']),
            '', '## After', focused_markdown(report['after'])])
    review = focused_review(report)
    summary = review['summary']
    lines = ['# TempoEvo · Temporal relation review (low noise)', '', review['notice'], '',
        'Parsing status: ' + review['status'] + '; tool version: ' + review['tool_version'],
        'Input SHA-256: ' + review['input_sha256'], 'Tool SHA-256: ' + review['tool_sha256'],
        'Original hints: %d; cards shown: %d; hidden: %d; merged: %d.' % (
            summary['raw_findings'], summary['cards'], summary['suppressed_findings'], summary['merged_findings'])]
    for card in review['cards']:
        lines += ['', '## ' + card['path'] + ' · Status ' + card['state'], card['message'],
            'Condition: ' + card['condition'], 'Review: ' + card['review_question']]
        lines += ['Note: ' + note for note in card.get('notes', [])]
        for event in card['evidence']:
            lines += ['', event['path'] + ':' + str(event['line']) + ' · ' + event['kind'] + (' · ' + event['role'] if event.get('role') else ''),
                '```text', event['text'].replace('```', '` ` `') + ('… [truncated; see source]' if event['truncated'] else ''), '```']
    if not review['cards']:
        lines += ['', 'No candidates shown by this filter; this does not establish the absence of temporal issues.']
    if review['context']:
        lines += ['', '## Ordering facts (neither alerts nor proof of sufficient protection)']
        for item in review['context']:
            lines.append('- %s: state %s is written at L%d; the external call is at L%d.' % (
                item['path'], item['state'], item['write_line'], item['callback_line']))
    lines += ['', '## Parsing coverage and limitations']
    for file in review['coverage']:
        lines.append('- ' + file['path'] + ': ' + file['status'])
        if file['analysis_scope']:
            lines.append('  ' + file['analysis_scope'])
        if file['error']:
            lines.append('  ' + str(file['error'].get('message', '')))
    lines += ['- Excluded/unread: ' + s['path'] + ' · ' + s['reason'] for s in review['skipped']]
    lines += ['- ' + limit for limit in review['limitations']]
    lines += ['', 'Reasons for hiding: ' + str(summary['suppressed_by_reason']),
              'Use --view exploratory for all hints; raw JSON and frozen experiment layers retain the complete evidence.']
    return '\n'.join(lines)
