"""Exercise the real scheduling and paid-call receipts using synthetic backends."""
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

REPO=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('growth_run',REPO/'experiments/experience-growth/train70-test30-20261118/run_growth.py')
growth=importlib.util.module_from_spec(spec);spec.loader.exec_module(growth)


class Meter:
    def __init__(self):self.started=set();self.results={}
    def before_stage(self,sid):
        if sid in self.started:return dict(allowed=False,reason='stage_already_registered')
        self.started.add(sid);return dict(allowed=True)
    def observe(self,result,sid):
        if sid in self.results and self.results[sid]!=result:raise ValueError('Changed accounting result')
        self.results[sid]=result


class MeteredRecoveryTests(unittest.TestCase):
    def test_completed_execution_reuses_result_without_paying_again(self):
        with tempfile.TemporaryDirectory() as temp:
            class Run:
                root=Path(temp);budget=Meter()
                run_id='synthetic';lock=threading.RLock()
                def verify(self):pass
                event=growth.Run.event
                def active(self,*args):pass
            class Backend:
                def __init__(self,*args):self.calls=0
                def execute(self,*args):self.calls+=1;return dict(valid=True,requests=1,output={'answer':'synthetic'})
            directory=Path(temp)/'jobs/T01/stage';directory.mkdir(parents=True)
            with patch.object(growth,'NativeV4Backend',Backend):wrapper=growth.MeteredBackend(Run(),{},'T01')
            args=('contract',{'task':'synthetic'},dict(model='synthetic'),dict(requests=12,seconds=600),directory)
            self.assertEqual(wrapper.execute(*args),wrapper.execute(*args))
            self.assertEqual(wrapper.backend.calls,1)

    def test_uncertain_started_execution_is_not_redispatched(self):
        with tempfile.TemporaryDirectory() as temp:
            class Run:
                root=Path(temp);budget=Meter()
                run_id='synthetic';lock=threading.RLock()
                def verify(self):pass
                event=growth.Run.event
                def active(self,*args):pass
            class Backend:
                def __init__(self,*args):self.calls=0
                def execute(self,*args):self.calls+=1;raise RuntimeError('Synthetic lost connection')
            directory=Path(temp)/'stage';directory.mkdir()
            with patch.object(growth,'NativeV4Backend',Backend):wrapper=growth.MeteredBackend(Run(),{},'T01')
            args=('action',{'task':'synthetic'},dict(model='synthetic'),dict(requests=24,seconds=600),directory)
            with self.assertRaises(RuntimeError):wrapper.execute(*args)
            with self.assertRaisesRegex(growth.EvidenceError,'stage_already_registered'):wrapper.execute(*args)
            self.assertEqual(wrapper.backend.calls,1)


class ScheduleTests(unittest.TestCase):
    def test_all_310_jobs_have_training_closure_and_checkpoint_barriers(self):
        with tempfile.TemporaryDirectory() as temp:
            class DummyBudget:
                def audit_balance(self):return {}
                def summary(self):return {}
            class DummyHandle:
                def join(self,**kwargs):pass
                def close(self):pass
            class Scheduled(growth.Run):
                def __init__(self):
                    self.root=Path(temp);self.store='synthetic';self.run_id='synthetic';self.pilot=False
                    self.training=[dict(rank=str(i),case_id='D'+str(i)) for i in range(1,71)]
                    self.testing=[dict(rank=str(i),case_id='T'+str(i)) for i in range(1,31)]
                    self.budget=DummyBudget();self.stopping=threading.Event();self.heartbeat=DummyHandle();self.writer=DummyHandle()
                    self.closed=0;self.rows=[];self.mutex=threading.Lock();self.snapshots={}
                def event(self,*args,**kwargs):pass
                def progress(self,*args,**kwargs):pass
                def results(self):return self.rows
                def job(self,row,mode,checkpoint,snapshot):
                    with self.mutex:
                        if mode=='learning':
                            expected=int(row['rank'])-1
                            assert self.closed==expected
                            # Every previous checkpoint must have all 30 results before next batch.
                            assert sum(r['mode']=='testing' and r['checkpoint']==checkpoint for r in self.rows)==30
                            assert snapshot['sha256']==str(expected)
                            self.closed+=1
                        else:
                            assert self.closed==checkpoint
                            assert snapshot['sha256']==str(checkpoint)
                        self.rows.append(dict(mode=mode,checkpoint=checkpoint,case_id=row['case_id']))
            run=Scheduled()
            with patch.object(growth.delegated_review,'freeze',side_effect=lambda _:dict(sha256=str(run.closed),entries=[])):
                run.execute()
            self.assertEqual(len(run.rows),310)
            self.assertEqual(sum(r['mode']=='learning' for r in run.rows),70)
            self.assertEqual([r['case_id'] for r in run.rows if r['mode']=='learning'],['D'+str(i) for i in range(1,71)])
            self.assertEqual(len(list((run.root/'checkpoints').glob('*.json'))),8)


if __name__=='__main__':unittest.main()
