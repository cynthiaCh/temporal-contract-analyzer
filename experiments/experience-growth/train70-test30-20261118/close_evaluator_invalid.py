"""Close a specifically audited invalid final evaluator; never rerun Gold or model."""
import argparse
import csv
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]

def read(p): return json.loads(p.read_text(encoding='utf8'))
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def close(run_id, job, evidence):
    root = (HERE/'runs'/run_id).resolve()
    folder = (root/'jobs'/job).resolve()
    assert root.parent == HERE/'runs' and folder.parent == root/'jobs'
    evidence = Path(evidence).resolve()
    assert evidence.is_relative_to(root/'engineering-observations')
    audit = read(evidence)
    assert audit['job'] == job and audit['disposition'] == 'retain_frozen_invalid_no_replay'
    with (root/'writer.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (folder/'completion.json').exists()
        for relative, sha in read(root/'manifest.json')['bindings'].items():
            assert digest(REPO/relative) == sha, relative
        state = read(folder/'trajectory/state.json')
        protocol = read(folder/'trajectory/protocol.json')
        assert protocol['mode'] == 'testing' and state['status'] == 'execution_invalid'
        stage = folder/'trajectory/stages/final-gold'
        result = read(stage/'result.json'); raw = read(stage/'raw-result.json')
        assert result['valid'] is False and raw['valid'] is False
        assert raw['error'] == 'Oracle process or schedule did not complete normally'
        score = raw['full_score']
        runtime_errors = score.get('runtime_errors') or [
            dict(schedule=name, error=value['runtimeError'])
            for name, value in score.get('schedules', {}).items() if value.get('runtimeError')]
        assert raw['probe_exit_code'] == 2 and runtime_errors
        assert digest(stage/'raw-result.json') == audit['raw_result_sha256']
        assert digest(folder/'trajectory/state.json') == audit['state_sha256']
        ledger = read(root/'balance.json')
        assert ledger['pending_stage_count'] == 0 and not ledger['incomplete_usage']
        stages = [s for s in ledger['stages'] if s['stage_id'].startswith('jobs/'+job+'/')]
        assert stages and all(s['state'] == 'settled' and s['usage_incomplete'] is False for s in stages)
        events = [json.loads(line) for line in (root/'events.jsonl').read_text().splitlines() if line]
        gold = [e for e in events if e['event'] == 'evaluation_finished' and e.get('job') == job and e.get('kind') == 'gold']
        assert len(gold) == 1 and gold[0]['valid'] is False
        row = next(r for r in csv.DictReader((HERE/'inputs/testing-cases.csv').open()) if r['case_id'] == protocol['task_id'])
        at = datetime.now(timezone.utc).isoformat()
        receipt = dict(schema_version='experience-growth-job-receipt-v1',run_id=run_id,job=job,case_id=row['case_id'],mode='testing',
            rank=int(row['rank']),core_case=row['core_case'],source_unit=row['source_unit'],runtime=row['runtime'],checkpoint=int(job.split('-')[0][1:]),
            snapshot_sha256=protocol['memory_snapshot_sha256'],status='execution_invalid',training_accepted=None,gold_valid=False,
            passed=None,verdict=None,attempts=len(state['attempts']),review=None,approved_entries_after=len(read(folder/'trajectory/memory-snapshot.json')['entries']),
            requests=sum(s['requests'] for s in stages),unknown_usage_requests=0,elapsed_seconds=None,closed_at=at,
            trajectory=str(folder/'trajectory'),state_sha256=digest(folder/'trajectory/state.json'),review_closure_sha256=None,
            invalid_reason='final_gold_candidate_runtime_error',gold_attempted=True,behavioral_failure=False,extra_model_calls=0,extra_gold_calls=0,
            engineering_evidence_sha256=digest(evidence))
        spec=importlib.util.spec_from_file_location('growth',HERE/'run_growth.py');growth=importlib.util.module_from_spec(spec);spec.loader.exec_module(growth)
        growth.immutable(folder/'completion.json',receipt)
        event=dict(at=at,run_id=run_id,event='job_closed',job=job,case_id=row['case_id'],mode='testing',checkpoint=receipt['checkpoint'],
            status='execution_invalid',passed=None,gold_valid=False,requests=receipt['requests'],reason=receipt['invalid_reason'],
            completion_sha256=digest(folder/'completion.json'),engineering_evidence_sha256=digest(evidence),extra_model_calls=0,extra_gold_calls=0)
        for path in (root/'events.jsonl',HERE/'EVENTS.jsonl'):
            with path.open('a',encoding='utf8') as stream:stream.write(json.dumps(event)+'\n')
        print(json.dumps(event),flush=True)

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id',required=True);parser.add_argument('--job',required=True);parser.add_argument('--evidence',required=True)
    args=parser.parse_args();close(args.run_id,args.job,args.evidence)
