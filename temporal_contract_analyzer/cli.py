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
    from . import archive_cli
    archive_cli.register(sub)
    from . import taxonomy_cli
    taxonomy_cli.register(sub)
    from . import experience_memory_cli
    experience_memory_cli.register(sub)
    from . import history_cli
    history_cli.register(sub)
    from . import tempoevo_cli
    tempoevo_cli.register(sub)
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
    for cmd in (s,c):
        cmd.add_argument('--node',help='Node executable for JS/TS/Vue')
        cmd.add_argument('--view',choices=['focused','exploratory'],default='focused',help='Human-readable report view; JSON always retains raw evidence')
        cmd.add_argument('--format',choices=['json','md','html'],default='json')
        cmd.add_argument('--output',type=Path,help='New file only; refuses overwrites')
    args=p.parse_args(argv)
    try:
        if args.command == 'tempoevo':
            return tempoevo_cli.run(args)
        if args.command == 'history':
            return history_cli.run(args)
        if args.command == 'experience-memory':
            return experience_memory_cli.run(args)
        if args.command in taxonomy_cli.COMMANDS:
            return taxonomy_cli.run(args)
        if args.command == 'reports':
            return archive_cli.run(args)
        if args.command=='verify-bundle':
            from .layers import verify_bundle
            from .core import sha
            manifest=verify_bundle(args.bundle)
            if args.candidate:
                sources,skipped=collect(args.candidate)
                inputs=[dict(path=x,sha256=sha(t.encode())) for x,t in sorted(sources.items())]
                report=json.loads((args.bundle/'report.json').read_text(encoding='utf-8'))
                if inputs!=report['inputs'] or skipped!=report['skipped']:raise EvidenceError('Candidate source or exclusion scope has changed')
                verify_bundle(args.bundle,sha(canonical(inputs).encode()))
            print(json.dumps(dict(verified=True,input_sha256=manifest['input_sha256'],conditions=list(manifest['layers']),analysis_validity='not_checked'),ensure_ascii=False));return 0
        if args.command=='freeze':
            from .layers import freeze_bundle
            from .core import sha
            target=args.output.resolve();source=args.candidate.resolve()
            if target==source or source in target.parents:raise EvidenceError('Experiment reports must be written outside the candidate project')
            report=scan(args.candidate,args.node)
            sources,skipped=collect(args.candidate)
            inputs=[dict(path=x,sha256=sha(t.encode())) for x,t in sorted(sources.items())]
            if inputs!=report['inputs'] or skipped!=report['skipped']:raise EvidenceError('Candidate source changed during scanning; freeze it again')
            manifest=freeze_bundle(report,args.output,args.max_chars)
            print(json.dumps(dict(output=str(args.output),input_sha256=manifest['input_sha256'],selection_sha256=manifest['selection_sha256'],layers=manifest['layers']),ensure_ascii=False));return 0
        if args.command=='verify':
            from .core import sha
            report=json.loads(args.report.read_text(encoding='utf-8'))
            if report.get('schema_version')!='temporal-contract-analysis-1':raise EvidenceError('verify requires a single-side scan JSON report')
            sources,skipped=collect(args.candidate)
            inputs=[dict(path=x,sha256=sha(t.encode())) for x,t in sorted(sources.items())]
            if inputs!=report['inputs'] or skipped!=report['skipped']:raise EvidenceError('Inputs or exclusion scope changed; the old report cannot serve as evidence for current source')
            if sha(canonical(inputs).encode())!=report['input_sha256']:raise EvidenceError('Report input digest does not match')
            print(json.dumps(dict(input_hashes_match=True,analysis_validity='not_checked',note='Checks input binding only; does not establish analysis or contract correctness.'),ensure_ascii=False));return 0
        if args.output and args.output.exists():raise EvidenceError('Output already exists; use a new path to preserve the previous report')
        roots=[args.candidate] if args.command=='scan' else [args.before,args.after]
        if args.output and any(root.resolve()==args.output.resolve() or root.resolve() in args.output.resolve().parents for root in roots):raise EvidenceError('Write reports outside the candidate project to avoid changing or contaminating candidate inputs')
        report=scan(args.candidate,args.node) if args.command=='scan' else compare(scan(args.before,args.node),scan(args.after,args.node))
        content=json.dumps(report,ensure_ascii=False,indent=2)+'\n' if args.format=='json' else markdown(report,view=args.view) if args.format=='md' else html_report(report,view=args.view)
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            with args.output.open('x',encoding='utf-8') as f:f.write(content)
            print(json.dumps(dict(output=str(args.output),status=report.get('status','comparison'),summary=report.get('summary'),comparable=report.get('comparable')),ensure_ascii=False))
        else:print(content)
        return 0 if (report.get('status')=='parsed' or report.get('comparable') is True) else 2
    except (EvidenceError,OSError,ValueError,KeyError) as e:
        print('temporal-contract-analyzer: '+str(e),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
