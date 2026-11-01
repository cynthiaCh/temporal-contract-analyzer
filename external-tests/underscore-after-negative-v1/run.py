#!/usr/bin/env python3
"""An activation counter negative control, not an injected once-style defect."""
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
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--node',default='/Applications/Visual Studio Code.app/Contents/MacOS/Code')
    args=p.parse_args()
    for name,digest in json.loads((HERE/'SOURCE_HASHES.json').read_text()).items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest,name
    env=dict(os.environ,ELECTRON_RUN_AS_NODE='1')
    version=subprocess.run([args.node,'--version'],env=env,text=True,capture_output=True,timeout=10)
    assert version.returncode==0 and int(version.stdout.strip().lstrip('v').split('.')[0])>=22
    out=args.output.resolve()
    assert out!=HERE and out!=HERE/'upstream' and HERE/'upstream' not in out.parents
    out.mkdir(parents=True,exist_ok=False)
    original=(HERE/'upstream/modules/after.js').read_text()
    before='    if (--times < 1) {\n      return func.apply(this, arguments);\n    }'
    after='    var result;\n    if (times < 2) {\n      result = func.apply(this, arguments);\n    }\n    --times;\n    return result;'
    assert original.count(before)==1
    sources=dict(original=original,reordered_valid_control=original.replace(before,after,1))
    reports,rows={},[]
    for name,source in sources.items():
        folder=out/name;folder.mkdir()
        (folder/'source.js').write_text(source)
        report=analyze_sources({'after.js':source},node=args.node)
        reports[name]=report
        focused=focused_review(report)
        dump(folder/'report.json',report);dump(folder/'focused.json',focused)
        (folder/'focused.md').write_text(markdown(report))
        (folder/'focused.html').write_text(html_report(report))
        (folder/'exploratory.md').write_text(markdown(report,view='exploratory'))
        with tempfile.TemporaryDirectory(prefix='tca-underscore-after-') as directory:
            temp=Path(directory)
            (temp/'after.mjs').write_text(source)
            shutil.copyfile(HERE/'witness.test.mjs',temp/'witness.test.mjs')
            runtime_env=dict(env,TCA_MODULE=str(temp/'after.mjs'),TCA_OBSERVATIONS=str(folder/'observations.json'))
            result=subprocess.run([args.node,'--test','--test-reporter=tap',str(temp/'witness.test.mjs')],
                env=runtime_env,text=True,capture_output=True,timeout=30)
        (folder/'runtime.tap').write_text(result.stdout);(folder/'runtime.stderr').write_text(result.stderr)
        counts={k:int(re.search(r'^# '+k+r' (\d+)$',result.stdout,re.M).group(1)) for k in ['tests','pass','fail','cancelled','skipped','todo']}
        assert counts==dict(tests=6,**{'pass':6},fail=0,cancelled=0,skipped=0,todo=0)
        assert result.returncode==0
        rows.append(dict(name=name,input_kind='unmodified_upstream_helper' if name=='original' else 'researcher_reordering_negative_control_not_fault',
            source_lines=len(source.splitlines()),status=report['status'],raw_hints=report['summary']['review_hints'],focused_cards=len(focused['cards']),
            tool_version=report['tool_version'],tool_sha256=report['tool_sha256'],input_sha256=report['input_sha256'],
            tests=counts,runtime_exit_code=result.returncode,observations=json.loads((folder/'observations.json').read_text())))
    assert rows[0]['observations']==rows[1]['observations']
    change=compare(reports['original'],reports['reordered_valid_control'])
    dump(out/'comparison.json',change);(out/'comparison.html').write_text(html_report(change))
    (out/'reordered-control.patch').write_text(''.join(difflib.unified_diff(original.splitlines(keepends=True),sources['reordered_valid_control'].splitlines(keepends=True),fromfile='original/after.js',tofile='reordered_valid_control/after.js')))
    provenance=json.loads((HERE/'PROVENANCE.json').read_text())
    summary=dict(repository=provenance['repository'],commit=provenance['commit'],package_version=provenance['package_version'],
        node_version=version.stdout.strip(),rows=rows,upstream_suite='not_run',
        interpretation='Both versions pass the chosen finite-integer activation tests, including two intended reentrant callbacks. No issue is injected or claimed. '
                       'Current numeric rule does not model this < activation predicate, so zero cards do not prove semantic understanding or overall precision.')
    dump(out/'summary.json',summary)
    dump(out/'reproduction_hashes.json',{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['run.py','witness.test.mjs','SOURCE_HASHES.json']})
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
