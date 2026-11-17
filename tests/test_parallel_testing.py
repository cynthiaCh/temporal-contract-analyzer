"""The test queue uses synthetic workers only, never providers or model processes."""
import importlib.util
from pathlib import Path
import threading
import time
import unittest

path=Path(__file__).resolve().parents[1]/'tools/tempoevo-docker/run_testing.py'
spec=importlib.util.spec_from_file_location('parallel_testing',path)
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


class ParallelTestingTests(unittest.TestCase):
    def test_four_workers_overlap_and_results_remain_in_frozen_order(self):
        lock=threading.Lock();barrier=threading.Barrier(4);active=0;peak=0;snapshots=[]
        def execute(job):
            nonlocal active,peak
            with lock:active+=1;peak=max(peak,active)
            if job['rank']<=4:barrier.wait(timeout=5)
            time.sleep((11-job['rank'])*0.001)
            with lock:active-=1
            return dict(job,status='scored',gold_passed=True)
        jobs=[dict(case_id='case-'+str(n),rank=n) for n in range(1,11)]
        rows=runner.schedule(jobs,4,execute,lambda rows:snapshots.append(list(rows)))
        self.assertEqual(peak,4);self.assertEqual(active,0)
        self.assertEqual([r['rank'] for r in rows],list(range(1,11)))
        self.assertEqual([len(x) for x in snapshots],list(range(1,11)))

    def test_eight_workers_overlap(self):
        barrier=threading.Barrier(8);lock=threading.Lock();active=0;peak=0
        def execute(job):
            nonlocal active,peak
            with lock:active+=1;peak=max(peak,active)
            barrier.wait(timeout=5)
            with lock:active-=1
            return dict(job,status='scored',gold_passed=True)
        runner.schedule([dict(case_id=str(n),rank=n) for n in range(8)],8,execute,lambda rows:None)
        self.assertEqual(peak,8)

    def test_capacity_fallback_is_bounded_and_not_triggered_by_bad_request(self):
        events=[];capacity=runner.Capacity(8,True,events.append)
        capacity.acquire();capacity.release(True);self.assertEqual(capacity.limit,6)
        capacity.acquire();capacity.release(True);self.assertEqual(capacity.limit,4)
        capacity.acquire();capacity.release(True);self.assertEqual(capacity.limit,4)
        self.assertEqual([x['workers'] for x in events],[6,4])
        self.assertFalse(runner.provider_capacity_error(['Bad Request','request budget exhausted']))
        self.assertTrue(runner.provider_capacity_error(['HTTP429 rate_limit_exceeded']))

    def test_worker_error_does_not_abort_other_cases_or_disappear_from_denominator(self):
        def execute(job):
            if job['rank']==2:raise RuntimeError('synthetic worker failure')
            return dict(job,status='scored',gold_passed=job['rank']==1,requests=1)
        jobs=[dict(case_id='case-'+str(n),rank=n) for n in (1,2,3)]
        rows=runner.schedule(jobs,4,execute,lambda rows:None);result=runner.summarize(rows,3)
        self.assertEqual(result['recorded_cases'],3);self.assertEqual(result['passed'],1)
        self.assertEqual(result['failed'],1);self.assertEqual(result['unscored'],1)
        self.assertEqual(result['queue_errors'],1);self.assertTrue(result['usage_incomplete'])

    def test_worker_bound_and_explicit_execution_are_enforced(self):
        for workers in (0,9,-1,True):
            with self.assertRaises(ValueError):runner.schedule([],workers,lambda job:None,lambda rows:None)
        with self.assertRaises(SystemExit):runner.main(['--root','/never-created'])


if __name__=='__main__':unittest.main()
