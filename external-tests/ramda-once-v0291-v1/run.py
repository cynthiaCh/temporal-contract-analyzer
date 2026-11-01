#!/usr/bin/env python3
"""Pinned small Ramda.once module, existing analyzer, labeled order mutation."""
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
    for name, digest in json.loads((HERE/'SOURCE_HASHES.json').read_text()).items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest() == digest, name
    env = dict(os.environ, ELECTRON_RUN_AS_NODE='1')
    version = subprocess.run([args.node, '--version'], env=env, capture_output=True, text=True, timeout=10)
    assert version.returncode == 0 and int(version.stdout.strip().lstrip('v').split('.')[0]) >= 22
    output = args.output.resolve()
    assert output != HERE and output != HERE/'upstream' and HERE/'upstream' not in output.parents
    output.mkdir(parents=True, exist_ok=False)
    original = (HERE/'upstream/source/once.js').read_text()
    before = '    called = true;\n    result = fn.apply(this, arguments);'
    after = '    result = fn.apply(this, arguments);\n    called = true;'
    assert original.count(before) == 1
    sources = dict(original=original, synthetic_late_flag=original.replace(before, after, 1))
    reports, rows = {}, []
    for name, source in sources.items():
        folder = output/name
        folder.mkdir()
        (folder/'source.js').write_text(source)
        # Neither tests nor runtime outcomes are supplied to the analyzer.
        report = analyze_sources({'once.js':source}, node=args.node)
        reports[name] = report
        focused = focused_review(report)
        dump(folder/'report.json', report)
        dump(folder/'focused.json', focused)
        (folder/'focused.md').write_text(markdown(report))
        (folder/'focused.html').write_text(html_report(report))
        (folder/'exploratory.md').write_text(markdown(report, view='exploratory'))
        with tempfile.TemporaryDirectory(prefix='tca-ramda-once-') as directory:
            temp = Path(directory)
            shutil.copytree(HERE/'upstream/source', temp/'source')
            (temp/'source/once.js').write_text(source)
            # The repository sources are authored as ESM; no code is transpiled or mocked.
            (temp/'package.json').write_text('{"type":"module"}\n')
            shutil.copyfile(HERE/'witness.test.mjs', temp/'witness.test.mjs')
            runtime_env = dict(env, TCA_MODULE=str(temp/'source/once.js'), TCA_OBSERVATIONS=str(folder/'observations.json'))
            result = subprocess.run([args.node, '--test', '--test-reporter=tap', str(temp/'witness.test.mjs')],
                                    env=runtime_env, capture_output=True, text=True, timeout=30)
        (folder/'runtime.tap').write_text(result.stdout)
        (folder/'runtime.stderr').write_text(result.stderr)
        counts = {k:int(re.search(r'^# '+k+r' (\d+)$', result.stdout, re.M).group(1))
                  for k in ['tests','pass','fail','cancelled','skipped','todo']}
        failures = 0 if name=='original' else 1
        assert counts == dict(tests=8, **{'pass':8-failures}, fail=failures, cancelled=0, skipped=0, todo=0)
        assert result.returncode == failures
        rows.append(dict(name=name, source_lines=len(source.splitlines()), input_kind='unmodified_upstream' if name=='original' else 'researcher_mutation_not_upstream_bug',
            status=report['status'], raw_hints=report['summary']['review_hints'], focused_cards=len(focused['cards']),
            publication_statuses=[f['state_publication']['status'] for f in report['findings'] if 'state_publication' in f],
            tool_version=report['tool_version'], tool_sha256=report['tool_sha256'], input_sha256=report['input_sha256'],
            tests=counts, runtime_exit_code=result.returncode, observations=json.loads((folder/'observations.json').read_text())))
    delta = compare(reports['original'], reports['synthetic_late_flag'])
    dump(output/'comparison.json', delta)
    (output/'comparison.html').write_text(html_report(delta))
    (output/'synthetic-order.patch').write_text(''.join(difflib.unified_diff(original.splitlines(keepends=True), sources['synthetic_late_flag'].splitlines(keepends=True), fromfile='original/once.js',tofile='synthetic_late_flag/once.js')))
    summary = dict(repository='https://github.com/ramda/ramda', ref='v0.29.1', commit='acbf91af8a3b39e22d3a1f24d068356891797851',
        node_version=version.stdout.strip(), rows=rows, upstream_mocha_suite='not_run',
        limits='Older pinned release selected for simplicity before scanning, source inspected, same once family. '
               'Unmodified analyzer. Synthetic order mutation is not an upstream defect or general precision/recall or LLM utility estimate.')
    dump(output/'summary.json', summary)
    dump(output/'reproduction_hashes.json', {name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ['run.py','witness.test.mjs','SOURCE_HASHES.json']})
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
