"""Supervise the unchanged frozen runner under the explicit invalid-case decision."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
def read(path):return json.loads(Path(path).read_text())
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def module(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-id',required=True);args=parser.parse_args()
    root=(HERE/'runs'/args.run_id).resolve();assert root.parent==HERE/'runs'
    files=['supervise_growth.py','close_bounded_invalid.py','recover_unlaunched.py','INVALID_HANDLING_AUTHORIZATION.json','close_review_invalid.py','REVIEW_INVALID_AUTHORIZATION.json','run_growth_parallel.py']
    bound={name:digest(HERE/name) for name in files}
    policy=HERE/'supervisor-policies'/(args.run_id+'-supervisor-v6.json')
    value=dict(version='bounded-invalid-supervisor-v6',bindings=bound,
        policy='Continue fixed trajectories after verified bounded invalid execution; no extra model calls or Gold; unlaunched stage recovery preserves completed results and original remaining budget.')
    if policy.exists():assert read(policy)==value,'Supervisor identity changed'
    else:module('run_growth').immutable(policy,value)
    closer=module('close_bounded_invalid');recovery=module('recover_unlaunched');review_closer=module('close_review_invalid')
    while True:
        if (root/'STOP_REQUESTED').exists():raise RuntimeError('Explicit stop request; no automatic resume')
        assert {name:digest(HERE/name) for name in files}==bound
        run=subprocess.run([sys.executable,'-B',str(HERE/'run_growth_parallel.py'),'--run-id',args.run_id])
        if run.returncode==0:return 0
        if (root/'STOP_REQUESTED').exists():raise RuntimeError('Explicit stop request; no automatic resume')
        ledger=read(root/'balance.json')
        if ledger['pending_stage_count'] or ledger['incomplete_usage']:
            raise RuntimeError('Unsettled/unknown accounting requires investigation; no automatic resume')
        bounded=[];unlaunched=[];review_invalid=[]
        for state_path in sorted((root/'jobs').glob('*/trajectory/state.json')):
            folder=state_path.parent.parent
            if (folder/'completion.json').exists():continue
            state=read(state_path)
            job=folder.name
            if state['status']!='execution_invalid':
                if review_closer.failed_reviews(folder):
                    review_closer.close(args.run_id,job,False);review_invalid.append(job)
                continue
            if recovery.controller_stopped(state,state_path.parent):unlaunched.append(job)
            else:
                closer.close(args.run_id,job,False);bounded.append(job)
        if not bounded and not review_invalid:raise RuntimeError('No authorized bounded failure explains this stop; inspect raw evidence')
        recover=[sys.executable,'-B',str(HERE/'recover_unlaunched.py'),'--run-id',args.run_id,'--jobs',*unlaunched]
        if unlaunched:subprocess.run(recover,check=True)
        for job in bounded:closer.close(args.run_id,job,True)
        for job in review_invalid:review_closer.close(args.run_id,job,True)
        if unlaunched:subprocess.run(recover+['--apply'],check=True)
        event=dict(at=datetime.now(timezone.utc).isoformat(),run_id=args.run_id,event='authorized_supervisor_resume',
            bounded_invalid_closed=bounded,review_invalid_closed=review_invalid,unlaunched_reconciled=unlaunched,extra_model_calls=0,supervisor_policy_sha256=digest(policy))
        for path in (root/'events.jsonl',HERE/'EVENTS.jsonl'):
            with path.open('a',encoding='utf8') as stream:
                stream.write(json.dumps(event)+'\n');stream.flush();os.fsync(stream.fileno())
        print(json.dumps(event),flush=True)


if __name__=='__main__':raise SystemExit(main())
