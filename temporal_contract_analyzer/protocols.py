"""Source-bound listener order and argument-cache publication candidates.

These describe bounded syntax paths, not runtime API or exception contracts.
No imported API is trusted solely because it is named on/off or memoize.
"""


def protocol_patterns(file, functions, grouped, owner, visible_writes, prefix, parameter_call):
    findings, relations = [], []
    headers = {e['scope']: e for e in file['events'] if e['kind'] == 'function_definition'}

    for entry, definition in functions.items():
        parent = definition.get('parent')
        if parent not in functions or definition.get('generator') or definition.get('async'):
            continue
        events = grouped[entry]
        sequence = [e for e, _ in prefix(entry) if e['scope'] == entry]
        index = {e['id']: i for i, e in enumerate(sequence)}

        # A closure with a single local wrapper, registered by the enclosing
        # method, and removal by an unchanged capture of that method's receiver.
        parent_header = headers.get(parent, {})
        target = parent_header.get('object_target')
        bindings = [b for b in file['bindings'] if b['scope'] == parent and b['target'] == entry]
        target_writes = [e for e in file['events'] if e['kind'] == 'write' and e.get('target') == target] if target else []
        if target and len(target_writes) == 1 and len(bindings) == 1:
            listener = bindings[0]['name']
            registrations = [e for e in grouped[parent] if e['kind'] == 'call' and
                             len(e.get('arguments', [])) == 3 and e['arguments'][1] == listener and
                             e.get('receiver') == 'this' and not e.get('conditions') and
                             not e.get('optional') and not e.get('construct')]
            calls = [e for e in sequence if e['kind'] == 'call' and not e.get('conditions')]
            if len(registrations) == 1 and len(calls) == 2 and all(e.get('linear_block') for e in calls):
                registration = registrations[0]
                method = registration['callee'].split('.')[-1]
                certificates = [h for h in headers.values() if h.get('object_target') == target and
                                h.get('listener_method', {}).get('role') == 'register' and h.get('name') == method]
                for register_header in certificates:
                    protocol = register_header['listener_method']
                    remove_headers = [h for h in headers.values() if h.get('object_target') == target and
                                      h.get('name') == protocol['remove_method'] and
                                      h.get('listener_method') == dict(protocol, role='remove')]
                    if len(remove_headers) != 1:
                        continue
                    # Reject visible replacement of the certified method table.
                    if any(e['kind'] == 'write' and (e.get('target') == target.split('.')[0] or
                           e.get('target', '').startswith(target + '.') or
                           e.get('target') == target and e.get('rhs_kind') != 'ObjectExpression') for e in file['events']):
                        continue
                    event_name = registration['arguments'][0]
                    if (event_name not in functions[parent]['parameters'] or owner(entry, event_name) != parent or
                            visible_writes(event_name, parent) or owner(entry, listener) != parent):
                        continue
                    for detach in calls:
                        if (detach.get('arguments') != [event_name, listener] or detach.get('optional') or
                                detach.get('construct') or detach.get('callee', '').split('.')[-1] != protocol['remove_method']):
                            continue
                        receiver = detach.get('receiver')
                        captures = visible_writes(receiver, parent)
                        if (owner(entry, receiver) != parent or len(captures) != 1 or
                                captures[0]['scope'] != parent or captures[0].get('declared_names') != [receiver] or
                                captures[0].get('rhs_kind') != 'ThisExpression' or captures[0].get('conditions') or
                                captures[0]['block'] != functions[parent]['body_block']):
                            continue
                        parent_prefix = [e['id'] for e, _ in prefix(parent)]
                        if (captures[0]['id'] not in parent_prefix or registration['id'] not in parent_prefix or
                                parent_prefix.index(captures[0]['id']) >= parent_prefix.index(registration['id'])):
                            continue
                        callback = next(e for e in calls if e != detach)
                        if not parameter_call(callback, entry) or owner(entry, callback['callee'].split('.')[0]) != parent:
                            continue
                        # All operations must be direct and on the wrapper's straight body.
                        if (len([e for e in events if e['kind'] == 'call']) != 2 or
                                any(e['kind'] in {'guard', 'write', 'await', 'yield', 'raise'} for e in events) or
                                any(e['block'] != definition['body_block'] for e in calls)):
                            continue
                        listener_writes = visible_writes(listener, parent)
                        if any(e['scope'] != parent or e.get('target') != listener + '.' + protocol['alias_property'] or
                               e.get('rhs_kind') != 'Identifier' or e.get('rhs_text') != callback['callee'].split('.')[0]
                               for e in listener_writes):
                            continue
                        prior = index[detach['id']] < index[callback['id']]
                        evidence = [registration['id'], captures[0]['id'], headers[entry]['id'],
                                    register_header['id'], remove_headers[0]['id'], callback['id'], detach['id']]
                        condition = ('One same-source array-backed registration/removal protocol, one captured receiver, '
                                     'matching event and local listener identity, and a straight synchronous wrapper. '
                                     'No runtime receiver-type, overridden method, array-intrinsic or callback-reentry proof.')
                        findings.append(dict(rule='reentrant-listener-detach', path=file['path'], scope=entry,
                            evidence=evidence, classification='review_hint_not_bug_verdict', condition=condition,
                            message=('This listener is removed before invoking the user callback.' if prior else
                                     'The registered listener is removed after the user callback; synchronous redispatch may invoke it again.'),
                            review_question='Does this wrapper require a single delivery? Trace registration and removal: is the listener still active if the callback immediately redispatches the event or throws?',
                            listener_detach=dict(state=listener, status='detach_before_call' if prior else 'detach_after_call',
                                registration=registration['id'], receiver_capture=captures[0]['id'], wrapper=headers[entry]['id'],
                                register_definition=register_header['id'], remove_definition=remove_headers[0]['id'],
                                callback=callback['id'], detach=detach['id'], uncertainties=[])))
                        first, second = (detach, callback) if prior else (callback, detach)
                        relations.append(dict(kind='listener_detach_before_callback' if prior else 'callback_before_listener_detach',
                                              before=first['id'], after=second['id'], qualification=condition))

        # An explicitly recognized argument-cache predicate and one flat commit
        # branch. A throw skips the result assignment, but not earlier key writes.
        if not definition.get('argument_cache_body_supported'):
            continue
        guards = [e for e in events if e['kind'] == 'guard']
        if len(guards) != 1 or not guards[0].get('argument_cache_guard'):
            continue
        guard = guards[0]
        spec = guard['argument_cache_guard']
        keys = [spec['key'], spec['receiver']]
        if len(set(keys)) != 2 or any(owner(entry, key) != parent for key in keys):
            continue
        if owner(entry, spec['arguments']) != entry:
            continue
        path = [dict(key=guard['guard_key'], arm='then')]
        branch = [e for e in sequence if e['block'] == guard['then_path_block'] and e.get('branch_path') == path]
        writes = [e for e in branch if e['kind'] == 'write']
        calls = [e for e in branch if e['kind'] == 'call']
        if (len(writes) != 3 or len(calls) != 1 or guard.get('conditions') or
                len([e for e in events if e['kind'] == 'return']) != 1):
            continue
        callback = calls[0]
        if (not parameter_call(callback, entry) or owner(entry, callback['callee'].split('.')[0]) != parent or
                not callback['callee'].endswith('.apply') or callback.get('arguments') != ['this', spec['arguments']]):
            continue
        result_writes = [e for e in writes if e.get('rhs_callee') == callback['callee'] and
                         e['statement'] == callback['statement'] and index[e['id']] > index[callback['id']]]
        if len(result_writes) != 1:
            continue
        result_write = result_writes[0]
        result_name = result_write.get('target')
        returns = [e for e in sequence if e['kind'] == 'return' and e.get('return_identifier') == result_name and
                   not e.get('conditions') and e['block'] == definition['body_block']]
        if (result_name in keys or owner(entry, result_name) != parent or len(returns) != 1 or
                index[returns[0]['id']] <= index[result_write['id']]):
            continue
        key_writes = [next((e for e in writes if e.get('target') == key), None) for key in keys]
        if (any(e is None for e in key_writes) or
                any(index[e['id']] >= index[callback['id']] for e in key_writes) or
                key_writes[0].get('rhs_kind') != 'Identifier' or key_writes[0].get('rhs_text') != spec['arguments'] or
                key_writes[1].get('rhs_kind') != 'ThisExpression'):
            continue
        initializers = []
        for name, update in zip([*keys, result_name], [*key_writes, result_write]):
            changes = visible_writes(name, parent)
            initial = [e for e in changes if e['scope'] == parent and e.get('declared_names') == [name] and
                       e.get('rhs_kind') == 'NullLiteral' and not e.get('conditions') and
                       e['block'] == functions[parent]['body_block']]
            if len(changes) != 2 or len(initial) != 1 or update not in changes:
                break
            initializers.append(initial[0])
        if len(initializers) != 3:
            continue
        parent_sequence = [e for e, _ in prefix(parent)]
        parent_index = {e['id']: i for i, e in enumerate(parent_sequence)}
        returned = [e for e in parent_sequence if e['kind'] == 'returned_callback' and e.get('target_scope') == entry]
        if len(returned) != 1 or any(e['id'] not in parent_index or
                parent_index[e['id']] >= parent_index[returned[0]['id']] for e in initializers):
            continue
        # A comparator with visible reassignment would not support a stable hit predicate.
        comparator_owner = owner(entry, spec['comparator'])
        if comparator_owner != parent:
            continue
        changes = visible_writes(spec['comparator'], parent)
        if len(changes) != 1 or changes[0].get('declared_names') != [spec['comparator']]:
            continue
        evidence = [guard['id'], *(e['id'] for e in initializers), *(e['id'] for e in key_writes),
                    callback['id'], result_write['id'], returns[0]['id']]
        condition = ('Recognized last-arguments/receiver cache-miss predicate with three null-initialized closure bindings '
                     'and one flat update branch. A thrown RHS skips result assignment after key writes. '
                     'Assumes a stable, reflexive argument comparator for a same-argument retry; exception/reentry contracts '
                     'and indirect mutation are not proven. No automatic rollback or repair is prescribed.')
        findings.append(dict(rule='argument-cache-publication', path=file['path'], scope=entry, evidence=evidence,
            classification='review_hint_not_bug_verdict', condition=condition,
            message='Cached arguments and receiver are updated before evaluating the user function and storing its result. A throw may let a same-argument retry use an old result; synchronous reentry may also read an unfinished result.',
            review_question='After evaluation throws, should the wrapper retry, throw again or return an old value? Check a successful call with other arguments, a failed call, a same-argument retry and synchronous reentry. Setting a key early does not establish cache validity.',
            cache_publication=dict(state=result_name, status='key_before_result', guard=guard['id'],
                initializers=[e['id'] for e in initializers], key_writes=[e['id'] for e in key_writes],
                callback=callback['id'], result_write=result_write['id'], result_return=returns[0]['id'], uncertainties=[])))
        relations.extend([dict(kind='cache_key_before_compute', before=e['id'], after=callback['id'], qualification=condition)
                          for e in key_writes])
        relations.append(dict(kind='compute_before_cache_result', before=callback['id'], after=result_write['id'],
                              qualification='The assignment is reached only after its RHS returns successfully.'))
    return findings, relations
