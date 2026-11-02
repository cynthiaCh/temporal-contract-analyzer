#!/usr/bin/env python3
"""Run an independent fast-check model against the same declarative plans."""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REFERENCE = ROOT/'external-tests/behavior-probe-feasibility-v1/run-02'
NODE = '/Applications/Visual Studio Code.app/Contents/MacOS/Code'
ENV = dict(os.environ, ELECTRON_RUN_AS_NODE='1')
SEEDS = [17, 42, 2027]


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


@contextmanager
def prepare(subject):
    with tempfile.TemporaryDirectory(prefix='temporal-fc-') as directory:
        runtime = Path(directory)
        source = runtime/'source'
        shutil.copytree(subject['root'], source, ignore=shutil.ignore_patterns('.git','node_modules','__pycache__'))
        (source/'package.json').write_text(json.dumps({'type':subject.get('module','commonjs')}))
        for root in [*subject.get('dependencies', []), str(HERE/'dependencies')]:
            for dependency in Path(root).iterdir():
                if dependency.is_dir(): shutil.copytree(dependency, runtime/'node_modules'/dependency.name)
        module = source/subject['entry']
        kind = subject.get('module','commonjs')
        if subject.get('flow_eraser'):
            result = subprocess.run([NODE,subject['flow_eraser'],str(module)],env=ENV,
                                    capture_output=True,text=True,timeout=15)
            assert result.returncode==0,result.stderr
            module=source/'prepared.mjs';module.write_text(json.loads(result.stdout)['source']);kind='module'
        if module.suffix=='.ts':
            for file in source.rglob('*.ts'):
                alias=file.with_suffix('')
                if not alias.exists():alias.symlink_to(file.name)
            kind='module'
        yield dict(module=str(module),source_root=str(source),runtime_root=str(runtime),module_kind=kind)


def run_worker(config, folder, seed, paired=None):
    request=dict(config,seed=seed,paired_replay=paired or {})
    result=subprocess.run([NODE,str(HERE/'baseline.mjs')],input=json.dumps(request),env=ENV,
                          capture_output=True,text=True,timeout=90)
    (folder/f'seed-{seed}.stdout').write_text(result.stdout)
    (folder/f'seed-{seed}.stderr').write_text(result.stderr)
    assert result.returncode==0,result.stderr+result.stdout[-500:]
    report=json.loads(result.stdout)
    assert report.get('fast_check_version')=='4.10.2',report
    assert all(row['classification']!='inconclusive_error' for row in report['rows']),report
    assert all(not row['failed'] or row['replay_matches'] for row in report['rows']),report
    dump(folder/f'seed-{seed}.json',report)
    for row in report['rows']:
        if row.get('native_failure_output'):
            (folder/f'seed-{seed}-{row["contract"]}.txt').write_text(row['native_failure_output']+'\n')
    return report


def smoke(out):
    for name, body in [
        ('bad','module.exports=fn=>{let used=false,value;return(...a)=>{if(used)return value;value=fn(...a);used=true;return value;}};'),
        ('good','module.exports=fn=>{let used=false,value;return(...a)=>{if(used)return value;used=true;value=fn(...a);return value;}};'),
        ('native','module.exports=require("node:events").EventEmitter;')]:
        folder=out/name;folder.mkdir()
        (folder/'index.cjs').write_text(body)
        if name=='native':
            api=dict(kind='emitter',construct=True,methods=dict(on='on',off='removeListener',emit='emit',once='once'))
            contracts=dict(once_delivery=True,snapshot_delivery=True)
        else:api=dict(kind='wrapper');contracts=dict(at_most_once=True,cache_repeated=True)
        with prepare(dict(root=str(folder),entry='index.cjs')) as runtime:
            report=run_worker(dict(runtime,api=api,contracts=contracts),folder,17)
        failures=[row['contract'] for row in report['rows'] if row['failed']]
        assert failures==(['at_most_once'] if name=='bad' else []),(name,failures)
    print('Independent model calibration passed: late publication detected; early guard and native EventEmitter pass.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--smoke',action='store_true')
    args=parser.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    if args.smoke:smoke(out);return
    definitions=json.loads((REFERENCE/'EVALUATION_PLAN.json').read_text())['plans']
    dump(out/'INPUT_PLANS.json',definitions)
    rows=[]
    engine=(HERE/'baseline.mjs').read_text();(out/'baseline.mjs').write_text(engine)
    for definition in definitions:
        folder=out/definition['name'];folder.mkdir()
        plan=definition['plan'];before_reports=[];after_reports=[];paired={}
        for side, reports in [('before',before_reports),('after',after_reports)]:
            destination=folder/side;destination.mkdir()
            with prepare(plan[side]) as runtime:
                for seed in SEEDS:
                    report=run_worker(dict(runtime,api=plan['api'],contracts=plan['contracts']),destination,seed,paired if side=='after' else None)
                    reports.append(report)
            if side=='before':
                for report in reports:
                    for prop in report['rows']:
                        if prop['failed']:
                            data=prop['counterexample'][0]
                            bucket=paired.setdefault(prop['contract'],[])
                            if data not in bucket:bucket.append(data)
        target=definition['target_contract']
        failure_contracts=lambda reports:sorted({prop['contract'] for report in reports for prop in report['rows'] if prop['failed']})
        paired_outcomes=[(prop['contract'],replay['result']['passed']) for report in after_reports
                         for prop in report['rows'] for replay in prop.get('paired_replay',[])]
        row=dict(name=definition['name'],target_contract=target,
            before_failed_contracts=failure_contracts(before_reports),after_failed_contracts=failure_contracts(after_reports),
            target_counterexample_obtained=bool(target and any(prop['contract']==target and prop['failed'] for report in before_reports for prop in report['rows'])),
            target_before_counterexample_passes_after=bool(target and any(contract==target and passed for contract,passed in paired_outcomes)),
            all_failed_cases_replayed=True,
            num_runs=sum(prop['numRuns'] for report in [*before_reports,*after_reports] for prop in report['rows']),
            num_shrinks=sum(prop['numShrinks'] for report in [*before_reports,*after_reports] for prop in report['rows']),
            failed_properties=sum(prop['failed'] for report in [*before_reports,*after_reports] for prop in report['rows']),
            counterexamples_with_subject_frames=sum(bool(prop.get('evidence',{}).get('frames')) for report in [*before_reports,*after_reports] for prop in report['rows'] if prop['failed']))
        rows.append(row);print(json.dumps(row),flush=True)
        assert (HERE/'baseline.mjs').read_text()==engine
    dump(out/'summary.json',dict(rows=rows,fast_check_version='4.10.2',seeds=SEEDS,num_runs_per_property=100,
        generation='Independent reusable property models; same bindings/contracts; bounded generated parameters and native shrinking.',
        limits='Previously seen development cases; different coverage and process-isolation costs. No human time, comprehension or superiority estimate.'))


if __name__=='__main__':main()
