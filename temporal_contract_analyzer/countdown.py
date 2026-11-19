"""Limited numeric countdown paths; budget meaning and runtime types need review."""
import re

IDENTIFIER = re.compile(r'^[A-Za-z_$][\w$]*$')


def countdown_patterns(file, functions, grouped, owner, visible_writes, prefix, parameter_call, rule, qualification):
    findings, relations = [], []
    for entry, definition in functions.items():
        if (definition.get('parent') is None or definition.get('generator') or
                not definition.get('countdown_body_supported')):
            continue
        events = grouped[entry]
        direct_guards = [e for e in events if e['kind'] == 'guard' and e['block'] == definition['body_block']]
        guards = [e for e in direct_guards if e.get('countdown_guard')]
        if len(guards) != 1:
            continue
        guard = guards[0]
        budget = guard['countdown_guard']
        counter = budget['counter']
        binding = owner(entry, counter)
        if (binding is None or binding == entry or
                counter not in functions.get(binding, {}).get('parameters', []) or guard.get('conditions')):
            continue
        sequence = [e for e, _ in prefix(entry) if e['scope'] == entry]
        index = {e['id']: i for i, e in enumerate(sequence)}
        if guard['id'] not in index:
            continue
        changes = visible_writes(counter, binding)
        if len(changes) != 1:
            continue
        decrement = changes[0]
        if (decrement['scope'] != entry or decrement.get('target') != counter or decrement.get('operator') != '--' or
                decrement['id'] not in index or owner(decrement['scope'], counter) != binding):
            continue
        path = [dict(key=guard['guard_key'], arm='then')]
        conditions = ['if ' + guard['expression']]
        branch = [e for e in sequence if e['block'] == guard['then_path_block'] and
                  e.get('branch_path') == path and e.get('conditions') == conditions and not e.get('conditional_path')]
        if budget['form'] == 'guard_prefix':
            if (not decrement.get('update_prefix') or decrement.get('update_standalone') or
                    decrement['block'] != guard['block'] or decrement.get('conditions') or
                    decrement['statement'] != guard['statement'] or index[decrement['id']] <= index[guard['id']]):
                continue
            cleanup_threshold = budget['threshold'] + 1
        else:
            if not decrement.get('update_standalone') or index[decrement['id']] <= index[guard['id']]:
                continue
            in_branch = decrement in branch
            after_branch = (decrement['block'] == guard['block'] and not decrement.get('conditions') and
                            decrement['statement'] > guard['statement'])
            if not (in_branch or after_branch):
                continue
            cleanup_threshold = budget['threshold']
        calls = [e for e in branch if e['kind'] == 'call']
        if len(calls) != 1:
            continue
        call = calls[0]
        parts = call.get('callee', '').split('.')
        target = parts[0]
        if (not IDENTIFIER.fullmatch(target) or target == counter or
                owner(entry, target) != binding or target not in functions[binding].get('parameters', []) or
                budget['form'] == 'guard_prefix' and index[decrement['id']] >= index[call['id']]):
            continue
        target_writes = visible_writes(target, binding)
        cleanup = cleanup_guard = None
        if target_writes:
            if len(target_writes) != 1:
                continue
            cleanup = target_writes[0]
            candidates = [e for e in direct_guards if e.get('countdown_cleanup') ==
                          dict(counter=counter, threshold=cleanup_threshold, target=target)]
            if len(candidates) != 1:
                continue
            cleanup_guard = candidates[0]
            if (cleanup['scope'] != entry or cleanup.get('target') != target or cleanup.get('rhs_kind') != 'NullLiteral' or
                    cleanup.get('operator') != '=' or cleanup['id'] not in index or cleanup_guard['id'] not in index or
                    cleanup_guard['statement'] <= guard['statement'] or
                    cleanup['block'] != cleanup_guard['then_path_block'] or
                    cleanup.get('branch_path') != [dict(key=cleanup_guard['guard_key'], arm='then')] or
                    cleanup.get('conditions') != ['if ' + cleanup_guard['expression']] or
                    index[cleanup['id']] <= index[cleanup_guard['id']]):
                continue
            if index[cleanup_guard['id']] <= max(index[call['id']], index[decrement['id']]):
                continue
        expected_guards = [guard] + ([cleanup_guard] if cleanup_guard else [])
        if len(direct_guards) != len(expected_guards) or any(e not in expected_guards for e in direct_guards):
            continue
        if not parameter_call(call, entry, allowed_later_clear=cleanup):
            continue
        prior = index[decrement['id']] < index[call['id']]
        status = 'write_before_call' if prior else 'write_after_call'
        condition = (qualification + ' A single -- update, safe-integer literal comparison, and one callback on the positive budget branch. '
                     'Assumes a finite safe-integer budget and the documented numeric quota meaning; coercion, exceptions, invocation-method overrides and indirect mutation are not proven.')
        evidence = [guard['id'], call['id'], decrement['id']]
        publication = dict(state=counter, binding_scope=binding, status=status,
            guard=guard['id'], callback=call['id'], write=decrement['id'], execution_path=[], uncertainties=[],
            write_value=None, write_operator='--', path_conditions=conditions,
            callback_binding_basis='countdown_parameter_on_guarded_path',
            numeric_budget=dict(form=budget['form'], threshold=budget['threshold'],
                                cleanup_threshold=cleanup_threshold, assumptions='finite_safe_integer_budget'))
        if cleanup:
            evidence += [cleanup_guard['id'], cleanup['id']]
            publication['execution_path'] = [cleanup_guard['id']]
            publication['callback_cleanup'] = dict(write=cleanup['id'], value='null',
                guard=cleanup_guard['id'], condition=cleanup_guard['expression'])
            relations.append(dict(kind='external_call_before_conditional_callback_clear',
                before=call['id'], after=cleanup['id'], qualification='Only if the later numeric cleanup guard is true; the callback clear is not judged erroneous.'))
        findings.append(dict(rule=rule, path=file['path'], scope=entry, evidence=evidence,
            classification='review_hint_not_bug_verdict', condition=condition,
            message=('In the selected count branch, the invocation budget is decremented before calling the user function.' if prior else
                     'The user function is called before decrementing the invocation budget; synchronous reentry may reuse the unconsumed budget.'),
            review_question='For a finite safe-integer invocation budget, can synchronous reentry exceed the allowed count? Check numeric input bounds, budget after exceptions and caching. This does not establish a later cleanup defect.',
            state_publication=publication))
        first, second = (decrement, call) if prior else (call, decrement)
        relations.extend([
            dict(kind='state_write_before_external_call' if prior else 'external_call_before_state_write',
                 before=first['id'], after=second['id'], qualification=condition),
            dict(kind='numeric_budget_guard_before_call', before=guard['id'], after=call['id'],
                 qualification='Selected positive branch of a numeric countdown predicate; budget type and application meaning remain assumptions.')])
    return findings, relations
