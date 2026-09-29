import tempfile
from pathlib import Path
import unittest

from temporal_contract_analyzer.core import analyze_sources, scan
from temporal_contract_analyzer.layers import coverage_summary, freeze_bundle, verify_bundle


JS = '''function makeSession() {
  let generation = 0;
  function check() {
    const expected = generation;
    request().then(value => {
      if (expected !== generation) return;
      timer = scheduleRetry(() => check());
    });
  }
  useEffect(() => () => { generation++; cancelRetry(timer); }, []);
  return { close() { generation++; }, reopen() { generation += 1; check(); } };
}'''


class LifecycleTests(unittest.TestCase):
    def rules(self, report):
        return {f['rule'] for f in report['findings']}

    def test_callback_retry_boundaries_and_guard_writes_have_source_anchors(self):
        report = analyze_sources({'client.ts': JS})
        self.assertTrue({'continuation-retry-scheduling', 'continuation-lifecycle-boundaries',
                         'continuation-guard-state-review'} <= self.rules(report))
        events = {e['id']: e for e in report['files'][0]['events']}
        guard = next(f for f in report['findings'] if f['rule'] == 'continuation-guard-state-review')
        selected = [events[e] for e in guard['evidence']]
        self.assertTrue(any(e['kind'] == 'guard' for e in selected))
        self.assertTrue(any(e.get('operator') == '++' for e in selected))
        self.assertTrue(any('generation += 1' in e['text'] for e in selected))
        self.assertTrue(any('close' in e['text'] for e in selected))
        retry = next(f for f in report['findings'] if f['rule'] == 'continuation-retry-scheduling')
        self.assertFalse(any(events[e].get('callee') == 'cancelRetry' for e in retry['evidence']))

    def test_renamed_custom_scheduler_and_python_class(self):
        source = '''class Client:
 async def load(self):
  value = await self.transport.read()
  if self.closed: return
  self.loop.call_later(1, self.load)
 def close(self):
  self.closed = True
'''
        report = analyze_sources({'worker.py': source})
        self.assertIn('continuation-lifecycle-boundaries', self.rules(report))
        self.assertIn('continuation-retry-scheduling', self.rules(report))
        self.assertIn('continuation-guard-state-review', self.rules(report))
        self.assertTrue(all(f['scope'] == '<module>/Client' for f in report['findings']
                            if f['rule'].startswith('continuation-')))

    def test_unrelated_functions_comments_and_strings_do_not_form_a_chain(self):
        report = analyze_sources({'a.js': '''function requestWork() { fetch('x').then(render); }
function other() { setTimeout(work); return { close() {} }; }
const text = "request().then(); scheduleRetry(); close();";
// useEffect(() => dispose());
'''})
        self.assertFalse(self.rules(report))

    def test_js_class_namespace_connects_methods_but_separates_other_classes(self):
        report = analyze_sources({'a.ts': '''class Session {
 async read() { const x = await fetch('x'); if (this.closed) return; publish(x); }
 close() { this.closed = true; }
}
class Other { read() { task.then(done); } }
class Unrelated { close() { clearInterval(timer); } }
'''})
        hints = [f for f in report['findings'] if f['rule'].startswith('continuation-')]
        self.assertTrue(hints)
        self.assertTrue(all(f['scope'] == '<module>/Session' for f in hints))

    def test_guards_are_not_required_to_find_a_lifecycle_boundary(self):
        report = analyze_sources({'a.js': 'function session() { request().then(save); return { close() {} }; }'})
        self.assertIn('continuation-lifecycle-boundaries', self.rules(report))
        self.assertNotIn('continuation-guard-state-review', self.rules(report))
        self.assertNotIn('verdict', report)
        self.assertTrue(all(f['classification'] == 'review_hint_not_bug_verdict' for f in report['findings']))

    def test_close_only_timer_cancellation_is_not_a_retry_schedule(self):
        report = analyze_sources({'a.js': 'function session() { task.then(done); return { close() { clearRetry(); cancelRetry(); } }; }'})
        self.assertNotIn('continuation-retry-scheduling', self.rules(report))

    def test_download_development_case_has_nonempty_shared_frozen_selection(self):
        root = Path(__file__).resolve().parents[1]
        report = scan(root/'case-clusters/download-polling-restoration/arms/download-polling-restoration-react18/base')
        counts = coverage_summary(report)
        self.assertTrue(counts['has_substantive_report'])
        self.assertGreater(counts['selected_locations'], 0)
        self.assertTrue(counts['within_limit'])
        self.assertTrue(any(f['path'].endswith('usePreparation.js') for f in report['findings']))
        self.assertTrue(any(f['path'].endswith('useBackgroundPreparation.js') for f in report['findings']))
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory)/'frozen'
            manifest = freeze_bundle(report, bundle)
            self.assertEqual(manifest, verify_bundle(bundle))
            self.assertEqual(counts['selected_locations'], len(manifest['selected_locations']))
            self.assertEqual(counts['layers']['review']['chars'], manifest['layers']['review']['chars'])

    def test_empty_selection_and_report_length_are_explicit(self):
        counts = coverage_summary(analyze_sources({'x.py': 'value = 1\n'}))
        self.assertFalse(counts['has_substantive_report'])
        self.assertEqual(counts['review_hints'], 0)
        self.assertEqual(counts['selected_locations'], 0)
        self.assertGreater(counts['layers']['review']['chars'], 0)
        self.assertTrue(counts['within_limit'])
        self.assertFalse(coverage_summary(analyze_sources({'x.ts': JS}), max_chars=1)['within_limit'])


if __name__ == '__main__':
    unittest.main()
