"""Bounded syntax clues for inline callbacks and captured-value/output lifetimes.

No case metadata, model traces, oracle, type inference or candidate execution.
The producer and subscriber clues are deliberately NOT joined into a proven
runtime chain: object factories, instances and arbitrary dispatch are unresolved.
"""
from collections import defaultdict
import re

from .lifecycle import words


MUTATORS = {'set', 'put', 'update', 'append', 'push', 'add', 'delete', 'remove',
            'insert', 'write', 'persist', 'save', 'commit'}
TRANSITIONS = {'open', 'close', 'reopen', 'navigate', 'replace', 'switch',
               'select', 'activate', 'deactivate', 'dispose', 'reset', 'unmount'}
RECORDS = {'capture', 'archive', 'persist', 'save', 'write', 'commit', 'append', 'store'}
OUTPUTS = {'render', 'display', 'show', 'publish', 'present'}
IDENTIFIER = re.compile(r'^[A-Za-z_$][\w$]*$')


def position(event):
    return event['line'], event['column']


def end(event):
    return event['end_line'], event['end_column']


def ancestors(scope):
    while scope:
        yield scope
        scope = scope.rsplit('/', 1)[0] if '/' in scope else ''


def names(call):
    return words(call.get('callee', '').rsplit('.', 1)[-1])


def references(event):
    return set(event.get('references', []))


def argument_refs(event):
    return {r for group in event.get('argument_references', []) for r in group}


def uses(refs, variable):
    return any(r == variable or r.startswith(variable + '.') for r in refs)


def exclusive(left, right):
    a, b = set(left.get('conditions', [])), set(right.get('conditions', []))
    return any(('else of ' + c[3:]) in b for c in a if c.startswith('if ')) or any(
        ('else of ' + c[3:]) in a for c in b if c.startswith('if '))


def reentrancy_patterns(files):
    findings, relations = [], []
    for file in files:
        events = file['events']
        functions = {f.get('local_id', f['id']): f for f in file['functions']}
        grouped = defaultdict(list)
        for event in events:
            grouped[event['scope']].append(event)

        def suspended_function(scope):
            definition = functions.get(scope, {})
            return (definition.get('async') or definition.get('generator') or
                    any(e['kind'] == 'yield' for e in grouped[scope]))

        def add(rule, scope, evidence, message, condition, question):
            chosen = sorted({e['id']: e for e in evidence}.values(),
                            key=lambda e: (e['line'], e['column'], e['id']))
            findings.append(dict(rule=rule, path=file['path'], scope=scope,
                evidence=[e['id'] for e in chosen], message=message, condition=condition,
                review_question=question, classification='review_hint_not_bug_verdict'))

        # Producer side. Direct invocation means a Call AST node in the same
        # function, including a loop body; never flatten a nested callback.
        for scope, local in grouped.items():
            if scope == '<module>' or suspended_function(scope):
                continue
            calls = [e for e in local if e['kind'] == 'call']
            mutations = [e for e in local if
                         (e['kind'] == 'write' and any(c in e.get('target', '') for c in '.[')) or
                         (e['kind'] == 'call' and e.get('receiver') and names(e) & MUTATORS)]
            for callback in calls:
                loop = any(b.get('target') == callback.get('callee')
                           for b in callback.get('loop_bindings', []))
                if not (callback.get('binding') == 'parameter_callback' or loop):
                    continue
                if any(e['kind'] in {'await', 'yield'} and position(e) < position(callback) for e in local):
                    continue
                prior = [e for e in mutations if end(e) <= position(callback) and not exclusive(e, callback)]
                if not prior:
                    continue
                mutation = max(prior, key=position)
                evidence = [mutation, callback]
                evidence += [e for e in local if e['kind'] == 'guard' and
                             position(mutation) < position(e) < position(callback)]
                add('state-write-inline-notification', scope, evidence,
                    '成员写入或集合/持久化名称调用之后，同一非 async 函数直接调用参数回调或循环取出的可调用项。',
                    '回调未位于另一个嵌套函数体，且此前未发现 await/yield；只是源码上的候选直接通知路径。'
                    '名称、循环元素和路径可达性未作类型/控制流证明，未证明它与其他文件中的订阅者是同一实例。',
                    '该调用是否通知外部消费者？消费者能否在返回前重新进入当前对象？调用后继续使用的状态是否仍有效，最新请求如何决定优先级？')
                relations.append(dict(kind='lexical_write_before_direct_call', before=mutation['id'],
                    after=callback['id'], qualification='Source order in one function; path execution, callback type and reentry remain unproven.'))

        # Subscriber side. Inline callback arguments and uniquely bound named
        # callbacks are scoped to the actual registration call. Passing an
        # object onward exposes its methods but does not establish invocation.
        registrations = [e for e in events if e['kind'] == 'call' and 'registration' in e.get('tags', [])]
        definitions = [e for e in events if e['kind'] == 'function_definition']

        def visible_object(obj, declaration_scope, callback_scope):
            # A callback parameter/local of the same spelling is not the outer
            # object. Reassigned outer objects are unresolved as well.
            root = obj.split('.', 1)[0]
            for scope in ancestors(callback_scope):
                writes = [e for e in grouped[scope] if e['kind'] == 'write' and e.get('target') == root]
                if scope == declaration_scope:
                    return len(writes) <= 1
                if (root in functions.get(scope, {}).get('parameters', []) or writes or
                        any(b['scope'] == scope and b['name'] == root for b in file['bindings'])):
                    return False
            return False

        for registration in registrations:
            callback_scopes = set()
            anchors = []
            for e in events:
                if (e['kind'] == 'callback_argument' and e['scope'] == registration['scope'] and
                        e.get('callee') == registration.get('callee') and
                        position(registration) <= position(e) and end(e) <= end(registration)):
                    callback_scopes.add(e['target_scope']); anchors.append(e)
            for arg in registration.get('arguments', []):
                if not IDENTIFIER.fullmatch(arg):
                    continue
                for enclosing in ancestors(registration['scope']):
                    bindings = [b for b in file['bindings'] if b['scope'] == enclosing and b['name'] == arg]
                    writes = [e for e in grouped[enclosing] if e['kind'] == 'write' and e.get('target') == arg]
                    if bindings or writes or arg in functions.get(enclosing, {}).get('parameters', []):
                        if len(bindings) == 1 and not writes:
                            callback_scopes.add(bindings[0]['target'])
                        break
            for scope in sorted(callback_scopes):
                if suspended_function(scope):
                    continue
                local = grouped[scope]
                calls = [e for e in local if e['kind'] == 'call' and not any(
                    w['kind'] in {'await', 'yield'} and position(w) < position(e) for w in local)]
                transitions = [e for e in calls if names(e) & TRANSITIONS]
                forwarded, methods = [], []
                for call in calls:
                    # Object ownership is syntax-bound, not guessed from names
                    # such as `navigation`, `view`, `session` or `current`.
                    for definition in definitions:
                        obj = definition.get('object_target')
                        parent = functions.get(definition['scope'], {}).get('parent')
                        if (obj and parent in set(ancestors(registration['scope'])) and
                                visible_object(obj, parent, scope) and
                                obj in argument_refs(call) and words(definition.get('name', '')) & TRANSITIONS):
                            forwarded.append(call); methods.append(definition)
                if not transitions and not forwarded:
                    continue
                evidence = [registration] + anchors + transitions + forwarded + methods
                evidence += [e for e in definitions if e['scope'] == scope]
                add('callback-reentrant-transition', scope, evidence,
                    '登记的回调体直接出现状态切换名称调用，或把具有状态切换方法的同作用域对象传给其他调用。',
                    '只关联当前注册实参及其回调作用域；没有把嵌套定时/Promise 回调内的操作算成直接调用。'
                    '登记 API 名称不证明通知是同步的，对象转交不证明下游调用其方法；与写入端是否连通需核查。',
                    '通知是否可能同步到达？接收者能否重入打开、关闭或切换操作？若外层调用随后恢复，应保留哪一次请求的状态？')

        # Local captured-value flow. Edges require AST references, lexical
        # statement order and no intervening assignment to the captured name.
        # These are potential flows, not alias/immutability or path proofs.
        for scope, local in grouped.items():
            captures = [e for e in local if e['kind'] == 'write' and e.get('operator') == '=' and
                        IDENTIFIER.fullmatch(e.get('target', '')) and
                        (e.get('rhs_callee') or e.get('rhs_kind') in {'ObjectExpression', 'Dict'})]
            calls = [e for e in local if e['kind'] == 'call']
            records = [e for e in calls if names(e) & RECORDS]
            outputs = [e for e in calls if names(e) & OUTPUTS]

            def stable(variable, start, stop):
                return not any(e['kind'] == 'write' and e.get('target') == variable and
                               end(start) <= position(e) < position(stop) for e in local)

            for capture in captures:
                variable = capture['target']
                for record in records:
                    if not (end(capture) <= position(record) and uses(argument_refs(record), variable)
                            and stable(variable, capture, record) and not exclusive(capture, record)):
                        continue
                    aliases = [e for e in local if e['kind'] == 'write' and e.get('rhs_callee') == record['callee']
                               and position(e) <= position(record) and end(record) <= end(e)
                               and IDENTIFIER.fullmatch(e.get('target', ''))]
                    consumers = []
                    for output in outputs:
                        if end(record) > position(output) or exclusive(record, output):
                            continue
                        direct = uses(argument_refs(output), variable) and stable(variable, capture, output)
                        returned = any(uses(argument_refs(output), a['target']) and stable(a['target'], a, output) for a in aliases)
                        if direct or returned:
                            consumers.append(output)
                    if not consumers:
                        continue
                    # The latest capture for this effect is one local clue;
                    # existing guards are included without rating sufficiency.
                    finish = max(end(o) for o in consumers)
                    context = [e for e in local if end(capture) <= position(e) <= finish and
                               e['kind'] in {'guard', 'await', 'yield'}]
                    intermediate = [e for e in calls if end(capture) <= position(e) < position(record) and
                                    e['block'] == capture['block']]
                    add('snapshot-output-lifetime-split', scope,
                        [capture, record] + aliases + consumers + context + intermediate,
                        '局部捕获值被归档/持久化名称调用消费；该值或调用返回值随后被界面/发布名称调用消费。',
                        '基于同一函数内原始变量/成员引用与源码顺序，未见变量重新赋值；不证明深拷贝、不可变、'
                        '对象别名稳定或跨分支数据流。归档与显示名称只是用途线索，不自动判定生命周期必须不同。',
                        '数据应绑定操作入口的哪份值？中间调用能否触发回调、编辑或导航？持久效果与显示效果是否共享失效条件？'
                        '当前标识相同是否足以代表同一次访问，现有身份判断在重开后仍成立吗？')
                    for consumer in consumers:
                        relations.append(dict(kind='lexical_capture_before_consumer', before=capture['id'],
                            after=consumer['id'], qualification='Local source references and lexical order; ownership, immutability and reachability remain unproven.'))
    return findings, relations
