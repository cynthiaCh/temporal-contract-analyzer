"""Numeric reservation order and its conditional callback cleanup path."""
import copy
import tempfile
from pathlib import Path
import unittest

from temporal_contract_analyzer.core import analyze_sources, compare
from temporal_contract_analyzer.layers import freeze_bundle, verify_bundle
from temporal_contract_analyzer.report import markdown
from temporal_contract_analyzer.review import focused_review

SOURCE = '''function before(remaining, invoke) {
  let memo;
  return function entry(...args) {
    if (--remaining > 0) {
      memo = invoke.apply(this, args);
    }
    if (remaining <= 1) invoke = null;
    return memo;
  };
}'''
LATE = SOURCE.replace('if (--remaining > 0)', 'if (remaining > 1)').replace(
    '    if (remaining <= 1)', '    --remaining;\n    if (remaining <= 1)')


class CountdownPublicationTests(unittest.TestCase):
    def report(self, source=SOURCE, path='a.js'):
        report = analyze_sources({path:source})
        self.assertEqual(report['status'], 'parsed')
        return report

    def hints(self, source=SOURCE):
        return [f for f in self.report(source)['findings'] if
                f.get('state_publication', {}).get('callback_binding_basis') == 'countdown_parameter_on_guarded_path']

    def test_guard_decrement_before_call_and_late_reservation_are_distinct(self):
        original, late = self.report(), self.report(LATE)
        self.assertEqual(self.hints()[0]['state_publication']['status'], 'write_before_call')
        publication = self.hints(LATE)[0]['state_publication']
        self.assertEqual(publication['status'], 'write_after_call')
        self.assertEqual(publication['write_operator'], '--')
        self.assertEqual(publication['numeric_budget']['assumptions'], 'finite_safe_integer_budget')
        self.assertEqual(len(focused_review(original)['cards']), 0)
        self.assertEqual(len(focused_review(late)['cards']), 1)
        change = compare(original, late)
        self.assertTrue(change['comparable'])
        self.assertEqual(len(change['added_hints']), 1)
        self.assertEqual(len(change['removed_hints']), 1)

    def test_names_thresholds_and_call_forms_are_not_project_specific(self):
        for threshold in [0, 2, 5]:
            for call in ['invoke()', 'invoke.call(this)', 'invoke.apply(this, args)']:
                source = SOURCE.replace('--remaining > 0', '--remaining > '+str(threshold)).replace(
                    'remaining <= 1', 'remaining <= '+str(threshold+1)).replace('invoke.apply(this, args)', call)
                source = source.replace('remaining', '$quota').replace('invoke', 'runUser')
                with self.subTest(threshold=threshold, call=call):
                    self.assertEqual(len(self.hints(source)), 1)

    def test_plain_guard_and_standalone_prefix_or_postfix_updates(self):
        for update in ['--remaining;', 'remaining--;']:
            for bound in [0, 1, 3]:
                source = LATE.replace('remaining > 1', 'remaining > '+str(bound)).replace(
                    'remaining <= 1', 'remaining <= '+str(bound)).replace('--remaining;', update)
                with self.subTest(update=update, bound=bound):
                    self.assertEqual(self.hints(source)[0]['state_publication']['status'], 'write_after_call')
        early = LATE.replace('    --remaining;\n', '').replace(
            '      memo = invoke.apply(this, args);', '      --remaining;\n      memo = invoke.apply(this, args);')
        self.assertEqual(self.hints(early)[0]['state_publication']['status'], 'write_before_call')

    def test_callback_without_cleanup_keeps_countdown_evidence(self):
        self.assertEqual(len(self.hints(SOURCE.replace('    if (remaining <= 1) invoke = null;\n', ''))), 1)

    def test_conditional_cleanup_is_neutral_and_must_have_evidence(self):
        report = self.report(LATE)
        card = focused_review(report)['cards'][0]
        self.assertIn('cannot be treated as an action on every path', ' '.join(card['notes']))
        self.assertIn('does not classify the cleanup statement itself as defective', markdown(report))
        publication = self.hints(LATE)[0]['state_publication']
        self.assertEqual(publication['callback_cleanup']['condition'], 'remaining <= 1')
        for action in ['relation', 'guard']:
            broken = copy.deepcopy(report)
            if action == 'relation':
                broken['relations'] = [r for r in broken['relations'] if r['kind'] != 'external_call_before_conditional_callback_clear']
            else:
                broken['findings'][0]['state_publication']['callback_cleanup']['guard'] = 'missing'
            with self.subTest(action=action):
                self.assertEqual(focused_review(broken)['cards'], [])

    def test_mismatched_or_early_cleanup_does_not_supply_callback_identity(self):
        examples = [
            SOURCE.replace('remaining <= 1', 'remaining <= 2'),
            SOURCE.replace('remaining <= 1', 'other <= 1'),
            SOURCE.replace('invoke = null;', 'invoke = other;'),
            SOURCE.replace('invoke = null;', 'invoke.apply = null;'),
            SOURCE.replace('    if (--remaining', '    if (remaining <= 1) invoke = null;\n    if (--remaining').replace('    if (remaining <= 1) invoke = null;\n    return memo;', '    return memo;'),
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_resets_reassignment_and_shadowing_are_unknown(self):
        examples = [
            SOURCE.replace('return function entry', 'function reset() { remaining = 2; } return function entry'),
            SOURCE.replace('return function entry', 'invoke = other; return function entry'),
            SOURCE.replace('entry(...args)', 'entry(remaining, ...args)'),
            SOURCE.replace('entry(...args)', 'entry(invoke, ...args)'),
            SOURCE.replace('if (--remaining', 'let remaining; if (--remaining'),
            SOURCE.replace('memo = invoke.apply', 'remaining = 2; memo = invoke.apply'),
            SOURCE.replace('invoke = null;', '({invoke} = other);'),
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_other_arithmetic_and_guard_forms_are_not_guessed(self):
        examples = [
            SOURCE.replace('--remaining > 0', 'remaining-- > 0'),
            SOURCE.replace('--remaining > 0', '++remaining > 0'),
            SOURCE.replace('--remaining > 0', '--remaining >= 0'),
            SOURCE.replace('--remaining > 0', '--remaining > limit'),
            SOURCE.replace('--remaining > 0', '--remaining > 0.5'),
            SOURCE.replace('--remaining > 0', '--remaining > 9007199254740991'),
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_unrelated_branches_and_duplicate_callbacks_are_not_joined(self):
        examples = [
            LATE.replace('    --remaining;', '    if (flag) --remaining;'),
            LATE.replace('      memo = invoke.apply(this, args);', '      if (flag) memo = invoke.apply(this, args);'),
            SOURCE.replace('      memo = invoke.apply(this, args);', '      invoke(); memo = invoke.apply(this, args);'),
            SOURCE.replace('      memo = invoke.apply(this, args);', '      memo = invoke.apply(this, args); } else { invoke();'),
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_suspend_delayed_calls_and_early_exit_are_not_linear_paths(self):
        examples = [
            SOURCE.replace('function entry', 'async function entry').replace('memo = invoke.apply', 'await pause(); memo = invoke.apply'),
            SOURCE.replace('invoke.apply(this, args)', 'setTimeout(() => invoke(), 0)'),
            LATE.replace('      memo = invoke.apply(this, args);', '      return invoke.apply(this, args);'),
            LATE.replace('    --remaining;', '    return memo; --remaining;'),
            SOURCE.replace('if (--remaining', 'return; if (--remaining'),
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_budget_exhaustion_fails_closed(self):
        source = LATE.replace('    --remaining;', '    ;\n' * 5 + '    --remaining;')
        self.assertEqual(len(self.hints(source)), 1)
        # Events outside the prefix must not be connected through the budget cap.
        source = LATE.replace('  return function entry', '  return function entry')
        source = source.replace('if (remaining > 1)', 'var ' + ','.join('a'+str(i)+'=0' for i in range(2100)) + '; if (remaining > 1)')
        self.assertEqual(self.hints(source), [])

    def test_typescript_vue_and_frozen_numeric_facts(self):
        for path, source in [('a.ts', LATE.replace('before(remaining, invoke)', 'before(remaining: number, invoke: Function)')),
                             ('A.vue', '<script setup>\n'+LATE+'\n</script>')]:
            report = self.report(source, path)
            self.assertEqual(len(focused_review(report)['cards']), 1)
            with tempfile.TemporaryDirectory() as directory:
                bundle = Path(directory)/'bundle'
                manifest = freeze_bundle(report, bundle)
                self.assertEqual(verify_bundle(bundle), manifest)
                facts = (bundle/'facts.md').read_text()
                self.assertIn('countdown_guard', facts)
                self.assertIn('update_prefix', facts)
                self.assertIn('numeric_budget_guard_before_call', facts)
                self.assertIn('numeric_budget', (bundle/'review.md').read_text())


if __name__ == '__main__':
    unittest.main()
