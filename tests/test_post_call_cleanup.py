"""A later simple clear must not erase evidence about an earlier callee value."""
import copy
import tempfile
from pathlib import Path
import unittest

from temporal_contract_analyzer.core import analyze_sources, compare
from temporal_contract_analyzer.layers import freeze_bundle, verify_bundle
from temporal_contract_analyzer.report import markdown
from temporal_contract_analyzer.review import focused_review

SOURCE = '''function once(callback) {
  let called, value;
  return function entry(...args) {
    if (called) return value;
    called = true;
    value = callback.apply(this, args);
    callback = undefined;
    return value;
  };
}'''
LATE = SOURCE.replace('called = true;\n    value = callback.apply(this, args);',
                      'value = callback.apply(this, args);\n    called = true;')


class PostCallCleanupTests(unittest.TestCase):
    def report(self, source=SOURCE, path='a.js'):
        report = analyze_sources({path: source})
        self.assertEqual(report['status'], 'parsed')
        return report

    def hints(self, source=SOURCE):
        return [f for f in self.report(source)['findings'] if f['rule'] == 'reentrant-state-publication']

    def test_cleanup_preserved_and_state_order_distinguishes_default_card(self):
        before, after = self.report(), self.report(LATE)
        self.assertEqual(self.hints()[0]['state_publication']['status'], 'write_before_call')
        self.assertEqual(self.hints(LATE)[0]['state_publication']['status'], 'write_after_call')
        self.assertEqual(len(focused_review(before)['cards']), 0)
        self.assertEqual(len(focused_review(after)['cards']), 1)
        delta = compare(before, after)
        self.assertTrue(delta['comparable'])
        self.assertEqual(len(delta['added_hints']), 1)
        self.assertEqual(len(delta['removed_hints']), 1)

    def test_default_report_labels_clear_as_fact_not_wrong_statement(self):
        report = self.report(LATE)
        publication = self.hints(LATE)[0]['state_publication']
        self.assertEqual(publication['callback_binding_basis'], 'parameter_before_simple_post_call_clear')
        self.assertEqual(publication['callback_cleanup']['value'], 'undefined')
        card = focused_review(report)['cards'][0]
        cleanup = next(e for e in card['evidence'] if e['id'] == publication['callback_cleanup']['write'])
        self.assertEqual(cleanup['role'], 'Binding cleared after call (ordering fact)')
        self.assertIn('does not classify the cleanup statement itself as defective', markdown(report))
        self.assertNotEqual(publication['write'], publication['callback_cleanup']['write'])

    def test_names_call_forms_and_null_clear_are_generic(self):
        for invocation in ['callback()', 'callback.call(this)', 'callback.apply(this, args)']:
            for value in ['undefined', 'null']:
                source = SOURCE.replace('callback.apply(this, args)', invocation).replace('callback = undefined', 'callback = '+value)
                source = source.replace('callback', 'deliver')
                with self.subTest(invocation=invocation, value=value):
                    self.assertEqual(len(self.hints(source)), 1)

    def test_before_call_reassignment_or_non_clear_replacement_stays_unknown(self):
        examples = [
            SOURCE.replace('called = true;', 'callback = undefined; called = true;').replace('    callback = undefined;\n', ''),
            SOURCE.replace('callback = undefined;', 'callback = other;'),
            SOURCE.replace('callback = undefined;', 'callback = "undefined";'),
            SOURCE.replace('callback = undefined;', 'callback = void 0;'),
            SOURCE.replace('called = true;', 'callback = other; called = true;'),
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_method_override_destructuring_and_multiple_writes_remain_unknown(self):
        for change in ['callback.apply = other;', '({callback} = other);', 'callback = null; callback = undefined;']:
            with self.subTest(change=change):
                self.assertEqual(self.hints(SOURCE.replace('callback = undefined;', change)), [])

    def test_sibling_class_and_expanded_helper_clears_are_not_same_frame(self):
        examples = [
            SOURCE.replace('return function entry', 'function reset() { callback = undefined; } return function entry').replace('    callback = undefined;\n', '    reset();\n'),
            SOURCE.replace('callback = undefined;', 'class X { static { callback = undefined; } }'),
            SOURCE.replace('return function entry', 'function invoke() { return callback(); } return function entry').replace('callback.apply(this, args)', 'invoke()'),
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_conditional_suspend_and_unreachable_clears_fail_closed(self):
        examples = [
            SOURCE.replace('callback = undefined;', 'if (flag) callback = undefined;'),
            SOURCE.replace('function entry', 'async function entry').replace('callback = undefined;', 'await pause(); callback = undefined;'),
            SOURCE.replace('callback = undefined;', 'return value; callback = undefined;'),
            SOURCE.replace('callback = undefined;', 'throw error; callback = undefined;'),
            SOURCE.replace('callback.apply(this, args)', 'setTimeout(() => callback(), 0)'),
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_undefined_shadowing_is_not_treated_as_builtin(self):
        examples = [
            SOURCE.replace('function once(callback)', 'function once(callback, undefined)'),
            'const undefined = other;\n'+SOURCE,
            'import undefined from "other";\n'+SOURCE,
            SOURCE.replace('return function entry', 'function undefined() {} return function entry'),
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_clear_relation_and_source_must_be_complete_for_low_noise(self):
        for mutation in ['relation', 'source']:
            report = copy.deepcopy(self.report(LATE))
            publication = report['findings'][0]['state_publication']
            if mutation == 'relation':
                report['relations'] = [r for r in report['relations'] if r['kind'] != 'external_call_before_callback_clear']
            else:
                publication['callback_cleanup']['write'] = 'missing'
            with self.subTest(mutation=mutation):
                self.assertEqual(focused_review(report)['cards'], [])
                self.assertEqual(focused_review(report)['summary']['suppressed_by_reason'], {'incomplete_evidence': 1})

    def test_calls_after_clear_do_not_reuse_the_old_parameter_candidate(self):
        source = SOURCE.replace('callback = undefined;', 'callback = undefined; callback();')
        hints = self.hints(source)
        self.assertEqual(len(hints), 1)
        events = {e['id']:e for e in self.report(source)['files'][0]['events']}
        self.assertEqual(events[hints[0]['state_publication']['callback']]['callee'], 'callback.apply')

    def test_clear_that_is_itself_entry_state_still_has_order_risk(self):
        source = 'function once(callback) { return function entry() { if (callback === null) return; callback(); callback = null; }; }'
        report = self.report(source)
        publication = report['findings'][0]['state_publication']
        self.assertEqual(publication['state'], 'callback')
        self.assertEqual(publication['write'], publication['callback_cleanup']['write'])
        self.assertEqual(len(focused_review(report)['cards']), 1)
        state_write = next(e for e in focused_review(report)['cards'][0]['evidence'] if e['id'] == publication['write'])
        self.assertNotIn('role', state_write)

    def test_typescript_vue_and_frozen_cleanup_relation(self):
        for path, source in [('a.ts', LATE), ('A.vue', '<script setup>\n'+LATE+'\n</script>')]:
            report = self.report(source, path)
            self.assertEqual(len(focused_review(report)['cards']), 1)
            with tempfile.TemporaryDirectory() as directory:
                target = Path(directory)/'bundle'
                manifest = freeze_bundle(report, target)
                self.assertEqual(verify_bundle(target), manifest)
                self.assertIn('external_call_before_callback_clear', (target/'facts.md').read_text())
                self.assertIn('callback_cleanup', (target/'review.md').read_text())


if __name__ == '__main__':
    unittest.main()
