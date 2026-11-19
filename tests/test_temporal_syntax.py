import unittest

from temporal_contract_analyzer.core import js_analyze
from temporal_contract_analyzer.python_adapter import analyze as python_analyze


class TemporalSyntaxTests(unittest.TestCase):
    def javascript(self, source, path='syntax.js'):
        files, parser = js_analyze({path: source})
        self.assertEqual(parser['status'], 'available', parser)
        self.assertEqual(files[0]['status'], 'parsed', files[0])
        return files[0]

    def python(self, source):
        file = python_analyze('syntax.py', source)
        self.assertEqual(file['status'], 'parsed', file)
        return file

    def event(self, file, kind, **fields):
        return next(e for e in file['events'] if e['kind'] == kind
                    and all(e.get(k) == v for k, v in fields.items()))

    def assert_exact_events(self, source, file):
        encoding = 'utf-16-le' if file['column_unit'] == 'utf16_code_units' else 'utf-8'
        width = 2 if encoding == 'utf-16-le' else 1
        lines = source.splitlines(keepends=True)
        for event in file['events']:
            start, end = event['line'] - 1, event['end_line'] - 1
            if start == end:
                actual = lines[start].encode(encoding)[event['column'] * width:event['end_column'] * width].decode(encoding)
            else:
                actual = (lines[start].encode(encoding)[event['column'] * width:].decode(encoding)
                          + ''.join(lines[start + 1:end])
                          + lines[end].encode(encoding)[:event['end_column'] * width].decode(encoding))
            self.assertEqual(event['text'], actual, event)

    def test_javascript_references_ignore_comments_strings_keys_and_callback_bodies(self):
        source = '''function run(state, other) {
  const snapshot = {misleading: state.current, other, text: "hidden.reference"};
  // ghost.reference; state.secret
  if (state.current && "hidden.guard") state.current = other.value;
  sink.send({keyOnly: snapshot, [selector]: other.value}, "hidden.arg", () => hidden.callback());
  return {keyOnly: snapshot, text: "hidden.return"};
}'''
        file = self.javascript(source)
        snapshot = self.event(file, 'write', target='snapshot')
        self.assertEqual(snapshot['references'], ['snapshot', 'state.current', 'other'])
        self.assertEqual(snapshot['value_references'], ['state.current', 'other'])
        self.assertEqual(snapshot['rhs_kind'], 'ObjectExpression')
        self.assertEqual(self.event(file, 'guard')['references'], ['state.current'])
        changed = self.event(file, 'write', target='state.current')
        self.assertEqual(changed['references'], ['state.current', 'other.value'])
        self.assertEqual(changed['value_references'], ['other.value'])
        sent = self.event(file, 'call', callee='sink.send')
        self.assertEqual(sent['references'], ['sink.send', 'snapshot', 'selector', 'other.value'])
        self.assertEqual(sent['argument_references'], [['snapshot', 'selector', 'other.value'], [], []])
        self.assertEqual(self.event(file, 'return')['references'], ['snapshot'])
        self.assert_exact_events(source, file)

    def test_destructured_typescript_parameters_are_bound_identifiers(self):
        source = '''function run(
  {publish: emit, nested: {value}, fallback = seed, ...rest}: Options,
  [first, , ...tail]: Item[], count = 0, ...extras: Extra[]
) { emit(value as HiddenType, {propertyKey: first}); }'''
        file = self.javascript(source, 'syntax.ts')
        function = next(f for f in file['functions'] if f['name'] == 'run')
        self.assertEqual(function['parameters'], ['emit', 'value', 'fallback', 'rest', 'first', 'tail', 'count', 'extras'])
        self.assertEqual(self.event(file, 'call', callee='emit')['argument_references'], [['value'], ['first']])

    def test_generator_callback_metadata_and_dynamic_member_callee_are_preserved(self):
        file = self.javascript('subscribe(function* (event) { port.close(event); yield 1; }); request().then(done);')
        callback = self.event(file, 'callback_argument', callee='subscribe')
        function = next(f for f in file['functions'] if f['id'] == callback['target_scope'])
        self.assertTrue(function['generator'])
        self.assertFalse(function['async'])
        continuation = self.event(file, 'call', callee='.then')
        self.assertEqual(continuation['references'], ['request', 'done'])
        self.assertEqual(continuation['argument_references'], [['done']])

    def test_loop_bindings_are_lexical_and_reset_for_nested_callbacks(self):
        source = '''function run(groups) {
  for (const listeners of groups) {
    for (const listener of listeners.values) {
      listener(state.current);
      later(() => listener(state.later));
    }
  }
}'''
        file = self.javascript(source)
        direct = next(e for e in file['events'] if e['kind'] == 'call' and e['callee'] == 'listener' and '<callback>' not in e['scope'])
        self.assertEqual(direct['loop_bindings'], [
            dict(target='listeners', iterable='groups', iterable_references=['groups']),
            dict(target='listener', iterable='listeners.values', iterable_references=['listeners.values']),
        ])
        deferred = next(e for e in file['events'] if e['kind'] == 'call' and e['callee'] == 'listener' and '<callback>' in e['scope'])
        self.assertNotIn('loop_bindings', deferred)
        callback = self.event(file, 'callback_argument', callee='later')
        self.assertEqual(callback['scope'], '<module>/run')
        self.assertEqual(callback['target_scope'], deferred['scope'])
        self.assertEqual(callback['argument_index'], 0)
        self.assertEqual(callback['loop_bindings'], direct['loop_bindings'])
        self.assertEqual(callback['text'], '() => ')
        self.assert_exact_events(source, file)

    def test_object_targets_are_scoped_to_direct_object_members(self):
        source = '''function factory() {
  const navigation = {open() { function nested() { act(); } }, close: () => stop()};
  const other = {open() { again(); }, close: function () { end(); }};
  return navigation;
}'''
        file = self.javascript(source)
        definitions = [e for e in file['events'] if e['kind'] == 'function_definition']
        self.assertEqual([(e['name'], e.get('object_target')) for e in definitions], [
            ('factory', None), ('open', 'navigation'), ('nested', None),
            ('close', 'navigation'), ('open', 'other'), ('close', 'other'),
        ])
        self.assertNotEqual(self.event(file, 'function_definition', name='open', object_target='navigation')['scope'],
                            self.event(file, 'function_definition', name='open', object_target='other')['scope'])

    def test_python_references_and_lambda_callback_metadata(self):
        source = '''def run(state, other, *rest, **options):
    # ghost.reference
    snapshot = {"hidden.key": state.current, "text": "hidden.value"}
    if state.current and "hidden.guard":
        state.current = other.value
    sink.send(snapshot, "hidden.arg", callback=lambda event: hidden.callback(event))
    return {"hidden.key": snapshot}
'''
        file = self.python(source)
        self.assertEqual(file['functions'][1]['parameters'], ['state', 'other', 'rest', 'options'])
        snapshot = self.event(file, 'write', target='snapshot')
        self.assertEqual(snapshot['references'], ['snapshot', 'state.current'])
        self.assertEqual(snapshot['value_references'], ['state.current'])
        self.assertEqual(snapshot['rhs_kind'], 'Dict')
        self.assertEqual(self.event(file, 'guard')['references'], ['state.current'])
        self.assertEqual(self.event(file, 'write', target='state.current')['value_references'], ['other.value'])
        sent = self.event(file, 'call', callee='sink.send')
        self.assertEqual(sent['references'], ['sink.send', 'snapshot'])
        self.assertEqual(sent['argument_references'], [['snapshot'], [], []])
        callback = self.event(file, 'callback_argument', callee='sink.send')
        self.assertEqual(callback['argument_index'], 2)
        self.assertEqual(callback['scope'], '<module>/run')
        self.assertEqual(callback['target_scope'], self.event(file, 'call', callee='hidden.callback')['scope'])
        self.assertEqual(callback['text'], 'lambda event: ')
        self.assertEqual(self.event(file, 'return')['references'], ['snapshot'])
        self.assert_exact_events(source, file)

    def test_python_for_loop_metadata_does_not_enter_deferred_lambda(self):
        source = '''def run(groups):
    for listeners in groups:
        for listener in listeners.values:
            listener(state.current)
            later(lambda: listener(state.later))
    return groups
'''
        file = self.python(source)
        calls = [e for e in file['events'] if e['kind'] == 'call' and e['callee'] == 'listener']
        self.assertEqual(calls[0]['loop_bindings'], [
            dict(target='listeners', iterable='groups', iterable_references=['groups']),
            dict(target='listener', iterable='listeners.values', iterable_references=['listeners.values']),
        ])
        self.assertNotIn('loop_bindings', calls[1])
        self.assertNotIn('loop_bindings', self.event(file, 'return'))
        self.assertEqual(self.event(file, 'callback_argument')['loop_bindings'], calls[0]['loop_bindings'])

    def test_javascript_unicode_coordinates_and_nested_callback_scopes(self):
        source = '''const marker = "😀"; bus.subscribe("\u4e8b\u4ef6", event => {
  later(() => navigation.close(event));
});'''
        file = self.javascript(source)
        registration = self.event(file, 'callback_argument', callee='bus.subscribe')
        deferred = self.event(file, 'callback_argument', callee='later')
        self.assertEqual(registration['scope'], '<module>')
        self.assertEqual(registration['argument_index'], 1)
        self.assertEqual(deferred['scope'], registration['target_scope'])
        self.assertEqual(self.event(file, 'call', callee='navigation.close')['scope'], deferred['target_scope'])
        self.assert_exact_events(source, file)

    def test_python_unicode_and_multiline_lambda_headers_are_source_exact(self):
        source = '''marker = "😀"; bus.subscribe("\u4e8b\u4ef6", lambda event:
    later(lambda: navigation.close(event)))
'''
        file = self.python(source)
        registration = self.event(file, 'callback_argument', callee='bus.subscribe')
        deferred = self.event(file, 'callback_argument', callee='later')
        self.assertEqual(registration['text'], 'lambda event:\n    ')
        self.assertEqual(registration['scope'], '<module>')
        self.assertEqual(registration['argument_index'], 1)
        self.assertEqual(deferred['scope'], registration['target_scope'])
        self.assert_exact_events(source, file)


if __name__ == '__main__':
    unittest.main()
