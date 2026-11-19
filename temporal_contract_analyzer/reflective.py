"""Bounded receiver captures and Reflect invocation candidates; no execution."""
import re

IDENTIFIER = re.compile(r'^[A-Za-z_$][\w$]*$')


def reflective_patterns(file, functions, grouped, owner, visible_writes, prefix, rule, qualification):
    findings, relations = [], []
    events = file['events']
    # Built-in provenance is only a static candidate. Fail closed for visible
    # shadows and mutations, including common explicit property mutators.
    if (any('Reflect' in f.get('parameters', []) or f.get('self_name') == 'Reflect' for f in functions.values()) or
            any(i['local'] == 'Reflect' for i in file['imports']) or
            any(b['name'] == 'Reflect' for b in file['bindings']) or
            any('Reflect' in e.get('declared_names', []) or 'Reflect' in e.get('write_roots', []) or
                e.get('target') in {'globalThis.Reflect', 'window.Reflect', 'global.Reflect', 'self.Reflect'}
                for e in events)):
        return findings, relations
    mutators = {'Object.assign', 'Object.defineProperty', 'Object.defineProperties',
                'Reflect.set', 'Reflect.defineProperty', 'Reflect.deleteProperty'}
    if any(re.fullmatch(r"(?:globalThis|window|global|self)(?:\.Reflect|\[['\"]Reflect['\"]\])",
                        re.sub(r'\s+', '', e.get('target', ''))) for e in events if e['kind'] == 'write'):
        return findings, relations
    if any(e['kind'] == 'call' and e.get('callee') in mutators and
           e.get('arguments', [None])[0:1] in [['Reflect'], ['globalThis'], ['global'], ['window'], ['self']] for e in events):
        return findings, relations

    def intrinsic(call):
        callee = call.get('callee', '')
        if callee in {'Reflect.apply', 'Reflect.construct'}:
            return callee.split('.')[1], None
        if not IDENTIFIER.fullmatch(callee):
            return None, None
        binding = owner(call['scope'], callee)
        if binding is None:
            return None, None
        writes = visible_writes(callee, binding)
        if len(writes) != 1:
            return None, None
        declaration = writes[0]
        if (declaration.get('object_binding_source') != 'Reflect' or declaration.get('conditions') or
                declaration.get('block') != functions.get(binding, {}).get('body_block')):
            return None, None
        properties = [p['property'] for p in declaration.get('object_bindings', []) if p['local'] == callee]
        if len(properties) != 1 or properties[0] not in {'apply', 'construct'}:
            return None, None
        if declaration['id'] not in {e['id'] for e, _ in prefix(binding)}:
            return None, None
        if binding == call['scope'] and grouped[binding].index(declaration) >= grouped[binding].index(call):
            return None, None
        return properties[0], declaration

    for entry, definition in functions.items():
        if definition.get('parent') is None or definition.get('generator'):
            continue
        local = grouped[entry]
        reachable = {e['id'] for e, _ in prefix(entry)}
        guards = [e for e in local if e['kind'] == 'guard' and e['block'] == definition.get('body_block')]
        if len(guards) != 1:
            continue
        guard = guards[0]
        flag = guard.get('test_identifier')
        binding = owner(entry, flag) if flag else None
        if (not flag or binding is None or binding == entry or guard.get('conditions') or
                guard['id'] not in reachable or not guard.get('reflective_branch_linear')):
            continue
        conditions = ['if ' + guard['expression']]
        path = [*guard.get('branch_path', []), dict(key=guard['guard_key'], arm='then')]
        branch = []
        for event in local[:2000]:
            if event.get('branch_path') != path:
                continue
            if event['block'] == guard['consequent_block'] and event['kind'] in {'return', 'raise', 'await', 'yield'}:
                break
            branch.append(event)
        writes = visible_writes(flag, binding)
        initial = [e for e in writes if e['scope'] == binding and flag in e.get('declared_names', []) and
                   e['block'] == functions.get(binding, {}).get('body_block') and not e.get('conditions') and
                   e.get('rhs_kind') == 'BooleanLiteral' and e.get('rhs_text') == 'true']
        publication = [e for e in writes if e in branch and e.get('target') == flag and e.get('operator') == '=' and
                       e['block'] == guard['consequent_block'] and e.get('conditions') == conditions and
                       e.get('rhs_kind') == 'BooleanLiteral' and e.get('rhs_text') == 'false' and
                       not e.get('conditional_path')]
        if len(writes) != 2 or len(initial) != 1 or len(publication) != 1:
            continue
        write = publication[0]
        factory_prefix = {e['id'] for e, _ in prefix(binding)}
        if initial[0]['id'] not in factory_prefix:
            continue
        for call in branch:
            if call['kind'] != 'call' or call.get('optional') or call.get('construct'):
                continue
            operation, api = intrinsic(call)
            args = call.get('arguments', [])
            if operation is None or len(args) != (3 if operation == 'apply' else 2) or not IDENTIFIER.fullmatch(args[0]):
                continue
            target = args[0]
            if owner(entry, target) != binding:
                continue
            captures = visible_writes(target, binding)
            if len(captures) != 1:
                continue
            capture = captures[0]
            if (target not in capture.get('declared_names', []) or capture.get('rhs_kind') != 'ThisExpression' or
                    capture['scope'] != binding or capture['block'] != functions[binding].get('body_block') or
                    capture.get('conditions') or capture['id'] not in factory_prefix):
                continue
            dispatch = call.get('conditional_path', [])
            if dispatch:
                if (len(dispatch) != 1 or dispatch[0]['parent_block'] != guard['consequent_block'] or
                        dispatch[0]['operator'] != 'instanceof' or dispatch[0]['left'] != 'this' or
                        dispatch[0]['right'] != definition.get('self_name') or
                        dispatch[0]['right'] in definition.get('parameters', []) or
                        any(dispatch[0]['right'] in e.get('declared_names', []) for e in local) or
                        call.get('conditions') != conditions + ['conditional expression ' + dispatch[0]['expression']]):
                    continue
                # Both arms have separate records; do not infer that both run.
                selected_conditions = conditions + [dispatch[0]['arm'] + ' of ' + dispatch[0]['expression']]
            elif call['block'] == guard['consequent_block'] and call.get('conditions') == conditions:
                selected_conditions = conditions
            else:
                continue
            before = branch.index(write) < branch.index(call)
            status = 'write_before_call' if before else 'write_after_call'
            anchors = [capture['id'], initial[0]['id'], *([api['id']] if api else [])]
            condition = (qualification + ' Positive shared-boolean branch, a stable receiver value capture, '
                         'and candidate Reflect.apply/construct provenance. Conditional arms are alternatives; '
                         'receiver callable type, native built-in identity and indirect mutation are not proven.')
            findings.append(dict(rule=rule, path=file['path'], scope=entry,
                evidence=list(dict.fromkeys([guard['id'], *anchors, call['id'], write['id']])),
                classification='review_hint_not_bug_verdict',
                message=('The repetition guard is written before reflectively invoking the captured receiver function.' if before else
                         'Reflective invocation of the captured receiver function precedes the repetition-guard write; synchronous reentry may invoke it again.'),
                condition=condition,
                review_question='Can ordinary or constructor calls repeat execution on synchronous reentry? Check branches, exceptions and cached results separately. An earlier write does not establish safety on every path.',
                state_publication=dict(state=flag, binding_scope=binding, status=status,
                    guard=guard['id'], callback=call['id'], write=write['id'], execution_path=anchors,
                    uncertainties=[], write_value='false', path_conditions=selected_conditions,
                    callback_binding_basis='stable_receiver_capture_via_reflect',
                    reflective_call=dict(operation=operation, target=target, capture=capture['id'],
                                         api_binding=api['id'] if api else None, conditional_path=dispatch))))
            first, second = (write, call) if before else (call, write)
            relations.extend([
                dict(kind='state_write_before_external_call' if before else 'external_call_before_state_write',
                     before=first['id'], after=second['id'], qualification=condition),
                dict(kind='receiver_capture_before_reflective_call', before=capture['id'], after=call['id'],
                     qualification='A stable this value capture reaches a candidate native Reflect invocation; actual callable type is unresolved.')])
    return findings, relations
