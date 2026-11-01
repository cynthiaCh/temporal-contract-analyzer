#!/usr/bin/env python3
"""Source-only development checks plus original upstream execution controls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from temporal_contract_analyzer.core import analyze_sources, compare
from temporal_contract_analyzer.layers import freeze_bundle, verify_bundle
from temporal_contract_analyzer.report import html_report

RULE = 'reentrant-state-publication'
UPSTREAM = ROOT.parent/'temporal-contract-bench/studies/p-debounce-real-fix-v1'


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')


def runtime():
    os.environ['ELECTRON_RUN_AS_NODE'] = '1'
    for binary in filter(None, [shutil.which('node'), '/Applications/Visual Studio Code.app/Contents/MacOS/Code']):
        p = subprocess.run([binary, '--version'], capture_output=True, text=True)
        if p.returncode == 0 and int(p.stdout.strip().lstrip('v').split('.')[0]) >= 22:
            return binary, p.stdout.strip()
    raise RuntimeError('Requires existing Node >=22; no installation is performed')


def behavior(source, output, node):
    outcomes = {}
    with tempfile.TemporaryDirectory(prefix='publication-upstream-') as folder:
        work = Path(folder)
        (work/'index.js').write_text(source)
        (work/'package.json').write_bytes((UPSTREAM/'snapshots/before/package.json').read_bytes())
        for suite, test, expected in [('existing', UPSTREAM/'snapshots/before/test.js', 80),
                                      ('regression', UPSTREAM/'regression.test.js', 3)]:
            (work/'test.js').write_bytes(test.read_bytes())
            p = subprocess.run([node, '--test', '--test-reporter=tap', 'test.js'], cwd=work,
                               capture_output=True, timeout=60)
            (output/(suite+'.tap')).write_bytes(p.stdout)
            (output/(suite+'.stderr')).write_bytes(p.stderr)
            counts = {}
            for line in p.stdout.decode().splitlines():
                for key in ('tests', 'pass', 'fail', 'cancelled', 'skipped', 'todo'):
                    if line.startswith('# '+key+' '):
                        counts[key] = int(line.split()[-1])
            outcomes[suite] = dict(exit_code=p.returncode, expected_tests=expected, **counts)
    save(output/'behavior.json', outcomes)
    return outcomes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists():
        parser.error('Use a new output directory; previous evidence is never overwritten')
    before = (UPSTREAM/'snapshots/before/index.js').read_text()
    after = (UPSTREAM/'snapshots/after/index.js').read_text()
    binding = json.loads((UPSTREAM/'provenance/snapshots.json').read_text())
    for label, source in [('before', before), ('after', after)]:
        if hashlib.sha256(source.encode()).hexdigest() != binding[label+'/index.js']:
            raise RuntimeError('Pinned upstream source changed')
    node, version = runtime()
    generic = 'function make(invoke) { let occupied; return function entry() { if (occupied) return; BODY }; }'
    variants = {
        'before': (before, ['write_after_call'], 'real_upstream'),
        'after': (after, ['write_before_call'], 'real_upstream'),
        'renamed-before': (before.replace('currentPromise', 'pending').replace('function_', 'handler'), ['write_after_call'], 'synthetic_rename'),
        'renamed-after': (after.replace('currentPromise', 'pending').replace('function_', 'handler'), ['write_before_call'], 'synthetic_rename'),
        'formatted-before': ('// Formatting control\n\n'+before.replace('\t', '  '), ['write_after_call'], 'synthetic_format'),
        'formatted-after': ('// Formatting control\n\n'+after.replace('\t', '  '), ['write_before_call'], 'synthetic_format'),
        'deferred-before': (before.replace('result = await function_.apply(this, arguments_);',
                             'await Promise.resolve();\n\t\t\t\tresult = await function_.apply(this, arguments_);'), [], 'synthetic_deferred_prefix'),
        'timer': (generic.replace('BODY', 'occupied = setTimeout(() => invoke(), 0);'), [], 'synthetic_deferred_callback'),
        'shadow': (generic.replace('BODY', 'occupied = (() => { const invoke = other; return invoke(); })();'), [], 'synthetic_shadow'),
        'conditional': (generic.replace('BODY', 'if (flag) occupied = true; invoke();'), ['not_established'], 'synthetic_unknown'),
        'undefined-write': (generic.replace('BODY', 'occupied = undefined; invoke();'), ['write_before_call'], 'synthetic_value_not_protection'),
    }
    out.mkdir(parents=True)
    implementation = ['temporal_contract_analyzer/core.py', 'temporal_contract_analyzer/publication.py',
                      'temporal_contract_analyzer/layers.py', 'temporal_contract_analyzer/boundary_cards.py',
                      'tools/temporal-contract-analyzer/parse.cjs', 'tests/test_state_publication.py']
    hashes = {}
    for name in implementation:
        target = out/'implementation'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/name, target)
        hashes[name] = hashlib.sha256(target.read_bytes()).hexdigest()
    save(out/'protocol.json', dict(scope='known development case and constructed controls; not a holdout or precision/recall estimate',
                                  node_version=version, expected={name:dict(statuses=v[1], provenance=v[2]) for name,v in variants.items()},
                                  runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                  implementation_sha256=hashes,
                                  tool_scope='index.js only; no tests, patch, labels or model output passed to scanner'))
    rows, reports = [], {}
    for name, (source, expected, provenance) in variants.items():
        target = out/name
        target.mkdir()
        (target/'index.js').write_text(source)
        report = analyze_sources({'index.js': source}, node=node)
        if report['status'] != 'parsed':
            raise RuntimeError('Incomplete scan: '+name)
        hints = [f for f in report['findings'] if f['rule'] == RULE]
        statuses = [f['state_publication']['status'] for f in hints]
        manifest = freeze_bundle(report, target/'bundle', max_chars=60000)
        verify_bundle(target/'bundle')
        (target/'report.html').write_text(html_report(report))
        reports[name] = report
        events = {e['id']: e for f in report['files'] for e in f['events']}
        rows.append(dict(name=name, provenance=provenance, statuses=statuses, expected=expected,
                         matches=statuses==expected, summary=report['summary'],
                         tool_version=report['tool_version'], input_sha256=report['input_sha256'],
                         tool_sha256=report['tool_sha256'],
                         report_characters=manifest['layers']['review']['chars'],
                         evidence=[dict(guard_line=events[f['state_publication']['guard']]['line'],
                                        callback_line=events[f['state_publication']['callback']]['line'],
                                        write_line=events[f['state_publication']['write']]['line'] if f['state_publication']['write'] else None)
                                   for f in hints]))
        print(name, statuses, 'matches', statuses==expected, flush=True)
    delta = compare(reports['before'], reports['after'])
    save(out/'comparison.json', delta)
    (out/'comparison.html').write_text(html_report(delta))
    neutral = {}
    for label in ('before', 'after'):
        change = compare(reports[label], reports['formatted-'+label])
        neutral[label] = not any(f['rule']==RULE for f in change['added_hints']+change['removed_hints'])
    native = {label: behavior(source, out/label, node) for label,source in [('before',before),('after',after)]}
    save(out/'summary.json', dict(rows=rows, all_development_checks_match=all(r['matches'] for r in rows),
                                 formatting_neutral=neutral, behavior=native,
                                 delta=dict(comparable=delta['comparable'],
                                            added=[f['rule'] for f in delta['added_hints']],
                                            removed=[f['rule'] for f in delta['removed_hints']]),
                                 limits='One known upstream defect; synthetic variants are not independent defects. No LLM calls or benefit measurement.'))
    assert all(r['matches'] for r in rows) and all(neutral.values())
    for label in ('before', 'after'):
        for suite, total in [('existing', 80), ('regression', 3)]:
            actual = native[label][suite]
            failures = 3 if label=='before' and suite=='regression' else 0
            expected = dict(exit_code=1 if failures else 0, tests=total, pass_count=total-failures,
                            fail=failures, cancelled=0, skipped=0, todo=0)
            observed = {key:actual.get('pass' if key=='pass_count' else key) for key in expected}
            assert observed == expected, (label, suite, observed, expected)
    print('All bounded checks matched; upstream behavior controls preserved.', flush=True)


if __name__ == '__main__':
    main()
