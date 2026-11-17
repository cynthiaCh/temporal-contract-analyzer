"""Bounded parallel testing through the public single-trajectory CLI; no learning."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import fcntl
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from temporal_contract_analyzer import archive
from temporal_contract_analyzer.tempoevo_v4 import Trajectory, current_protocol


def load_jobs(root):
    rows = json.loads((root/'batch/progress.json').read_text())
    plan = json.loads((root/'plan.json').read_text())
    if len(rows) != plan['test_cases'] or not rows:
        raise ValueError('Prepared count differs from the frozen test plan')
    jobs, cases, banks = [], set(), set()
    for item in rows:
        if item['status'] != 'prepared' or item['case_id'] in cases:
            raise ValueError('All testing cases must be uniquely prepared')
        trajectory = Path(item['root'])/'trajectory'
        protocol = Trajectory(trajectory).verify()
        if not current_protocol(protocol) or protocol['mode'] != 'testing' or protocol['max_attempts'] != 1:
            raise ValueError('Only current single-submission testing is supported')
        if protocol['learning_policy'] != 'frozen' or protocol.get('training_evaluator') or protocol.get('training_recipe'):
            raise ValueError('Testing cannot use training acceptance or online learning')
        if len(protocol['memory_snapshot']['entries']) != plan['approved_entries']:
            raise ValueError('Testing bank differs from the frozen plan')
        banks.add(protocol['memory_snapshot_sha256']);cases.add(item['case_id'])
        jobs.append(dict(case_id=item['case_id'],rank=item['rank'],trajectory=str(trajectory)))
    if banks != {plan['memory_snapshot_sha256']}:
        raise ValueError('All cases must use the same frozen approved bank')
    return sorted(jobs, key=lambda x: x['rank'])


def provider_capacity_error(messages):
    return any(re.search(r'\b429\b|rate[_ -]?limit|too many concurrent|concurrency limit', str(m), re.I) for m in messages)


def capacity_from_archive(trajectory):
    messages=[]
    for p in trajectory.glob('stages/**/service-errors.json'):
        try:data=json.loads(p.read_text())
        except (OSError,ValueError):continue
        for row in data.get('raw_cli_errors',[]):
            event=row.get('event',{});messages.append(event.get('message') or (event.get('error') or {}).get('message'))
        for row in data.get('failed_request_hooks',[]):messages.append(row.get('event',{}).get('error'))
    return provider_capacity_error(messages)


def result_row(job, exit_code=None, queue_error=None):
    trajectory = Path(job['trajectory'])
    state = json.loads((trajectory/'state.json').read_text())
    path = trajectory/'summary.json'
    report = json.loads(path.read_text()) if path.exists() else {}
    gold = state.get('gold_result') or {}
    stages = state['stages']
    return dict(case_id=job['case_id'],rank=job['rank'],status=state['status'],
                actions=len(state['attempts']),gold_passed=gold.get('passed') if state['status']=='scored' else None,
                gold_verdict=gold.get('verdict'),queue_exit_code=exit_code,queue_error=queue_error,
                requests=sum(s['requests'] for s in stages if type(s.get('requests')) is int),
                known_tokens=report.get('known_tokens',0),usage_incomplete=report.get('usage_incomplete',False),
                unknown_request_stages=[s['key'] for s in stages if s['kind'] in ('routing','selection','contract','action','diagnosis','extract') and type(s.get('requests')) is not int],
                preparation_corrections=report.get('preparation_corrections',0),
                preparation_warnings=state.get('preparation_warnings',[]),
                transport_retries=report.get('transport_retries',0),tool_policy_recoveries=report.get('tool_policy_recoveries',0),
                provider_capacity_error=capacity_from_archive(trajectory),error=state.get('error'))


def execute_job(job, event):
    trajectory = Path(job['trajectory'])
    state = json.loads((trajectory/'state.json').read_text())
    if state['status'] in ('scored','execution_invalid','cancelled'):
        return result_row(job)
    if any(s['status']=='started' for s in state['stages']):
        row=result_row(job,queue_error='Previously started incomplete stage; explicit investigation required')
        row['status']='not_replayed'
        return row
    command=[sys.executable,'-B','-m','temporal_contract_analyzer','tempoevo','run','--root',str(trajectory),'--execute']
    with (trajectory.parent/'testing.log').open('a') as log:
        process=subprocess.Popen(command,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
        event(dict(event='job_started',case_id=job['case_id'],rank=job['rank'],pid=process.pid))
        code=process.wait()
    event(dict(event='job_finished',case_id=job['case_id'],rank=job['rank'],exit_code=code))
    return result_row(job,exit_code=code)


class Capacity:
    def __init__(self, workers, adaptive=False, event=None):
        self.limit=workers;self.active=0;self.peak=0;self.adaptive=adaptive;self.event=event;self.lock=threading.Condition()
    def acquire(self):
        with self.lock:
            self.lock.wait_for(lambda:self.active<self.limit)
            self.active+=1;self.peak=max(self.peak,self.active)
    def release(self, pressure=False):
        with self.lock:
            self.active-=1
            if pressure and self.adaptive and self.limit>4:
                before=self.limit;self.limit=6 if before>6 else 4
                if self.event:self.event(dict(event='concurrency_reduced',previous=before,workers=self.limit,reason='explicit_provider_capacity_error',started_requests_replayed=False))
            self.lock.notify_all()


def schedule(jobs, workers, execute, on_result, adaptive=False, event=None):
    if type(workers) is not int or not 1 <= workers <= 8:
        raise ValueError('Use between one and eight workers')
    capacity=Capacity(workers,adaptive,event)
    def guarded(job):
        capacity.acquire();pressure=False
        try:
            result=execute(job);pressure=result.get('provider_capacity_error',False) or provider_capacity_error([result.get('error'),result.get('queue_error')]);return result
        except Exception as e:
            pressure=provider_capacity_error([str(e)]);raise
        finally:capacity.release(pressure)
    results=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(guarded,job):job for job in jobs}
        for future in as_completed(futures):
            job=futures[future]
            try:row=future.result()
            except Exception as error:
                row=dict(case_id=job['case_id'],rank=job['rank'],status='queue_error',gold_passed=None,
                         actions=0,queue_error=repr(error),queue_exit_code=None,requests=None,known_tokens=0,usage_incomplete=True)
            results.append(row);on_result(sorted(results,key=lambda x:x['rank']))
    if event:event(dict(event='concurrency_summary',initial_workers=workers,final_workers=capacity.limit,peak_active_cases=capacity.peak))
    return sorted(results,key=lambda x:x['rank'])


def summarize(rows, expected):
    return dict(expected_cases=expected,recorded_cases=len(rows),
                passed=sum(r['gold_passed'] is True for r in rows),failed=sum(r['gold_passed'] is False for r in rows),
                execution_invalid=sum(r['status']=='execution_invalid' for r in rows),
                queue_errors=sum(bool(r.get('queue_error')) for r in rows),
                unscored=sum(r['gold_passed'] is None for r in rows),
                model_requests=sum(r.get('requests') or 0 for r in rows),
                known_tokens=sum(r.get('known_tokens') or 0 for r in rows),
                usage_incomplete=any(r.get('usage_incomplete') or r.get('unknown_request_stages') for r in rows),
                preparation_corrections=sum(r.get('preparation_corrections',0) for r in rows),
                experience_updates=False,cases=rows)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--workers',type=int,choices=range(1,9),default=4)
    parser.add_argument('--adaptive-workers',action='store_true',help='Reduce future concurrency8->6->4 on explicit provider capacity errors; never replay requests')
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args(argv)
    if not args.execute:parser.error('--execute is required for model calls')
    root=args.root.resolve()
    with (root/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (root/'completion.json').exists():parser.error('Completed runs are read-only; use a new root')
        jobs=load_jobs(root);started=time.time();event_lock=threading.Lock()
        def event(value):
            value=dict(at_utc=datetime.now(timezone.utc).isoformat(),**value)
            with event_lock:
                with (root/'queue-events.jsonl').open('a') as output:output.write(json.dumps(value)+'\n')
        event(dict(event='queue_started',workers=args.workers,cases=len(jobs)))
        def progress(rows):archive.atomic_json(root/'testing-progress.json',summarize(rows,len(jobs)))
        progress([])
        results=schedule(jobs,args.workers,lambda job:execute_job(job,event),progress,adaptive=args.adaptive_workers,event=event)
        summary=dict(summarize(results,len(jobs)),workers=args.workers,
                     adaptive_workers=args.adaptive_workers,elapsed_seconds=time.time()-started,finished_at_utc=datetime.now(timezone.utc).isoformat())
        archive.atomic_json(root/'completion.json',summary)
        target=REPO/'experiments/testing-runs'/root.name;target.mkdir(parents=True,exist_ok=True)
        for name in ['completion.json','testing-progress.json','queue-events.jsonl']:shutil.copyfile(root/name,target/name)
        print(json.dumps({k:v for k,v in summary.items() if k!='cases'}),flush=True)
        return int(bool(summary['unscored'] or summary['queue_errors'] or any(r.get('queue_exit_code') not in (None,0) for r in results)))


if __name__=='__main__':sys.exit(main())
