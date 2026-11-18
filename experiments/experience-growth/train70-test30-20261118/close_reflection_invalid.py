"""Archive a proven rejected success reflection, preserving its valid training PASS."""
import argparse
import csv
import fcntl
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import run_growth as growth
import close_bounded_invalid as bounded
from temporal_contract_analyzer import delegated_review,experience_reflection
from temporal_contract_analyzer.tempoevo_v4 import Trajectory
from temporal_contract_analyzer._session_runtime.schema_validator import validate
from temporal_contract_analyzer.core import EvidenceError

ERROR='Implementation failure alone does not justify changing experience'

def close(run_id,job,apply=False):
    root=growth.HERE/'runs'/run_id;folder=root/'jobs'/job
    assert root.resolve().parent==growth.HERE/'runs' and folder.resolve().parent==root/'jobs'
    with (root/'writer.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for name,digest in growth.read(root/'manifest.json')['bindings'].items():
            assert growth.file_sha(growth.REPO/name)==digest,name
        trajectory=Trajectory(folder/'trajectory');protocol=trajectory.verify();state=trajectory.state()
        assert protocol['mode']=='learning' and state['status']=='execution_invalid'
        assert state['error']==repr(EvidenceError(ERROR))
        assert state['training_accepted'] is True and state['gold_result']['valid'] is True and state['gold_result']['passed'] is True
        assert not (folder/'completion.json').exists() and not (folder/'review/closure.json').exists()
        assert not (trajectory.root/'candidate-pool/success.json').exists()
        assert all(s['status']=='complete' for s in state['stages']) and state['stages'][-1]['key']=='extract'
        stage=trajectory.root/'stages/extract';result=growth.read(stage/'result.json');payload=growth.read(stage/'input.json')
        assert result['valid'] is True and growth.file_sha(stage/'result.json')==state['stages'][-1]['result_sha256']
        learned=result['output'];validate(learned,payload['schema'])
        try:experience_reflection.plan(learned['experience'],learned['update'],payload['related_experiences'],len(state['attempts']))
        except EvidenceError as error:assert str(error)==ERROR
        else:raise AssertionError('Original semantic rejection not reproduced')
        ledger=growth.read(root/'balance.json');assert ledger['pending_stage_count']==0 and not ledger['incomplete_usage']
        stages=[s for s in ledger['stages'] if s['stage_id'].startswith('jobs/'+job+'/')]
        bounded.classify_result(dict(result,valid=False,failure_type='invalid_output'),stages)
        snapshot=delegated_review.freeze(root/'store')
        assert snapshot['sha256']==protocol['memory_snapshot_sha256']
        row=next(r for r in csv.DictReader((growth.HERE/'inputs/training-order.csv').open()) if r['case_id']==protocol['task_id'])
        evidence=dict(job=job,layer='frozen_reflection_semantics',error=ERROR,original_error_reproduced=True,
            raw_native_valid=True,raw_output_schema_valid=True,update=learned['update'],
            result_sha256=growth.file_sha(stage/'result.json'),state_sha256=growth.file_sha(trajectory.root/'state.json'),
            tool_sha256=growth.file_sha(Path(__file__)),raw_result_unchanged=True,raw_state_unchanged=True,
            training_score_preserved=True,extra_model_calls=0,extra_gold_calls=0,new_guidance_activated=False)
        if apply:
            growth.immutable(root/'engineering-observations'/(job+'-reflection-semantic-invalid.json'),evidence)
            review=delegated_review.record_no_update(root/'store',trajectory.root,
                'Success reflection rejected by existing semantic validation: '+ERROR+'. No answer repair, candidate activation or additional model call. Original valid training PASS retained.',
                folder/'review/invalid',dict(model='deterministic_controller'))
            review=dict(review,outcome='review_execution_invalid_no_update',review_execution_invalid=True,evidence=evidence)
            growth.immutable(folder/'review/closure.json',review)
            receipt=dict(schema_version='experience-growth-job-receipt-v1',run_id=run_id,job=job,case_id=row['case_id'],mode='learning',
                rank=int(row['rank']),core_case=row['core_case'],source_unit=row['source_unit'],runtime=row['runtime'],checkpoint=((int(row['rank'])-1)//10)*10,
                snapshot_sha256=protocol['memory_snapshot_sha256'],status='review_execution_invalid',training_accepted=True,
                gold_valid=True,passed=True,verdict=state['gold_result']['verdict'],attempts=len(state['attempts']),review=review,
                approved_entries_after=len(snapshot['entries']),requests=sum(s['requests'] for s in stages),unknown_usage_requests=0,
                elapsed_seconds=None,closed_at=growth.now(),trajectory=str(trajectory.root),state_sha256=growth.file_sha(trajectory.root/'state.json'),
                review_closure_sha256=growth.file_sha(folder/'review/closure.json'),review_execution_invalid=True,
                review_invalid_reason='reflection_semantic_invalid',extra_model_calls=0,extra_gold_calls=0)
            growth.immutable(folder/'completion.json',receipt)
            event=dict(at=receipt['closed_at'],run_id=run_id,event='job_closed',job=job,case_id=row['case_id'],mode='learning',
                checkpoint=receipt['checkpoint'],status=receipt['status'],passed=True,gold_valid=True,approved_entries=len(snapshot['entries']),review_failure=evidence)
            for path in (root/'events.jsonl',growth.HERE/'EVENTS.jsonl'):
                with path.open('a',encoding='utf8') as stream:stream.write(growth.json.dumps(event)+'\n')
        print(growth.json.dumps(dict(job=job,applied=apply,semantic_rejection_reproduced=True,training_passed=True,
                                   approved_entries=len(snapshot['entries']),requests=sum(s['requests'] for s in stages),extra_model_calls=0)))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-id',required=True)
    parser.add_argument('--job',required=True);parser.add_argument('--apply',action='store_true')
    args=parser.parse_args();close(args.run_id,args.job,args.apply)
