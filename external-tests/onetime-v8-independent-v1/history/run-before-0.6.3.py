#!/usr/bin/env python3
"""Reproduce the frozen source scan and custom runtime probes without npm install."""
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
from temporal_contract_analyzer.core import analyze_sources
from temporal_contract_analyzer.report import markdown, html_report
from temporal_contract_analyzer.review import focused_review


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def runtime(requested):
    candidates = [requested] if requested else [shutil.which('node'), '/Applications/Visual Studio Code.app/Contents/MacOS/Code']
    for candidate in candidates:
        if not candidate or not Path(candidate).is_file():
            continue
        env = dict(os.environ, ELECTRON_RUN_AS_NODE='1')
        check = subprocess.run([candidate, '--version'], env=env, capture_output=True, text=True, timeout=10)
        if check.returncode == 0 and int(check.stdout.strip().lstrip('v').split('.')[0]) >= 22:
            return candidate, check.stdout.strip(), env
    raise RuntimeError('An existing Node >=22 executable is required; pass --node. No packages are installed.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--node')
    args = parser.parse_args()
    expected = json.loads((HERE/'SOURCE_HASHES.json').read_text())
    for name, digest in expected.items():
        if hashlib.sha256((HERE/name).read_bytes()).hexdigest() != digest:
            raise RuntimeError('Frozen source changed: ' + name)
    node, node_version, env = runtime(args.node)
    output = args.output.resolve()
    if output == HERE or HERE in output.parents:
        # The output must be a new sibling directory within this study, not upstream/dependency.
        if output.parent != HERE or output.name in {'upstream', 'dependency'}:
            raise RuntimeError('Use a new direct child of the study or a directory outside it')
    output.mkdir(parents=True, exist_ok=False)
    report = analyze_sources({'index.js': (HERE/'upstream/index.js').read_text()}, node=node)
    focused = focused_review(report)
    dump(output/'report.json', report)
    dump(output/'focused.json', focused)
    (output/'focused.md').write_text(markdown(report), encoding='utf-8')
    (output/'focused.html').write_text(html_report(report), encoding='utf-8')
    (output/'exploratory.md').write_text(markdown(report, view='exploratory'), encoding='utf-8')
    (output/'exploratory.html').write_text(html_report(report, view='exploratory'), encoding='utf-8')
    # Only the unmodified implementation and real runtime dependency are loaded.
    # No shim, patch, oracle or runtime observation is supplied to the analyzer.
    with tempfile.TemporaryDirectory(prefix='tca-onetime-') as directory:
        temp = Path(directory)
        shutil.copytree(HERE/'upstream', temp/'upstream')
        shutil.copytree(HERE/'dependency/mimic-function', temp/'upstream/node_modules/mimic-function')
        shutil.copy2(HERE/'witness.test.mjs', temp/'witness.test.mjs')
        observations = output/'observations.json'
        env['TCA_OBSERVATIONS'] = str(observations)
        command = [node, '--test', '--test-reporter=tap', str(temp/'witness.test.mjs')]
        result = subprocess.run(command, cwd=temp, env=env, capture_output=True, text=True, timeout=30)
        (output/'runtime.tap').write_text(result.stdout, encoding='utf-8')
        (output/'runtime.stderr').write_text(result.stderr, encoding='utf-8')
        observed = json.loads(observations.read_text()) if observations.exists() else {}
        summary = dict(repository='sindresorhus/onetime',
            commit=json.loads((HERE/'PROVENANCE.json').read_text())['commit'],
            source_lines=len((HERE/'upstream/index.js').read_text().splitlines()),
            tool_version=report['tool_version'], tool_sha256=report['tool_sha256'],
            input_sha256=report['input_sha256'], scan_status=report['status'],
            events=report['summary']['events'], raw_hints=report['summary']['review_hints'],
            focused_cards=len(focused['cards']), node=node, node_version=node_version,
            runtime_command=command, runtime_exit_code=result.returncode,
            custom_checks=7, passed=5 if '# pass 5\n' in result.stdout else None,
            failed=2 if '# fail 2\n' in result.stdout else None,
            observations=observed, upstream_ava_suite='not_run',
            interpretation='Custom synchronous-reentry expectations fail, but the analyzer emits no hint. '
                'This is an observed coverage gap on an inspected source, not a maintainer-confirmed defect '
                'or evidence of precision/recall or developer/LLM improvement.')
        dump(output/'summary.json', summary)
        dump(output/'reproduction_hashes.json', {
            name: hashlib.sha256((HERE/name).read_bytes()).hexdigest()
            for name in ['run.py', 'witness.test.mjs', 'SOURCE_HASHES.json']})
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if summary['passed'] != 5 or summary['failed'] != 2 or result.returncode != 1:
            raise RuntimeError('Runtime outcome differs from the recorded 5 controls / 2 failing probes; inspect raw TAP')
        if observed.get('synchronous', {}).get('callbackCalls') != 2:
            raise RuntimeError('The synchronous reentry observation was not reproduced')


if __name__ == '__main__':
    main()
