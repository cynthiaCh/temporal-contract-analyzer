"""Targeted offline tests: scheduling and accounting only; no service or Gold."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import threading
import time
import json
from types import MethodType
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from run_growth_parallel import ParallelRun
from temporal_contract_analyzer.balance_budget import BalanceBudget

def fake_balance():return dict(is_available=True,balance_infos=[dict(currency='CNY',total_balance='200')])
def usage():return dict(valid=True,requests=1,tokens=dict(input_tokens=10,cached_input_tokens=0,
    cache_write_input_tokens=0,output_tokens=2,reasoning_output_tokens=1,total_tokens=12),
    usage_incomplete=False,unknown_usage_requests=0,native_receipt=dict(exit_code=0,infrastructure_valid=True,
    turn_complete=True,archive_failure_requires_stop=False,archive_status=dict(status='OK',errors=[])))

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);(root/'checkpoints').mkdir()
    (root/'scheduler-amendment.json').write_text('{}')
    maxima={}
    for point,workers in ((0,2),(10,2),(20,4),(70,4)):
        snapshot=dict(entries=[] if point==0 else ['frozen-entry'],sha256='fixed-snapshot')
        (root/'checkpoints'/f'M{point}.json').write_text(json.dumps(snapshot))
        run=object.__new__(ParallelRun);run.root=root;run.testing=list(range(30));run.stopping=threading.Event()
        run.event=lambda *args,**kwargs:None
        counts=dict(active=0,maximum=0);seen=[];lock=threading.Lock()
        def job(self,row,mode,n,bank):
            assert mode=='testing' and n==point and bank==snapshot
            with lock:
                counts['active']+=1;counts['maximum']=max(counts['maximum'],counts['active']);seen.append(row)
            time.sleep(0.02)
            with lock:counts['active']-=1
        run.job=MethodType(job,run)
        run.test_checkpoint(point)
        assert sorted(seen)==list(range(30)) and counts['maximum']==workers
        maxima[point]=counts['maximum']
    guard=BalanceBudget(root/'budget.json',authorized_total_cny=None,max_inflight_stages=4,max_requests=30000,fetcher=fake_balance)
    guard.initialize()
    with ThreadPoolExecutor(max_workers=5) as pool:
        admitted=list(pool.map(lambda i:(i,guard.before_stage(f'stage-{i}')['allowed']),range(5)))
    assert sum(ok for _,ok in admitted)==4
    assert guard.summary()['pending_stage_count']==4
    for i,ok in admitted:
        if ok:guard.observe(usage(),f'stage-{i}')
    settled=guard.summary()
    assert settled['requests']==4 and settled['pending_stage_count']==0 and not settled['incomplete_usage']
    print(json.dumps(dict(status='passed',observed_workers=maxima,unique_jobs_per_checkpoint=30,
        four_admitted_fifth_denied=True,settled_requests=4,model_calls=0,gold_calls=0)))
