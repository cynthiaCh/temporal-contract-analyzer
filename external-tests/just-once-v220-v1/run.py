#!/usr/bin/env python3
"""Fixed no-dependency wrapper and a labeled synthetic state-order regression."""
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
import shutil

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from temporal_contract_analyzer.core import analyze_sources, compare
from temporal_contract_analyzer.report import markdown, html_report
from temporal_contract_analyzer.review import focused_review


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--node', default='/Applications/Visual Studio Code.app/Contents/MacOS/Code')
    args = p.parse_args()
    for name,digest in json.loads((HERE/'SOURCE_HASHES.json').read_text()).items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest,name
    env = dict(os.environ, ELECTRON_RUN_AS_NODE='1')
    version = subprocess.run([args.node,'--version'],env=env,text=True,capture_output=True,timeout=10)
    assert version.returncode==0 and int(version.stdout.strip().lstrip('v').split('.')[0])>=22
    out=args.output.resolve()
    assert out!=HERE and out!=HERE/'upstream' and HERE/'upstream' not in out.parents
    out.mkdir(parents=True,exist_ok=False)
    original=(HERE/'upstream/packages/function-once/index.cjs').read_text()
    before='    called = true;\n    value = fn.apply(this, arguments);'
    after='    value = fn.apply(this, arguments);\n    called = true;'
    assert original.count(before)==1
    sources=dict(original=original,synthetic_late_flag=original.replace(before,after,1))
    reports,rows={},[]
    for name,source in sources.items():
        folder=out/name;folder.mkdir()
        (folder/'source.cjs').write_text(source)
        report=analyze_sources({'index.cjs':source},node=args.node)
        reports[name]=report
        review=focused_review(report)
        dump(folder/'report.json',report);dump(folder/'focused.json',review)
        (folder/'focused.md').write_text(markdown(report))
        (folder/'focused.html').write_text(html_report(report))
        (folder/'exploratory.md').write_text(markdown(report,view='exploratory'))
        with tempfile.TemporaryDirectory(prefix='tca-just-once-') as directory:
            temp=Path(directory)
            (temp/'index.cjs').write_text(source)
            shutil.copyfile(HERE/'witness.test.mjs',temp/'witness.test.mjs')
            runtime_env=dict(env,TCA_MODULE=str(temp/'index.cjs'),TCA_OBSERVATIONS=str(folder/'observations.json'))
            result=subprocess.run([args.node,'--test','--test-reporter=tap',str(temp/'witness.test.mjs')],
                env=runtime_env,text=True,capture_output=True,timeout=30)
        (folder/'runtime.tap').write_text(result.stdout);(folder/'runtime.stderr').write_text(result.stderr)
        counts={k:int(re.search(r'^# '+k+r' (\d+)$',result.stdout,re.M).group(1)) for k in ['tests','pass','fail','cancelled','skipped','todo']}
        failures=0 if name=='original' else 1
        assert counts==dict(tests=7,**{'pass':7-failures},fail=failures,cancelled=0,skipped=0,todo=0)
        assert result.returncode==failures
        rows.append(dict(name=name,input_kind='unmodified_upstream' if name=='original' else 'researcher_mutation_not_upstream_defect',
            source_lines=len(source.splitlines()),status=report['status'],raw_hints=report['summary']['review_hints'],
            focused_cards=len(review['cards']),tool_version=report['tool_version'],tool_sha256=report['tool_sha256'],
            input_sha256=report['input_sha256'],tests=counts,runtime_exit_code=result.returncode,
            observations=json.loads((folder/'observations.json').read_text())))
    delta=compare(reports['original'],reports['synthetic_late_flag'])
    dump(out/'comparison.json',delta);(out/'comparison.html').write_text(html_report(delta))
    (out/'synthetic-order.patch').write_text(''.join(difflib.unified_diff(original.splitlines(keepends=True),sources['synthetic_late_flag'].splitlines(keepends=True),fromfile='original/index.cjs',tofile='synthetic_late_flag/index.cjs')))
    # Static diagnostic only: deleting cleanup is NOT a proposed fix or another real case.
    diagnostics=[]
    for name,source in sources.items():
        diagnostic=source.replace('    fn = undefined;\n','',1)
        r=analyze_sources({'index.cjs':diagnostic},node=args.node)
        diagnostics.append(dict(name=name,mutation='remove post-call cleanup for static diagnosis only; not executed or proposed as a fix',
            raw_hints=r['summary']['review_hints'],focused_cards=len(focused_review(r)['cards']),
            statuses=[f['state_publication']['status'] for f in r['findings'] if 'state_publication' in f],input_sha256=r['input_sha256']))
    dump(out/'cleanup-diagnostic.json',diagnostics)
    summary=dict(repository='https://github.com/angus-c/just',commit='d8c5dd18941062d8db7e9310ecc8f53fd607df54',package='just-once',version='2.2.0',
        node_version=version.stdout.strip(),rows=rows,upstream_suite='not_run',
        limits='Source inspected before analysis. No analyzer changes. Synthetic reordering and cleanup-removal diagnostic are not real upstream defects, independent validation sets, or precision/recall or LLM-benefit measurements.')
    dump(out/'summary.json',summary)
    dump(out/'reproduction_hashes.json',{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['run.py','witness.test.mjs','SOURCE_HASHES.json']})
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
