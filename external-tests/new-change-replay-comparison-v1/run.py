#!/usr/bin/env python3
"""Frozen-engine migration comparison; all per-project bindings live in plan.json."""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NODE = '/Applications/Visual Studio Code.app/Contents/MacOS/Code'
ENV = dict(os.environ, ELECTRON_RUN_AS_NODE='1')


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_frozen():
    manifest = json.loads((HERE / 'FROZEN.json').read_text())
    for relative, expected in manifest.items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected, relative


def plans():
    original = json.loads((HERE / 'plan.json').read_text())
    reverse = copy.deepcopy(original)
    reverse['before'], reverse['after'] = reverse['after'], reverse['before']
    control = copy.deepcopy(original)
    control['before'] = copy.deepcopy(control['after'])
    return dict(repair=original, regression=reverse, control=control)


def run_probe(destination, plan):
    probe = load('frozen_probe', ROOT / 'tools/temporal-behavior-probe/probe.py')
    dump(destination / 'plan.json', plan)
    report = probe.compare_plan(plan, NODE, HERE)
    dump(destination / 'report.json', report)
    candidates = [row for row in report['rows'] if any(not check['passed']
                  for side in ['before', 'after'] for check in row[side]['checks'])]
    replay = None
    if candidates:
        witness = candidates[0]
        replay = probe.compare_plan(plan, NODE, HERE, witness['scenario']['id'])
        dump(destination / 'replay.json', replay)
        # Compare full semantic observations, excluding no trace content from the saved reports.
        matches = all(witness[side]['observation'] == replay['rows'][0][side]['observation']
                      for side in ['before', 'after'])
    else:
        matches = None
    return dict(summary=report['summary'], witness=candidates[0]['scenario'] if candidates else None,
                paired_replay_matches=matches,
                runner_processes=2 * len(report['rows']) + (2 if replay else 0),
                failing_scenarios=[row['scenario']['id'] for row in candidates])


def run_fast_check(destination, plan):
    helper = load('frozen_fc', ROOT / 'external-tests/fast-check-comparison-v1/run.py')
    absolute = copy.deepcopy(plan)
    for side in ['before', 'after']:
        absolute[side]['root'] = str((HERE / plan[side]['root']).resolve())
    dump(destination / 'plan.json', plan)
    paired = {}
    records = {}
    for side in ['before', 'after']:
        folder = destination / side
        folder.mkdir()
        records[side] = []
        with helper.prepare(absolute[side]) as runtime:
            for seed in [17, 42, 2027]:
                report = helper.run_worker(dict(runtime, api=plan['api'], contracts=plan['contracts']),
                                           folder, seed, paired if side == 'after' else None)
                records[side].append(report)
        if side == 'before':
            for report in records[side]:
                for row in report['rows']:
                    if row['failed']:
                        data = row['counterexample'][0]
                        bucket = paired.setdefault(row['contract'], [])
                        if data not in bucket:
                            bucket.append(data)
    rows = {side: [row for report in reports for row in report['rows']] for side, reports in records.items()}
    return dict(worker_processes=6, before_failures=sum(row['failed'] for row in rows['before']),
                after_failures=sum(row['failed'] for row in rows['after']),
                shrunk_witnesses=paired,
                native_replays_match=all(row.get('replay_matches', True) for side in rows for row in rows[side]),
                paired_after_results=[replay for row in rows['after'] for replay in row.get('paired_replay', [])],
                initial_search_num_runs=sum(row['numRuns'] for side in rows for row in rows[side]))


def run_plain(destination):
    records = []
    for side in ['before', 'after']:
        for repeat in [1, 2]:
            command = [NODE, str(HERE / 'plain-assert.cjs'), str(HERE / 'snapshots' / side / 'EventEmitter.js')]
            start = time.monotonic()
            result = subprocess.run(command, env=ENV, text=True, capture_output=True, timeout=10)
            prefix = destination / f'{side}-{repeat}'
            prefix.with_suffix('.stdout').write_text(result.stdout)
            prefix.with_suffix('.stderr').write_text(result.stderr)
            observation = json.loads(result.stdout) if result.stdout.strip() else None
            record = dict(side=side, repeat=repeat, command=command, exit_code=result.returncode,
                          elapsed_seconds=round(time.monotonic() - start, 4), observation=observation)
            dump(prefix.with_suffix('.json'), record)
            records.append(record)
    return dict(worker_processes=4, records=records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--arm', choices=['P', 'F', 'N', 'all'], default='all')
    args = parser.parse_args()
    verify_frozen()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    jobs = [(arm, direction, plan) for arm in ['P', 'F'] for direction, plan in plans().items()]
    jobs.append(('N', 'snapshots', None))
    records = []
    for arm, direction, plan in jobs:
        if args.arm not in [arm, 'all']:
            continue
        destination = out / f'{arm}-{direction}'
        destination.mkdir()
        start = time.monotonic()
        row = dict(arm=arm, direction=direction, attempt=1)
        try:
            row['result'] = (run_probe(destination, plan) if arm == 'P' else
                             run_fast_check(destination, plan) if arm == 'F' else run_plain(destination))
            row['status'] = 'completed'
        except Exception:
            row['status'] = 'infrastructure_error'
            row['error'] = traceback.format_exc()
        row['elapsed_seconds'] = round(time.monotonic() - start, 4)
        dump(destination / 'STATUS.json', row)
        records.append(row)
        print(json.dumps(dict(arm=arm, direction=direction, status=row['status']), ensure_ascii=False), flush=True)
    verify_frozen()
    dump(out / 'SUMMARY.json', dict(records=records, frozen_inputs_unchanged=True,
                                  timing_scope='Mechanical durations only; not developer effort or comparable coverage.'))


if __name__ == '__main__':
    main()
