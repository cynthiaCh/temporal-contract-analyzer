"""Bounded positive guard paths, with adversarial binding and control-flow cases."""
import tempfile
from pathlib import Path
import unittest

from temporal_contract_analyzer.core import analyze_sources, compare
from temporal_contract_analyzer.layers import freeze_bundle, verify_bundle
from temporal_contract_analyzer.review import focused_review

RULE = 'reentrant-state-publication'
SOURCE = '''function once(run) {
  return function entry() {
    if (run) {
      const value = run();
      run = undefined;
      return value;
    }
  };
}'''


class GuardedPublicationTests(unittest.TestCase):
    def report(self, source=SOURCE, path='module.js'):
        report = analyze_sources({path: source})
        self.assertEqual(report['status'], 'parsed')
        return report

    def hints(self, source=SOURCE, path='module.js'):
        return [f for f in self.report(source, path)['findings'] if f['rule'] == RULE]

    def test_guarded_callback_clear_has_complete_low_noise_evidence(self):
        report = self.report()
        review = focused_review(report)
        self.assertEqual(len(review['cards']), 1)
        finding = next(f for f in report['findings'] if f['rule'] == RULE)
        publication = finding['state_publication']
        self.assertEqual(publication['status'], 'write_after_call')
        self.assertEqual(publication['path_conditions'], ['if run'])
        self.assertEqual(publication['callback_binding_basis'], 'outer_parameter_with_only_later_clear')
        events = {e['id']: e for e in report['files'][0]['events']}
        self.assertEqual(events[publication['guard']]['line'], 3)
        self.assertEqual(events[publication['callback']]['line'], 4)
        self.assertEqual(events[publication['write']]['line'], 5)
        self.assertIn('retry', finding['review_question'])

    def test_identifiers_formatting_and_null_are_generic(self):
        for name in ['callback', 'deliver', '$fn']:
            for value in ['undefined', 'null']:
                source = SOURCE.replace('run', name).replace('undefined', value)
                with self.subTest(name=name, value=value):
                    self.assertEqual(len(self.hints(source)), 1)
        delta = compare(self.report(), self.report(SOURCE.replace('if (run)', 'if ( run )').replace('run = undefined;', 'run  =  undefined ;')))
        self.assertEqual(delta['added_hints'], [])
        self.assertEqual(delta['removed_hints'], [])

    def test_direct_call_and_apply_supported_without_executing_candidate(self):
        for invocation in ['run()', 'run.call(this)', 'run.apply(this, [])']:
            with self.subTest(invocation=invocation):
                self.assertEqual(len(self.hints(SOURCE.replace('run()', invocation))), 1)

    def test_clear_before_call_or_different_branch_not_a_late_clear(self):
        examples = [
            SOURCE.replace('const value = run();\n      run = undefined;', 'run = undefined;\n      const value = run();'),
            'function once(run) { return function entry() { if (run) run(); else run = undefined; }; }',
            'function once(run) { return function entry() { if (run) { run(); } run = undefined; }; }',
            'function once(run) { return function entry() { if (run) { run(); } if (run) { run = undefined; } }; }',
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_prior_sibling_destructured_and_method_writes_stay_unknown(self):
        examples = [
            SOURCE.replace('return function entry()', 'run = replacement; return function entry()'),
            SOURCE.replace('const value = run();', 'run = replacement; const value = run();'),
            SOURCE.replace('const value = run();', '({run} = other); const value = run();'),
            SOURCE.replace('const value = run();', 'run.apply = other; const value = run();'),
            SOURCE.replace('return function entry()', 'function replace() { run = other; } return function entry()'),
            SOURCE.replace('return function entry()', 'class X { static { run = other; } } return function entry()'),
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_shadowed_callback_state_and_undefined_are_excluded(self):
        examples = [
            SOURCE.replace('function entry()', 'function entry(run)'),
            SOURCE.replace('if (run)', 'let run; if (run)'),
            SOURCE.replace('function once(run)', 'function once(run, undefined)'),
            SOURCE.replace('return function entry()', 'const undefined = replacement; return function entry()'),
            SOURCE.replace('function entry()', 'function run()'),
            'import undefined from "other"; ' + SOURCE,
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_await_yield_or_deferred_callback_not_treated_as_linear_call(self):
        examples = [
            SOURCE.replace('function entry()', 'async function entry()').replace('const value = run();', 'await pause(); const value = run();'),
            SOURCE.replace('function entry()', 'async function entry()').replace('const value = run();', 'const value = await run();'),
            SOURCE.replace('function entry()', 'function* entry()').replace('const value = run();', 'yield 1; const value = run();'),
            SOURCE.replace('const value = run();', 'const value = setTimeout(() => run(), 0);'),
            SOURCE.replace('const value = run();', 'const value = Promise.resolve().then(() => run());'),
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_nested_controls_loops_try_and_unreachable_clears_are_excluded(self):
        replacements = [
            'if (flag) return; const value = run();',
            'if (flag) run(); const value = 1;',
            'while (flag) run(); const value = 1;',
            'try { run(); } finally {} const value = 1;',
            '{ run(); } const value = 1;',
            'return run(); const value = 1;',
            'throw run(); const value = 1;',
        ]
        for expression in replacements:
            with self.subTest(expression=expression):
                self.assertEqual(self.hints(SOURCE.replace('const value = run();', expression)), [])

    def test_other_guard_forms_and_non_clear_assignments_are_not_guessed(self):
        for guard in ['!run', 'run && flag', 'typeof run === "function"', 'object.run']:
            with self.subTest(guard=guard):
                self.assertEqual(self.hints(SOURCE.replace('if (run)', 'if (' + guard + ')')), [])
        for value in ['other', 'false', '0', 'flag ? undefined : other', 'void 0']:
            with self.subTest(value=value):
                self.assertEqual(self.hints(SOURCE.replace('run = undefined;', 'run = ' + value + ';')), [])

    def test_optional_construction_and_indirect_calls_remain_unmodeled(self):
        for invocation in ['run?.()', 'new run()', 'run.bind(this)()', 'setTimeout(run, 0)']:
            with self.subTest(invocation=invocation):
                self.assertEqual(self.hints(SOURCE.replace('run()', invocation)), [])

    def test_two_invocations_keep_both_evidence_locations_in_one_card(self):
        report = self.report(SOURCE.replace('const value = run();', 'run(); const value = run();'))
        hints = [f for f in report['findings'] if f['rule'] == RULE]
        self.assertEqual(len(hints), 2)
        review = focused_review(report)
        self.assertEqual(len(review['cards']), 1)
        self.assertEqual(len(review['cards'][0]['finding_ids']), 2)
        self.assertEqual(len([e for e in review['cards'][0]['evidence'] if e['kind'] == 'call']), 2)

    def test_typescript_and_vue_inline_scripts_keep_guard_scope_and_lines(self):
        typescript = SOURCE.replace('once(run)', 'once(run: (...args: unknown[]) => unknown)')
        self.assertEqual(len(self.hints(typescript, 'module.ts')), 1)
        self.assertEqual(len(self.hints('<script setup>\n' + SOURCE + '\n</script>', 'Once.vue')), 1)

    def test_new_guard_metadata_freezes_and_verifies(self):
        report = self.report()
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory)/'bundle'
            manifest = freeze_bundle(report, bundle)
            self.assertEqual(verify_bundle(bundle), manifest)
            facts = (bundle/'facts.md').read_text()
            review = (bundle/'review.md').read_text()
            self.assertIn('external_call_before_state_write', facts)
            self.assertIn('outer_parameter_with_only_later_clear', review)


if __name__ == '__main__':
    unittest.main()
