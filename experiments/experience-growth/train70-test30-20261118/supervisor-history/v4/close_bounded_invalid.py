"""User-authorized closure of bounded model failures; never launches models."""
import argparse
import csv
from datetime import datetime,timezone
import fcntl
import hashlib
import importlib.util
import json
from pathlib import Path
from temporal_contract_analyzer import delegated_review
from temporal_contract_analyzer.tempoevo_v4 import Trajectory

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
def read(path):return json.loads(Path(path).read_text())
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def classify_result(result,stages):
    if result.get('valid') is not False or result.get('failure_type') not in ('model_resource_limit','invalid_output','timeout','tool_policy_denied'):
        raise ValueError('Failure needs individual engineering investigation')
    native=result.get('native_receipt') or {};meter=native.get('native') or {}
    if result.get('failure_type')=='tool_policy_denied':
        denial=result.get('policy_denial') or {}
        if not meter.get('blocked_tools') or not denial.get('tool_name') or not denial.get('reason') or not denial.get('command'):
            raise ValueError('Tool denial needs a recorded guard decision')
    if (result.get('usage_incomplete') is not False or type(result.get('requests')) is not int
            or meter.get('started')!=meter.get('completed') or meter.get('started')!=result['requests']
            or (native.get('archive_status') or {}).get('status')!='OK'
            or native.get('archive_failure_requires_stop') is not False or native.get('transport_cleanup_error')):
        raise ValueError('Unknown usage, incomplete archive or cleanup cannot be auto-closed')
    if not stages or any(s['state']!='settled' or s.get('usage_incomplete') is not False for s in stages):
        raise ValueError('All job model stages must be settled with complete usage')
    return result['failure_type']


def classify(state,result,stages):
    if state.get('status')!='execution_invalid':raise ValueError('Not a terminal solver execution failure')
    failure=classify_result(result,stages)
    if not state.get('stages') or state['stages'][-1].get('status')!='invalid':raise ValueError('Failure stage is not finalized')
    if state['stages'][-1].get('kind') in ('visible','gold'):raise ValueError('Grader failures require separate investigation')
    return failure


def close(run_id,job,apply=False):
    root=(HERE/'runs'/run_id).resolve();assert root.parent==HERE/'runs'
    folder=(root/'jobs'/job).resolve();assert folder.parent==root/'jobs'
    with (root/'writer.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        authorization=read(HERE/'INVALID_HANDLING_AUTHORIZATION.json')
        assert authorization['approved'] is True and authorization['extra_model_calls'] is False
        manifest=read(root/'manifest.json')
        for relative,sha in manifest['bindings'].items():assert digest(REPO/relative)==sha,relative
        trajectory=Trajectory(folder/'trajectory');protocol=trajectory.verify();state=trajectory.state()
        if (folder/'completion.json').exists():raise ValueError('Completed job cannot be overwritten')
        budget=read(root/'balance.json');assert budget['pending_stage_count']==0
        stages=[s for s in budget['stages'] if s['stage_id'].startswith('jobs/'+job+'/')]
        last=state['stages'][-1];stage=trajectory.root/'stages'/last['key']
        result=read(stage/'result.json')
        assert digest(stage/'result.json')==last['result_sha256']
        # The combined engine result retains the underlying native receipt.
        failure=classify(state,result,stages)
        mode=protocol['mode'];source=HERE/'inputs'/('training-order.csv' if mode=='learning' else 'testing-cases.csv')
        row=next(r for r in csv.DictReader(source.open()) if r['case_id']==protocol['task_id'])
        checkpoint=((int(row['rank'])-1)//10)*10 if mode=='learning' else int(job.split('-')[0][1:])
        events=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines() if line]
        start=next(e['at'] for e in events if e['event']=='job_prepared' and e.get('job')==job)
        end=[e['at'] for e in events if e['event']=='stage_settled' and e.get('job')==job][-1]
        elapsed=(datetime.fromisoformat(end)-datetime.fromisoformat(start)).total_seconds()
        spec=importlib.util.spec_from_file_location('frozen_growth',HERE/'run_growth.py');growth=importlib.util.module_from_spec(spec);spec.loader.exec_module(growth)
        review=None
        if apply and mode=='learning':
            review=delegated_review.record_no_update(root/'store',trajectory.root,
                'Bounded solver execution invalid; no additional Action, Gold or learned candidate is authorized. No new guidance is activated.',
                folder/'review/invalid',dict(model='deterministic_controller'))
            growth.immutable(folder/'review/closure.json',review)
        receipt=dict(schema_version='experience-growth-job-receipt-v1',run_id=run_id,job=job,case_id=row['case_id'],mode=mode,
            rank=int(row['rank']),core_case=row['core_case'],source_unit=row['source_unit'],runtime=row['runtime'],checkpoint=checkpoint,
            snapshot_sha256=protocol['memory_snapshot_sha256'],status='execution_invalid',training_accepted=None,gold_valid=False,
            passed=None,verdict=None,attempts=len(state['attempts']),actions_started=sum(s['kind']=='action' for s in state['stages']),review=review,
            approved_entries_after=len(delegated_review.freeze(root/'store')['entries']),requests=sum(s['requests'] for s in stages),
            unknown_usage_requests=0,elapsed_seconds=elapsed,elapsed_basis='job preparation to final stage settlement; supervisor pause excluded',
            closed_at=datetime.now(timezone.utc).isoformat(),trajectory=str(trajectory.root),state_sha256=digest(trajectory.root/'state.json'),
            review_closure_sha256=digest(folder/'review/closure.json') if review else None,
            invalid_reason=failure,invalid_handling_authorization_sha256=digest(HERE/'INVALID_HANDLING_AUTHORIZATION.json'),
            extra_model_calls=0,behavioral_failure=False)
        if apply:
            growth.immutable(folder/'completion.json',receipt)
            event=dict(at=receipt['closed_at'],run_id=run_id,event='job_closed',job=job,case_id=row['case_id'],mode=mode,
                checkpoint=checkpoint,status='execution_invalid',passed=None,gold_valid=False,requests=receipt['requests'],
                reason=failure,authorization_sha256=receipt['invalid_handling_authorization_sha256'],extra_model_calls=0,
                completion_sha256=digest(folder/'completion.json'))
            for path in (root/'events.jsonl',HERE/'EVENTS.jsonl'):
                with path.open('a',encoding='utf8') as stream:stream.write(json.dumps(event)+'\n')
        print(json.dumps(dict(job=job,applied=apply,failure=failure,requests=receipt['requests'],gold_valid=False,extra_model_calls=0)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-id',required=True);parser.add_argument('--job',required=True);parser.add_argument('--apply',action='store_true')
    args=parser.parse_args();close(args.run_id,args.job,args.apply)
