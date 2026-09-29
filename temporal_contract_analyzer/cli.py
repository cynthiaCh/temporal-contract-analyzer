#!/usr/bin/env python3
"""Analyze source-derived temporal-contract evidence without executing candidates."""
import argparse
import json
from pathlib import Path
import sys
from .core import EvidenceError, collect, scan, compare, canonical
from .report import markdown, html_report


def main(argv=None):
    p=argparse.ArgumentParser(prog='temporal-contract-analyzer', description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    s=sub.add_parser('scan',help='Analyze an explicit candidate root, e.g. case/base')
    s.add_argument('candidate',type=Path)
    c=sub.add_parser('compare',help='Compare two candidate roots; never apply or execute patches')
    c.add_argument('before',type=Path);c.add_argument('after',type=Path)
    v=sub.add_parser('verify',help='Verify report input hashes against current source; does not rerun analysis')
    v.add_argument('report',type=Path);v.add_argument('candidate',type=Path)
    f=sub.add_parser('freeze',help='Freeze complete scan as source-report and open-review experiment inputs')
    f.add_argument('candidate',type=Path);f.add_argument('--output',type=Path,required=True)
    f.add_argument('--node',help='Node executable for JS/TS/Vue')
    f.add_argument('--max-chars',type=int,help='Reject bundle if any layer exceeds this length; never truncate')
    b=sub.add_parser('verify-bundle',help='Verify frozen files, hashes and deterministic rendering')
    b.add_argument('bundle',type=Path);b.add_argument('--candidate',type=Path)
    pe=sub.add_parser('profile',help='Freeze researcher-side profile evidence from a review packet; never an agent input')
    pe.add_argument('packet',type=Path);pe.add_argument('--output',type=Path,required=True)
    pv=sub.add_parser('verify-profile',help='Verify profile sidecar against frozen review packet bytes and metadata')
    pv.add_argument('evidence',type=Path);pv.add_argument('packet',type=Path)
    for cmd in (s,c):
        cmd.add_argument('--node',help='Node executable for JS/TS/Vue')
        cmd.add_argument('--format',choices=['json','md','html'],default='json')
        cmd.add_argument('--output',type=Path,help='New file only; refuses overwrites')
    args=p.parse_args(argv)
    try:
        if args.command in {'profile','verify-profile'}:
            from .profile import build_profile_evidence, verify_profile_evidence
            packet=json.loads(args.packet.read_text(encoding='utf-8'))
            if args.command=='verify-profile':
                evidence=json.loads(args.evidence.read_text(encoding='utf-8'))
                print(json.dumps(verify_profile_evidence(packet,evidence),ensure_ascii=False));return 0
            if args.output.exists():raise EvidenceError('输出已存在，请使用新路径，保留旧证据卡')
            evidence=build_profile_evidence(packet)
            args.output.parent.mkdir(parents=True,exist_ok=True)
            with args.output.open('x',encoding='utf-8') as target:target.write(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps(dict(output=str(args.output),evidence_hash=evidence['evidence_hash'],coverage=evidence['coverage'],semantic_validity='not_checked'),ensure_ascii=False));return 0
        if args.command=='verify-bundle':
            from .layers import verify_bundle
            from .core import sha
            manifest=verify_bundle(args.bundle)
            if args.candidate:
                sources,skipped=collect(args.candidate)
                inputs=[dict(path=x,sha256=sha(t.encode())) for x,t in sorted(sources.items())]
                report=json.loads((args.bundle/'report.json').read_text(encoding='utf-8'))
                if inputs!=report['inputs'] or skipped!=report['skipped']:raise EvidenceError('候选源码/排除范围已变化')
                verify_bundle(args.bundle,sha(canonical(inputs).encode()))
            print(json.dumps(dict(verified=True,input_sha256=manifest['input_sha256'],conditions=list(manifest['layers']),analysis_validity='not_checked'),ensure_ascii=False));return 0
        if args.command=='freeze':
            from .layers import freeze_bundle
            from .core import sha
            target=args.output.resolve();source=args.candidate.resolve()
            if target==source or source in target.parents:raise EvidenceError('实验报告必须写在候选工程外')
            report=scan(args.candidate,args.node)
            sources,skipped=collect(args.candidate)
            inputs=[dict(path=x,sha256=sha(t.encode())) for x,t in sorted(sources.items())]
            if inputs!=report['inputs'] or skipped!=report['skipped']:raise EvidenceError('扫描过程中候选源码变化，请重新冻结')
            manifest=freeze_bundle(report,args.output,args.max_chars)
            print(json.dumps(dict(output=str(args.output),input_sha256=manifest['input_sha256'],selection_sha256=manifest['selection_sha256'],layers=manifest['layers']),ensure_ascii=False));return 0
        if args.command=='verify':
            from .core import sha
            report=json.loads(args.report.read_text(encoding='utf-8'))
            if report.get('schema_version')!='temporal-contract-analysis-1':raise EvidenceError('verify 需要单侧 scan JSON 报告')
            sources,skipped=collect(args.candidate)
            inputs=[dict(path=x,sha256=sha(t.encode())) for x,t in sorted(sources.items())]
            if inputs!=report['inputs'] or skipped!=report['skipped']:raise EvidenceError('输入文件/排除范围已变化，旧报告不能作为当前源码证据')
            if sha(canonical(inputs).encode())!=report['input_sha256']:raise EvidenceError('报告输入摘要不一致')
            print(json.dumps(dict(input_hashes_match=True,analysis_validity='not_checked',note='只校验输入绑定，不证明分析结果或契约正确。'),ensure_ascii=False));return 0
        if args.output and args.output.exists():raise EvidenceError('输出已存在，请使用新路径，保留旧报告')
        roots=[args.candidate] if args.command=='scan' else [args.before,args.after]
        if args.output and any(root.resolve()==args.output.resolve() or root.resolve() in args.output.resolve().parents for root in roots):raise EvidenceError('报告必须写在候选工程外，避免改变或污染候选输入')
        report=scan(args.candidate,args.node) if args.command=='scan' else compare(scan(args.before,args.node),scan(args.after,args.node))
        content=json.dumps(report,ensure_ascii=False,indent=2)+'\n' if args.format=='json' else markdown(report) if args.format=='md' else html_report(report)
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            with args.output.open('x',encoding='utf-8') as f:f.write(content)
            print(json.dumps(dict(output=str(args.output),status=report.get('status','comparison'),summary=report.get('summary'),comparable=report.get('comparable')),ensure_ascii=False))
        else:print(content)
        return 0 if (report.get('status')=='parsed' or report.get('comparable') is True) else 2
    except (EvidenceError,OSError,ValueError,KeyError) as e:
        print('temporal-contract-analyzer: '+str(e),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
