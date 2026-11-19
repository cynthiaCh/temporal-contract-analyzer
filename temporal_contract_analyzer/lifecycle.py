"""Lexically bounded lifecycle clues, never dataflow or business-contract proofs.

Uses parsed calls/definitions/guards/writes only. Names narrow the search; they
do not establish API identity. No case IDs, oracle inputs or model outcomes.
"""
from collections import defaultdict
import re


BOUNDARIES = {'close', 'aclose', 'dispose', 'destroy', 'unmount', 'stop', 'cancel',
              'abort', 'reopen', 'invalidate', 'disconnect', 'detach'}
RETRY_WORDS = {'schedule', 'retry', 'poll'}


def words(name):
    return set(re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name).lower().split('_'))


def owner(scope):
    # One top-level lexical function or class namespace; never an entire
    # file containing otherwise unrelated functions. Nested factories may still
    # contain multiple owners: the report explicitly leaves that unresolved.
    return '/'.join(scope.split('/')[:2])


def lifecycle_patterns(files):
    findings = []
    for file in files:
        groups = defaultdict(list)
        for event in file['events']:
            groups[owner(event['scope'])].append(event)
        for scope, events in groups.items():
            calls = [e for e in events if e['kind'] == 'call']
            continuations = [e for e in events if e['kind'] == 'await' or
                             (e['kind'] == 'call' and 'continuation' in e['tags'])]
            if not continuations:
                continue
            definitions = [e for e in events if e['kind'] == 'function_definition'
                           and words(e.get('name', '')) & BOUNDARIES]
            effects = [e for e in calls if e['callee'].rsplit('.', 1)[-1] in
                       {'useEffect', 'useLayoutEffect', 'onUnmounted', 'onBeforeUnmount', 'onCleanup'}]
            cleanup = [e for e in calls if 'cleanup_or_cancel' in e['tags'] or
                       words(e['callee'].rsplit('.', 1)[-1]) & BOUNDARIES]
            boundaries = definitions + effects + cleanup
            scheduled = [e for e in calls if 'scheduling' in e['tags'] or
                         (words(e['callee'].rsplit('.', 1)[-1]) & RETRY_WORDS and not
                          words(e['callee'].rsplit('.', 1)[-1]) & {'clear', 'cancel', 'stop', 'remove'})]
            qualification = ('This is syntax co-occurrence within a lexical function/class namespace. Names do not establish API types, shared request/instance/lifetime, callback reachability, retry loops or sufficient protection.')

            def add(rule, evidence, message, question):
                ordered = sorted({e['id']: e for e in evidence}.values(),
                                 key=lambda e: (e['line'], e['column'], e['id']))
                findings.append(dict(rule=rule, path=file['path'], scope=scope,
                    evidence=[e['id'] for e in ordered], message=message,
                    condition=qualification, review_question=question,
                    classification='review_hint_not_bug_verdict'))

            if scheduled:
                add('continuation-retry-scheduling', continuations + scheduled,
                    'Completion callbacks or waits co-occur with scheduling, retry or poll-related calls in one lexical unit.',
                    'Do these schedules continue the same work? Can another attempt be registered or triggered after completion, cancellation or switching?')
            if not boundaries:
                continue
            add('continuation-lifecycle-boundaries', continuations + boundaries,
                'Completion callbacks or waits co-occur with close, reopen or cleanup-related names in one lexical unit.',
                'Are close, unmount and switch distinct boundaries? Use repository evidence to establish which results expire and which work must continue.')
            guards = [e for e in events if e['kind'] == 'guard']
            # Select writes inside named lifecycle methods or syntactically
            # returned cleanup callbacks. Do not guess arbitrary variable names.
            cleanup_scopes = [e['scope'] for e in definitions]
            cleanup_scopes += [e['target_scope'] for e in events if e['kind'] == 'returned_callback']
            writes = [e for e in events if e['kind'] == 'write' and
                      any(e['scope'] == s or e['scope'].startswith(s + '/') for s in cleanup_scopes)]
            if guards or writes:
                add('continuation-guard-state-review', continuations + boundaries + guards + writes,
                    'The evidence lists lexical guards and state writes in close or returned cleanup functions. A guard alone does not establish validity protection.',
                    'What state does the callback check? What changes on close, unmount and reopen? Can timer cancellation constrain requests already sent? Does the check remain valid when an identifier is reused?')
    return findings
