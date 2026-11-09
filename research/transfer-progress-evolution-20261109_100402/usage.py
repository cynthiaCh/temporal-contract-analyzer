"""Null-safe accounting. Known subtotals never masquerade as complete usage."""
KEYS = ['input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
        'output_tokens', 'reasoning_output_tokens', 'total_tokens']


def summarize_ledger(ledger):
    if not isinstance(ledger, dict):
        return {'requests_started': None, 'requests_completed': None, 'successful_requests': None,
                'usage_unknown_requests': None, 'observed_usage_subtotal': None,
                'total_usage': None, 'usage_incomplete': True, 'measurement_errors': ['ledger unavailable']}
    events = ledger.get('events') or []
    malformed_events = not isinstance(events,list)
    if malformed_events:events=[]
    posts = [x['event'] for x in events if isinstance(x, dict) and isinstance(x.get('event'), dict)
             and x['event'].get('hook_event_name') == 'PostModelRequest']
    started, terminated = ledger.get('started'), ledger.get('completed')
    errors = ['invalid event collection'] if malformed_events else []
    if type(started) is not int or type(terminated) is not int or min(started, terminated) < 0:
        errors.append('invalid counters')
    if type(terminated) is int and terminated != len(posts):
        errors.append('post-hook/counter disagreement')
    pending = max(started - len(posts), 0) if type(started) is int else None
    if type(started) is int and started < len(posts):
        errors.append('more terminated than started')
    known = [e['token_usage'] for e in posts if isinstance(e.get('token_usage'), dict)]
    values = {k: [u[k] for u in known if type(u.get(k)) in [int, float] and u[k] >= 0] for k in KEYS}
    subtotal = {k: sum(v) if v else None for k, v in values.items()}
    unknown_per_field = {k: (pending + len(posts) - len(v)) if pending is not None else None
                         for k, v in values.items()}
    unknown_requests = (pending + sum(not isinstance(e.get('token_usage'), dict)
                                     or any(type(e['token_usage'].get(k)) not in [int, float] for k in KEYS)
                                     for e in posts)) if pending is not None else None
    incomplete = bool(errors) or unknown_requests is None or unknown_requests > 0
    totals = {k: subtotal[k] if unknown_per_field[k] == 0 else None for k in KEYS}
    return {'requests_started': started, 'requests_completed': terminated, 'post_request_hooks': len(posts),
            'successful_requests': sum(e.get('status') == 'completed' for e in posts),
            'failed_requests': sum(e.get('status') != 'completed' for e in posts),
            'pending_requests': pending, 'usage_unknown_requests': unknown_requests,
            'unknown_requests_per_field': unknown_per_field,
            'blocked_dispatches': ledger.get('blocked_requests'), 'tool_hook_attempts': ledger.get('tool_attempts'),
            'observed_usage_subtotal': subtotal if posts else None,
            'total_usage': None if incomplete else totals, 'usage_incomplete': incomplete,
            'measurement_errors': errors}
