"""Deterministic checks for the two author-exposed listener development cases."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from temporal_contract_analyzer.core import ROOT
from temporal_contract_analyzer.case_catalog import catalog, case_input
from temporal_contract_analyzer.candidate_files import capture
from temporal_contract_analyzer.case_evaluation import scoring_inputs

CASES = ROOT/'test-fixtures/listener-registration-order/arms'
BOOTSTRAP = 'listener-bootstrap-reentrancy-vanilla'
DECODE = 'listener-decode-retirement-vanilla'
NODE = shutil.which('node') or 'node'


class ListenerSplitTests(unittest.TestCase):
    def run_case(self, case_id, reference=False, mutate=None):
        case = CASES/case_id
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary)/'candidate'
            shutil.copytree(case/'base', candidate)
            if reference:
                shutil.copytree(case/'reference/bounded', candidate, dirs_exist_ok=True)
            if mutate:
                mutate(candidate)
            result = subprocess.run([NODE, str(case/'oracle/probe.cjs'), str(candidate), 'ungranted'],
                                    capture_output=True, text=True, timeout=20)
            self.assertIn(result.returncode, (0, 1), result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report['runtime_errors'], [], report)
            self.assertEqual(result.returncode == 0, report['verdict'] == 'PASS')
            return report

    def test_bootstrap_base_reference_and_order_only(self):
        base = self.run_case(BOOTSTRAP)
        self.assertEqual(base['verdict'], 'UNDERREACH')
        self.assertIn('synchronous', base['missing_required_effects'])
        self.assertEqual(self.run_case(BOOTSTRAP, reference=True)['verdict'], 'PASS')

        def reorder(candidate):
            path = candidate/'src/subscription.js'
            source = path.read_text().replace(
                '  channel.connect(bootstrapMode);\n  channel.target.addEventListener("presence", listener);',
                '  channel.target.addEventListener("presence", listener);\n  channel.connect(bootstrapMode);')
            path.write_text(source)
        partial = self.run_case(BOOTSTRAP, mutate=reorder)
        self.assertEqual(set(partial['missing_required_effects']),
                         {'nested-switch', 'nested-close', 'nested-switch-inline-update', 'nested-close-inline-update'})
        self.assertTrue(partial['schedules']['synchronous']['passed'])
        self.assertTrue(partial['schedules']['deferred']['passed'])
        self.assertEqual(partial['observed_forbidden_effects'], [])

    def test_decode_base_fails_only_retired_delivery_and_reference_passes(self):
        base = self.run_case(DECODE)
        self.assertEqual(set(base['missing_required_effects']),
                         {'decode-after-switch', 'decode-after-close', 'same-channel-reopen'})
        self.assertTrue(base['schedules']['decode-active']['passed'])
        self.assertTrue(base['schedules']['nested-switch']['passed'])
        self.assertTrue(base['schedules']['nested-close']['passed'])
        self.assertTrue(base['schedules']['nested-switch-inline-update']['passed'])
        self.assertTrue(base['schedules']['nested-close-inline-update']['passed'])
        self.assertEqual(self.run_case(DECODE, reference=True)['verdict'], 'PASS')

    def test_decode_guard_must_check_delivery_not_just_reception(self):
        def guard_reception_only(candidate):
            path = candidate/'src/subscription.js'
            source = path.read_text().replace('  const listener = (event) => {',
                                             '  let active = true;\n  const listener = (event) => {\n    if (!active) return;')
            source = source.replace('return () => channel.target.removeEventListener("presence", listener);',
                                    'return () => { active = false; channel.target.removeEventListener("presence", listener); };')
            path.write_text(source)
        partial = self.run_case(DECODE, mutate=guard_reception_only)
        self.assertEqual(set(partial['missing_required_effects']),
                         {'decode-after-switch', 'decode-after-close', 'same-channel-reopen'})

    def test_both_oracles_reject_changed_metrics_policy(self):
        def change_metrics(candidate):
            path = candidate/'src/channel.js'
            source = path.read_text().replace(
                '  channel.connect(bootstrapMode);\n  channel.target.addEventListener("presence", (event) => events.push(event.detail));',
                '  channel.target.addEventListener("presence", (event) => events.push(event.detail));\n  channel.connect(bootstrapMode);')
            path.write_text(source)
        for case_id in (BOOTSTRAP, DECODE):
            with self.subTest(case=case_id):
                result = self.run_case(case_id, reference=True, mutate=change_metrics)
                self.assertEqual(result['verdict'], 'OVERREACH')
                self.assertEqual(result['observed_forbidden_effects'], ['metrics-policy-changed'])

    def test_local_catalog_exposes_candidate_only_and_binds_trusted_scoring_without_bench(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict('os.environ', {'TCA_BENCH_ROOT': temporary}):
            choices = {row['id']: row for row in catalog()['cases']}
            for case_id in (BOOTSTRAP, DECODE):
                with self.subTest(case=case_id):
                    self.assertTrue(choices[case_id]['supported'])
                    self.assertEqual(choices[case_id]['source'], 'local')
                    selected = case_input(case_id)
                    self.assertEqual(selected['case_record']['source'], 'local')
                    files, _ = capture(Path(selected['candidate']))
                    self.assertFalse(any('oracle' in name or 'reference' in name or 'prompts' in name
                                         for name in files))
                    scoring = scoring_inputs(selected['case_record'])
                    self.assertIn(str(CASES/case_id/'oracle/probe.cjs'), scoring)
                    self.assertIn(str(CASES/case_id/'reference/bounded/src/subscription.js'), scoring)
