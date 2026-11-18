"""At a settled boundary, retain the old ledger and amend only concurrency 2->4."""
import argparse
from copy import deepcopy
import fcntl
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import run_growth as frozen
from temporal_contract_analyzer.balance_budget import BalanceBudget
from temporal_contract_analyzer.live_budget import _digest


def main(run_id):
    root=frozen.HERE/'runs'/run_id
    assert (root/'STOP_REQUESTED').exists()
    with (root/'writer.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        manifest=frozen.read(root/'manifest.json')
        for name,digest in manifest['bindings'].items():assert frozen.file_sha(frozen.REPO/name)==digest,name
        assert all((root/'jobs'/f'M10-T{i:02d}'/'completion.json').exists() for i in range(1,31))
        old=BalanceBudget(root/'balance.json',authorized_total_cny=None,max_inflight_stages=2,max_requests=30000)
        new=BalanceBudget(root/'balance.json',authorized_total_cny=None,max_inflight_stages=4,max_requests=30000)
        with old._lock():
            before=old._load()
            assert before['pending_stage_count']==0 and not before['incomplete_usage']
            assert not any(s['stage_id'].startswith('jobs/D11/') for s in before['stages'])
            archive=root/'engineering-observations/scheduler-2-to-4'
            archive.mkdir(exist_ok=False)
            (archive/'balance-before.json').write_bytes((root/'balance.json').read_bytes())
            value=deepcopy(before)
            value['policy']=deepcopy(new.policy);value['policy_sha256']=_digest(new.policy)
            changed={k for k in before['policy'] if before['policy'][k]!=value['policy'][k]}
            assert changed=={'max_inflight_stages'}
            for key in before:
                if key not in ('policy','policy_sha256'):assert before[key]==value[key],key
            names=['run_growth_parallel.py','amend_scheduler.py','supervise_growth.py']
            amendment=dict(version='v4-operational-scheduler-2-to-4-v1',at=frozen.now(),run_id=run_id,
                authorization='User requested faster execution on 2026-11-18, after delegating engineering and comparability decisions; no solver method change.',
                original_manifest_sha256=frozen.file_sha(root/'manifest.json'),from_checkpoint=20,
                previous_testing_workers=2,testing_workers=4,training_workers=1,
                previous_ledger_sha256=frozen.file_sha(archive/'balance-before.json'),
                previous_policy=before['policy'],policy=value['policy'],
                scheduler_bindings={name:frozen.file_sha(frozen.HERE/name) for name in names},
                preserved=['All 102 frozen source/input bindings','Original manifest','All historical results and stage usage',
                           'DeepSeek Flash/high','Single-case request/time/Action budgets','70/30 members and training order',
                           'Checkpoint snapshots and test Gold isolation','AI review and strict evidence/schema constraints'],
                comparability='Operational concurrency changed at M20; disclose it in all reports. Model latency/resource competition may affect invalid rates; do not describe all nodes as identical scheduling. No prompt, tool, model capability, output constraint or per-case budget change.',
                extra_model_calls=0,extra_gold_calls=0)
            frozen.immutable(root/'scheduler-amendment.json',amendment)
            new._save(value)
            after=new._load()
            for key in before:
                if key not in ('policy','policy_sha256'):assert before[key]==after[key],key
            event=dict(at=frozen.now(),run_id=run_id,event='scheduler_concurrency_amended',
                       amendment_sha256=frozen.file_sha(root/'scheduler-amendment.json'),from_checkpoint=20,
                       previous_testing_workers=2,testing_workers=4,training_workers=1,extra_model_calls=0)
            for path in (root/'events.jsonl',frozen.HERE/'EVENTS.jsonl'):
                with path.open('a',encoding='utf8') as stream:stream.write(frozen.json.dumps(event)+'\n')
            print(frozen.json.dumps(event))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-id',required=True)
    main(parser.parse_args().run_id)
