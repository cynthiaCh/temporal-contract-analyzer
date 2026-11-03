import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from temporal_contract_analyzer import archive
from temporal_contract_analyzer.context import build_context, expand, merge_ranges, parse_sources
from temporal_contract_analyzer.core import ROOT, EvidenceError
from temporal_contract_analyzer.mcp_server import Session


class ContextTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root/'project'
        self.project.mkdir()
        self.store = self.root/'reports'
        env = patch.dict(os.environ, {'TCA_CONFIG': str(self.root/'config.json')})
        env.start()
        self.addCleanup(env.stop)

    def write(self, name, text):
        path = self.project/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def scan(self):
        return archive.scan_path(self.project, self.store)['archive']['report_id']

    def test_cli_spine_uses_snapshot_and_writes_new_artifact(self):
        self.write('main.js', 'async function load(){await fetch(); store.save();}\n')
        rid = self.scan()
        self.write('main.js', 'CHANGED WORKING TREE')
        target = self.root/'context.json'
        result = subprocess.run([sys.executable, '-B', '-m', 'temporal_contract_analyzer',
                                 'reports', 'context', rid, '--store', str(self.store),
                                 '--depth', '0', '--output', str(target)],
                                cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        packet = json.loads(target.read_text())
        self.assertEqual(packet['schema_version'], 'temporal-context-1')
        self.assertTrue(packet['snippets'])
        self.assertIn('await fetch()', packet['snippets'][0]['code'])
        self.assertNotIn('CHANGED', json.dumps(packet))
        self.assertTrue(archive.verify(rid, self.store)['verified'])

    def enrich(self, sources, file='main.js', start=2, end=2, depth=1, budget=12000, aliases=None):
        parsed, metadata = parse_sources(sources)
        self.assertEqual(metadata['status'], 'available', metadata)
        seeds = merge_ranges([dict(file=file, start_line=start, end_line=end, kind='seed', reasons=[])], sources)
        return expand(seeds, sources, parsed, depth, budget, aliases or {})

    def test_named_alias_function_and_constant_exports(self):
        sources = {'main.js': "import { save as publish, config } from './shared';\npublish(config);\n",
                   'shared.js': "export function save(value) { return value / 2; }\nexport const config = { pattern: /abc/, label: `x${1}` };\n"}
        snippets, gaps = self.enrich(sources)
        self.assertFalse(gaps)
        self.assertEqual({s['file'] for s in snippets}, {'main.js','shared.js'})
        shared = next(s for s in snippets if s['file']=='shared.js')
        self.assertIn('function save', shared['code'])
        self.assertIn('pattern: /abc/', shared['code'])
        self.assertEqual({r['symbol'] for r in shared['reasons']}, {'save', 'config'})

    def test_shadowed_parameter_and_property_names_do_not_follow_import(self):
        sources = {'main.js': "import { save } from './absent';\nfunction f(save) { save(); obj.save; const x = {save: 1}; }\n"}
        snippets, gaps = self.enrich(sources)
        self.assertEqual(len(snippets), 1)
        self.assertFalse(gaps)

    def test_same_line_private_declaration_is_not_exported(self):
        sources={'main.js':"import { secret } from './shared';\nsecret();\n",
                 'shared.js':'export const publicValue = 1; const secret = 2;\n'}
        snippets,gaps=self.enrich(sources)
        self.assertEqual(len(snippets),1)
        self.assertEqual(gaps[0]['reason'],'export-not-supported-or-missing')

    def test_declaration_level_type_export_is_not_runtime_export(self):
        sources={'main.ts':"import { Foo } from './shared';\nnew Foo();\n",
                 'shared.ts':'class Foo {}\nexport type { Foo };\n'}
        snippets,gaps=self.enrich(sources,file='main.ts')
        self.assertEqual(len(snippets),1)
        self.assertEqual(gaps[0]['reason'],'export-not-supported-or-missing')

    def test_computed_method_key_uses_enclosing_scope(self):
        sources={'main.js':"import { key } from './shared';\nconst obj = { [key](key) { return key; } };\n",
                 'shared.js':'export const key = "method";\n'}
        snippets,gaps=self.enrich(sources)
        self.assertFalse(gaps)
        self.assertTrue(any(s['file']=='shared.js' for s in snippets))

    def test_default_parameter_does_not_see_body_var_binding(self):
        sources={'main.js':"import { save } from './shared';\nfunction f(value=save) { var save; return value; }\n",
                 'shared.js':'export function save() {}\n'}
        snippets,gaps=self.enrich(sources)
        self.assertFalse(gaps)
        self.assertTrue(any(s['file']=='shared.js' for s in snippets))

    def test_typescript_runtime_constructs_report_explicit_gap(self):
        sources={'main.ts':"import { save } from './shared';\nenum Values { Entry=save() }\n",
                 'shared.ts':'export function save() { return 1; }\n'}
        _,gaps=self.enrich(sources,file='main.ts')
        self.assertIn('typescript-runtime-declaration-not-modeled',{g['reason'] for g in gaps})
        _,gaps=self.enrich({'main.ts':'enum Status { Ready=1 }\nconsole.log(Status.Ready);\n'},file='main.ts')
        self.assertIn('typescript-runtime-declaration-not-modeled',{g['reason'] for g in gaps})

    def test_block_shadow_and_var_hoisting(self):
        sources = {'main.js': "import { save } from './absent';\nfunction f() { save(); var save = () => 1; }\n"}
        _, gaps = self.enrich(sources)
        self.assertFalse(gaps)

    def test_default_export_list_and_local_definition(self):
        sources = {'main.ts': "import publish, { config as c } from './shared';\npublish(c);\n",
                   'shared.ts': 'const value = 42;\nconst config = { value };\nexport { config };\nexport default function save(x: unknown) { return x; }\n'}
        snippets, gaps = self.enrich(sources, file='main.ts', depth=2)
        self.assertTrue(any('const value = 42' in s['code'] for s in snippets))
        self.assertFalse(gaps)

    def test_vue_setup_references_use_original_lines_and_isolated_scopes(self):
        sources = {'Main.vue': '<template>{{ view }}</template>\n<script setup lang="ts">\nimport { save } from "./shared";\nsave();\n</script>\n',
                   'shared.ts': 'export function save() {}\n'}
        snippets, gaps = self.enrich(sources, file='Main.vue', start=4, end=4)
        self.assertEqual(snippets[0]['start_line'], 4)
        self.assertTrue(any(s['file']=='shared.ts' for s in snippets))
        self.assertIn('vue-template-and-cross-block-bindings-not-modeled', {g['reason'] for g in gaps})

    def test_depth_budget_cycles_and_overlap(self):
        sources = {'main.js': "import { a } from './a';\na();\n",
                   'a.js': "import { b } from './b';\nexport const a = () => b();\n",
                   'b.js': "import { a } from './a';\nexport function b() { return a; }\n"}
        snippets, gaps = self.enrich(sources)
        self.assertIn('depth-limit', {g['reason'] for g in gaps})
        self.assertFalse(any(s['file']=='b.js' for s in snippets))
        snippets, gaps = self.enrich(sources, depth=5)
        self.assertEqual(len(snippets), 3)
        self.assertFalse(gaps)
        snippets, gaps = self.enrich(sources, budget=len('a();\n'))
        self.assertEqual(len(snippets),1)
        self.assertIn('budget-limit', {g['reason'] for g in gaps})

    def test_missing_external_reexports_namespace_and_ambiguous_paths_are_gaps(self):
        sources = {'main.js': "import { a } from './missing'; import b from 'external'; import * as ns from './shared'; import { c } from './barrel'; import { d } from './amb';\n[a, b, ns.x, c, d];\n",
                   'shared.js': 'export const x = 1;\n',
                   'barrel.js': 'export { c } from "./shared";\n',
                   'amb.js': 'export const d = 1;\n', 'amb.ts': 'export const d = 2;\n'}
        _, gaps = self.enrich(sources)
        self.assertEqual({g['reason'] for g in gaps}, {'module-not-in-snapshot','external-or-unmapped-module',
                         'namespace-import-not-supported','reexport-not-supported','ambiguous-module'})

    def test_explicit_alias_and_type_only_imports(self):
        sources = {'main.ts': "import type { Type } from './missing'; import { type T, save } from 'App/shared';\nsave({} as Type);\n",
                   'src/shared.ts': 'export function save(x: unknown) { return x; }\n'}
        snippets, gaps = self.enrich(sources, file='main.ts', aliases={'App': 'src'})
        self.assertFalse(gaps)
        self.assertTrue(any(s['file']=='src/shared.ts' for s in snippets))

    def test_archived_real_findings_expand_import_without_working_tree_reads(self):
        self.write('main.js', "import { publish } from './shared';\nasync function load() {\n await fetch();\n publish();\n}\n")
        self.write('shared.js', 'export function publish() { return 1; }\n')
        rid = self.scan()
        self.write('shared.js', 'export function publish() { return 999; }\n')
        packet = build_context(rid, self.store)
        self.assertTrue(packet['finding_ids'])
        self.assertTrue(any('return 1' in s['code'] for s in packet['snippets']))
        self.assertNotIn('999', json.dumps(packet))
        self.assertLessEqual(packet['usage']['code_chars'],12000)
        self.assertEqual(packet['usage']['code_chars'],sum(len(s['code']) for s in packet['snippets']))
        with self.assertRaisesRegex(EvidenceError, 'Seed code'):
            build_context(rid, self.store, max_chars=1)
        with self.assertRaisesRegex(EvidenceError, 'Unknown finding'):
            build_context(rid, self.store, finding_id='missing')
        with self.assertRaisesRegex(EvidenceError, 'within the snapshot'):
            build_context(rid, self.store, aliases={'App':'../outside'})

    def test_no_findings_and_unavailable_parser(self):
        self.write('main.js', 'const x = 1;\n')
        packet = build_context(self.scan(), self.store)
        self.assertEqual(packet['snippets'], [])
        self.assertEqual(packet['parser']['status'], 'not-needed')
        self.write('main.js', 'async function f() { await fetch(); store.save(); }\n')
        packet = build_context(self.scan(), self.store, node='/does/not/exist')
        self.assertTrue(packet['snippets'])
        self.assertIn('parser-unavailable', {g['reason'] for g in packet['unresolved']})

    def test_mcp_context_pages_exact_json_and_records_delivery(self):
        self.write('main.js', "import { publish } from './shared';\nasync function f() { await fetch(); publish(); }\n")
        self.write('shared.js', 'export function publish() { return 1; }\n')
        rid = self.scan()
        session = Session(self.store)
        offset, chunks, digest = 0, [], None
        while offset is not None:
            page = session.call('read_context', dict(report_id=rid, offset=offset, limit=250))
            self.assertTrue(page['material'].startswith('context:'))
            digest = digest or page['material_sha256']
            self.assertEqual(digest, page['material_sha256'])
            chunks.append(page['text'])
            offset = page['next_offset']
            session.written()
        packet = json.loads(''.join(chunks))
        self.assertTrue(any(s['file']=='shared.js' for s in packet['snippets']))
        records = archive.records('deliveries', rid, self.store)
        self.assertEqual(len(records), len(chunks)*2)
        restricted = Session(self.store, report_id=rid, layer='facts')
        with self.assertRaisesRegex(EvidenceError, 'unavailable tool'):
            restricted.call('read_context', dict(report_id=rid))
        for args in [dict(aliases=[]),dict(aliases={'App':42}),dict(depth=True),dict(max_chars=0)]:
            with self.subTest(args=args), self.assertRaises(EvidenceError):
                session.call('read_context',dict(report_id=rid, **args))

    def test_cli_markdown_rejects_overwrite_and_candidate_output(self):
        self.write('main.js', 'async function f() { await fetch(); store.save(); }\n')
        rid = self.scan()
        command = [sys.executable,'-B','-m','temporal_contract_analyzer','reports','context',rid,
                   '--store',str(self.store),'--format','md']
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('未解析项',result.stdout)
        self.assertIn('input_sha256',result.stdout)
        self.assertIn('implementation_sha256',result.stdout)
        for target in [self.project/'context.md', self.root/'existing.md',self.store/'runs'/rid/'context.md']:
            if target.name=='existing.md':target.write_text('keep')
            result = subprocess.run(command+['--output',str(target)],cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(result.returncode,1,result.stdout)
        self.assertEqual((self.root/'existing.md').read_text(),'keep')
        self.assertTrue(archive.verify(rid,self.store)['verified'])

    def test_python_and_dynamic_dependencies_report_gaps(self):
        sources = {'main.js': "const name='x';\nconst value = require(name);\n"}
        _, gaps = self.enrich(sources)
        self.assertIn('dynamic-or-commonjs-import',{g['reason'] for g in gaps})
        _, gaps = self.enrich({'main.py':'x=1\nprint(x)\n'},file='main.py')
        self.assertEqual(gaps[0]['reason'],'unsupported-language')

    def test_snapshot_tampering_is_rejected(self):
        self.write('main.js','async function f() { await fetch(); store.save(); }\n')
        rid=self.scan()
        snapshot=self.store/'runs'/rid/'snapshot.json'
        data=json.loads(snapshot.read_text())
        data['sources']['main.js']='tampered'
        snapshot.write_text(json.dumps(data))
        with self.assertRaises(EvidenceError):build_context(rid,self.store)
