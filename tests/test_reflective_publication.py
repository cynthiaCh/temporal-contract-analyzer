"""Receiver captures, native Reflect candidates, and separate dispatch arms."""
import tempfile
from pathlib import Path
import unittest

from temporal_contract_analyzer.core import analyze_sources, compare
from temporal_contract_analyzer.layers import freeze_bundle, verify_bundle
from temporal_contract_analyzer.review import focused_review

SOURCE = '''const {apply: invoke, construct: create} = Reflect;
function factory() {
  let target = this, allowed = true, result;
  return function entry(...args) {
    if (allowed) {
      allowed = false;
      result = this instanceof entry ? create(target, args) : invoke(target, this, args);
    }
    return result;
  };
}'''
LATE = SOURCE.replace('      allowed = false;\n', '').replace(
    '      result = this instanceof entry ? create(target, args) : invoke(target, this, args);',
    '      result = this instanceof entry ? create(target, args) : invoke(target, this, args);\n      allowed = false;')


class ReflectivePublicationTests(unittest.TestCase):
    def report(self, source=SOURCE, path='a.js'):
        report = analyze_sources({path: source})
        self.assertEqual(report['status'], 'parsed')
        return report

    def hints(self, source=SOURCE):
        return [f for f in self.report(source)['findings']
                if f.get('state_publication', {}).get('callback_binding_basis') == 'stable_receiver_capture_via_reflect']

    def test_early_and_late_flags_preserve_both_calls_and_low_noise_policy(self):
        early, late = self.report(), self.report(LATE)
        self.assertEqual([f['state_publication']['status'] for f in self.hints()], ['write_before_call'] * 2)
        self.assertEqual([f['state_publication']['status'] for f in self.hints(LATE)], ['write_after_call'] * 2)
        self.assertEqual(len(focused_review(early)['cards']), 0)
        card = focused_review(late)['cards'][0]
        self.assertEqual(len(card['finding_ids']), 2)
        self.assertEqual(len([e for e in card['evidence'] if e['kind'] == 'call']), 2)
        modes = {f['state_publication']['reflective_call']['operation'] for f in self.hints()}
        self.assertEqual(modes, {'apply', 'construct'})
        arms = {f['state_publication']['reflective_call']['conditional_path'][0]['arm'] for f in self.hints()}
        self.assertEqual(arms, {'then', 'else'})
        delta = compare(early, late)
        self.assertTrue(delta['comparable'])
        self.assertEqual(len(delta['added_hints']), 2)
        self.assertEqual(len(delta['removed_hints']), 2)

    def test_direct_reflect_and_renamed_bindings_are_supported(self):
        direct = SOURCE.replace('const {apply: invoke, construct: create} = Reflect;\n', '').replace('invoke(target', 'Reflect.apply(target').replace('create(target', 'Reflect.construct(target')
        self.assertEqual(len(self.hints(direct)), 2)
        renamed = SOURCE.replace('target', '$callable').replace('allowed', 'pending').replace('invoke', 'callUser').replace('create', 'newUser')
        self.assertEqual(len(self.hints(renamed)), 2)
        plain = SOURCE.replace('this instanceof entry ? create(target, args) : ', '')
        self.assertEqual(len(self.hints(plain)), 1)

    def test_lookalike_calls_and_shadowed_reflect_are_not_intrinsics(self):
        examples = [
            SOURCE.replace('= Reflect;', '= other;'),
            'const Reflect = other;\n' + SOURCE,
            SOURCE.replace('function factory()', 'function factory(Reflect)'),
            'import Reflect from "other";\n' + SOURCE,
            'function Reflect() {}\n' + SOURCE,
            SOURCE.replace('const {apply: invoke, construct: create} = Reflect;', 'function invoke() {} function create() {}'),
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_visible_global_reflect_mutations_block_association(self):
        for mutation in ['Reflect.apply = other;', 'Reflect["construct"] = other;',
                         'globalThis.Reflect = other;', 'globalThis["Reflect"] = other;',
                         'Object.assign(Reflect, other);', 'Object.defineProperty(Reflect, "apply", descriptor);',
                         'Object.defineProperty(globalThis, "Reflect", descriptor);']:
            with self.subTest(mutation=mutation):
                self.assertEqual(self.hints(SOURCE + '\n' + mutation), [])

    def test_api_alias_changes_or_wrong_extraction_are_unknown(self):
        for mutation in ['invoke = other; create = other;', 'invoke.call = other; create.call = other;',
                         '({invoke, create} = other);']:
            source = SOURCE.replace('const {apply:', 'let {apply:') + '\n' + mutation
            with self.subTest(mutation=mutation):
                self.assertEqual(self.hints(source), [])
        self.assertEqual(self.hints(SOURCE.replace('apply: invoke, construct: create', 'other: invoke, other2: create')), [])

    def test_receiver_capture_must_be_stable_and_shared_with_flag(self):
        examples = [
            SOURCE.replace('target = this', 'target = other'),
            SOURCE.replace('if (allowed)', 'target = other; if (allowed)'),
            SOURCE.replace('if (allowed)', 'target.apply = other; if (allowed)'),
            SOURCE.replace('entry(...args)', 'entry(target, ...args)'),
            SOURCE.replace('let target = this, allowed = true, result;', 'return; let target = this, allowed = true, result;'),
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_flag_changes_and_shadowing_are_conservative(self):
        examples = [
            SOURCE.replace('allowed = true', 'allowed = false'),
            SOURCE.replace('allowed = false;', 'allowed = false; allowed = true;'),
            SOURCE.replace('if (allowed)', 'let allowed; if (allowed)'),
            SOURCE.replace('entry(...args)', 'entry(allowed, ...args)'),
            SOURCE.replace('if (allowed)', 'if (!allowed)'),
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_dispatch_must_use_current_wrapper_and_separate_conditional_arms(self):
        for replacement in ['flag', 'this instanceof Other', 'check()']:
            with self.subTest(replacement=replacement):
                self.assertEqual(self.hints(SOURCE.replace('this instanceof entry', replacement)), [])
        self.assertEqual(self.hints(SOURCE.replace('entry(...args)', 'entry(entry, ...args)')), [])
        self.assertEqual(self.hints(SOURCE.replace('if (allowed)', 'let entry; if (allowed)')), [])

    def test_await_deferred_calls_extra_controls_and_unreachable_writes(self):
        examples = [
            SOURCE.replace('function entry', 'async function entry').replace('allowed = false;', 'await pause(); allowed = false;'),
            SOURCE.replace('allowed = false;', 'if (flag) allowed = false;'),
            SOURCE.replace('result = this instanceof entry ? create(target, args) : invoke(target, this, args);',
                           'setTimeout(() => invoke(target, this, args), 0);'),
            LATE.replace('      allowed = false;', '      return; allowed = false;'),
            SOURCE.replace('if (allowed)', 'return; if (allowed)'),
        ]
        for source in examples:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source), [])

    def test_wrong_target_or_arity_is_not_a_receiver_invocation(self):
        self.assertEqual(self.hints(SOURCE.replace('create(target, args)', 'create(other, args)').replace('invoke(target, this, args)', 'invoke(other, this, args)')), [])
        self.assertEqual(self.hints(SOURCE.replace('create(target, args)', 'create(target)').replace('invoke(target, this, args)', 'invoke(target, args)')), [])

    def test_unreachable_native_extraction_and_budget_are_not_guessed(self):
        source = SOURCE.replace('const {apply: invoke, construct: create} = Reflect;\n', '')
        source = source.replace('return result;', 'return result; const {apply: invoke, construct: create} = Reflect;')
        self.assertEqual(self.hints(source), [])
        self.assertEqual(self.hints(SOURCE.replace('if (allowed)', 'noop();' * 2100 + 'if (allowed)')), [])

    def test_typescript_vue_and_frozen_receiver_facts(self):
        for path, source in [('a.ts', SOURCE.replace('target = this', 'target: Function = this')),
                             ('A.vue', '<script setup>\n'+SOURCE+'\n</script>')]:
            report = self.report(source, path)
            self.assertEqual(len(focused_review(report)['context']), 2)
            with tempfile.TemporaryDirectory() as directory:
                bundle = Path(directory)/'bundle'
                manifest = freeze_bundle(report, bundle)
                self.assertEqual(verify_bundle(bundle), manifest)
                facts = (bundle/'facts.md').read_text()
                self.assertIn('receiver_capture_before_reflective_call', facts)
                self.assertIn('object_bindings', facts)
                self.assertIn('conditional_path', facts)
                self.assertIn('reflective_call', (bundle/'review.md').read_text())


if __name__ == '__main__':
    unittest.main()
