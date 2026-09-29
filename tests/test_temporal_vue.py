"""Vue source-only support, using synthetic cases independent of the benchmark."""
import json
from pathlib import Path
import tempfile
import unittest

from temporal_contract_analyzer.core import (
    EvidenceError, analyze_sources, compare, js_analyze, scan, sha,
)
from temporal_contract_analyzer.layers import (
    AUDIT_PROMPT, freeze_bundle, render_layers, verify_bundle,
)
from temporal_contract_analyzer.report import html_report, markdown


class TemporalVueTests(unittest.TestCase):
    def vue(self, source):
        report = analyze_sources({'Demo.vue': source})
        self.assertEqual(report['status'], 'parsed', report['files'])
        self.assertEqual(report['files'][0]['language'], 'vue')
        return report

    def assert_exact_events(self, source, file):
        self.assertEqual(file['column_unit'], 'utf16_code_units')
        lines = source.splitlines(keepends=True)
        for event in file['events']:
            start, end = event['line'] - 1, event['end_line'] - 1
            if start == end:
                actual = lines[start].encode('utf-16-le')[event['column'] * 2:event['end_column'] * 2].decode('utf-16-le')
            else:
                actual = (lines[start].encode('utf-16-le')[event['column'] * 2:].decode('utf-16-le')
                          + ''.join(lines[start + 1:end])
                          + lines[end].encode('utf-16-le')[:event['end_column'] * 2].decode('utf-16-le'))
            self.assertEqual(event['text'], actual, event)

    def test_options_and_composition_api_expose_existing_temporal_hints(self):
        # Shapes represented in the benchmark's Vue 2 bootstrap and Vue 3 editors.
        sources = {
            'Options.vue': '''<template><div/></template>
<script>
export default {
  created() { this.bootstrap(); },
  methods: { async bootstrap() { await fetch('/ticket'); store.save(); } }
};
</script>''',
            'Composition.vue': '''<script setup lang="ts">
import {onMounted} from 'vue';
async function load(id: string) { await fetch(id); store.save(); }
onMounted(() => load('draft'));
</script><template><div/></template>''',
        }
        report = analyze_sources(sources)
        self.assertEqual(report['status'], 'parsed')
        self.assertEqual({f['path'] for f in report['findings'] if f['rule'] == 'effect-after-await'}, set(sources))
        options = next(f for f in report['files'] if f['path'] == 'Options.vue')
        dispatch = next(e for e in options['events'] if e.get('callee') == 'this.bootstrap')
        self.assertEqual(dispatch['binding'], 'unresolved')
        self.assertNotIn(dispatch['id'], {link['call'] for link in report['call_links']})

    def test_script_languages_and_top_level_await(self):
        for language, body in (
            ('js', 'await fetch(); save();'),
            ('ts', 'const id: string = "x"; await fetch(id); save();'),
            ('jsx', 'const view = <div/>; await fetch(); save();'),
            ('tsx', 'const view: unknown = <div/>; await fetch(); save();'),
        ):
            with self.subTest(language=language):
                report = self.vue('<script setup lang="' + language + '">' + body + '</script>')
                self.assertIn('effect-after-await', {f['rule'] for f in report['findings']})

    def test_source_locations_preserve_inline_tags_unicode_and_crlf(self):
        source = ('<!-- 😀 -->\r\n<template><div>😀</div></template><script lang="ts">'
                  'const label: string = "😀";\r\n'
                  'async function load() {\r\n  await fetch(\r\n    label\r\n  );\r\n  store.save(label);\r\n}\r\n'
                  '</script>\r\n<script setup>bus.subscribe("事件😀", e => {\r\n'
                  '  later(() => bus.close(e));\r\n});</script>\r\n'
                  '<style>.example { content: "😀"; }</style>')
        file = self.vue(source)['files'][0]
        self.assert_exact_events(source, file)
        write = next(e for e in file['events'] if e.get('target') == 'label')
        self.assertEqual(write['line'], 2)
        prefix = source.splitlines()[1].split('label:')[0]
        self.assertEqual(write['column'], len(prefix.encode('utf-16-le')) // 2)
        save = next(e for e in file['events'] if e.get('callee') == 'store.save')
        self.assertEqual((save['line'], save['column']), (7, 2))

    def test_templates_styles_comments_and_template_only_files_have_no_code_events(self):
        source = '''<!-- <script>commentGhost()</script> -->
<template><button @click="templateGhost()">{{ anotherGhost() }}</button></template>
<script setup>const literal = "stringGhost()"; realCall();</script>
<style>.x { content: "styleGhost()"; }</style>'''
        report = self.vue(source)
        self.assertEqual([e['callee'] for e in report['files'][0]['events'] if e['kind'] == 'call'], ['realCall'])
        empty = self.vue('<template><div>{{ templateGhost() }}</div></template>')
        self.assertEqual(empty['files'][0]['events'], [])
        self.assertEqual(empty['findings'], [])
        self.assertIn('template expressions', empty['files'][0]['analysis_scope'])

    def test_dual_scripts_keep_bindings_and_event_ids_independent(self):
        source = '''<script>
function run() { normalCall(); }
function normalOnly() {}
run();
</script><script setup>
function run() { setupCall(); }
run(); normalOnly();
</script>'''
        report = self.vue(source)
        file = report['files'][0]
        self.assertEqual(len({f['id'] for f in file['functions']}), len(file['functions']))
        self.assertEqual(len({e['id'] for e in file['events']}), len(file['events']))
        self.assertEqual({l['target'] for l in report['call_links']},
                         {'Demo.vue::<module>/run', 'Demo.vue::<setup>/run'})
        unknown = next(e for e in file['events'] if e.get('callee') == 'normalOnly')
        self.assertEqual(unknown['binding'], 'unresolved')
        self.assert_exact_events(source, file)

    def test_setup_scope_is_stable_when_normal_script_is_added(self):
        setup = '<script setup>function run() { work(); } run();</script>'
        first = self.vue(setup)
        second = self.vue('<script>export const name = "demo";</script>' + setup)
        self.assertEqual(first['call_links'], second['call_links'])

    def test_no_lexical_order_or_continuation_hint_across_script_blocks(self):
        report = self.vue('''<script>channel.connect(); pending.then(done);</script>
<script setup>channel.addEventListener('ready', done); channel.removeEventListener('ready', done);</script>''')
        rules = {f['rule'] for f in report['findings']}
        self.assertNotIn('connect-before-listen', rules)
        self.assertNotIn('continuation-and-listener-removal', rules)
        self.assertFalse([r for r in report['relations'] if r['kind'] == 'lexical_before_same_block'])
        same = self.vue('<script setup>pending.then(done); channel.removeEventListener("ready", done);</script>')
        self.assertIn('continuation-and-listener-removal', {f['rule'] for f in same['findings']})

    def test_relative_import_candidates_work_in_both_directions(self):
        report = analyze_sources({
            'Demo.vue': '''<script>export function normal() {}</script>
<script setup>import {save as persist} from './helper.js'; persist();</script>''',
            'helper.js': 'export function save() {}',
            'caller.ts': "import {normal} from './Demo.vue'; normal();",
        })
        self.assertEqual(report['status'], 'parsed')
        self.assertEqual({l['target'] for l in report['call_links']},
                         {'helper.js::<module>/save', 'Demo.vue::<module>/normal'})

    def test_unsupported_or_broken_sfc_is_partial_and_cannot_be_frozen(self):
        cases = [
            ('<script src="./missing.js"></script>', 'External <script src>'),
            ('<template src="./missing.html"/><script>realCall();</script>', 'External Vue templates'),
            ('<script lang="coffee">x = -> 1</script>', 'Unsupported Vue script language'),
            ('<script>realCall();</script><i18n>{}</i18n>', 'custom blocks'),
            ('<script>function broken(</script>', None),
            ('<script>realCall();</script><script>otherCall();</script>', None),
            ('<script>realCall();</script><script setup>function broken(</script>', None),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            for source, reason in cases:
                with self.subTest(source=source):
                    report = analyze_sources({'Broken.vue': source, 'ok.js': 'ok();'})
                    self.assertEqual(report['status'], 'partial')
                    file = next(f for f in report['files'] if f['path'] == 'Broken.vue')
                    self.assertEqual(file['status'], 'parse_error')
                    self.assertEqual(file['events'], [])
                    self.assertEqual(file['functions'], [])
                    if reason:
                        self.assertIn(reason, file['error']['message'])
                    with self.assertRaisesRegex(EvidenceError, 'Broken.vue: parse_error'):
                        freeze_bundle(report, Path(temporary) / 'bundle')
                    self.assertFalse((Path(temporary) / 'bundle').exists())

    def test_partial_report_explains_error_and_html_escapes_source(self):
        report = analyze_sources({'Broken.vue': '<script src="./missing.js"></script>'})
        self.assertIn('External <script src>', markdown(report))
        rendered = html_report(report)
        self.assertIn('External &lt;script src&gt;', rendered)
        self.assertNotIn('<script src>', rendered)

    def test_missing_node_preserves_vue_inventory_and_refuses_freeze(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = analyze_sources({'Demo.vue': '<script>save();</script>'},
                                     node=str(Path(temporary) / 'missing-node'))
            self.assertEqual(report['status'], 'partial')
            self.assertEqual(report['files'][0]['language'], 'vue')
            self.assertEqual(report['files'][0]['status'], 'parser_unavailable')
            with self.assertRaisesRegex(EvidenceError, 'Demo.vue: parser_unavailable'):
                freeze_bundle(report, Path(temporary) / 'bundle')

    def test_scan_freeze_verify_and_compare_with_script_scope_disclosure(self):
        source = '<script setup>channel.connect(); channel.addEventListener("ready", done);</script>'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / 'candidate'
            candidate.mkdir()
            file = candidate / 'Demo.vue'
            file.write_text(source, encoding='utf-8')
            before = scan(candidate)
            self.assertEqual(before['files'][0]['sha256'], sha(file.read_bytes()))
            manifest = freeze_bundle(before, root / 'bundle')
            self.assertEqual(verify_bundle(root / 'bundle', before['input_sha256']), manifest)
            self.assertEqual(file.read_text(), source)
            layers = render_layers(before)
            for name in ('locations', 'facts', 'review', 'audit_review'):
                self.assertIn('## Vue analysis scope', layers[name])
            self.assertEqual(layers['audit'], AUDIT_PROMPT)
            self.assertNotIn('Demo.vue', layers['risk'])
            self.assertIn('inline script', markdown(before))
            self.assertIn('inline script', html_report(before))
            file.write_text('<script setup>channel.addEventListener("ready", done); channel.connect();</script>')
            delta = compare(before, scan(candidate))
            self.assertTrue(delta['comparable'])
            self.assertEqual(delta['changed_files'], ['Demo.vue'])
            self.assertIn('connect-before-listen', {f['rule'] for f in delta['removed_hints']})
            self.assertIn('listen-before-connect', {f['rule'] for f in delta['added_hints']})
            with self.assertRaises(EvidenceError):
                verify_bundle(root / 'bundle', scan(candidate)['input_sha256'])

    def test_only_parses_source_without_executing_modules_or_reading_imports(self):
        with tempfile.TemporaryDirectory() as temporary:
            sentinel = Path(temporary) / 'should-not-exist'
            source = ('<script setup>import "./absent.js";\n'
                      'require("fs").writeFileSync(' + json.dumps(str(sentinel)) + ', "executed");\n'
                      'throw new Error("must not execute");</script>')
            report = self.vue(source)
            self.assertFalse(sentinel.exists())
            self.assertEqual(len(report['files']), 1)

    def test_mixed_large_input_and_vue_parser_provenance(self):
        source = '<template><div>' + '😀 text ' * 20000 + '</div></template><script setup>work();</script>'
        report = analyze_sources({'Large.VUE': source, 'helper.js': 'helper();', 'worker.py': 'work()'})
        self.assertEqual(report['status'], 'parsed', report['files'])
        self.assertEqual(report['summary']['parsed_files'], 3)
        parser = report['adapters']['javascript_typescript']['sfc_parser']
        self.assertEqual(parser['parser'], '@vue/compiler-sfc')
        self.assertEqual(parser['version'], '3.5.13')
        self.assertRegex(parser['library_sha256'], r'^[0-9a-f]{64}$')
        files, metadata = js_analyze({'plain.js': 'plain();'})
        self.assertEqual(files[0]['status'], 'parsed')
        self.assertNotIn('sfc_parser', metadata)


if __name__ == '__main__':
    unittest.main()
