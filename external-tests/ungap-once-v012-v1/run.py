#!/usr/bin/env python3
"""Pinned polyfill, upstream assertions, and a labeled order mutation."""
import argparse
import difflib
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
sys.path.insert(0, str(HERE.parents[1]))
from temporal_contract_analyzer.core import analyze_sources, compare
from temporal_contract_analyzer.report import markdown, html_report
from temporal_contract_analyzer.review import focused_review


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--node', default='/Applications/Visual Studio Code.app/Contents/MacOS/Code')
    args = p.parse_args()
    for name, expected in json.loads((HERE/'SOURCE_HASHES.json').read_text()).items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest() == expected, name
    env = dict(os.environ, ELECTRON_RUN_AS_NODE='1')
    version = subprocess.run([args.node, '--version'], env=env, capture_output=True, text=True, timeout=10)
    assert version.returncode == 0 and int(version.stdout.strip().lstrip('v').split('.')[0]) >= 22
    output = args.output.resolve()
    assert output != HERE and output != HERE/'upstream' and HERE/'upstream' not in output.parents
    output.mkdir(parents=True, exist_ok=False)
    original = (HERE/'upstream/esm/index.js').read_text()
    assert (HERE/'upstream/cjs/index.js').read_text() == "'use strict';\n" + original
    before = '          execute = false;\n'
    after = '                      apply(fn, this, arguments);\n'
    assert original.count(before) == original.count(after) == 1
    mutated = original.replace(before, '', 1).replace(after, after + before, 1)
    sources = dict(original=original, synthetic_late_flag=mutated)
    rows, reports = [], {}
    for name, source in sources.items():
        folder = output/name
        folder.mkdir()
        (folder/'source.js').write_text(source)
        report = analyze_sources({'index.js':source}, node=args.node)
        reports[name] = report
        focused = focused_review(report)
        dump(folder/'report.json', report)
        dump(folder/'focused.json', focused)
        (folder/'focused.md').write_text(markdown(report))
        (folder/'focused.html').write_text(html_report(report))
        (folder/'exploratory.md').write_text(markdown(report, view='exploratory'))
        with tempfile.TemporaryDirectory(prefix='tca-ungap-once-') as directory:
            temp = Path(directory)
            (temp/'once.mjs').write_text(source)
            shutil.copyfile(HERE/'witness.test.mjs', temp/'witness.test.mjs')
            run_env = dict(env, TCA_MODULE=str(temp/'once.mjs'), TCA_OBSERVATIONS=str(folder/'observations.json'))
            result = subprocess.run([args.node, '--test', '--test-reporter=tap', str(temp/'witness.test.mjs')],
                                    env=run_env, text=True, capture_output=True, timeout=30)
        (folder/'runtime.tap').write_text(result.stdout)
        (folder/'runtime.stderr').write_text(result.stderr)
        counts = {k:int(re.search(r'^# '+k+r' (\d+)$', result.stdout, re.M).group(1))
                  for k in ['tests','pass','fail','cancelled','skipped','todo']}
        failures = 0 if name=='original' else 1
        assert counts == dict(tests=7, **{'pass':7-failures}, fail=failures, cancelled=0, skipped=0, todo=0)
        assert result.returncode == failures
        rows.append(dict(name=name, source_lines=len(source.splitlines()), input_kind='unmodified_upstream' if name=='original' else 'researcher_mutation_not_upstream_bug',
            status=report['status'], raw_hints=report['summary']['review_hints'], focused_cards=len(focused['cards']),
            rules=[f['rule'] for f in report['findings']], tool_version=report['tool_version'],
            tool_sha256=report['tool_sha256'], input_sha256=report['input_sha256'],
            tests=counts, runtime_exit_code=result.returncode, observations=json.loads((folder/'observations.json').read_text())))
    # Run the exact upstream test file. Only console.assert is strengthened;
    # the package and tests are not patched, and the npm coverage wrapper is not installed.
    native = output/'upstream-test'
    native.mkdir()
    with tempfile.TemporaryDirectory(prefix='tca-ungap-native-') as directory:
        temp = Path(directory)
        shutil.copytree(HERE/'upstream', temp/'upstream')
        shutil.copyfile(HERE/'strict-console-assert.cjs', temp/'strict-console-assert.cjs')
        native_env = dict(env, TCA_NATIVE_RESULT=str(native/'assertions.json'))
        result = subprocess.run([args.node, '--require', str(temp/'strict-console-assert.cjs'), str(temp/'upstream/test/index.js')],
                                env=native_env, text=True, capture_output=True, timeout=30)
    (native/'stdout.log').write_text(result.stdout)
    (native/'stderr.log').write_text(result.stderr)
    assert result.returncode == 0, result.stderr
    assertions = json.loads((native/'assertions.json').read_text())
    assert assertions == dict(assertions=10, exitCode=0), assertions
    (output/'synthetic-order.patch').write_text(''.join(difflib.unified_diff(original.splitlines(keepends=True), mutated.splitlines(keepends=True), fromfile='original/index.js',tofile='synthetic_late_flag/index.js')))
    delta = compare(reports['original'], reports['synthetic_late_flag'])
    dump(output/'comparison.json', delta)
    (output/'comparison.html').write_text(html_report(delta))
    summary=dict(repository='https://github.com/ungap/once', commit='18958325cefa455d45cf90aa2907c5a156c0dc7d', version='0.1.2',
        node_version=version.stdout.strip(), rows=rows, upstream_assertions=assertions,
        upstream_test_mode='Exact pinned test/index.js on CJS export with test-only console.assert-to-throw adapter; npm c8 wrapper not run.',
        limits='Inspected small polyfill. Analyzer unchanged during testing. A synthetic mutation is not an upstream real defect or independent evidence of precision/recall or LLM utility.')
    dump(output/'summary.json', summary)
    dump(output/'reproduction_hashes.json', {n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['run.py','witness.test.mjs','strict-console-assert.cjs','SOURCE_HASHES.json']})
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
