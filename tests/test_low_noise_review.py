"""Presentation checks: source evidence, suppression and raw-data preservation."""
import copy
import io
import json
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

from temporal_contract_analyzer import cli
import unittest

from temporal_contract_analyzer.core import analyze_sources, compare
from temporal_contract_analyzer.report import markdown, html_report
from temporal_contract_analyzer.review import focused_review

LATE = '''function wrap(deliver) {
 let active;
 return function entry() {
  if (active) return active;
  active = deliver();
 };
}'''


class LowNoiseReviewTests(unittest.TestCase):
    def scan(self, source=LATE):
        return analyze_sources({'a.js': source})

    def test_complete_late_write_shown_without_changing_raw_evidence(self):
        report = self.scan()
        original = copy.deepcopy(report)
        review = focused_review(report)
        self.assertEqual(len(review['cards']), 1)
        self.assertEqual({e['kind'] for e in review['cards'][0]['evidence']}, {'guard', 'call', 'write'})
        self.assertEqual(report, original)

    def test_early_and_unknown_writes_are_not_warnings(self):
        for source, reason in [
            (LATE.replace('active = deliver();', 'active = true; deliver();'), 'write_before_call'),
            (LATE.replace('active = deliver();', 'deliver();'), 'not_established'),
        ]:
            with self.subTest(reason=reason):
                review = focused_review(self.scan(source))
                self.assertEqual(review['cards'], [])
                self.assertEqual(review['summary']['suppressed_by_reason'][reason], 1)

    def test_missing_or_uncertain_evidence_is_hidden(self):
        for change in ['relation', 'event', 'uncertainty', 'file_status']:
            report = self.scan()
            finding = next(f for f in report['findings'] if 'state_publication' in f)
            if change == 'relation':
                report['relations'] = []
            elif change == 'event':
                finding['state_publication']['write'] = 'missing'
            elif change == 'uncertainty':
                finding['state_publication']['uncertainties'] = ['unknown']
            else:
                report['files'][0]['status'] = 'parse_error'
            with self.subTest(change=change):
                review = focused_review(report)
                self.assertEqual(review['cards'], [])
                self.assertEqual(review['summary']['suppressed_by_reason']['incomplete_evidence'], 1)

    def test_duplicate_evidence_merges_but_distinct_states_do_not(self):
        report = self.scan()
        finding = next(f for f in report['findings'] if 'state_publication' in f)
        duplicate = copy.deepcopy(finding)
        duplicate['id'] = 'duplicate'
        report['findings'].append(duplicate)
        review = focused_review(report)
        self.assertEqual(len(review['cards']), 1)
        self.assertEqual(review['summary']['merged_findings'], 1)
        duplicate['state_publication']['state'] = 'other'
        self.assertEqual(len(focused_review(report)['cards']), 2)

    def test_broad_rules_remain_available_only_in_exploratory_view(self):
        report = self.scan('function f(c){ c.connect(); c.addEventListener("x", handler); }')
        self.assertTrue(report['findings'])
        self.assertEqual(focused_review(report)['cards'], [])
        self.assertNotIn('### hint-', markdown(report))
        self.assertIn('### hint-', markdown(report, view='exploratory'))

    def test_comparison_keeps_early_write_as_context_without_safe_verdict(self):
        result = compare(self.scan(), self.scan(LATE.replace('active = deliver();', 'active = true; deliver();')))
        text = markdown(result)
        self.assertIn('write_before_call', text)
        self.assertIn('卡片减少不等于已修复', text)
        self.assertIn('## 修改前', text)
        self.assertIn('## 修改后', text)

    def test_parse_failure_stays_visible_when_no_cards(self):
        report = self.scan('function broken(')
        self.assertIn('partial', markdown(report))
        self.assertIn('a.js：parse_error', markdown(report))

    def test_html_escapes_focused_evidence(self):
        report = self.scan(LATE.replace('deliver()', 'deliver("<script>alert(1)</script>")'))
        text = html_report(report)
        self.assertNotIn('<script>', text)
        self.assertIn('&lt;script&gt;', text)

    def test_cli_json_keeps_raw_evidence_and_exploratory_restores_all_hints(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'a.js'
            path.write_text('function f(c){ c.connect(); c.addEventListener("x", handler); }')
            outputs = {}
            for fmt, view in [('json', 'focused'), ('md', 'focused'), ('md', 'exploratory')]:
                with redirect_stdout(io.StringIO()) as output:
                    code = cli.main(['scan', directory, '--format', fmt, '--view', view])
                self.assertEqual(code, 0)
                outputs[(fmt, view)] = output.getvalue()
            self.assertTrue(json.loads(outputs[('json', 'focused')])['findings'])
            self.assertNotIn('### hint-', outputs[('md', 'focused')])
            self.assertIn('### hint-', outputs[('md', 'exploratory')])

    def test_snippets_are_bounded_with_explicit_truncation(self):
        report = self.scan(LATE.replace('deliver()', 'deliver("' + 'x' * 400 + '")'))
        evidence = focused_review(report)['cards'][0]['evidence']
        self.assertTrue(any(e['truncated'] for e in evidence))
        self.assertTrue(all(len(e['text']) <= 240 for e in evidence))
        self.assertIn('截短', markdown(report))


if __name__ == '__main__':
    unittest.main()
