#!/usr/bin/env python3
"""Two-phase, immutable-tool evaluation: runtime first, static analysis second."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from temporal_contract_analyzer.core import analyze_sources
from temporal_contract_analyzer.report import markdown, html_report
from temporal_contract_analyzer.review import focused_review

FAILURES = {
    'event-once': ['once survives nested emission with one listener', 'once survives nested emission with multiple listeners'],
    'mitt-removal': ['self removal does not skip the following listener', 'wildcard self removal does not skip the following listener'],
    'memo-exception-cache': ['same failing arguments rethrow the cached exception', 'failed arguments never return an earlier successful value'],
    'promise-cache': ['consecutive non awaited calls share the in flight evaluation'],
    'inflight': ['callback throw still releases the request key'],
}


def read(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_freeze():
    for name, expected in read(HERE/'INPUT_HASHES.json').items():
        assert digest(HERE/name) == expected, name
    for name, expected in read(HERE/'frozen-tool/FILES.json').items():
        assert digest(ROOT/name) == expected, name
    empty = analyze_sources({})
    protocol = read(HERE/'PROTOCOL.json')
    assert empty['tool_sha256'] == protocol['tool_sha256']
    assert empty['tool_version'] == protocol['tool_version']


def runtime(case, folder, node, env):
    original = HERE/'snapshots'/case['id']
    with tempfile.TemporaryDirectory(prefix='tca-unseen-') as directory:
        root = Path(directory)
        tree = root/'source'
        shutil.copytree(original, tree)
        (root/'node_modules').mkdir()
        for dependency in (HERE/'dependencies').iterdir():
            # Copies keep nested bare imports within this isolated resolution tree.
            shutil.copytree(dependency, root/'node_modules'/dependency.name)
        entry = tree/case['entry']
        flow = entry.read_text().startswith('// @flow')
        if flow:
            erased = subprocess.run([node, str(HERE/'erase-flow.cjs'), str(entry)], env=env,
                                    text=True, capture_output=True, timeout=15)
            (folder/'flow-adapter.stderr').write_text(erased.stderr)
            assert erased.returncode == 0, erased.stderr
            adapter = json.loads(erased.stdout)
            entry = tree/'runtime.mjs'
            entry.write_text(adapter.pop('source'))
            shutil.copyfile(entry, folder/'runtime-erased.mjs')
            adapter.update(original_sha256=digest(original/case['entry']), runtime_sha256=digest(entry))
            dump(folder/'flow-adapter.json', adapter)
        if entry.suffix == '.ts':
            (tree/'package.json').write_text('{"type":"module"}\n')
            # Native Node type erasure; resolve the original extensionless import
            # with a symlink, preserving both TS source files byte-for-byte.
            for source in tree.rglob('*.ts'):
                alias = source.with_suffix('')
                if not alias.exists():
                    alias.symlink_to(source.name)
        elif not flow:
            (tree/'package.json').write_text('{"type":"commonjs"}\n')
        result = subprocess.run([node, '--test', '--test-reporter=tap', str(HERE/'witness.test.mjs')],
            env=dict(env, TCA_MODULE=str(entry), TCA_WITNESS=case['witness'],
                     TCA_OBSERVATIONS=str(folder/'observations.json')),
            capture_output=True, text=True, timeout=30)
    (folder/'runtime.tap').write_text(result.stdout)
    (folder/'runtime.stderr').write_text(result.stderr)
    counts = {key: int(re.search(r'^# '+key+r' (\d+)$', result.stdout, re.M).group(1))
              for key in ['tests', 'pass', 'fail', 'cancelled', 'skipped', 'todo']}
    failed = re.findall(r'^not ok \d+ - (.+)$', result.stdout, re.M)
    expected = FAILURES[case['witness']] if case['label'] == 'upstream_bug' else []
    assert sorted(failed) == sorted(expected), (case['id'], failed, expected)
    assert counts['cancelled'] == counts['skipped'] == counts['todo'] == 0
    assert counts['tests'] > 0 and counts['fail'] == len(expected)
    assert result.returncode == int(bool(expected))
    return dict(case=case['id'], label=case['label'], tests=counts, failed_tests=failed,
                exit_code=result.returncode, runtime_adapter='flow_type_erasure' if flow else 'native_node',
                observations=read(folder/'observations.json'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['runtime', 'analyze'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--node', default='/Applications/Visual Studio Code.app/Contents/MacOS/Code')
    args = parser.parse_args()
    check_freeze()
    cases = read(HERE/'CASES.json')['cases']
    out = args.output.resolve()
    env = dict(os.environ, ELECTRON_RUN_AS_NODE='1')
    node_version = subprocess.check_output([args.node, '--version'], env=env, text=True).strip()
    code_hashes = {name: digest(HERE/name) for name in ['run.py', 'witness.test.mjs', 'erase-flow.cjs', 'prepare.py']}
    if args.phase == 'runtime':
        assert out != HERE and HERE/'snapshots' not in (out, *out.parents)
        out.mkdir(parents=True, exist_ok=False)
        dump(out/'TEST_PLAN.json', dict(cases=[dict(id=c['id'], label=c['label'], witness=c['witness'],
             expected_failed_tests=FAILURES[c['witness']] if c['label'] == 'upstream_bug' else []) for c in cases],
             written_before_runtime=True, source_freeze_sha256=digest(HERE/'INPUT_HASHES.json'),
             test_code_hashes=code_hashes))
        rows = []
        for case in cases:
            folder = out/case['id']; folder.mkdir()
            row = runtime(case, folder, args.node, env)
            dump(folder/'runtime.json', row); rows.append(row)
            print(case['id'], row['tests'], flush=True)
        dump(out/'RUNTIME_LABELS.json', dict(rows=rows, node_version=node_version,
             test_code_hashes=code_hashes, analysis_not_yet_run=True))
    else:
        labels = read(out/'RUNTIME_LABELS.json')
        assert labels['test_code_hashes'] == code_hashes
        assert not (out/'summary.json').exists()
        rows = []
        for case, behavior in zip(cases, labels['rows']):
            assert case['id'] == behavior['case']
            folder = out/case['id']
            source = {name: (HERE/'snapshots'/case['id']/name).read_text() for name in case['sources']}
            report = analyze_sources(source, node=args.node)
            focused = focused_review(report)
            dump(folder/'report.json', report); dump(folder/'focused.json', focused)
            (folder/'focused.md').write_text(markdown(report))
            (folder/'focused.html').write_text(html_report(report))
            (folder/'exploratory.md').write_text(markdown(report, view='exploratory'))
            row = dict(**behavior, implementation=case['implementation'], commit=case['commit'],
                source_url=case['source_url'], source_lines=case['source_lines'], status=report['status'],
                coverage=[dict(path=f['path'], status=f['status'], error=f.get('error')) for f in report['files']],
                raw_hints=report['summary']['review_hints'], focused_cards=len(focused['cards']),
                finding_rules=[f['rule'] for f in report['findings']], tool_version=report['tool_version'],
                tool_sha256=report['tool_sha256'], input_sha256=report['input_sha256'])
            rows.append(row)
            print(case['id'], report['status'], row['focused_cards'], row['finding_rules'], flush=True)
        dump(out/'summary.json', dict(rows=rows, node_version=node_version,
             independent_implementations=len({c['implementation'] for c in cases}), snapshots=len(cases),
             interpretation='Original upstream sources only. Historical versions correlated. Runtime-correct means selected contract checks only. Flow erasure is runtime-only; static parse failures retained. No accuracy or LLM-utility estimate.'))
    check_freeze()


if __name__ == '__main__':
    main()
