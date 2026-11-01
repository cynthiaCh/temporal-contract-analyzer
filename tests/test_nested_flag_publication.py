"""Independent shared flag on a bounded nested if path; reject path splicing."""
import tempfile
from pathlib import Path
import unittest

from temporal_contract_analyzer.core import analyze_sources
from temporal_contract_analyzer.layers import freeze_bundle, verify_bundle
from temporal_contract_analyzer.review import focused_review

SOURCE = '''function wrap(deliver) {
  let done;
  return function entry(mode) {
    if (mode) {
      if (done) return;
      const result = deliver();
      done = true;
      return result;
    }
  };
}'''


class NestedFlagTests(unittest.TestCase):
    def report(self, source=SOURCE, path='a.js'):
        report = analyze_sources({path: source})
        self.assertEqual(report['status'], 'parsed')
        return report

    def hints(self, source=SOURCE):
        return [f for f in self.report(source)['findings']
                if f.get('state_publication', {}).get('callback_binding_basis') == 'unchanged_parameter_on_nested_flag_path']

    def test_late_and_early_publication_have_distinct_default_views(self):
        late = self.report()
        early = self.report(SOURCE.replace('const result = deliver();\n      done = true;', 'done = true;\n      const result = deliver();'))
        self.assertEqual(len(focused_review(late)['cards']), 1)
        self.assertEqual(len(focused_review(early)['cards']), 0)
        hint = self.hints()[0]['state_publication']
        self.assertEqual(hint['status'], 'write_after_call')
        self.assertEqual(hint['path_conditions'], ['if mode', 'fallthrough of done'])
        self.assertEqual(len(hint['execution_path']), 1)
        self.assertEqual(focused_review(early)['context'][0]['state'], 'done')

    def test_names_initial_false_and_call_forms_are_generic(self):
        for name in ['active', 'called', '$busy']:
            for call in ['deliver()', 'deliver.call(this)', 'deliver.apply(this, [])']:
                source = SOURCE.replace('done', name).replace('deliver()', call).replace('let '+name+';', 'let '+name+' = false;')
                with self.subTest(name=name, call=call):
                    self.assertEqual(len(self.hints(source)), 1)

    def test_else_and_deeper_paths_keep_all_ancestor_evidence(self):
        for outer in ['if (other) {} else { BODY }', 'if (other) { if (mode) { BODY } }']:
            source = 'function wrap(deliver) { let done; return function entry(mode, other) { '+outer.replace('BODY', 'if (done) return; deliver(); done = true;')+' }; }'
            hints = self.hints(source)
            self.assertEqual(len(hints), 1)
            self.assertEqual(len(hints[0]['state_publication']['execution_path']), 1 if 'else' in outer else 2)

    def test_mutually_exclusive_or_repeated_text_branches_do_not_mix(self):
        bodies = [
            'if (mode) { if (done) return; deliver(); } else { done = true; }',
            'if (mode) { if (done) return; deliver(); } if (mode) { done = true; }',
            'if (mode) { if (done) return; done = true; } else { deliver(); }',
        ]
        for body in bodies:
            with self.subTest(body=body):
                self.assertEqual(self.hints('function wrap(deliver) { let done; return function entry(mode) { '+body+' }; }'), [])

    def test_reassignments_shadowing_reset_and_non_boolean_writes_are_excluded(self):
        examples = [
            SOURCE.replace('if (mode)', 'let done; if (mode)'),
            SOURCE.replace('entry(mode)', 'entry(mode, done)'),
            SOURCE.replace('const result = deliver();', 'deliver = other; const result = deliver();'),
            SOURCE.replace('const result = deliver();', '({deliver} = other); const result = deliver();'),
            SOURCE.replace('return function entry', 'function reset() { done = false; } return function entry'),
            SOURCE.replace('return function entry', 'function reset() { deliver.apply = other; } return function entry'),
            SOURCE.replace('done = true;', '({done} = other);'),
            SOURCE.replace('done = true;', 'done = false;'),
            SOURCE.replace('let done;', 'let done = true;'),
            SOURCE.replace('done = true;', 'done = true; done = false;'),
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_suspend_defer_unsupported_guard_and_extra_control_stay_unknown(self):
        examples = [
            SOURCE.replace('function entry', 'async function entry').replace('deliver()', 'await deliver()'),
            SOURCE.replace('function entry', 'async function entry').replace('const result = deliver();', 'flag && await pause(); const result = deliver();'),
            SOURCE.replace('deliver()', 'setTimeout(() => deliver(), 0)'),
            SOURCE.replace('if (done) return;', 'if (!done) return;'),
            SOURCE.replace('if (done) return;', 'if (done) return; if (other) return;'),
            SOURCE.replace('if (mode)', 'if (test())'),
            SOURCE.replace('const result = deliver();', 'return; const result = deliver();'),
            SOURCE.replace('const result = deliver();', 'throw problem; const result = deliver();'),
            SOURCE.replace('if (mode)', 'while (mode)'),
            SOURCE.replace('if (mode) {', 'try { if (mode) {').replace('    }\n  };', '    } } finally {}\n  };'),
            SOURCE.replace('if (mode) {', 'return; if (mode) {'),
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_constant_or_contradictory_ancestor_paths_are_not_reported(self):
        body = 'if (done) return; deliver(); done = true;'
        for path in ['if (false) { BODY }', 'if (1 === 2) { BODY }',
                     'if (mode) { if (!mode) { BODY } }', 'if (done) { BODY }',
                     'if (mode) {} else { if (mode) { BODY } }']:
            source = 'function wrap(deliver) { let done; return function entry(mode) { '+path.replace('BODY', body)+' }; }'
            with self.subTest(path=path):
                self.assertEqual(self.hints(source), [])

    def test_receivers_are_not_reinterpreted_as_plain_shared_flags(self):
        source = SOURCE.replace('let done;', '').replace('if (done)', 'if (this.done)').replace('done = true;', 'this.done = true;')
        self.assertEqual(self.hints(source), [])

    def test_depth_limit_and_event_budget_fail_closed(self):
        body = 'if (done) return; deliver(); done = true;'
        for _ in range(5):
            body = 'if (mode) { '+body+' }'
        self.assertEqual(self.hints('function wrap(deliver) { let done; return function entry(mode) { '+body+' }; }'), [])
        source = SOURCE.replace('if (done) return;', 'noop();' * 2100 + 'if (done) return;')
        self.assertEqual(self.hints(source), [])

    def test_typescript_vue_and_frozen_source_facts(self):
        for path, source in [('a.ts', SOURCE), ('A.vue', '<script setup>\n'+SOURCE+'\n</script>')]:
            report = self.report(source, path)
            self.assertEqual(len(focused_review(report)['cards']), 1)
            with tempfile.TemporaryDirectory() as directory:
                target = Path(directory)/'bundle'
                manifest = freeze_bundle(report, target)
                self.assertEqual(verify_bundle(target), manifest)
                self.assertIn('branch_path', (target/'facts.md').read_text())
                self.assertIn('fallthrough of done', (target/'review.md').read_text())


if __name__ == '__main__':
    unittest.main()
