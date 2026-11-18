"""Close explicitly authorized bounded review failures without new guidance or calls."""
import argparse
import csv
from datetime import datetime, timezone
import fcntl
import importlib.util
import json
from pathlib import Path
from temporal_contract_analyzer import delegated_review
from temporal_contract_analyzer.tempoevo_v4 import Trajectory

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
def module(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=module('close_bounded_invalid')
read=base.read
digest=base.digest


def failed_reviews(folder):
    return [p for p in (Path(folder)/'review').glob('*/result.json')
            if (p.parent/'started.json').exists() and review_validation_failure(p) is not None]


def review_validation_failure(path):
    result=read(path)
    if result.get('valid') is False:return dict(layer='native',error=result.get('error'))
    if result.get('valid') is not True:return None
    from temporal_contract_analyzer._session_runtime.schema_validator import validate
    payload=read(path.parent/'input.json')
    try:validate(result.get('output'),payload['schema'])
    except ValueError as error:return dict(layer='controller_schema',error=str(error))
    return None


def close(run_id,job,apply=False):
    root=(HERE/'runs'/run_id).resolve();assert root.parent==HERE/'runs'
    folder=(root/'jobs'/job).resolve();assert folder.parent==root/'jobs'
    with (root/'writer.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        auth=read(HERE/'REVIEW_INVALID_AUTHORIZATION.json')
        assert auth['approved'] is True and auth['extra_model_calls'] is False
        for path,sha in read(root/'manifest.json')['bindings'].items():assert digest(REPO/path)==sha,path
        trajectory=Trajectory(folder/'trajectory');protocol=trajectory.verify();state=trajectory.state()
        assert protocol['mode']=='learning' and state.get('finalized') is True
        assert not (folder/'completion.json').exists() and not (folder/'review/closure.json').exists()
        assert state['status']!='execution_invalid' and all(s['status']=='complete' for s in state['stages'])
        gold=state.get('gold_result') or {};assert gold.get('valid') is True
        failed=failed_reviews(folder);assert len(failed)==1
        result_path=failed[0];result=read(result_path)
        metered=read(result_path.parent/'execution/metered-result.json')
        assert metered['result']==result and metered['model']==protocol['model']
        assert metered['limits']==dict(requests=12,seconds=600)
        assert not (result_path.parent/'decision.json').exists()
        budget=read(root/'balance.json');assert budget['pending_stage_count']==0 and not budget['incomplete_usage']
        stages=[s for s in budget['stages'] if s['stage_id'].startswith('jobs/'+job+'/')]
        validation_failure=review_validation_failure(result_path)
        assert validation_failure is not None
        # Preserve the raw native receipt. Classify the existing downstream
        # rejection, without editing or reinterpreting the model's answer.
        classified=result if result.get('valid') is False else dict(result,valid=False,failure_type='invalid_output')
        failure=base.classify_result(classified,stages)
        snapshot=delegated_review.freeze(root/'store')
        assert snapshot['sha256']==protocol['memory_snapshot_sha256'],'Unexpected active guidance change before review closure'
        row=next(r for r in csv.DictReader((HERE/'inputs/training-order.csv').open()) if r['case_id']==protocol['task_id'])
        evidence=dict(failure_type=failure,stage=result_path.parent.relative_to(folder).as_posix(),
            result_sha256=digest(result_path),authorization_sha256=digest(HERE/'REVIEW_INVALID_AUTHORIZATION.json'),
            extra_model_calls=0,training_score_preserved=True,new_guidance_activated=False,
            validation_failure=validation_failure,raw_native_valid=result.get('valid'),raw_result_unchanged=True)
        if apply:
            growth=module('run_growth')
            review=delegated_review.record_no_update(root/'store',trajectory.root,
                'User-authorized no-update closure: bounded AI experience-stage execution failed. No valid expert summary or content acceptance is claimed; original training scores are retained.',
                folder/'review/invalid',dict(model='deterministic_controller'))
            review=dict(review,outcome='review_execution_invalid_no_update',review_execution_invalid=True,evidence=evidence)
            growth.immutable(folder/'review/closure.json',review)
            at=datetime.now(timezone.utc).isoformat()
            receipt=dict(schema_version='experience-growth-job-receipt-v1',run_id=run_id,job=job,case_id=row['case_id'],mode='learning',
                rank=int(row['rank']),core_case=row['core_case'],source_unit=row['source_unit'],runtime=row['runtime'],checkpoint=((int(row['rank'])-1)//10)*10,
                snapshot_sha256=protocol['memory_snapshot_sha256'],status='review_execution_invalid',training_accepted=state['training_accepted'],
                gold_valid=True,passed=gold['passed'],verdict=gold.get('verdict'),attempts=len(state['attempts']),review=review,
                approved_entries_after=len(snapshot['entries']),requests=sum(s['requests'] for s in stages),unknown_usage_requests=0,
                elapsed_seconds=None,closed_at=at,trajectory=str(trajectory.root),state_sha256=digest(trajectory.root/'state.json'),
                review_closure_sha256=digest(folder/'review/closure.json'),review_execution_invalid=True,review_invalid_reason=failure)
            growth.immutable(folder/'completion.json',receipt)
            event=dict(at=at,run_id=run_id,event='job_closed',job=job,case_id=row['case_id'],mode='learning',checkpoint=receipt['checkpoint'],
                status='review_execution_invalid',passed=gold['passed'],gold_valid=True,approved_entries=len(snapshot['entries']),review_failure=evidence)
            for path in (root/'events.jsonl',HERE/'EVENTS.jsonl'):
                with path.open('a',encoding='utf8') as stream:stream.write(json.dumps(event)+'\n')
        print(json.dumps(dict(job=job,applied=apply,failure=failure,training_gold_valid=True,training_passed=gold['passed'],requests=sum(s['requests'] for s in stages),extra_model_calls=0)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-id',required=True);parser.add_argument('--job',required=True);parser.add_argument('--apply',action='store_true')
    args=parser.parse_args();close(args.run_id,args.job,args.apply)
