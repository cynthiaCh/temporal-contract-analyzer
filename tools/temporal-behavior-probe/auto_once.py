#!/usr/bin/env python3
"""Propose narrow callback-wrapper bindings without executing subject modules."""
import argparse
import importlib.util
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
NODE = shutil.which('node') or 'node'


def discover(path, node=NODE):
    if path.suffix not in {'.js', '.cjs'}:
        return {'status': 'unsupported', 'reason': 'only_commonjs_js_or_cjs'}
    result = subprocess.run([node, str(HERE / 'discover_once.cjs')],
                            input=json.dumps({'source': path.read_text()}),
                            text=True, capture_output=True, timeout=15,
                            env=dict(os.environ, ELECTRON_RUN_AS_NODE='1'))
    if result.returncode:
        return {'status': 'unsupported', 'reason': 'discovery_unavailable', 'detail': result.stderr[-1500:]}
    return json.loads(result.stdout)


def propose(before, after, node=NODE):
    subjects = {'before': before.resolve(), 'after': after.resolve()}
    discoveries = {side: discover(path, node) for side, path in subjects.items()}
    report = {'status': 'unsupported', 'subject_executed': False, 'discovery': discoveries,
              'requirement': 'At most one callback entry during one synchronous reentry; user confirmation required.'}
    if all(found['status'] == 'candidate' for found in discoveries.values()):
        report['status'] = 'confirmation_required'
        report['candidate_plan'] = dict(api={'kind': 'wrapper'}, contracts={'at_most_once': True},
            **{side: dict(root=str(path.parent), entry=path.name, module='commonjs')
               for side, path in subjects.items()})
    return report


def execute(report, before, after, output, node=NODE):
    if report['status'] != 'confirmation_required':
        return report
    spec = importlib.util.spec_from_file_location('once_probe', HERE / 'probe.py')
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    behavior = probe.compare_plan(report['candidate_plan'], node, Path.cwd(), 'reentry')
    validity = {}
    for row in behavior['rows']:
        for side in ['before', 'after']:
            result = row[side]
            trace = result.get('trace', [])
            outer = next((event['step'] for event in trace if event['event'] == 'invoke' and event['label'] == 'call-0'), None)
            construction_callbacks = any(event['event'] == 'callback' and (outer is None or event['step'] < outer)
                                         for event in trace)
            validity[side] = dict(construction_callback=construction_callbacks,
                                  reentry_attempted=any(event['event'] == 'invoke' and event['label'] == 'nested' for event in trace))
            if construction_callbacks:
                result.update(status='inconclusive', reason='callback_during_factory_setup', checks=[])
        if any(row[side]['status'] != 'observed' for side in ['before', 'after']):
            row.update(transition='inconclusive', behavior_changed=None)
            behavior['summary'].update(inconclusive=1, differences=0, resolved_scenes=0,
                                       introduced_scenes=0, violations_on_both=0)
    report.update(status='inconclusive' if behavior['summary']['inconclusive'] else 'observed',
                  subject_executed=True, confirmation={'at_most_once': True, 'source': 'explicit_cli_flag'},
                  scope='One outer invocation and a synchronous reentry attempt on first callback entry; no entry means no reentry. Numeric argument 0; no safety or liveness claim.',
                  execution_validity=validity,
                  behavior=behavior,
                  replay_command=[sys.executable, str(HERE / 'auto_once.py'), str(before.resolve()), str(after.resolve()),
                                  '--confirm-at-most-once', '--node', node, '--output',
                                  str(output.resolve().with_name(output.stem + '-replay.json'))])
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--node', default=NODE)
    parser.add_argument('--confirm-at-most-once', action='store_true',
                        help='Confirm this requirement and authorize executing the local modules in the bounded reentry scenario')
    args = parser.parse_args()
    with args.output.open('x') as stream:
        report = propose(args.before, args.after, args.node)
        if args.confirm_at_most_once:
            report = execute(report, args.before, args.after, args.output, args.node)
        json.dump(report, stream, indent=2)
        stream.write('\n')
    return 2 if report['status'] == 'unsupported' else 0


if __name__ == '__main__':
    sys.exit(main())
