#!/usr/bin/env python3
"""Development feasibility campaign; no project-specific test functions."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = ROOT/'external-tests/unseen-small-implementations-v1'
ENGINE = ROOT/'tools/temporal-behavior-probe'
spec = importlib.util.spec_from_file_location('behavior_probe', ENGINE/'probe.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--node', default='/Applications/Visual Studio Code.app/Contents/MacOS/Code')
    args = parser.parse_args()
    for path, expected in json.loads((DATA/'INPUT_HASHES.json').read_text()).items():
        assert hashlib.sha256((DATA/path).read_bytes()).hexdigest() == expected, path
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    cases = {c['id']: c for c in json.loads((DATA/'CASES.json').read_text())['cases']}

    def subject(id):
        case = cases[id]
        result = dict(root=str(DATA/'snapshots'/id), entry=case['entry'],
            module='module' if case['entry'].endswith('.ts') else 'commonjs',
            dependencies=[str(DATA/'dependencies')])
        if (DATA/'snapshots'/id/case['entry']).read_text().startswith('// @flow'):
            result['flow_eraser'] = str(DATA/'erase-flow.cjs')
        return result

    definitions = [
        ('eventemitter3', 'eventemitter3-before', 'eventemitter3-fixed',
         dict(kind='emitter',construct=True,methods=dict(on='on',off='removeListener',emit='emit',once='once')),
         dict(once_delivery=True,snapshot_delivery=True), 'once_delivery'),
        ('mitt', 'mitt-before', 'mitt-fixed',
         dict(kind='emitter',methods=dict(on='on',off='off',emit='emit')),
         dict(snapshot_delivery=True), 'snapshot_delivery'),
        ('memoize-one-historical', 'memoize-one-before', 'memoize-one-fixed',dict(kind='wrapper'),
         dict(cache_repeated=True,failure_rethrows=True), 'failure_rethrows'),
        ('p-memoize', 'p-memoize-before', 'p-memoize-fixed',dict(kind='wrapper'),
         dict(cache_repeated=True,failure_rethrows=True,coalesce_pending=True), 'coalesce_pending'),
        ('inflight', 'inflight-before', 'inflight-fixed',dict(kind='keyed_completion'),
         dict(restart_after_failure=True,queued_delivery=True), 'restart_after_failure'),
        ('once-control', 'once-control', 'once-control',dict(kind='wrapper'),
         dict(at_most_once=True,cache_repeated=True), None),
        ('once-strict-control', 'once-control', 'once-control',dict(kind='wrapper',export='default.strict'),
         dict(at_most_once=True,repeat_rejected=True), None),
        ('memoize-one-control', 'memoize-one-control', 'memoize-one-control',dict(kind='wrapper'),
         dict(cache_repeated=True,failure_rethrows=True,preserve_success_after_failure=True), None),
        ('mitt-control', 'mitt-control', 'mitt-control',dict(kind='emitter',methods=dict(on='on',off='off',emit='emit')),
         dict(snapshot_delivery=True), None),
        ('memoize-control', 'memoize-control', 'memoize-control',dict(kind='wrapper'),
         dict(cache_repeated=True,failure_rethrows=True,preserve_success_after_failure=True), None),
    ]
    plans = []
    for name, before, after, api, contracts, target in definitions:
        plan = dict(api=api,contracts=contracts,before=subject(before),after=subject(after))
        probe.validate_plan(plan)
        folder=out/name;folder.mkdir();dump(folder/'plan.json',plan)
        plans.append(dict(name=name,before=before,after=after,plan=plan,target_contract=target))
    # Freeze API/contract choices before running any generated scenario.
    dump(out/'EVALUATION_PLAN.json',dict(plans=plans,
        data_role='Previously inspected development cases, not a new held-out evaluation.',
        baseline='Ordinary sequential scenes, not an LLM or competitive testing baseline.',
        generation='Only API bindings/contracts passed to engine; no labels, patches, test functions or case identifiers.'))
    frozen={name:(ENGINE/name).read_text() for name in ['probe.py','runner.mjs']}
    (out/'engine').mkdir()
    for name, source in frozen.items(): (out/'engine'/name).write_text(source)
    rows=[]
    for item in plans:
        folder=out/item['name']
        report=probe.compare_plan(item['plan'],args.node,folder)
        dump(folder/'report.json',report)
        dump(folder/'generated-scenarios.json',[r['scenario'] for r in report['rows']])
        baseline_before=[];stress_before=[];after=[];resolved=[];inconclusive=[]
        for row in report['rows']:
            id=row['scenario']['id']
            dump(folder/(id+'.json'),row)
            for side in ['before','after']:
                failed=[c['contract'] for c in row[side]['checks'] if not c['passed']]
                if side=='after' and failed: after.append(dict(scenario=id,contracts=failed))
                if side=='before' and failed:
                    (baseline_before if row['scenario']['tier']=='baseline' else stress_before).append(dict(scenario=id,contracts=failed))
            if row['transition']=='resolved_for_generated_scene': resolved.append(id)
            if row['transition']=='inconclusive': inconclusive.append(id)
        row=dict(name=item['name'],before=item['before'],after=item['after'],target_contract=item['target_contract'],
            generated_scenarios=len(report['rows']),baseline_violations_before=baseline_before,
            stress_violations_before=stress_before,violations_after=after,resolved_scenes=resolved,
            inconclusive=inconclusive,summary=report['summary'])
        rows.append(row); print(json.dumps(row,ensure_ascii=False),flush=True)
        assert all((ENGINE/name).read_text()==source for name,source in frozen.items())
    dump(out/'summary.json',dict(rows=rows,probe_version=probe.VERSION,
        conclusions_scope='Generated scenario feasibility with manual API/contract input on seen implementations. No general synthesis, unseen effectiveness, novelty or LLM-benefit claim.'))


if __name__ == '__main__':
    main()
