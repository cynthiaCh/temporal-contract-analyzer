#!/usr/bin/env python3
"""Close paired evidence in both directions and audit frozen observations."""
import json
from pathlib import Path

import run

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'run-01'


def main():
    run.verify_frozen()
    summary = json.loads((RESULTS / 'SUMMARY.json').read_text())
    assert all(row['status'] == 'completed' for row in summary['records'])
    p = {direction: json.loads((RESULTS / f'P-{direction}/report.json').read_text())
         for direction in ['repair', 'regression', 'control']}
    assert p['repair']['summary']['resolved_scenes'] == 2
    assert p['regression']['summary']['introduced_scenes'] == 2
    assert p['control']['summary']['differences'] == 0
    assert all(report['summary']['inconclusive'] == 0 for report in p.values())
    for direction in p:
        for row in p[direction]['rows']:
            for side in ['before', 'after']:
                if row[side]['checks']:
                    assert all(event['source'] and 'EventEmitter.js:' in event['source']
                               for event in row[side]['trace'] if event['event'] == 'callback')
    forward = next(row for row in p['repair']['rows'] if row['scenario']['id'] == 'once-reentry-1')
    assert forward['before']['observation']['counts'] == {'0': 2}
    assert forward['after']['observation']['counts'] == {'0': 1}
    for direction in ['repair', 'regression']:
        status = json.loads((RESULTS / f'P-{direction}/STATUS.json').read_text())
        assert status['result']['paired_replay_matches']

    failures = {}
    for direction in ['repair', 'regression', 'control']:
        for side in ['before', 'after']:
            reports = [json.loads((RESULTS / f'F-{direction}' / side / f'seed-{seed}.json').read_text())
                       for seed in [17, 42, 2027]]
            rows = [report['rows'][0] for report in reports]
            bad = (direction, side) in [('repair', 'before'), ('regression', 'after')]
            assert all(row['failed'] == bad for row in rows)
            assert all(row['classification'] == ('contract_counterexample' if bad else 'no_counterexample') for row in rows)
            if bad:
                assert all(row['replay_matches'] for row in rows)
                assert all(row['evidence']['counts'] == {'0': 2} for row in rows)
                assert all(row['evidence']['frames'][0]['source'] for row in rows)
                failures[direction] = rows[0]

    # The initial harness forwards before-side failures to after. In the reverse
    # direction, before passes: replay the after-discovered input on before too.
    # This adds measurement plumbing only; neither engine nor predicate changes.
    helper = run.load('audit_frozen_fc', run.ROOT / 'external-tests/fast-check-comparison-v1/run.py')
    plan = run.plans()['regression']
    destination = RESULTS / 'F-regression/backward-paired-replay'
    destination.mkdir(exist_ok=False)
    subject = dict(plan['before'], root=str((HERE / plan['before']['root']).resolve()))
    data = failures['regression']['counterexample'][0]
    with helper.prepare(subject) as runtime:
        report = helper.run_worker(dict(runtime, api=plan['api'], contracts=plan['contracts']),
                                   destination, 17, {'once_delivery': [data]})
    paired = report['rows'][0]['paired_replay'][0]['result']
    assert paired['passed'] and paired['counts'] == {'0': 1}
    plain = next(row for row in summary['records'] if row['arm'] == 'N')['result']['records']
    for row in plain:
        bad = row['side'] == 'before'
        assert row['exit_code'] == (1 if bad else 0)
        assert row['observation']['count'] == (2 if bad else 1)
        assert all(event['source'] for event in row['observation']['trace'])
    run.verify_frozen()
    validation = dict(frozen_files_unchanged=True, probe_directions_and_control_verified=True,
                      fast_check_all_three_seeds_verified=True, paired_counterexample_on_both_versions=True,
                      backward_replay_supplement=dict(reason='Initial harness paired before→after only; regression failure is discovered after.',
                                                     additional_worker_processes=1, data=data, before=paired),
                      plain_assert_repeats_match=True, source_frames_present=True,
                      input_fields=13, plan_lines=23, plain_script_lines=20,
                      infrastructure_errors=0, source_or_engine_repair_attempts=0,
                      limitation='Local deterministic audit by the implementer; not an independent review or developer study.')
    run.dump(RESULTS / 'VALIDATION.json', validation)
    print(json.dumps(validation, indent=2))


if __name__ == '__main__':
    main()
