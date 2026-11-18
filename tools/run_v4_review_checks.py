"""Scoped offline regression for the v4 review snapshot; no provider/Gold calls."""
import json
from pathlib import Path
import runpy
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
names=('test_deepseek_audit.py','test_model_profiles_and_retries.py','test_research_read_policy.py',
       'test_readonly_analysis_roles.py','test_guard_collector_diagnostics.py','test_balance_budget.py',
       'test_delegated_review.py','test_growth_orchestrator.py','test_growth_invalid_closure.py',
       'test_growth_unlaunched_evaluation.py','test_growth_reporting.py','test_central_case_catalog.py')
loader=unittest.TestLoader()
suite=unittest.TestSuite(loader.discover(str(ROOT/'tests'),pattern=name) for name in names)
result=unittest.TextTestRunner(verbosity=1).run(suite)
summary=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
             skipped=len(result.skipped),model_calls=0,gold_calls=0)
print(json.dumps(summary))
if not result.wasSuccessful():raise SystemExit(1)
runpy.run_path(str(ROOT/'experiments/experience-growth/train70-test30-20261118/test_parallel_scheduler.py'),run_name='__main__')
