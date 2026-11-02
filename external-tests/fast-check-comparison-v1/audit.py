#!/usr/bin/env python3
"""Check recorded searches, paired replay and preservation of existing inputs."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=HERE/'run-02'
summary=json.loads((OUT/'summary.json').read_text())
rows=summary['rows']
assert len(rows)==10
target_rows=[r for r in rows if r['target_contract']]
controls=[r for r in rows if not r['target_contract']]
assert len(target_rows)==len(controls)==5
assert all(r['target_counterexample_obtained'] and r['target_before_counterexample_passes_after'] for r in target_rows)
assert all(not r['before_failed_contracts'] and not r['after_failed_contracts'] for r in controls)
property_records=0;failures=0;paired=0;shrink_steps=0
for row in rows:
    for side in ['before','after']:
        for seed in summary['seeds']:
            report=json.loads((OUT/row['name']/side/f'seed-{seed}.json').read_text())
            assert report['fast_check_version']=='4.10.2'
            for prop in report['rows']:
                property_records+=1
                assert not prop['interrupted']
                assert prop['classification']!='inconclusive_error'
                if row['target_contract'] and side=='before' and prop['contract']==row['target_contract']:
                    assert prop['failed']
                if prop['failed']:
                    failures+=1;shrink_steps+=prop['numShrinks']
                    assert prop['replay_matches'] and prop['evidence']['frames']
                    assert all(frame['source'] and '<subject>/' in frame['source'] for frame in prop['evidence']['frames'])
                    assert f'Shrunk {prop["numShrinks"]} time(s)' in prop['native_failure_output']
                if side=='after' and prop['contract']==row['target_contract']:
                    assert prop.get('paired_replay')
                    for replay in prop['paired_replay']:
                        paired+=1;assert replay['result']['passed']
assert property_records==126 and failures==18 and shrink_steps==25 and paired==15
assert (OUT/'baseline.mjs').read_text()==(HERE/'baseline.mjs').read_text()
prototype=ROOT/'external-tests/behavior-probe-feasibility-v1/run-02/engine'
for name in ['probe.py','runner.mjs']:
    assert (prototype/name).read_text()==(ROOT/'tools/temporal-behavior-probe'/name).read_text()
data=ROOT/'external-tests/unseen-small-implementations-v1'
for path,expected in json.loads((data/'INPUT_HASHES.json').read_text()).items():
    assert hashlib.sha256((data/path).read_bytes()).hexdigest()==expected,path
for path,expected in json.loads((data/'frozen-tool/FILES.json').read_text()).items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,path
for name in ['run.py','fetch_dependencies.py','audit.py']:ast.parse((HERE/name).read_text())
result=dict(plans=10,seeds=3,property_search_records=property_records,known_issue_pairs_obtained=5,
            successful_target_paired_replays=paired,failed_property_records=failures,
            all_failed_records_replayed=True,records_with_callback_source_frames=failures,
            successful_shrink_steps=shrink_steps,passing_control_plans=5,
            num_runs=sum(r['num_runs'] for r in rows),prototype_and_prior_inputs_unchanged=True,
            conclusions='No obtaining/localization advantage established; comprehension and task effort unmeasured.',
            assurance='Deterministic local checks; no independent external audit or user study.')
destination=OUT/'VALIDATION.json';assert not destination.exists()
destination.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
