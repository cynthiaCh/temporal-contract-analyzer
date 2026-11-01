"""Behavioral distinctions for bounded state publication; no upstream oracle inputs."""
import tempfile
from pathlib import Path
import unittest

from temporal_contract_analyzer.core import analyze_sources, compare
from temporal_contract_analyzer.layers import freeze_bundle, render_layers, verify_bundle
from temporal_contract_analyzer.boundary_cards import cards


RULE = 'reentrant-state-publication'
LATE = '''function wrap(deliver) {
  let active;
  return async function entry() {
    if (active) return active;
    active = (async () => { return await deliver.apply(this, []); })();
    return active;
  };
}'''
EARLY = '''function wrap(deliver) {
  let active;
  return async function entry() {
    if (active) return active;
    const {promise, resolve} = Promise.withResolvers();
    active = promise;
    resolve((async () => { return await deliver.apply(this, []); })());
    return active;
  };
}'''


class StatePublicationTests(unittest.TestCase):
    def report(self, source, path='module.js'):
        report = analyze_sources({path: source})
        self.assertEqual(report['status'], 'parsed')
        return report

    def hints(self, report):
        return [f for f in report['findings'] if f['rule'] == RULE]

    def statuses(self, source):
        return [f['state_publication']['status'] for f in self.hints(self.report(source))]

    def test_async_iife_await_operand_runs_before_assignment(self):
        self.assertEqual(self.statuses(LATE), ['write_after_call'])

    def test_published_state_has_distinct_status_and_comparison(self):
        before, after = self.report(LATE), self.report(EARLY)
        self.assertEqual([f['state_publication']['status'] for f in self.hints(after)], ['write_before_call'])
        delta = compare(before, after)
        self.assertTrue(delta['comparable'])
        self.assertTrue(any(f['rule'] == RULE for f in delta['added_hints']))
        self.assertTrue(any(f['rule'] == RULE for f in delta['removed_hints']))

    def test_direct_call_apply_and_call_are_name_independent(self):
        for invocation in ['deliver()', 'deliver.call(this)', 'deliver.apply(this, [])']:
            for state, callback in [('active', 'deliver'), ('ticket', 'runUserCode')]:
                source = LATE.replace('deliver.apply(this, [])', invocation)
                source = source.replace('active', state).replace('deliver', callback)
                with self.subTest(invocation=invocation, state=state):
                    self.assertEqual(self.statuses(source), ['write_after_call'])

    def test_named_local_helper_is_expanded(self):
        source = '''function wrap(deliver) {
  let active;
  function invoke() { return deliver(); }
  return function entry() { if (active) return active; active = invoke(); };
}'''
        self.assertEqual(self.statuses(source), ['write_after_call'])

    def test_async_direct_await_operand_precedes_state_write(self):
        source = '''function wrap(deliver) {
  let active;
  return async function entry() {
    if (active) return active;
    active = await deliver();
  };
}'''
        # The write occurs only after suspension, outside the initial prefix.
        self.assertEqual(self.statuses(source), ['not_established'])

    def test_timer_promise_generator_and_later_async_code_are_not_inlined(self):
        replacements = [
            'setTimeout(() => deliver(), 0)',
            'Promise.resolve().then(() => deliver())',
            '(async () => { await pause(); return deliver(); })()',
            '(function* () { deliver(); yield 1; })()',
        ]
        for expression in replacements:
            source = LATE.replace('(async () => { return await deliver.apply(this, []); })()', expression)
            with self.subTest(expression=expression):
                self.assertEqual(self.statuses(source), [])

    def test_non_invoked_function_body_is_not_inlined(self):
        source = LATE.replace('(async () => { return await deliver.apply(this, []); })()',
                              'async () => { return await deliver(); }')
        self.assertEqual(self.statuses(source), [])

    def test_shadowed_or_reassigned_callback_is_not_bound_to_outer_parameter(self):
        replacements = [
            '(async () => { const deliver = other; return deliver(); })()',
            '(async deliver => { return deliver(); })(other)',
            '(async () => { const {deliver} = other; return deliver(); })()',
        ]
        # An IIFE parameter is a new unknown callable; do not connect it to the
        # factory's callback. Argument-to-parameter propagation is not modeled.
        for expression in replacements:
            with self.subTest(expression=expression):
                self.assertEqual(self.statuses(LATE.replace(
                    '(async () => { return await deliver.apply(this, []); })()', expression)), [])
        self.assertEqual(self.statuses(LATE.replace('    active =', '    deliver = other;\n    active =')), [])

    def test_parameter_or_local_state_is_not_closure_shared(self):
        for source in [
            'function entry(active, deliver) { if (active) return; active = deliver(); }',
            'function entry(deliver) { let active; if (active) return; active = deliver(); }',
        ]:
            self.assertEqual(self.statuses(source), [])

    def test_sibling_and_destructured_callback_reassignments_are_unknown(self):
        bodies = [
            'function replace() { deliver = () => 1; }',
            'function replace() { ({deliver} = other); }',
            'function replace() { deliver["apply"] = other; }',
        ]
        for body in bodies:
            source = '''function wrap(deliver) { let active; BODY
return function entry() { if (active) return; replace(); active = deliver.apply(this, []); }; }'''.replace('BODY', body)
            with self.subTest(body=body):
                self.assertEqual(self.statuses(source), [])
        source = LATE.replace('    active =', '    ({deliver} = other);\n    active =')
        self.assertEqual(self.statuses(source), [])

    def test_sibling_helper_reassignment_does_not_expand_old_body(self):
        source = '''function wrap(deliver) {
  let active;
  function invoke() { return deliver(); }
  function replace() { invoke = () => 1; }
  return function entry() { if (active) return; replace(); active = invoke(); };
}'''
        self.assertEqual(self.statuses(source), [])

    def test_block_and_named_function_self_bindings_are_not_outer_callbacks(self):
        examples = [
            '''function wrap(deliver) { let active; { function deliver() { return 1; }
return function entry() { if (active) return; active = deliver(); }; } }''',
            '''function wrap(deliver) { let active;
const factory = function deliver() { return function entry() { if (active) return; active = deliver(); }; };
return factory(); }''',
            '''function wrap(deliver) { let active; function helper() {}
return function entry() { if (active) return; { const helper = () => deliver(); }
active = helper(); }; }''',
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.statuses(source), [])

    def test_named_function_expression_variable_binding_still_resolves(self):
        source = '''function wrap(deliver) { let active;
const helper = function internalName() { return deliver(); };
return function entry() { if (active) return; active = helper(); }; }'''
        self.assertEqual(self.statuses(source), ['write_after_call'])

    def test_destructured_state_write_does_not_invent_its_value(self):
        source = EARLY.replace('active = promise;', '({active} = source);')
        hint = self.hints(self.report(source))[0]
        self.assertEqual(hint['state_publication']['status'], 'not_established')
        self.assertIn('destructured_state_write', hint['state_publication']['uncertainties'])

    def test_ambiguous_sibling_write_and_member_pattern_override_invalidate(self):
        examples = [
            '''function wrap(deliver) { let active;
function replace() { deliver = () => 1; { let deliver; } }
return function entry() { if (active) return; replace(); active = deliver(); }; }''',
            '''function wrap(deliver) { let active; return function entry() { if (active) return;
({method:deliver.apply} = {method:() => 1}); active = deliver.apply(this, []); }; }''',
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.statuses(source), [])

    def test_class_static_callback_writes_and_catch_class_shadows_are_unknown(self):
        examples = [
            '''function wrap(deliver) { let active; return function entry() { if (active) return;
class X { static { deliver = () => 1; } } active = deliver(); }; }''',
            '''function wrap(deliver) { let active; return function entry() { if (active) return;
class X { static value = (deliver = () => 1); } active = deliver(); }; }''',
            '''function wrap(deliver) { let active; try { throw () => 1; } catch (deliver) {
return function entry() { if (active) return; active = deliver(); }; } }''',
            '''function wrap(deliver) { let active; { class deliver {}
return function entry() { if (active) return; active = deliver(); }; } }''',
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.statuses(source), [])

    def test_ambiguous_and_class_state_writes_do_not_invent_a_relation(self):
        examples = [
            '''function wrap(deliver) { let active;
function publish() { { let active; } active = true; }
return function entry() { if (active) return; publish(); const value = deliver(); active = value; }; }''',
            '''function wrap(deliver) { let active; return function entry() { if (active) return;
class X { static { active = true; } } const value = deliver(); active = value; }; }''',
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.statuses(source), ['not_established'])

    def test_inner_state_shadow_is_not_the_outer_write(self):
        source = LATE.replace('return await deliver.apply(this, []);',
                              'let active; active = 1; return deliver();')
        self.assertEqual(self.statuses(source), ['write_after_call'])

    def test_different_functions_do_not_supply_a_publication(self):
        source = '''function wrap(deliver) {
  let active;
  function other() { active = 1; }
  return function entry() { if (active) return; deliver(); };
}'''
        self.assertEqual(self.statuses(source), ['not_established'])

    def test_writing_undefined_is_not_reported_as_proven_protection(self):
        report = self.report(EARLY.replace('active = promise;', 'active = undefined;'))
        hint = self.hints(report)[0]
        self.assertEqual(hint['state_publication']['write_value'], 'undefined')
        self.assertEqual(hint['classification'], 'review_hint_not_bug_verdict')
        self.assertNotIn('verdict', hint)

    def test_conditional_publication_stays_unknown(self):
        source = EARLY.replace('active = promise;', 'if (flag) active = promise;')
        hint = self.hints(self.report(source))[0]
        self.assertEqual(hint['state_publication']['status'], 'not_established')
        self.assertIn('conditional_state_write', hint['state_publication']['uncertainties'])

    def test_formatting_is_neutral_and_value_changes_are_visible(self):
        formatted = EARLY.replace('active = promise;', 'active  =  promise ;')
        delta = compare(self.report(EARLY), self.report(formatted))
        self.assertFalse(any(f['rule'] == RULE for f in delta['added_hints']+delta['removed_hints']))
        delta = compare(self.report(EARLY), self.report(EARLY.replace('active = promise;', 'active = undefined;')))
        self.assertTrue(any(f['rule'] == RULE for f in delta['added_hints']))

    def test_spaces_inside_a_state_string_are_not_normalized_away(self):
        a = EARLY.replace('active = promise;', 'active = "a  b";')
        b = EARLY.replace('active = promise;', 'active = "a b";')
        delta = compare(self.report(a), self.report(b))
        self.assertTrue(any(f['rule'] == RULE for f in delta['added_hints']))

    def test_report_has_sources_relations_effect_and_frozen_delivery(self):
        report = self.report(LATE)
        hint = self.hints(report)[0]
        events = {e['id']: e for f in report['files'] for e in f['events']}
        self.assertTrue(all(i in events for i in hint['evidence']))
        self.assertTrue(any(r['kind'] == 'external_call_before_state_write' for r in report['relations']))
        card = next(c for c in cards(report) if c['rule'] == RULE)
        self.assertIn(hint['state_publication']['write'], card['effects']['evidence_ids'])
        self.assertIn(hint['state_publication']['callback'], card['boundary']['evidence_ids'])
        self.assertEqual(card['requirement_protection']['evidence_ids'], [hint['state_publication']['guard']])
        rendered = render_layers(report)
        self.assertIn('external_call_before_state_write', rendered['facts'])
        self.assertIn('write_after_call', rendered['review'])
        self.assertNotIn('state_publication', rendered['facts'])
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/'bundle'
            manifest = freeze_bundle(report, target)
            self.assertEqual(verify_bundle(target), manifest)

    def test_python_coroutine_is_not_given_javascript_prefix_semantics(self):
        source = 'def wrap(deliver):\n    active = None\n    async def entry():\n        if active:\n            return active\n        return deliver()\n    return entry\n'
        self.assertEqual(self.hints(self.report(source, 'module.py')), [])


if __name__ == '__main__':
    unittest.main()
