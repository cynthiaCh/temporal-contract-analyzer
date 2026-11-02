#!/usr/bin/env python3
"""Run generated, bounded callback scenarios against explicitly supplied modules."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
VERSION = '0.1.0'

CONTRACTS = {
    'wrapper': {'at_most_once', 'repeat_rejected', 'cache_repeated', 'failure_rethrows',
                'preserve_success_after_failure', 'coalesce_pending'},
    'emitter': {'once_delivery', 'snapshot_delivery'},
    'keyed_completion': {'restart_after_failure', 'queued_delivery'},
}


def validate_plan(plan):
    if set(plan) - {'api', 'contracts', 'before', 'after'}:
        raise ValueError('Plan accepts API bindings and contracts, not test code or expected outcomes')
    api = plan['api']
    if api.get('kind') not in CONTRACTS or set(api) - {'kind', 'export', 'construct', 'methods'}:
        raise ValueError('Unsupported API binding')
    if not isinstance(api.get('export', 'default'), str):
        raise ValueError('export must be a property path')
    contracts = plan.get('contracts', {})
    if set(contracts) - CONTRACTS[api['kind']] or any(type(value) is not bool for value in contracts.values()):
        raise ValueError('Contracts must be supported boolean requirements')
    if api['kind'] == 'emitter':
        methods = api.get('methods', {})
        if set(methods) - {'on', 'off', 'emit', 'once'} or not {'on', 'off', 'emit'} <= set(methods):
            raise ValueError('Emitter requires on/off/emit method bindings')
        if not all(isinstance(value, str) and value for value in methods.values()):
            raise ValueError('Emitter methods must be property names')
        if contracts.get('once_delivery') and not methods.get('once'):
            raise ValueError('once_delivery requires a once method binding')
    for side in ['before', 'after']:
        subject = plan[side]
        if (set(subject) - {'root', 'entry', 'module', 'dependencies', 'flow_eraser'} or
                subject.get('module', 'commonjs') not in {'commonjs', 'module'}):
            raise ValueError('Unsupported subject configuration')


def scenarios(api, contracts):
    if api['kind'] == 'wrapper':
        return [dict(id=name, kind=name, tier='baseline' if name == 'repeat' else 'stress')
                for name in ['repeat', 'reentry', 'failure-retry', 'failure-first', 'failure-restore', 'overlap']]
    if api['kind'] == 'emitter':
        result = [dict(id='emit-repeat', kind='emit-repeat', tier='baseline', registration='on', listeners=1)]
        if api['methods'].get('once'):
            result.append(dict(id='once-repeat', kind='once-repeat', tier='baseline', registration='once', listeners=1))
            result += [dict(id='once-reentry-'+str(n), kind='emit-reentry', tier='stress', registration='once', listeners=n)
                       for n in [1, 2]]
        result.append(dict(id='ordinary-reentry', kind='emit-reentry', tier='stress', registration='on', listeners=2))
        result += [dict(id='remove-self-'+str(n), kind='emit-mutation', tier='stress', registration='on', listeners=n,
                        remove='self') for n in [2, 3]]
        result.append(dict(id='remove-next', kind='emit-mutation', tier='stress', registration='on', listeners=2, remove='next'))
        return result
    if api['kind'] == 'keyed_completion':
        return [dict(id=name, kind=name, tier='baseline' if name == 'keyed-repeat' else 'stress')
                for name in ['keyed-repeat', 'keyed-failure', 'keyed-reentry']]
    raise ValueError('Unsupported API kind')


def run_scene(subject, api, scene, node, base, timeout=5):
    root = (base/subject['root']).resolve()
    entry = Path(subject['entry'])
    if entry.is_absolute() or '..' in entry.parts:
        raise ValueError('entry must be relative to root')
    env = dict(os.environ, ELECTRON_RUN_AS_NODE='1')
    with tempfile.TemporaryDirectory(prefix='temporal-probe-') as directory:
        container = Path(directory)
        source = container/'source'
        shutil.copytree(root, source, ignore=shutil.ignore_patterns('.git', 'node_modules', '__pycache__'))
        module = source/entry
        (source/'package.json').write_text(json.dumps({'type': subject.get('module', 'commonjs')}))
        for directory in subject.get('dependencies', []):
            dependency_root = (base/directory).resolve()
            for dependency in dependency_root.iterdir():
                if dependency.is_dir():
                    shutil.copytree(dependency, container/'node_modules'/dependency.name)
        if subject.get('flow_eraser'):
            erased = subprocess.run([node, str((base/subject['flow_eraser']).resolve()), str(module)],
                                    env=env, text=True, capture_output=True, timeout=10)
            if erased.returncode != 0:
                return dict(status='inconclusive', reason='source_preparation_error', stderr=erased.stderr)
            prepared = json.loads(erased.stdout)
            module = source/'probe-erased.mjs'
            module.write_text(prepared['source'])
        if module.suffix == '.ts':
            for path in source.rglob('*.ts'):
                alias = path.with_suffix('')
                if not alias.exists():
                    alias.symlink_to(path.name)
        payload = dict(module=str(module), source_root=str(source), api=api, scenario=scene)
        try:
            result = subprocess.run([node, str(HERE/'runner.mjs')], input=json.dumps(payload),
                text=True, capture_output=True, timeout=timeout, env=env)
        except subprocess.TimeoutExpired:
            return dict(status='inconclusive', reason='timeout')
        if result.returncode != 0:
            return dict(status='inconclusive', reason='runner_exit', stdout=result.stdout, stderr=result.stderr)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return dict(status='inconclusive', reason='invalid_runner_output', stdout=result.stdout, stderr=result.stderr)


def evaluate(scene, result, contracts):
    if result['status'] != 'observed':
        return []
    observation = result['observation']
    operations = observation['operations']
    calls = observation['calls']
    checks = []

    def check(name, condition, labels=()):
        if contracts.get(name):
            checks.append(dict(contract=name, passed=bool(condition), operation_labels=list(labels)))

    check('at_most_once', calls <= 1)
    if scene['kind'] in {'repeat', 'reentry'}:
        label = 'call-1' if scene['kind'] == 'repeat' else 'nested'
        selected = [op for op in operations if op['label'] == label]
        check('repeat_rejected', len(selected) == 1 and selected[0]['status'] == 'threw', [label])
    if scene['kind'] in {'repeat', 'overlap'}:
        returned = [op.get('result') for op in operations if op['status'] == 'returned']
        name = 'cache_repeated' if scene['kind'] == 'repeat' else 'coalesce_pending'
        check(name, calls == 1 and len(returned) == 2 and returned[0] == returned[1], ['call-0', 'call-1'])
    if scene['kind'].startswith('failure-'):
        failing = [op for op in operations if op.get('arguments') == [dict(kind='value', value=1)]]
        check('failure_rethrows', bool(failing) and all(op['status'] == 'threw' for op in failing), [op['label'] for op in failing])
        if scene['kind'] == 'failure-restore':
            success = [op for op in operations if op.get('arguments') == [dict(kind='value', value=0)]]
            check('preserve_success_after_failure', calls == 2 and len(success) == 2 and
                  all(op['status'] == 'returned' for op in success) and success[0]['result'] == success[1]['result'],
                  [op['label'] for op in success])
    if scene.get('registration') == 'once':
        check('once_delivery', all(observation['counts'].get(str(i), 0) == 1 for i in range(scene['listeners'])))
    if scene['kind'] == 'emit-mutation':
        check('snapshot_delivery', all(observation['counts'].get(str(i), 0) == 1 for i in range(scene['listeners'])))
    if scene['kind'] == 'emit-repeat':
        check('snapshot_delivery', all(observation['counts'].get(str(i), 0) == 2 for i in range(scene['listeners'])))
    if scene['kind'] == 'keyed-failure':
        restarted = [op for op in operations if op['label'] == 'register-after']
        check('restart_after_failure', len(restarted) == 1 and restarted[0].get('result') == dict(kind='function'), ['register-after'])
    if scene['kind'] == 'keyed-reentry':
        check('queued_delivery', observation['counts'].get('first') == observation['counts'].get('nested') == 1)
    if scene['kind'] == 'keyed-repeat':
        check('queued_delivery', all(observation['counts'].get(name) == 1 for name in ['first', 'second', 'after']))
    return checks


def compare_plan(plan, node, base, only_scenario=None):
    validate_plan(plan)
    generated = scenarios(plan['api'], plan.get('contracts', {}))
    if only_scenario is not None:
        generated = [scene for scene in generated if scene['id'] == only_scenario]
        if not generated:
            raise ValueError('Unknown generated scenario: '+only_scenario)
    rows = []
    for scene in generated:
        observations = {side: run_scene(plan[side], plan['api'], scene, node, base) for side in ['before', 'after']}
        for result in observations.values():
            result['checks'] = evaluate(scene, result, plan.get('contracts', {}))
        if any(result['status'] != 'observed' for result in observations.values()):
            changed, transition = None, 'inconclusive'
        else:
            changed = observations['before']['observation'] != observations['after']['observation']
            failures = {side: any(not check['passed'] for check in result['checks']) for side, result in observations.items()}
            transition = ('violates_on_both' if all(failures.values()) else
                          'resolved_for_generated_scene' if failures['before'] else
                          'introduced_for_generated_scene' if failures['after'] else
                          'both_meet_checked_contracts' if any(r['checks'] for r in observations.values()) else 'observation_only')
        rows.append(dict(scenario=scene, **observations, behavior_changed=changed, transition=transition))
    return dict(schema_version='temporal-behavior-probe-1', probe_version=VERSION, rows=rows,
                plan=plan, summary=dict(scenarios=len(rows), differences=sum(r['behavior_changed'] is True for r in rows),
                    resolved_scenes=sum(r['transition'] == 'resolved_for_generated_scene' for r in rows),
                    introduced_scenes=sum(r['transition'] == 'introduced_for_generated_scene' for r in rows),
                    violations_on_both=sum(r['transition'] == 'violates_on_both' for r in rows),
                    inconclusive=sum(r['transition'] == 'inconclusive' for r in rows)),
                limitations=['Generated from declared API profiles and contracts; not arbitrary code or contract inference.',
                    'A difference is not automatically a defect. Passing the bounded scenes does not establish safety.',
                    'Candidate code executes locally. Temporary processes are not security sandboxes.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    parser.add_argument('--node', default='/Applications/Visual Studio Code.app/Contents/MacOS/Code')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scenario', help='Replay one generated scenario by its reported id')
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    report = compare_plan(plan, args.node, args.plan.resolve().parent, args.scenario)
    with args.output.open('x') as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    main()
