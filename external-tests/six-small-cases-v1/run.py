#!/usr/bin/env python3
"""Run a fixed six-module sample without changing analyzer rules."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from temporal_contract_analyzer.core import analyze_sources
from temporal_contract_analyzer.review import focused_review
from temporal_contract_analyzer.report import markdown, html_report


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--node', default='/Applications/Visual Studio Code.app/Contents/MacOS/Code')
    args = parser.parse_args()
    for name, digest in json.loads((HERE / 'SOURCE_HASHES.json').read_text()).items():
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
    out = args.output.resolve()
    assert out != HERE and HERE / 'upstream' not in (out, *out.parents)
    out.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, ELECTRON_RUN_AS_NODE='1')
    node_version = subprocess.check_output([args.node, '--version'], env=env, text=True).strip()
    rows = []
    for case in json.loads((HERE / 'PROVENANCE.json').read_text())['cases']:
        original = (HERE / case['source_file']).read_text()
        variants = {'original': original}
        if case['id'] == 'async-only-once':
            old = '        fn = null;\n        callFn.apply(this, args);'
            new = '        callFn.apply(this, args);\n        fn = null;'
            assert original.count(old) == 1
            variants['late-clear-mutant'] = original.replace(old, new, 1)
        if case['id'] == 'tiny-emitter':
            old = '      self.off(name, listener);\n      callback.apply(ctx, arguments);'
            new = '      callback.apply(ctx, arguments);\n      self.off(name, listener);'
            assert original.count(old) == 1
            variants['late-off-mutant'] = original.replace(old, new, 1)
        for variant, source in variants.items():
            folder = out / case['id'] / variant
            folder.mkdir(parents=True)
            suffix = Path(case['source_file']).suffix
            (folder / ('source' + suffix)).write_text(source)
            report = analyze_sources({case['path']: source}, node=args.node)
            focused = focused_review(report)
            dump(folder / 'report.json', report)
            dump(folder / 'focused.json', focused)
            (folder / 'focused.md').write_text(markdown(report))
            (folder / 'focused.html').write_text(html_report(report))
            (folder / 'exploratory.md').write_text(markdown(report, view='exploratory'))
            if variant != 'original':
                (folder / 'injected.patch').write_text(''.join(difflib.unified_diff(
                    original.splitlines(keepends=True), source.splitlines(keepends=True),
                    fromfile='original/' + case['path'], tofile=variant + '/' + case['path'])))
            with tempfile.TemporaryDirectory(prefix='tca-six-') as directory:
                module = Path(directory) / ('source' + suffix)
                module.write_text(source)
                runtime = subprocess.run([args.node, '--test', '--test-reporter=tap', str(HERE / 'witness.test.mjs')],
                    env=dict(env, TCA_CASE=case['id'], TCA_MODULE=str(module),
                             TCA_OBSERVATIONS=str(folder / 'observations.json')),
                    capture_output=True, text=True, timeout=30)
            (folder / 'runtime.tap').write_text(runtime.stdout)
            (folder / 'runtime.stderr').write_text(runtime.stderr)
            counts = {key: int(re.search(r'^# ' + key + r' (\d+)$', runtime.stdout, re.M).group(1))
                      for key in ['tests', 'pass', 'fail', 'cancelled', 'skipped', 'todo']}
            assert counts['tests'] > 0 and counts['cancelled'] == counts['skipped'] == counts['todo'] == 0
            assert (counts['fail'] == 0 if variant == 'original' else counts['fail'] >= 1), (case['id'], variant, counts)
            assert runtime.returncode == (0 if variant == 'original' else 1)
            row = dict(case=case['id'], variant=variant, source_lines=len(source.splitlines()),
                       status=report['status'], raw_hints=report['summary']['review_hints'],
                       focused_cards=len(focused['cards']), tests=counts,
                       runtime_exit_code=runtime.returncode, tool_version=report['tool_version'],
                       tool_sha256=report['tool_sha256'], input_sha256=report['input_sha256'],
                       observations=json.loads((folder / 'observations.json').read_text()))
            rows.append(row)
            print(json.dumps(row), flush=True)
    assert len({row['tool_sha256'] for row in rows}) == 1
    summary = dict(rows=rows, node_version=node_version, upstream_suites='not_run',
                   mutants='Two researcher-injected order faults, not upstream bugs.',
                   limits='Fixed convenience sample; no general precision/recall or LLM-benefit estimate. Memoization observations have no asserted normative oracle.')
    dump(out / 'summary.json', summary)
    dump(out / 'reproduction_hashes.json', {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
         for name in ['run.py', 'witness.test.mjs', 'PROTOCOL.md', 'SOURCE_HASHES.json']})


if __name__ == '__main__':
    main()
