import copy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from temporal_contract_analyzer import cli
from temporal_contract_analyzer.core import analyze_sources, scan, compare, EvidenceError
from temporal_contract_analyzer.report import html_report

ROOT=Path(__file__).resolve().parents[1]
LISTENER=ROOT/'test-fixtures/listener-registration-order/arms/listener-registration-order-vanilla/base'


class TemporalEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def rules(self,report):return [h['rule'] for h in report['findings']]
    def test_comments_and_strings_are_not_calls(self):
        r=analyze_sources({'a.py':'# asyncio.create_task(fetch())\ntext = "await fetch(); cancel();"\n','b.js':'// fetch().then(close)\nconst x = "channel.connect(); dispatchEvent()";\n'})
        self.assertEqual(r['status'],'parsed')
        self.assertFalse([e for f in r['files'] for e in f['events'] if e['kind']=='call'])
    def test_listener_reports_source_patterns_and_direct_import_links(self):
        r=scan(LISTENER)
        self.assertEqual(r['status'],'parsed')
        self.assertEqual(self.rules(r).count('connect-before-listen'),2)
        self.assertIn('cleanup-handle-after-call',self.rules(r))
        self.assertIn('continuation-and-listener-removal',self.rules(r))
        self.assertTrue(any(x['target'].endswith('subscription.js::<module>/subscribeChannel') for x in r['call_links']))
        self.assertNotIn('verdict',r);self.assertNotIn('score',r)
    def test_switching_order_changes_only_observation_not_verdict(self):
        a=scan(LISTENER);dest=self.root/'changed';shutil.copytree(LISTENER,dest)
        p=dest/'src/subscription.js';s=p.read_text().replace('  channel.connect(bootstrapMode);\n  channel.target.addEventListener("presence", listener);','  channel.target.addEventListener("presence", listener);\n  channel.connect(bootstrapMode);');p.write_text(s)
        b=scan(dest);d=compare(a,b)
        self.assertTrue(d['comparable']);self.assertEqual(d['changed_files'],['src/subscription.js'])
        self.assertEqual([h['rule'] for h in d['added_hints']],['listen-before-connect'])
        self.assertEqual([h['rule'] for h in d['removed_hints']],['connect-before-listen'])
        self.assertIn('cleanup-handle-after-call',self.rules(b))
    def test_line_shift_does_not_invent_structure_change(self):
        s='function open(c) { c.connect(); c.target.addEventListener("x", handler); }'
        d=compare(analyze_sources({'a.js':s}),analyze_sources({'a.js':'\n// comment\n'+s}))
        self.assertEqual(d['added_hints'],[]);self.assertEqual(d['removed_hints'],[])
    def test_no_order_between_different_functions_or_branches(self):
        s='function a(c){c.connect();} function b(c){c.target.addEventListener("x", h);} function d(c,x){if(x){c.connect();}else{c.target.addEventListener("x",h);}}'
        self.assertNotIn('connect-before-listen',self.rules(analyze_sources({'a.js':s})))
    def test_callbacks_are_distinct_scopes_not_assumed_inline(self):
        r=analyze_sources({'a.js':'function work(publish){ later(() => publish()); return 3; }'})
        calls=[e for e in r['files'][0]['events'] if e['kind']=='call']
        pub=next(e for e in calls if e['callee']=='publish')
        self.assertIn('<callback>',pub['scope']);self.assertEqual(pub['binding'],'parameter_callback')
        self.assertFalse(r['call_links'])
    def test_python_import_alias_resolves_in_method_but_shadow_is_unknown(self):
        s='import asyncio as aio\nclass Cache:\n async def get(self, task):\n  return await aio.shield(task)\n'
        r=analyze_sources({'a.py':s});self.assertIn('asyncio-shield-call',self.rules(r))
        s+='\ndef shadow(aio, task):\n return aio.shield(task)\n'
        r=analyze_sources({'a.py':s});self.assertEqual(self.rules(r).count('asyncio-shield-call'),1)
    def test_python_transaction_and_cleanup(self):
        source='def transaction(connection):\n try:\n  yield connection\n  connection.commit()\n finally:\n  connection.close()\n'
        r=analyze_sources({'a.py':source});self.assertIn('commit-after-yield',self.rules(r));self.assertIn('cleanup-in-finally',self.rules(r))
    def test_async_iteration_return_is_a_question_not_a_cleanup_verdict(self):
        r=analyze_sources({'a.py':'async def first(records):\n async for item in records:\n  if item: return item\n'})
        self.assertIn('early-return-from-async-iteration',self.rules(r))
        self.assertEqual(r['findings'][0]['classification'],'review_hint_not_bug_verdict')
    def test_parse_errors_are_not_clean_results_or_diffs(self):
        a=analyze_sources({'a.py':'async def work():\n await read()\n save()\n'})
        b=analyze_sources({'a.py':'def broken(\n'})
        self.assertEqual(b['status'],'partial');self.assertEqual(b['files'][0]['events'],[])
        d=compare(a,b);self.assertFalse(d['comparable']);self.assertEqual(d['removed_hints'],[])
    def test_typescript_and_jsx_parse_without_running_code(self):
        r=analyze_sources({'a.tsx':'export async function f(x: string) { await fetch(x); return <div>{x}</div>; }'})
        self.assertEqual(r['status'],'parsed');self.assertTrue(any(e['kind']=='await' for e in r['files'][0]['events']))
    def test_missing_node_is_explicit(self):
        r=analyze_sources({'a.js':'fetch("x")'},node='/nonexistent/node')
        self.assertEqual(r['status'],'partial');self.assertEqual(r['files'][0]['status'],'parser_unavailable')
    def test_unsupported_language_is_reported(self):
        r=analyze_sources({'x.go':'package main'})
        self.assertEqual(r['status'],'partial');self.assertEqual(r['files'][0]['status'],'unsupported_language')
    def test_candidate_source_is_never_executed(self):
        code="raise RuntimeError('MUST NOT EXECUTE')\n"
        r=analyze_sources({'a.py':code,'b.js':'throw new Error("MUST NOT EXECUTE");'})
        self.assertEqual(r['status'],'parsed')
    def test_excluded_materials_and_symlinks(self):
        base=self.root/'base';base.mkdir();(base/'app.py').write_text('print(1)\n')
        for name in ['oracle','results','reference','node_modules']:
            (base/name).mkdir();(base/name/'hidden.py').write_bytes(b'\xff invalid; should not be read')
        (base/'link.py').symlink_to(base/'oracle/hidden.py')
        r=scan(base);self.assertEqual([i['path'] for i in r['inputs']],['app.py']);self.assertEqual(r['status'],'partial')
        for path in ['oracle/x.py','../x.py','/tmp/x.py']:
            with self.assertRaises(EvidenceError):analyze_sources({path:'print(1)'})
        (base/'reference/bounded').mkdir()
        with self.assertRaises(EvidenceError):scan(base/'reference/bounded')
    def test_deterministic_and_relocatable(self):
        a=self.root/'a';b=self.root/'b';a.mkdir();b.mkdir()
        for p in [a,b]:(p/'x.py').write_text('async def f():\n await wait()\n publish()\n')
        self.assertEqual(scan(a),scan(a));self.assertEqual(scan(a),scan(b))
    def test_verify_rejects_source_drift_and_overwrite(self):
        base=self.root/'base';base.mkdir();p=base/'x.py';p.write_text('value=1\n');output=self.root/'report.json'
        self.assertEqual(cli.main(['scan',str(base),'--output',str(output)]),0)
        self.assertEqual(cli.main(['verify',str(output),str(base)]),0)
        self.assertEqual(cli.main(['scan',str(base),'--output',str(output)]),1)
        p.write_text('value=2\n');self.assertEqual(cli.main(['verify',str(output),str(base)]),1)
        self.assertEqual(cli.main(['scan',str(base),'--output',str(base/'report.json')]),1)
    def test_html_escapes_source_and_has_no_executable_script(self):
        r=analyze_sources({'a.js':'const x = "<script>alert(1)</script>";'})
        rendered=html_report(r,view='exploratory');self.assertNotIn('<script>',rendered);self.assertIn('&lt;script&gt;',rendered)


if __name__=='__main__':unittest.main()
