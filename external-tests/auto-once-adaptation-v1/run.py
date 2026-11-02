#!/usr/bin/env python3
"""Fixed new-source migration and engine-independent automatic-plan check."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
AUTO = ROOT / 'tools/temporal-behavior-probe/auto_once.py'
NODE = '/Applications/Visual Studio Code.app/Contents/MacOS/Code'
ENV = dict(os.environ, ELECTRON_RUN_AS_NODE='1')


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def frozen():
    for relative, expected in json.loads((HERE / 'FROZEN.json').read_text()).items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected, relative


def leaves(value):
    return sum(map(leaves, value.values())) if isinstance(value, dict) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    frozen()
    out = args.output.resolve()
    out.mkdir(exist_ok=False)
    spec = importlib.util.spec_from_file_location('independent_fc', ROOT / 'external-tests/fast-check-comparison-v1/run.py')
    fc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fc)
    rows = []
    cases = [('release-dependency', 'source', 'source'), ('upstream-refactor', 'old', 'refactor'),
             ('control', 'old', 'old'), ('artificial-regression', 'old', 'artificial-regression')]
    for name, before, after in cases:
        folder = out / name
        folder.mkdir()
        paths = [HERE / 'snapshots' / version / 'index.js' for version in [before, after]]
        command = [sys.executable, '-B', str(AUTO), *map(str, paths), '--output', str(folder / 'proposal.json')]
        first = subprocess.run(command, capture_output=True, text=True, timeout=20)
        dump(folder / 'proposal-command.json', command)
        assert first.returncode == 0, first.stderr
        proposal = json.loads((folder / 'proposal.json').read_text())
        assert proposal['status'] == 'confirmation_required' and not proposal['subject_executed']
        command[-1] = str(folder / 'report.json')
        command.append('--confirm-at-most-once')
        result = subprocess.run(command, capture_output=True, text=True, timeout=25)
        dump(folder / 'execution-command.json', command)
        (folder / 'stderr.txt').write_text(result.stderr)
        assert result.returncode == 0, result.stderr
        report = json.loads((folder / 'report.json').read_text())
        replay_process = subprocess.run(report['replay_command'], capture_output=True, text=True, timeout=25)
        assert replay_process.returncode == 0, replay_process.stderr
        replay = json.loads((folder / 'report-replay.json').read_text())
        left, right = report['behavior']['rows'][0], replay['behavior']['rows'][0]
        assert left['transition'] == right['transition']
        for side in ['before', 'after']:
            assert left[side]['status'] == right[side]['status']
            if left[side]['status'] == 'observed':
                assert left[side]['observation'] == right[side]['observation']
            else:
                # Error strings contain fresh temporary paths. Compare the actual
                # classification; retain full original errors in both artifacts.
                assert left[side]['reason'] == right[side]['reason']
        oracle = []
        for index, subject in enumerate(paths):
            check = subprocess.run([NODE, str(HERE / 'oracle.cjs'), str(subject)], env=ENV,
                                   capture_output=True, text=True, timeout=10)
            (folder / f'oracle-{index}.stdout').write_text(check.stdout)
            (folder / f'oracle-{index}.stderr').write_text(check.stderr)
            oracle.append(dict(exit=check.returncode, observation=json.loads(check.stdout)))
        dump(folder / 'ORACLE.json', oracle)
        plan = proposal['candidate_plan']
        fc_results = []
        for side in ['before', 'after']:
            destination = folder / ('fast-check-' + side)
            destination.mkdir()
            try:
                with fc.prepare(plan[side]) as runtime:
                    baseline = fc.run_worker(dict(runtime, api=plan['api'], contracts=plan['contracts']),
                                             destination, 17, {'at_most_once': [{'mode': 'reenter', 'times': 2}]})
                fc_results.append(dict(side=side, status='completed', paired=baseline['rows'][0]['paired_replay']))
            except Exception:
                fc_results.append(dict(side=side, status='inconclusive', error=traceback.format_exc()))
        dump(folder / 'FAST_CHECK_STATUS.json', fc_results)
        observed = report['behavior']['rows'][0]
        for index, side in enumerate(['before', 'after']):
            if report['status'] == 'observed':
                expected = oracle[index]['observation']
                assert expected['status'] == 'observed'
                assert observed[side]['observation']['calls'] == expected['count']
                assert fc_results[index]['paired'][0]['result']['counts']['callback'] == expected['count']
            else:
                assert observed[side]['status'] == 'inconclusive'
                assert oracle[index]['observation']['status'] == 'setup_error'
                assert fc_results[index]['status'] == 'inconclusive'
        rows.append(dict(name=name, status=report['status'], transition=observed['transition'],
                         counts={side: observed[side].get('observation', {}).get('calls') for side in ['before', 'after']},
                         generated_plan_leaf_fields=leaves(plan), entered_domain_values=3,
                         generated_replay_matches=True, independent_oracle_agrees=True,
                         baseline_consumes_same_generated_plan=True))
        print(json.dumps(rows[-1]), flush=True)
    frozen()
    dump(out / 'SUMMARY.json', dict(rows=rows, frozen_engines_unchanged=True,
         minimal_manual_plan_leaf_fields=6, explicit_module_manual_plan_leaf_fields=8,
         auto_entered_domain_values=3, output_and_runtime_options_excluded_on_both_sides=True,
         limits=['One new implementation, deliberately selected older dependency-free source.',
                 'Only artificial regression fails the contract; not an upstream bug discovery.',
                 'No human effort, usability, productivity or general accuracy measurement.']))


if __name__ == '__main__':
    main()
