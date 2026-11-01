"""Bounded JS entry-state review, independent of keyword-selected findings.

Only direct IIFEs and uniquely bound local functions are expanded. Event order
comes from AST evaluation, not the starting column of an assignment or await.
This describes candidate paths; it does not prove callback behavior or safety.
"""
from collections import defaultdict
import re


RULE = 'reentrant-state-publication'
IDENTIFIER = re.compile(r'^[A-Za-z_$][\w$]*$')
QUALIFICATION = (
    'Bounded JavaScript evaluation prefix on the selected normal path; direct IIFEs '
    'and unique local functions only. Callback reentry, runtime types, state value '
    'meaning, exceptions and full control flow are not proven.'
)


def publication_patterns(files):
    findings, relations = [], []
    for file in files:
        if file.get('language') not in {'javascript', 'typescript', 'vue'}:
            continue
        functions = {f.get('local_id', f['id']): f for f in file['functions']}
        grouped = defaultdict(list)
        declarations = defaultdict(set)
        uncertain_names = defaultdict(set)
        for event in file['events']:
            grouped[event['scope']].append(event)
            if event['kind'] in {'write', 'binding'}:
                declarations[event['scope']].update(event.get('declared_names', []))
                if (event.get('binding_kind') == 'catch' or
                        event['block'] != functions.get(event['scope'], {}).get('body_block')):
                    uncertain_names[event['scope']].update(event.get('declared_names', []))
        for binding in file['bindings']:
            declarations[binding['scope']].add(binding['name'])
            if binding.get('block') != functions.get(binding['scope'], {}).get('body_block'):
                uncertain_names[binding['scope']].add(binding['name'])
        for scope, definition in functions.items():
            if definition.get('self_name'):
                declarations[scope].add(definition['self_name'])

        def ancestry(scope):
            visited = set()
            while scope and scope not in visited:
                visited.add(scope)
                yield scope
                scope = (functions[scope].get('parent') if scope in functions else
                         scope.rsplit('/', 1)[0] if '/' in scope else None)

        def owner(scope, name):
            for current in ancestry(scope):
                if name in uncertain_names[current]:
                    return None
                if (name in functions.get(current, {}).get('parameters', []) or
                        name in declarations[current]):
                    return current
            return None

        def possible_owner(scope, name, binding):
            resolved = owner(scope, name)
            return resolved == binding or resolved is None and binding in set(ancestry(scope))

        def visible_writes(name, binding):
            return [e for e in file['events'] if e['kind'] == 'write' and
                    name in e.get('write_roots', [e.get('target')]) and
                    possible_owner(e['scope'], name, binding)]

        def parameter_call(event, entry):
            parts = event.get('callee', '').split('.')
            if (event.get('construct') or event.get('optional') or
                    not (len(parts) == 1 or len(parts) == 2 and parts[1] in {'call', 'apply'})):
                return False
            binding = owner(event['scope'], parts[0])
            if binding is None or parts[0] not in functions.get(binding, {}).get('parameters', []):
                return False
            # Block-local declarations share the parser's function namespace.
            # Ambiguous declarations are excluded, not guessed to be parameters.
            if parts[0] in declarations[binding]:
                return False
            if binding not in set(ancestry(entry)):
                return False
            # Reassigning or writing .call/.apply leaves invocation semantics unknown.
            return not visible_writes(parts[0], binding)

        def local_target(event):
            target = event.get('immediate_target_scope')
            if target:
                return target
            callee = event.get('callee', '')
            if not IDENTIFIER.fullmatch(callee) or event.get('construct') or event.get('optional'):
                return None
            binding = owner(event['scope'], callee)
            candidates = [b['target'] for b in file['bindings']
                          if b['scope'] == binding and b['name'] == callee]
            if len(candidates) != 1:
                return None
            assignments = visible_writes(callee, binding)
            if assignments and not (len(assignments) == 1 and
                                    callee in assignments[0].get('declared_names', []) and
                                    assignments[0]['scope'] == binding and
                                    assignments[0].get('rhs_kind') in {'ArrowFunctionExpression', 'FunctionExpression'}):
                return None
            return candidates[0]

        def prefix(scope, stack=(), anchors=(), budget=None):
            if budget is None:
                budget = [2000]
            if scope not in functions or scope in stack or len(stack) >= 4 or functions[scope].get('generator'):
                return
            for event in grouped[scope]:
                if budget[0] <= 0:
                    return
                budget[0] -= 1
                # An optional branch suspension may occur; do not claim the
                # later code is part of the initial synchronous prefix.
                if event['kind'] in {'await', 'yield'}:
                    return
                if event['kind'] == 'function_definition':
                    continue
                if event.get('conditions'):
                    yield event, anchors
                    continue
                if event['kind'] == 'call':
                    target = local_target(event)
                    if target:
                        yield from prefix(target, (*stack, scope), (*anchors, event), budget)
                yield event, anchors
                if event['kind'] in {'return', 'raise'}:
                    return

        for entry, definition in functions.items():
            if definition.get('parent') is None or definition.get('generator'):
                continue
            local_guards = [e for e in grouped[entry] if e['kind'] == 'guard' and not e.get('conditions')]
            if not local_guards:
                continue
            sequence = list(prefix(entry))
            indices = {e['id']: i for i, (e, _) in enumerate(sequence)}
            emitted = set()
            for guard in local_guards:
                if guard['id'] not in indices:
                    continue
                for name in guard.get('references', []):
                    if not IDENTIFIER.fullmatch(name):
                        continue
                    binding = owner(entry, name)
                    # A per-invocation local/parameter is not closure-shared state.
                    if binding is None or binding == entry:
                        continue
                    state_writes = [(i, e) for i, (e, _) in enumerate(sequence)
                                    if e['kind'] == 'write' and e.get('operator') == '=' and
                                    not e.get('conditions') and
                                    e.get('target') == name and owner(e['scope'], name) == binding]
                    for i, (callback, anchors) in enumerate(sequence):
                        if (callback['kind'] != 'call' or callback.get('conditions') or i <= indices[guard['id']] or
                                not parameter_call(callback, entry) or (name, callback['id']) in emitted):
                            continue
                        emitted.add((name, callback['id']))
                        prior = [(j, e) for j, e in state_writes if indices[guard['id']] < j < i]
                        later = [(j, e) for j, e in state_writes if j > i]
                        uncertain = [e for j, (e, _) in enumerate(sequence)
                                     if indices[guard['id']] < j < i and e['kind'] == 'write' and
                                     (e.get('conditions') and e.get('target') == name or
                                      name in e.get('assigned_names', []) and e.get('target') != name) and
                                     owner(e['scope'], name) == binding]
                        ambiguous = [e for j, (e, _) in enumerate(sequence)
                                     if indices[guard['id']] < j < i and e['kind'] == 'write' and
                                     name in e.get('assigned_names', []) and owner(e['scope'], name) is None and
                                     binding in set(ancestry(e['scope']))]
                        non_function_writes = [e for e in file['events'] if e['kind'] == 'write' and
                                               e['scope'] not in functions and name in e.get('assigned_names', []) and
                                               possible_owner(e['scope'], name, binding)]
                        uncertain += ambiguous + non_function_writes
                        status = ('not_established' if uncertain else 'write_before_call' if prior else
                                  'write_after_call' if later else 'not_established')
                        write = None if uncertain else prior[-1][1] if prior else later[0][1] if later else None
                        observed = {
                            'write_before_call': '在进入用户函数之前，已对入口读取的闭包状态写入。',
                            'write_after_call': '进入用户函数时，入口读取的闭包状态尚未完成后续写入。',
                            'not_established': '已定位入口状态读取和用户函数调用，当前同步前缀未建立对应写入关系。',
                        }[status]
                        evidence = [guard, callback, *anchors, *uncertain] + ([write] if write else [])
                        evidence = list({e['id']: e for e in evidence}.values())
                        findings.append(dict(rule=RULE, path=file['path'], scope=entry,
                            evidence=[e['id'] for e in evidence], classification='review_hint_not_bug_verdict',
                            message=observed, condition=QUALIFICATION +
                                ' .call/.apply are invocation candidates; overridden methods remain unresolved.',
                            review_question='若该用户函数同步重入当前入口，状态是否已表示工作正在执行？'
                                '调用前写入不等于保护充分；需核对写入值、清理和异常路径。'
                                '可用立即重入测试检查执行次数、排队及拒绝结果。',
                            state_publication=dict(state=name, binding_scope=binding,
                                status=status, guard=guard['id'], callback=callback['id'],
                                write=write['id'] if write else None,
                                execution_path=[e['id'] for e in anchors],
                                uncertainties=sorted({'conditional_state_write' if e.get('conditions') else
                                                      'non_function_scope_state_write' if e in non_function_writes else
                                                      'ambiguous_state_binding' if e in ambiguous else
                                                      'destructured_state_write' for e in uncertain}),
                                write_value=write.get('rhs_text') if write else None)))
                        if write:
                            before, after = (write, callback) if prior else (callback, write)
                            relations.append(dict(kind='state_write_before_external_call' if prior else
                                                  'external_call_before_state_write',
                                                  before=before['id'], after=after['id'],
                                                  qualification=QUALIFICATION))
    return findings, relations
