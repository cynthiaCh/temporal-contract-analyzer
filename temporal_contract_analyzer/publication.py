"""Bounded JS entry-state review, independent of keyword-selected findings.

Only direct IIFEs and uniquely bound local functions are expanded. Event order
comes from AST evaluation, not the starting column of an assignment or await.
This describes candidate paths; it does not prove callback behavior or safety.
"""
from collections import defaultdict
import re

from .reflective import reflective_patterns
from .countdown import countdown_patterns
from .protocols import protocol_patterns


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

        def post_call_clear(event, entry):
            # A later clear cannot rewrite a callee value already evaluated.
            # Admit only one simple, same-frame clear on the straight prefix;
            # this is not a general reaching-definitions or alias analysis.
            name = event.get('callee', '').split('.')[0]
            binding = owner(event['scope'], name)
            writes = visible_writes(name, binding) if binding is not None else []
            if len(writes) != 1 or event['scope'] != entry:
                return None
            write = writes[0]
            if (write['scope'] != entry or write.get('target') != name or write.get('operator') != '=' or
                    event['block'] != functions[entry].get('body_block') or write['block'] != event['block'] or
                    event.get('conditions') or write.get('conditions') or event.get('conditional_path') or
                    write.get('conditional_path') or not event.get('linear_block') or not write.get('linear_block')):
                return None
            is_null = write.get('rhs_kind') == 'NullLiteral'
            is_undefined = (write.get('rhs_kind') == 'Identifier' and write.get('rhs_text') == 'undefined' and
                not any('undefined' in names for names in declarations.values()) and
                not any('undefined' in f.get('parameters', []) for f in functions.values()) and
                not any(i['local'] == 'undefined' for i in file['imports']))
            if not (is_null or is_undefined):
                return None
            sequence = [e['id'] for e, _ in prefix(entry)]
            if event['id'] not in sequence or write['id'] not in sequence or sequence.index(write['id']) <= sequence.index(event['id']):
                return None
            return write

        def parameter_call(event, entry, allowed_later_clear=None):
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
            # Other reassignments and .call/.apply writes remain unresolved.
            writes = visible_writes(parts[0], binding)
            if not writes:
                return True
            if allowed_later_clear is not None:
                return [e['id'] for e in writes] == [allowed_later_clear['id']]
            return post_call_clear(event, entry) is not None

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

        def alias_snapshot_patterns(entry):
            # One-hop value snapshots, not a general alias/call graph. In
            # particular, clearing the source does not rewrite an earlier copy.
            events = grouped[entry]
            reachable = {e['id'] for e, _ in prefix(entry)}
            region = []
            for event in events[:2000]:
                if (event['block'] != functions[entry].get('body_block') or
                        event.get('conditions') or event.get('branch_path')):
                    continue
                if event['kind'] in {'return', 'raise', 'await', 'yield'}:
                    break
                region.append(event)
            guards = [e for e in region if e['kind'] == 'guard']
            if len(guards) != 1:
                return
            guard = guards[0]
            name = guard.get('null_return_identifier') or guard.get('null_throw_identifier')
            if not name or not guard.get('linear_block') or guard['id'] not in reachable:
                return
            throwing = bool(guard.get('null_throw_identifier'))
            if throwing and (owner(entry, 'Error') is not None or
                    any(i['local'] == 'Error' for i in file['imports']) or
                    any(e['kind'] == 'write' and e.get('target', '').split('.')[0] == 'Error' for e in file['events'])):
                return
            binding = owner(entry, name)
            if (binding is None or binding == entry or
                    name not in functions.get(binding, {}).get('parameters', [])):
                return
            writes = visible_writes(name, binding)
            if len(writes) != 1:
                return
            write = writes[0]
            if (write not in region or write.get('target') != name or write.get('operator') != '=' or
                    write.get('rhs_kind') != 'NullLiteral' or owner(write['scope'], name) != binding):
                return
            for snapshot in region:
                alias = snapshot.get('target', '')
                if (snapshot['kind'] != 'write' or not IDENTIFIER.fullmatch(alias) or alias == name or
                        snapshot.get('declared_names') != [alias] or snapshot.get('operator') != '=' or
                        snapshot.get('rhs_kind') != 'Identifier' or snapshot.get('rhs_text') != name or
                        owner(entry, alias) != entry or
                        not region.index(guard) < region.index(snapshot) < region.index(write)):
                    continue
                # Reassignment, method writes, destructuring and ambiguous
                # sibling bindings invalidate the saved callable candidate.
                if [e['id'] for e in visible_writes(alias, entry)] != [snapshot['id']]:
                    continue
                for callback in region[region.index(snapshot) + 1:]:
                    parts = callback.get('callee', '').split('.')
                    if (callback['kind'] != 'call' or callback.get('optional') or callback.get('construct') or
                            parts[0] != alias or not (len(parts) == 1 or len(parts) == 2 and parts[1] in {'call', 'apply'})):
                        continue
                    prior = region.index(write) < region.index(callback)
                    status = 'write_before_call' if prior else 'write_after_call'
                    qualification = (QUALIFICATION + ' One simple local declaration snapshots an outer '
                        'parameter after a strict null ' + ('early-throw' if throwing else 'early-return') +
                        ' guard and before its only visible null clear. '
                        'The alias has no other visible writes; runtime callable types and method replacement remain unresolved.')
                    findings.append(dict(rule=RULE, path=file['path'], scope=entry,
                        evidence=[guard['id'], snapshot['id'], callback['id'], write['id']],
                        classification='review_hint_not_bug_verdict',
                        message=('调用本地回调快照之前，已清空入口读取的原始绑定；快照仍保留清空前的候选函数值。' if prior else
                                 '先调用本地回调快照，随后才清空入口读取的原始绑定；同步重入可能再次取得同一函数。'),
                        condition=qualification,
                        review_question=('回调经局部副本调用时，原绑定是否已使重入入口拒绝再次调用？请核对同步重入和首次抛错后的行为；清空原变量不等于清空先前副本。' if throwing else
                            '回调经局部副本调用时，原绑定是否已使重入入口返回？请核对同步重入和异常语义；清空原变量不等于清空先前副本。'),
                        state_publication=dict(state=name, binding_scope=binding, status=status,
                            guard=guard['id'], callback=callback['id'], write=write['id'],
                            execution_path=[snapshot['id']], uncertainties=[], write_value=write.get('rhs_text'),
                            path_conditions=['fallthrough of ' + guard['expression']],
                            callback_binding_basis='local_snapshot_of_outer_parameter',
                            **(dict(guard_exit='throw') if throwing else {}),
                            callback_alias=dict(name=alias, source=name, copy=snapshot['id'], binding_scope=entry))))
                    before, after = (write, callback) if prior else (callback, write)
                    relations.extend([
                        dict(kind='state_write_before_external_call' if prior else 'external_call_before_state_write',
                             before=before['id'], after=after['id'], qualification=qualification),
                        dict(kind='local_alias_snapshot_before_call', before=snapshot['id'], after=callback['id'],
                             qualification='A simple local value copy before its candidate invocation; later source clearing does not rewrite the copy.')])

        def nested_flag_patterns(entry):
            # A linear block on a bounded, explicitly selected if/else path.
            # Do not concatenate sibling branches or infer property identities.
            events = grouped[entry]
            guards = {e['guard_key']: e for e in events if e['kind'] == 'guard' and e.get('guard_key')}
            reachable = {e['id'] for e, _ in prefix(entry)}
            for guard in events:
                name = guard.get('early_return_identifier')
                path = guard.get('branch_path', [])
                if (not name or not path or len(path) > 4 or not guard.get('linear_block') or
                        guard['id'] not in reachable):
                    continue
                binding = owner(entry, name)
                if binding is None or binding == entry:
                    continue
                parents = [guards.get(part['key']) for part in path]
                if any(p is None or not p.get('condition_path_supported') for p in parents):
                    continue
                # Reject constant-only predicates above, and contradictory bare
                # identifier predicates here; this is not a general SAT solver.
                truth = {name: False}  # fallthrough of `if (flag) return`
                consistent = True
                for part, parent in zip(path, parents):
                    identifier = parent.get('condition_identifier')
                    if identifier:
                        value = parent['condition_truthy'] == (part['arm'] == 'then')
                        if identifier in truth and truth[identifier] != value:
                            consistent = False
                            break
                        truth[identifier] = value
                if not consistent:
                    continue
                expected_block = functions[entry].get('body_block')
                valid_path = True
                for part, parent in zip(path, parents):
                    if parent['block'] != expected_block:
                        valid_path = False
                        break
                    expected_block = parent.get('then_path_block' if part['arm'] == 'then' else 'else_path_block')
                if not valid_path or guard['block'] != expected_block:
                    continue
                # Loops, catch/finally and other conditional regions are not if paths.
                conditions = [('if ' if part['arm'] == 'then' else 'else of ') + parent['expression']
                              for part, parent in zip(path, parents)]
                if guard.get('conditions') != conditions:
                    continue
                region = []
                for event in events[:2000]:
                    if (event['block'] != guard['block'] or event.get('branch_path') != path or
                            event.get('conditions') != conditions):
                        continue
                    if event['kind'] in {'return', 'raise', 'await', 'yield'}:
                        break
                    region.append(event)
                if guard not in region or any(e['kind'] == 'guard' and e is not guard for e in region):
                    continue
                writes = visible_writes(name, binding)
                changes = [e for e in writes if e not in region]
                # Only an uninitialized/false closure declaration may precede
                # the selected block's one true publication. Other writes stay unknown.
                if any(not (e['scope'] == binding and name in e.get('declared_names', []) and
                            (e.get('rhs_kind') is None or
                             e.get('rhs_kind') == 'BooleanLiteral' and e.get('rhs_text') == 'false'))
                       for e in changes):
                    continue
                publications = [e for e in writes if e in region]
                if len(publications) != 1:
                    continue
                write = publications[0]
                if (write.get('target') != name or write.get('operator') != '=' or
                        write.get('rhs_kind') != 'BooleanLiteral' or write.get('rhs_text') != 'true' or
                        owner(write['scope'], name) != binding or region.index(write) <= region.index(guard)):
                    continue
                for callback in region[region.index(guard) + 1:]:
                    if (callback['kind'] != 'call' or callback.get('callee', '').split('.')[0] == name or
                            not parameter_call(callback, entry)):
                        continue
                    prior = region.index(write) < region.index(callback)
                    status = 'write_before_call' if prior else 'write_after_call'
                    qualification = (QUALIFICATION + ' Selected nested if/else path and fallthrough of a '
                        'bare-identifier early-return guard; one true flag publication in this linear block. '
                        'Receiver property state, indirect mutations and other paths remain unresolved.')
                    anchors = [p['id'] for p in parents]
                    findings.append(dict(rule=RULE, path=file['path'], scope=entry,
                        evidence=[*anchors, guard['id'], callback['id'], write['id']],
                        classification='review_hint_not_bug_verdict',
                        message=('选定嵌套分支中，入口防重复标志在外部调用前写入。' if prior else
                                 '选定嵌套分支中，外部调用发生后才写入入口防重复标志；同步重入可能再次通过检查。'),
                        condition=qualification,
                        review_question='在相同接收者和分支条件下，用户函数同步重入是否会重复执行？请核对异常路径与标志含义；调用前写入不等于所有路径安全。',
                        state_publication=dict(state=name, binding_scope=binding, status=status,
                            guard=guard['id'], callback=callback['id'], write=write['id'],
                            execution_path=anchors, uncertainties=[], write_value=write.get('rhs_text'),
                            path_conditions=[*conditions, 'fallthrough of ' + guard['expression']],
                            callback_binding_basis='unchanged_parameter_on_nested_flag_path')))
                    before, after = (write, callback) if prior else (callback, write)
                    relations.append(dict(kind='state_write_before_external_call' if prior else
                                          'external_call_before_state_write', before=before['id'],
                                          after=after['id'], qualification=qualification))

        reflect_findings, reflect_relations = reflective_patterns(
            file, functions, grouped, owner, visible_writes, prefix, RULE, QUALIFICATION)
        findings.extend(reflect_findings)
        relations.extend(reflect_relations)

        budget_findings, budget_relations = countdown_patterns(
            file, functions, grouped, owner, visible_writes, prefix, parameter_call, RULE, QUALIFICATION)
        findings.extend(budget_findings)
        relations.extend(budget_relations)

        protocol_findings, protocol_relations = protocol_patterns(
            file, functions, grouped, owner, visible_writes, prefix, parameter_call)
        findings.extend(protocol_findings)
        relations.extend(protocol_relations)

        for entry, definition in functions.items():
            if definition.get('parent') is None or definition.get('generator'):
                continue
            alias_snapshot_patterns(entry)
            nested_flag_patterns(entry)
            local_guards = [e for e in grouped[entry] if e['kind'] == 'guard' and not e.get('conditions')]
            if not local_guards:
                continue
            sequence = list(prefix(entry))
            indices = {e['id']: i for i, (e, _) in enumerate(sequence)}
            emitted = set()
            # A one-shot callable can also be its own entry-state variable.
            # Keep this separate from the unconditional-prefix analysis: only
            # the selected positive branch, with one later null/undefined clear,
            # permits a parameter write without losing its candidate identity.
            for guard in local_guards:
                name = guard.get('test_identifier')
                if (not name or guard['id'] not in indices or
                        guard['block'] != definition.get('body_block') or
                        not guard.get('consequent_linear')):
                    continue
                binding = owner(entry, name)
                if (binding is None or binding == entry or
                        name not in functions.get(binding, {}).get('parameters', [])):
                    continue
                conditions = ['if ' + guard['expression']]
                branch = []
                for event, _ in sequence:
                    if (event['scope'] != entry or event['block'] != guard['consequent_block'] or
                            event.get('conditions') != conditions):
                        continue
                    if event['kind'] in {'return', 'raise'}:
                        break
                    branch.append(event)
                writes = visible_writes(name, binding)
                if len(writes) != 1:
                    continue
                write = writes[0]
                if (write not in branch or write.get('target') != name or
                        write.get('operator') != '=' or owner(write['scope'], name) != binding):
                    continue
                is_null = write.get('rhs_kind') == 'NullLiteral'
                is_undefined = (write.get('rhs_kind') == 'Identifier' and
                                write.get('rhs_text') == 'undefined' and
                                not any(i['local'] == 'undefined' for i in file['imports']) and
                                not any('undefined' in names for names in declarations.values()) and
                                not any('undefined' in f.get('parameters', []) for f in functions.values()))
                if not (is_null or is_undefined):
                    continue
                for callback in branch[:branch.index(write)]:
                    if (callback['kind'] != 'call' or
                            callback.get('callee', '').split('.')[0] != name or
                            not parameter_call(callback, entry, allowed_later_clear=write)):
                        continue
                    emitted.add((name, callback['id']))
                    qualification = (QUALIFICATION + ' Selected positive identifier guard branch only; '
                        'the only visible write to this parameter is a later null/undefined clear. '
                        'Other branches, indirect mutation and overridden .call/.apply remain unresolved.')
                    findings.append(dict(rule=RULE, path=file['path'], scope=entry,
                        evidence=[guard['id'], callback['id'], write['id']],
                        classification='review_hint_not_bug_verdict',
                        message='入口条件仍持有用户函数时调用该函数，随后才清空同一闭包绑定；同步重入可能再次进入该分支。',
                        condition=qualification,
                        review_question='用户函数若立即重入包装入口，是否会再次执行？请检查同步重入、throw 选项与首次抛错后的重试语义；不能直接提前清空而忽略重试行为。',
                        state_publication=dict(state=name, binding_scope=binding,
                            status='write_after_call', guard=guard['id'], callback=callback['id'],
                            write=write['id'], execution_path=[], uncertainties=[],
                            write_value=write.get('rhs_text'), path_conditions=conditions,
                            callback_binding_basis='outer_parameter_with_only_later_clear')))
                    relations.append(dict(kind='external_call_before_state_write',
                        before=callback['id'], after=write['id'], qualification=qualification))
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
                        cleanup = post_call_clear(callback, entry)
                        if cleanup:
                            finding = findings[-1]
                            finding['evidence'] = list(dict.fromkeys([*finding['evidence'], cleanup['id']]))
                            finding['state_publication'].update(
                                callback_binding_basis='parameter_before_simple_post_call_clear',
                                callback_cleanup=dict(write=cleanup['id'], value=cleanup.get('rhs_text')))
                            finding['condition'] += ' The only visible callback binding write is a later simple clear in this entry prefix; clearing itself is not a defect verdict.'
                            relations.append(dict(kind='external_call_before_callback_clear',
                                before=callback['id'], after=cleanup['id'],
                                qualification='The direct parameter invocation is evaluated before its same-frame null/undefined clear; this does not judge the clear as erroneous.'))
                        if write:
                            before, after = (write, callback) if prior else (callback, write)
                            relations.append(dict(kind='state_write_before_external_call' if prior else
                                                  'external_call_before_state_write',
                                                  before=before['id'], after=after['id'],
                                                  qualification=QUALIFICATION))
    return findings, relations
