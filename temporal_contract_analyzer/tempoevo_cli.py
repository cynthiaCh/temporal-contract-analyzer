"""Explicit V4 entrypoint; preparation, status and review never call a model."""
import json
from pathlib import Path
from .tempoevo_v4 import Trajectory


def register(sub):
    parser=sub.add_parser('tempoevo',help='V4 three-Action learning/testing trajectories')
    actions=parser.add_subparsers(dest='tempo_action',required=True)
    for name in ('prepare','run','status','cancel','expert-summary','publish-candidate'):
        p=actions.add_parser(name);p.add_argument('--root',type=Path,required=True)
        if name in ('prepare','expert-summary'):p.add_argument('input',type=Path)
        if name=='run':p.add_argument('--execute',action='store_true')
        if name=='publish-candidate':p.add_argument('name',choices=('success','expert'))


def run(args):
    loop=Trajectory(args.root)
    if args.tempo_action=='prepare':result=loop.prepare(json.loads(args.input.read_text()))
    elif args.tempo_action=='status':loop.verify();result=loop.report()
    elif args.tempo_action=='cancel':result=loop.cancel()
    elif args.tempo_action=='expert-summary':result=loop.submit_expert(json.loads(args.input.read_text()))
    elif args.tempo_action=='publish-candidate':result=dict(sha256=loop.publish_candidate(args.name),approved=False)
    else:
        from .tempoevo_backend import NativeV4Backend
        result=loop.run(NativeV4Backend(loop.verify()),execute=args.execute)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 1 if result.get('status') in ('execution_invalid','repair_exhausted','awaiting_expert_summary','cancelled') else 0
