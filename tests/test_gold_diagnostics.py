"""Worker diagnostics must preserve the frozen benchmark's grading decision."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SPEC=importlib.util.spec_from_file_location('gold_diagnostics_fixture',Path(__file__).resolve().parents[1]/'tools/tempoevo-docker/gold.py')
GOLD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GOLD)


class GoldDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.case=Path(self.temp.name);(self.case/'oracle').mkdir()
        (self.case/'oracle/worker.cjs').write_text('// synthetic worker')
        (self.case/'oracle/schedules.json').write_text(json.dumps(dict(schedules=[dict(id='reentrant')])) )

    def probe(self,score,code=1):
        return SimpleNamespace(returncode=code,stdout=json.dumps(score),stderr='')

    def error_score(self):
        return dict(verdict='UNDERREACH',runtime_errors=[dict(schedule='reentrant',error='worker exited 2')],
                    schedules={'reentrant':dict(runtimeError='worker exited 2')})

    def test_worker_stdout_is_retained_without_reclassifying_runtime_error_as_fail(self):
        score=self.error_score();worker=dict(runtimeError='TypeError: navigation is undefined',passed=False)
        with patch.object(GOLD.subprocess,'run',side_effect=[self.probe(score,2),self.probe(worker,2)]) as run:
            result=GOLD.grade(self.case,'/submission','node')
        self.assertFalse(result['valid'])
        self.assertEqual(result['verdict'],'UNDERREACH')
        self.assertEqual(result['full_score'],score)
        self.assertEqual(result['failure_type'],'oracle_runtime_error')
        self.assertEqual(result['runtime_diagnostics'][0]['runtime_error'],worker['runtimeError'])
        self.assertEqual(json.loads(result['runtime_diagnostics'][0]['stdout']),worker)
        self.assertEqual(run.call_args.args[0][-3:],['/submission','reentrant','ungranted'])
        self.assertLessEqual(run.call_args.kwargs['timeout'],5)

    def test_ordinary_pass_and_fail_do_not_replay_workers(self):
        for verdict,code in [('PASS',0),('UNDERREACH',1)]:
            with self.subTest(verdict=verdict),patch.object(GOLD.subprocess,'run',return_value=self.probe(dict(verdict=verdict),code)) as run:
                result=GOLD.grade(self.case,'/submission','node')
                self.assertTrue(result['valid'])
                self.assertEqual(result['passed'],verdict=='PASS')
                self.assertEqual(run.call_count,1)
                self.assertNotIn('runtime_diagnostics',result)

    def test_process_error_is_distinct_from_oracle_worker_error(self):
        with patch.object(GOLD.subprocess,'run',return_value=self.probe(dict(verdict='UNDERREACH'),2)):
            result=GOLD.grade(self.case,'/submission','node')
        self.assertFalse(result['valid'])
        self.assertEqual(result['failure_type'],'infrastructure_error')

    def test_diagnostic_timeout_does_not_change_original_result(self):
        score=self.error_score()
        with patch.object(GOLD.subprocess,'run',side_effect=[self.probe(score,2),subprocess.TimeoutExpired('worker',5)]):
            result=GOLD.grade(self.case,'/submission','node')
        self.assertFalse(result['valid'])
        self.assertEqual(result['full_score'],score)
        self.assertIn('diagnostic_error',result['runtime_diagnostics'][0])

    def test_only_registered_schedule_ids_are_replayed(self):
        score=dict(verdict='UNDERREACH',runtime_errors=[dict(schedule='unknown',error='worker exited 2')])
        with patch.object(GOLD.subprocess,'run',return_value=self.probe(score,2)) as run:
            result=GOLD.grade(self.case,'/submission','node')
        self.assertFalse(result['valid'])
        self.assertEqual(result['runtime_diagnostics'],[])
        self.assertEqual(run.call_count,1)

    def test_expired_diagnostic_budget_starts_no_worker(self):
        with patch.object(GOLD.time,'monotonic',return_value=101),patch.object(GOLD.subprocess,'run') as run:
            self.assertEqual(GOLD.worker_diagnostics(self.case,'/submission','node',self.error_score(),100),[])
        run.assert_not_called()


if __name__=='__main__':unittest.main()
