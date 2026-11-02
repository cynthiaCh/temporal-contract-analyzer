#!/usr/bin/env python3
"""Prepare anonymized review prompts; labels are never included in packets."""
import difflib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
DATA=ROOT/'external-tests/unseen-small-implementations-v1'
PROBE=ROOT/'external-tests/behavior-probe-feasibility-v1/run-02'
FC=ROOT/'external-tests/fast-check-comparison-v1/run-02'

CONTRACTS={
 'eventemitter3': ('Each registered once listener must run exactly once across the outer and nested dispatch. Evaluate only S1/S2 below; ordinary on listeners are not once listeners.',
   [('S1','once-reentry-1','Register one once listener A. On its first callback, immediately emit the same event once more.'),
    ('S2','once-reentry-2','Register two once listeners A then B. On A\'s first callback, immediately emit the same event once more.')]),
 'p-memoize':('Two immediate same-argument invocations, made before settling the callback promises, must share one underlying evaluation. No synchronous reentry or falsy rejection case is in scope.',
   [('S1','overlap','Call the wrapped function twice with argument 0, without awaiting the first. The injected callback returns a deferred promise. Release all deferred results, then await both calls.')]),
 'memoize-one-historical':('A callback throws on argument 1 and succeeds on argument 0. Every invocation with failing argument 1 must throw, including an identical retry; it must not return undefined or an older successful result. Either retrying or caching the exception is allowed.',
   [('S1','failure-first','Invoke with 1 (callback throws), then invoke with 1 again.'),
    ('S2','failure-retry','Invoke with 0 (success), then 1 (callback throws), then 1 again.')]),
}


def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def observation(result,emitter):
    value=result['observation'];counts=value['counts']
    ordered=[counts[key] for key in sorted(counts,key=lambda k:int(k))] if emitter else [counts.get('callback',0)]
    operations=sorted((op for op in value['operations'] if op['label'].startswith('call-')),key=lambda op:op['label'])
    return dict(counts=ordered,outcomes=[] if emitter else [op['status'] for op in operations],
                source_frames=[event['source'] for event in result['trace'] if event['event']=='callback'])


def violates(project,observed):
    if project=='eventemitter3':return any(count!=1 for count in observed['counts'])
    if project=='p-memoize':return observed['counts']!=[1]
    # S1 has no successful prefix; S2 has exactly one successful prefix.
    outcomes=observed['outcomes']
    return outcomes[-2:]!=['threw','threw']


def main():
    out=HERE/'tasks';out.mkdir(exist_ok=False)
    definitions=json.loads((PROBE/'EVALUATION_PLAN.json').read_text())['plans']
    gold=[];task_order=[]
    for project in ['eventemitter3','p-memoize','memoize-one-historical']:
        definition=next(d for d in definitions if d['name']==project)
        report=json.loads((PROBE/project/'report.json').read_text())
        req,scenes=CONTRACTS[project]
        for reverse in [False,True]:
            task_id=f'T{len(gold)+1:02d}';task_order.append(task_id)
            folder=out/task_id;folder.mkdir()
            side_map={'before':'after','after':'before'} if reverse else {'before':'before','after':'after'}
            sources={side:(Path(definition['plan'][original]['root'])/definition['plan'][original]['entry']).read_text()
                     for side,original in side_map.items()}
            baseline_scene='once-repeat' if project=='eventemitter3' else 'repeat'
            baseline=next(r for r in report['rows'] if r['scenario']['id']==baseline_scene)
            smoke={side:observation(baseline[original],project=='eventemitter3') for side,original in side_map.items()}
            raw={};truth={};valid_refs=['REQ-1','SMOKE']
            for id,scene_id,description in scenes:
                row=next(r for r in report['rows'] if r['scenario']['id']==scene_id)
                raw[id]=dict(description=description)
                for side,original in side_map.items():
                    raw[id][side]=observation(row[original],project=='eventemitter3')
                    valid_refs.append(f'OBS-{id}-{side}')
                truth[id]={side:violates(project,raw[id][side]) for side in ['before','after']}
            baseline_text=json.dumps({side:dict(counts=value['counts'],outcomes=value['outcomes']) for side,value in smoke.items()},indent=2)
            common=f'TASK {task_id}\nREQ-1: {req}\nPermitted scenarios:\n'
            common+='\n'.join(f'{id}: {description}' for id,_,description in scenes)
            common+='\nSMOKE: ordinary sequential success calls/dispatches only, with no reentry/failure/overlap. Observed results:\n'+baseline_text
            for side,source in sources.items():
                common+='\nSOURCE '+side+':\n'+'\n'.join(f'{side}:L{i}: {line}' for i,line in enumerate(source.splitlines(),1))+'\n'
                valid_refs += [f'{side}:L{i}' for i in range(1,len(source.splitlines())+1)]
            diff=''.join(difflib.unified_diff(sources['before'].splitlines(keepends=True),sources['after'].splitlines(keepends=True),fromfile='before',tofile='after'))
            common+='\nUNIFIED DIFF:\n'+diff+'\n'
            native={}
            for side,original in side_map.items():
                native[side]='\n'.join(path.read_text() for path in sorted((FC/project/original).glob('seed-17-*.txt')))
            evidence='\nADDITIONAL EXECUTION MATERIAL\n'
            evidence+='Native property report (an observed test failure is not an answer about whether the change introduced it):\n'+json.dumps(native,indent=2)
            evidence+='\nPaired raw observations; counts ordered by listener ID or the single callback; event outcome arrays intentionally empty:\n'+json.dumps(raw,indent=2)
            index='\nREDUNDANT EVIDENCE INDEX (no additional execution or verdict)\n'
            for id,_,_ in scenes:
                index+=f'{id}: before counts {raw[id]["before"]["counts"]}, outcomes {raw[id]["before"]["outcomes"]}; after counts {raw[id]["after"]["counts"]}, outcomes {raw[id]["after"]["outcomes"]}. References OBS-{id}-before, OBS-{id}-after.\n'
                for side in ['before','after']:
                    lines=sorted(set(int(m.group(1)) for frame in raw[id][side]['source_frames'] if frame
                        for m in [re.search(r':(\d+):\d+\)?$',frame)] if m))
                    for line in lines:
                        index+=f'{side}:L{line}: {sources[side].splitlines()[line-1]}\n'
            for arm,body in [('A',common),('B',common+evidence),('C',common+evidence+index)]:
                (folder/(arm+'.txt')).write_text(body)
            dump(folder/'raw-observations.json',raw)
            gold.append(dict(task_id=task_id,project=project,direction='reverse' if reverse else 'forward',
                introduces_violation=any(not t['before'] and t['after'] for t in truth.values()),
                after_has_violation=any(t['after'] for t in truth.values()),scenario_truth=truth,
                observations=raw,valid_refs=valid_refs))
    dump(HERE/'GOLD.json',gold)
    dump(HERE/'TASK_ORDER.json',task_order)
    schema=dict(type='object',properties=dict(answers=dict(type='array',items=dict(type='object',
        properties=dict(task_id=dict(type='string'),introduces_violation=dict(type='string',enum=['yes','no','uncertain']),
            after_has_violation=dict(type='string',enum=['yes','no','uncertain']),scenario_id=dict(type='string'),
            before_counts=dict(type='array',items=dict(type='integer')),after_counts=dict(type='array',items=dict(type='integer')),
            before_outcomes=dict(type='array',items=dict(type='string')),after_outcomes=dict(type='array',items=dict(type='string')),
            source_refs=dict(type='array',items=dict(type='string')),evidence_refs=dict(type='array',items=dict(type='string')),
            reason=dict(type='string')),
        required=['task_id','introduces_violation','after_has_violation','scenario_id','before_counts','after_counts','before_outcomes','after_outcomes','source_refs','evidence_refs','reason'],
        additionalProperties=False))),required=['answers'],additionalProperties=False)
    dump(HERE/'OUTPUT_SCHEMA.json',schema)
    print('Prepared',len(gold),'tasks with forward/reverse changes; gold labels kept outside prompts.')


if __name__=='__main__':main()
