#!/usr/bin/env python3
"""Replay only the five supplied scenes and check evidence packet consistency."""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    preparation = load('pilot_preparation', HERE / 'prepare.py')
    probe = load('pilot_probe', ROOT / 'tools/temporal-behavior-probe/probe.py')
    gold = json.loads((HERE / 'GOLD.json').read_text())
    replay = HERE / 'run-01/replay'
    replay.mkdir(exist_ok=False)
    checked = []
    for task in gold:
        folder = HERE / 'tasks' / task['task_id']
        a, b, c = [(folder / f'{arm}.txt').read_text() for arm in ['A', 'B', 'C']]
        assert b.startswith(a) and c.startswith(b)
        assert (folder / 'raw-observations.json').read_text().strip() == json.dumps(task['observations'], ensure_ascii=False, indent=2)
        if task['direction'] != 'forward':
            continue
        project = task['project']
        plan_file = preparation.PROBE / project / 'plan.json'
        plan = json.loads(plan_file.read_text())
        for scene_id, engine_id, _ in preparation.CONTRACTS[project][1]:
            report = probe.compare_plan(plan, '/Applications/Visual Studio Code.app/Contents/MacOS/Code', plan_file.parent, engine_id)
            (replay / f'{project}-{engine_id}.json').write_text(json.dumps(report, indent=2) + '\n')
            row = report['rows'][0]
            for side in ['before', 'after']:
                assert row[side]['status'] == 'observed'
                observed = preparation.observation(row[side], project == 'eventemitter3')
                assert observed == task['observations'][scene_id][side], (project, scene_id, side)
                assert preparation.violates(project, observed) == task['scenario_truth'][scene_id][side]
            checked.append(dict(project=project, scenario=engine_id, transition=row['transition']))
    result = dict(replayed_scenes=len(checked), side_executions=2 * len(checked),
                  fresh_observations_match_frozen_gold=True, evidence_packets_are_nested=True, rows=checked)
    (HERE / 'run-01/REPLAY_VALIDATION.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
