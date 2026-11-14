"""Explicit trajectory entrypoint; preparation, status and review never call a model."""
import json
from pathlib import Path
from .tempoevo_v4 import Trajectory


def register(sub):
    parser=sub.add_parser('tempoevo',help='V8 three-Action learning/testing trajectories')
    actions=parser.add_subparsers(dest='tempo_action',required=True)
    for name in ('prepare','run','status','cancel','expert-summary','publish-candidate'):
        p=actions.add_parser(name);p.add_argument('--root',type=Path,required=True)
        if name in ('prepare','expert-summary'):p.add_argument('input',type=Path)
        if name=='prepare':
            p.add_argument('--model-config',type=Path)
            p.add_argument('--model-profile')
            p.add_argument('--learning-policy',choices=['frozen','online'])
            p.add_argument('--online-memory',type=Path)
        if name=='run':p.add_argument('--execute',action='store_true')
        if name=='publish-candidate':p.add_argument('name',choices=('success','expert'))


def run(args):
    loop=Trajectory(args.root)
    if args.tempo_action=='prepare':
        config=json.loads(args.input.read_text())
        for key in ('model_config','model_profile','learning_policy','online_memory'):
            value=getattr(args,key,None)
            if value is not None:config[key]=str(value)
        result=loop.prepare(config)
    elif args.tempo_action=='status':
        # Historical inspection must not execute, rewrite archives, or require
        # today's runtime to match a completed trajectory's implementation.
        result=json.loads((loop.root/'summary.json').read_text())
        state=loop.state();result.update(status=state['status'],stages=state['stages'],error=state.get('error'))
    elif args.tempo_action=='cancel':result=loop.cancel()
    elif args.tempo_action=='expert-summary':result=loop.submit_expert(json.loads(args.input.read_text()))
    elif args.tempo_action=='publish-candidate':
        code=loop.publish_candidate(args.name)
        candidate=json.loads((loop.root/'candidate-pool'/(args.name+'.json')).read_text())
        result=dict(sha256=code,kind=candidate['publication_kind'],reflection_update=candidate['reflection_update'],approved=False)
    else:
        from .core import EvidenceError
        from .tempoevo_backend import NativeV4Backend
        protocol=loop.verify()
        if protocol.get('backend',{}).get('kind')!='docker':
            raise EvidenceError('New live training requires backend.kind=docker; prepare a new Docker trajectory')
        if any(protocol.get(key) and not protocol[key].get('image') for key in ('visible_evaluator','training_evaluator','gold_evaluator')):
            raise EvidenceError('Docker training requires containerized visible and gold evaluators')
        result=loop.run(NativeV4Backend(protocol),execute=args.execute)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 1 if result.get('status') in ('execution_invalid','repair_exhausted','awaiting_expert_summary','cancelled') else 0
