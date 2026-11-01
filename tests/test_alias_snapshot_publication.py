"""Value snapshots preserve the callable when its source binding is cleared."""
import tempfile
from pathlib import Path
import unittest

from temporal_contract_analyzer.core import analyze_sources, compare
from temporal_contract_analyzer.layers import freeze_bundle, verify_bundle
from temporal_contract_analyzer.review import focused_review

SOURCE = '''function wrap(fn) {
  return function entry(...args) {
    if (fn === null) return;
    const saved = fn;
    fn = null;
    saved.apply(this, args);
  };
}'''


class AliasSnapshotTests(unittest.TestCase):
    def report(self, source=SOURCE, path='a.js'):
        report = analyze_sources({path: source})
        self.assertEqual(report['status'], 'parsed')
        return report

    def hints(self, source=SOURCE):
        return [f for f in self.report(source)['findings']
                if f.get('state_publication', {}).get('callback_binding_basis') == 'local_snapshot_of_outer_parameter']

    def test_early_clear_preserves_alias_and_is_only_context(self):
        report = self.report()
        hint = self.hints()[0]['state_publication']
        self.assertEqual(hint['status'], 'write_before_call')
        self.assertEqual(hint['callback_alias']['name'], 'saved')
        self.assertEqual(hint['callback_alias']['source'], 'fn')
        self.assertEqual(hint['execution_path'], [hint['callback_alias']['copy']])
        self.assertEqual(focused_review(report)['cards'], [])
        self.assertEqual(focused_review(report)['context'][0]['state'], 'fn')

    def test_late_clear_is_a_complete_default_card(self):
        source = SOURCE.replace('fn = null;\n    saved.apply(this, args);', 'saved.apply(this, args);\n    fn = null;')
        report = self.report(source)
        finding = self.hints(source)[0]
        self.assertEqual(finding['state_publication']['status'], 'write_after_call')
        card = focused_review(report)['cards'][0]
        self.assertIn(finding['state_publication']['callback_alias']['copy'], [e['id'] for e in card['evidence']])
        delta = compare(self.report(), report)
        self.assertTrue(delta['comparable'])
        self.assertEqual(len(delta['added_hints']), 1)
        self.assertEqual(len(delta['removed_hints']), 1)

    def test_renaming_declarations_and_direct_call_forms(self):
        for declaration in ['var', 'let', 'const']:
            for call in ['saved()', 'saved.call(this)', 'saved.apply(this, args)']:
                source = SOURCE.replace('const saved', declaration+' saved').replace('saved.apply(this, args)', call)
                source = source.replace('fn', 'callback').replace('saved', '$copy')
                with self.subTest(declaration=declaration, call=call):
                    self.assertEqual(len(self.hints(source)), 1)
        self.assertEqual(len(self.hints(SOURCE.replace('fn === null', 'null === fn'))), 1)

    def test_clear_before_snapshot_cannot_supply_a_callable(self):
        source = SOURCE.replace('const saved = fn;\n    fn = null;', 'fn = null;\n    const saved = fn;')
        self.assertEqual(self.hints(source), [])

    def test_alias_reassignment_member_override_and_destructuring_are_unknown(self):
        for write in ['saved = other;', 'saved.apply = other;', '({saved} = other);', '({method:saved.apply} = other);']:
            source = SOURCE.replace('const saved', 'let saved').replace('    saved.apply', '    '+write+'\n    saved.apply')
            with self.subTest(write=write):
                self.assertEqual(self.hints(source), [])
        self.assertEqual(self.hints(SOURCE.replace('const saved = fn;', 'var saved = fn; var saved;')), [])

    def test_source_changes_and_shadowing_cannot_invent_a_snapshot(self):
        examples = [
            SOURCE.replace('const saved = fn;', 'fn = other; const saved = fn;'),
            SOURCE.replace('return function entry', 'fn = other; return function entry'),
            SOURCE.replace('entry(...args)', 'entry(fn, ...args)'),
            SOURCE.replace('function wrap(fn)', 'function wrap()').replace('return function entry', 'const fn = other; return function entry'),
            SOURCE.replace('const saved = fn;', 'const saved = other;'),
            SOURCE.replace('const saved = fn;', 'const saved = fn; { let saved; }'),
            SOURCE.replace('return function entry', 'function change() { fn = other; } return function entry'),
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_branch_conditional_and_multihop_aliases_are_not_propagated(self):
        examples = [
            SOURCE.replace('const saved = fn;', 'let saved; if (flag) saved = fn;'),
            SOURCE.replace('const saved = fn;', 'const saved = flag ? fn : other;'),
            SOURCE.replace('const saved = fn;', 'const saved = fn; const second = saved;').replace('saved.apply', 'second.apply'),
            SOURCE.replace('const saved = fn;', 'const saved = fn.bind(this);'),
            SOURCE.replace('const saved = fn;', 'let saved; saved = fn;'),
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_suspend_defer_unsupported_invocations_and_unreachable_clear(self):
        examples = [
            SOURCE.replace('function entry', 'async function entry').replace('fn = null;', 'await pause(); fn = null;'),
            SOURCE.replace('saved.apply(this, args)', 'setTimeout(() => saved.apply(this, args), 0)'),
            SOURCE.replace('saved.apply(this, args)', 'saved?.()'),
            SOURCE.replace('saved.apply(this, args)', 'new saved()'),
            SOURCE.replace('saved.apply(this, args)', 'saved.bind(this)()'),
            SOURCE.replace('fn = null;', 'return; fn = null;'),
            SOURCE.replace('if (fn === null)', 'return; if (fn === null)'),
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_guard_and_clear_must_match_supported_null_semantics(self):
        for guard in ['fn == null', 'fn !== null', '!fn', 'fn === undefined']:
            with self.subTest(guard=guard):
                self.assertEqual(self.hints(SOURCE.replace('fn === null', guard)), [])
        for value in ['undefined', 'false', 'other']:
            with self.subTest(value=value):
                self.assertEqual(self.hints(SOURCE.replace('fn = null;', 'fn = '+value+';')), [])

    def test_multiple_copies_keep_each_snapshot_and_merge_default_card(self):
        source = SOURCE.replace('const saved = fn;', 'const saved = fn; const second = fn;')
        source = source.replace('fn = null;\n    saved.apply(this, args);', 'saved(); second(); fn = null;')
        report = self.report(source)
        self.assertEqual(len(self.hints(source)), 2)
        review = focused_review(report)
        self.assertEqual(len(review['cards']), 1)
        self.assertEqual(len([e for e in review['cards'][0]['evidence'] if e['kind'] == 'call']), 2)
        self.assertEqual(len([e for e in review['cards'][0]['evidence'] if e['kind'] == 'write']), 3)

    def test_typescript_vue_and_frozen_alias_relation(self):
        for path, source in [('a.ts', SOURCE.replace('const saved = fn;', 'const saved: typeof fn = fn;')),
                             ('A.vue', '<script setup>\n'+SOURCE+'\n</script>')]:
            report = self.report(source, path)
            self.assertEqual(focused_review(report)['context'][0]['state'], 'fn')
            with tempfile.TemporaryDirectory() as directory:
                bundle = Path(directory)/'bundle'
                manifest = freeze_bundle(report, bundle)
                self.assertEqual(verify_bundle(bundle), manifest)
                self.assertIn('local_alias_snapshot_before_call', (bundle/'facts.md').read_text())
                self.assertIn('null_return_identifier', (bundle/'facts.md').read_text())
                self.assertIn('callback_alias', (bundle/'review.md').read_text())


if __name__ == '__main__':
    unittest.main()
