#!/usr/bin/env python3
"""Scan an unchanged GitHub snapshot and one explicitly synthetic order mutation."""
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


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--node', default='/Applications/Visual Studio Code.app/Contents/MacOS/Code')
    args = parser.parse_args()
    for name, expected in json.loads((HERE/'SOURCE_HASHES.json').read_text()).items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest() == expected, name
    env = dict(os.environ, ELECTRON_RUN_AS_NODE='1')
    version = subprocess.run([args.node, '--version'], env=env, text=True, capture_output=True, timeout=10)
    assert version.returncode == 0 and int(version.stdout.strip().lstrip('v').split('.')[0]) >= 22
    output = args.output.resolve()
    assert output != HERE and HERE/'upstream' not in output.parents and output != HERE/'upstream'
    output.mkdir(parents=True, exist_ok=False)
    original = (HERE/'upstream/index.js').read_text()
    before = '      called = true;\n      return fn.apply(this, arguments);'
    after = '      var result = fn.apply(this, arguments);\n      called = true;\n      return result;'
    assert original.count(before) == 1
    sources = dict(original=original, synthetic_late_flag=original.replace(before, after, 1))
    reports = {}
    rows = []
    for label, source in sources.items():
        folder = output/label
        folder.mkdir()
        (folder/'source.js').write_text(source)
        report = analyze_sources({'index.js': source}, node=args.node)
        reports[label] = report
        review = focused_review(report)
        dump(folder/'report.json', report)
        dump(folder/'focused.json', review)
        (folder/'focused.md').write_text(markdown(report))
        (folder/'focused.html').write_text(html_report(report))
        (folder/'exploratory.md').write_text(markdown(report, view='exploratory'))
        # Run original bytes through CommonJS; no mocking, instrumentation or packages.
        with tempfile.TemporaryDirectory(prefix='tca-component-once-') as directory:
            temp = Path(directory)
            (temp/'index.js').write_text(source)
            shutil.copyfile(HERE/'witness.test.mjs', temp/'witness.test.mjs')
            run_env = dict(env, TCA_MODULE=str(temp/'index.js'), TCA_OBSERVATIONS=str(folder/'observations.json'))
            command = [args.node, '--test', '--test-reporter=tap', str(temp/'witness.test.mjs')]
            result = subprocess.run(command, env=run_env, text=True, capture_output=True, timeout=30)
        (folder/'runtime.tap').write_text(result.stdout)
        (folder/'runtime.stderr').write_text(result.stderr)
        counts = {key: int(re.search(r'^# '+key+r' (\d+)$', result.stdout, re.M).group(1))
                  for key in ['tests', 'pass', 'fail', 'cancelled', 'skipped', 'todo']}
        observations = json.loads((folder/'observations.json').read_text())
        rows.append(dict(name=label, input_kind='unmodified_upstream' if label=='original' else 'researcher_created_mutation_not_upstream_bug',
            source_lines=len(source.splitlines()), scan_status=report['status'],
            raw_hints=report['summary']['review_hints'], rules=[f['rule'] for f in report['findings']],
            focused_cards=len(review['cards']), tool_version=report['tool_version'], tool_sha256=report['tool_sha256'],
            input_sha256=report['input_sha256'], runtime_exit_code=result.returncode,
            tests=counts, observations=observations, upstream_mocha_suite='not_run'))
        expected_failures = 0 if label=='original' else 1
        assert counts == dict(tests=7, **{'pass':7-expected_failures}, fail=expected_failures, cancelled=0, skipped=0, todo=0)
        assert result.returncode == expected_failures
    summary = dict(repository='https://github.com/component/once', commit='a65667875a7598352d2a869aa1f937e1771db781',
        node_version=version.stdout.strip(), rows=rows,
        limits='Inspected, small, old project. No analyzer changes. Synthetic mutation is not an independent real defect. '
               'Zero hints do not establish correct protection recognition. Custom probes are not upstream Mocha results or a precision/recall estimate.')
    dump(output/'summary.json', summary)
    dump(output/'reproduction_hashes.json', {name:hashlib.sha256((HERE/name).read_bytes()).hexdigest()
        for name in ['run.py', 'witness.test.mjs', 'SOURCE_HASHES.json']})
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
