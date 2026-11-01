#!/usr/bin/env python3
"""A ten-line helper: frozen original and a labeled synthetic reordering."""
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
    original = (HERE/'upstream/lib/internal/once.js').read_text()
    before = '        fn = null;\n        callFn.apply(this, args);'
    after = '        callFn.apply(this, args);\n        fn = null;'
    assert original.count(before) == 1
    sources = dict(original=original, synthetic_late_clear=original.replace(before, after, 1))
    reports, rows = {}, []
    for name, source in sources.items():
        folder = output/name
        folder.mkdir()
        (folder/'source.js').write_text(source)
        report = analyze_sources({'once.js': source}, node=args.node)
        reports[name] = report
        focused = focused_review(report)
        dump(folder/'report.json', report)
        dump(folder/'focused.json', focused)
        (folder/'focused.md').write_text(markdown(report))
        (folder/'focused.html').write_text(html_report(report))
        (folder/'exploratory.md').write_text(markdown(report, view='exploratory'))
        with tempfile.TemporaryDirectory(prefix='tca-async-once-') as directory:
            temp = Path(directory)
            # .mjs supplies the source module's authored ESM interpretation; bytes are unchanged.
            (temp/'once.mjs').write_text(source)
            shutil.copyfile(HERE/'witness.test.mjs', temp/'witness.test.mjs')
            run_env = dict(env, TCA_MODULE=str(temp/'once.mjs'), TCA_OBSERVATIONS=str(folder/'observations.json'))
            result = subprocess.run([args.node, '--test', '--test-reporter=tap', str(temp/'witness.test.mjs')],
                                    env=run_env, capture_output=True, text=True, timeout=30)
        (folder/'runtime.tap').write_text(result.stdout)
        (folder/'runtime.stderr').write_text(result.stderr)
        counts = {key:int(re.search(r'^# '+key+r' (\d+)$', result.stdout, re.M).group(1))
                  for key in ['tests', 'pass', 'fail', 'cancelled', 'skipped', 'todo']}
        failed = 0 if name == 'original' else 1
        assert counts == dict(tests=7, **{'pass':7-failed}, fail=failed, cancelled=0, skipped=0, todo=0)
        assert result.returncode == failed
        rows.append(dict(name=name, input_kind='unmodified_upstream_helper' if name=='original' else 'researcher_mutation_not_upstream_bug',
            source_lines=len(source.splitlines()), scan_status=report['status'], raw_hints=report['summary']['review_hints'],
            focused_cards=len(focused['cards']), rules=[f['rule'] for f in report['findings']],
            tool_version=report['tool_version'], tool_sha256=report['tool_sha256'], input_sha256=report['input_sha256'],
            tests=counts, runtime_exit_code=result.returncode, observations=json.loads((folder/'observations.json').read_text())))
    change=compare(reports['original'], reports['synthetic_late_clear'])
    dump(output/'comparison.json', change)
    (output/'comparison.html').write_text(html_report(change))
    (output/'synthetic-order.patch').write_text(''.join(difflib.unified_diff(
        sources['original'].splitlines(keepends=True), sources['synthetic_late_clear'].splitlines(keepends=True),
        fromfile='original/once.js', tofile='synthetic_late_clear/once.js')))
    summary=dict(repository='https://github.com/caolan/async', ref='v3.2.6',
        commit='85fb18f3d319d14d893ec24648929ff0eb908768', node_version=version.stdout.strip(), rows=rows,
        upstream_full_suite='not_run',
        limits='Isolated helper inspected before scanning. Synthetic mutation is not an upstream defect. '
        'Analyzer rules unchanged during this check. Custom tests do not establish full safety or precision/recall.')
    dump(output/'summary.json', summary)
    dump(output/'reproduction_hashes.json', {name:hashlib.sha256((HERE/name).read_bytes()).hexdigest()
         for name in ['run.py','witness.test.mjs','SOURCE_HASHES.json']})
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
