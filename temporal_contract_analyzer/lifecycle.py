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
            qualification = ('仅表示同一词法函数/类命名空间中的语法共现；名称不保证 API 类型，'
                             '未证明属于同一请求、实例或生命周期，也未证明回调可达、重试循环或保护充分。')

            def add(rule, evidence, message, question):
                ordered = sorted({e['id']: e for e in evidence}.values(),
                                 key=lambda e: (e['line'], e['column'], e['id']))
                findings.append(dict(rule=rule, path=file['path'], scope=scope,
                    evidence=[e['id'] for e in ordered], message=message,
                    condition=qualification, review_question=question,
                    classification='review_hint_not_bug_verdict'))

            if scheduled:
                add('continuation-retry-scheduling', continuations + scheduled,
                    '完成回调/等待点与调度、retry 或 poll 名称调用出现在同一词法单元。',
                    '这些调度是否继续同一工作？结束、取消或切换后，仍可能登记或触发下一次吗？')
            if not boundaries:
                continue
            add('continuation-lifecycle-boundaries', continuations + boundaries,
                '完成回调/等待点与关闭、重新打开或清理边界名称线索出现在同一词法单元。',
                '关闭、卸载和切换是否是不同边界？哪些边界应使旧结果失效，哪些工作应继续？需从仓库证据确认。')
            guards = [e for e in events if e['kind'] == 'guard']
            # Select writes inside named lifecycle methods or syntactically
            # returned cleanup callbacks. Do not guess arbitrary variable names.
            cleanup_scopes = [e['scope'] for e in definitions]
            cleanup_scopes += [e['target_scope'] for e in events if e['kind'] == 'returned_callback']
            writes = [e for e in events if e['kind'] == 'write' and
                      any(e['scope'] == s or e['scope'].startswith(s + '/') for s in cleanup_scopes)]
            if guards or writes:
                add('continuation-guard-state-review', continuations + boundaries + guards + writes,
                    '列出相关词法单元中的条件判断，以及关闭/返回清理函数内的状态写入；存在判断不等于有效性保护。',
                    '回调检查了什么状态？关闭、卸载、重开分别更新了什么？只取消计时器能否约束已发请求？相同标识重新使用时判断是否仍适用？')
    return findings
