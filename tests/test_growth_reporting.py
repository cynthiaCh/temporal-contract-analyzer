"""Missing/invalid measurements cannot silently become behavioral failures."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('growth_report',Path(__file__).resolve().parents[1]/'experiments/experience-growth/train70-test30-20261118/export_results.py')
report=importlib.util.module_from_spec(spec);spec.loader.exec_module(report)


class ReportingTests(unittest.TestCase):
    def test_partial_checkpoint_keeps_unknown_gap_and_exclusive_outcomes(self):
        rows=[dict(completed=True,gold_valid=True,passed=True,execution_invalid=False),
              dict(completed=True,gold_valid=True,passed=False,execution_invalid=False),
              dict(completed=False,gold_valid=False,passed=None,execution_invalid=True)]
        result=report.aggregate(rows,30)
        self.assertIsNone(result['final_accuracy'])
        self.assertEqual(result['pass_over_valid'],.5)
        self.assertEqual((result['passed'],result['behavioral_failed'],result['execution_invalid'],result['unfinished']),(1,1,1,27))
        self.assertEqual(result['observed_pass_over_30_progress'],1/30)


if __name__=='__main__':unittest.main()
