"""Daily review views of archived hints; never inferred obligations or labels.

This projection is deliberately separate from the frozen analysis/layer payloads.
All locations refer to the finding's existing syntax evidence.
"""
from .lifecycle import BOUNDARIES, words


CHANGE_QUESTIONS = {
    'reentrant-state-publication': 'A user function may synchronously reenter before returning. Check when shared state is written and what value it receives.',
    'effect-after-await': 'The request, object lifetime or result version may change during a wait. Check which changes matter here.',
    'commit-after-yield': 'Transaction state or exit paths may change across yield. Check commit and notification requirements.',
    'cleanup-handle-after-call': 'Reentry, close or switching may occur during the right-hand-side call. Check which work owns the returned handle.',
    'continuation-and-listener-removal': 'A listener may be removed while work already started continues. Trace the continuation.',
    'continuation-lifecycle-boundaries': 'Close, unmount, reopen or switching may occur during a wait or callback. Check whether the same lifetime still applies.',
    'continuation-guard-state-review': 'Close or reopen may change guard state. Check whether the guard and callback refer to the same work.',
    'continuation-retry-scheduling': 'Old work may continue scheduling after completion, cancellation or switching. Check reachability.',
    'state-write-inline-notification': 'A user callback may change state or reenter the operation during synchronous notification. Check the actual call path.',
    'callback-reentrant-transition': 'A callback may close, switch or reenter. Check whether state remains applicable when the callback returns.',
    'snapshot-output-lifetime-split': 'Captured values and output objects may have different lifetimes. Check historical-record and current-display requirements.',
    'listen-before-connect': 'Check the API and callers to establish whether connection emits synchronously and whether the listener is already active.',
    'connect-before-listen': 'Check the API and callers to establish whether connection emits synchronously and whether the listener is already active.',
    'early-return-from-async-iteration': 'An early return changes the resource-use lifetime. Check ownership and closing responsibility.',
    'cleanup-in-finally': 'Cleanup completion and exception paths may change during exit or cancellation. Check required behavior.',
    'asyncio-shield-call': 'A waiter may be cancelled. Check whether the shared task should continue and who owns it.',
}


def cards(report):
    if not report:
        return []
    events = {event['id']: event for file in report['files'] for event in file['events']}
    result = []
    for finding in report['findings']:
        evidence = [events[eid] for eid in finding['evidence']]
        boundaries, effects, guards = [], [], []
        for event in evidence:
            tags = set(event.get('tags', []))
            name = event.get('callee', event.get('name', '')).rsplit('.', 1)[-1]
            if (event['kind'] in {'await', 'yield', 'async_iteration', 'resource_scope', 'returned_callback'}
                    or tags & {'continuation', 'parameter_callback', 'registration', 'notification',
                               'coordination', 'cleanup_or_cancel', 'scheduling'}
                    or words(name) & BOUNDARIES):
                boundaries.append(event['id'])
            if event['kind'] == 'write' or 'effect' in tags:
                effects.append(event['id'])
            if event['kind'] == 'guard' or 'cleanup_or_cancel' in tags:
                guards.append(event['id'])
        publication = finding.get('state_publication')
        if publication:
            boundaries = [publication['callback'], *publication['execution_path']]
            guards = [publication['guard']]
        result.append({
            'finding_id': finding['id'], 'rule': finding['rule'], 'title': finding['message'],
            'classification': 'candidate_boundary_review',
            'boundary': {'summary': 'A candidate wait, notification, call or exit point. Review the actual execution boundary.',
                         'evidence_ids': boundaries or finding['evidence']},
            'possible_changes': {'summary': CHANGE_QUESTIONS.get(finding['rule'],
                                 'State, identity or resource ownership may change across this point. Establish the requirement from repository evidence.')},
            'effects': {'summary': 'Candidate writes or effect calls. Review their business meaning and reachability.' if effects else
                        'This hint does not locate a concrete effect. Trace writes, notifications, cleanup and scheduling in continuations or callbacks.',
                        'evidence_ids': effects},
            'requirement_protection': {'summary': finding['review_question'], 'evidence_ids': guards},
            'condition': finding['condition'], 'evidence_ids': finding['evidence'],
        })
    return result
