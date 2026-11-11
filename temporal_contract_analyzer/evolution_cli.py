"""Explicit prepare/run/review entry points; no background model startup."""
import json
from pathlib import Path

from .core import EvidenceError
from .experience_evolution import Evolution


def register(sub):
    parser=sub.add_parser('experience-evolution',help='Bounded automation with unified memory review')
    actions=parser.add_subparsers(dest='evolution_action',required=True)
    for name in ('prepare','run','status','report','review-analysis','review-candidate','docker-check','docker-calibrate'):
        action=actions.add_parser(name)
        action.add_argument('--root',type=Path,required=True)
        if name in ('prepare','review-analysis','review-candidate','docker-check','docker-calibrate'):action.add_argument('input',type=Path)
        if name == 'run':action.add_argument('--execute',action='store_true')


def run(args):
    loop=Evolution(args.root)
    action=args.evolution_action
    if action=='prepare':
        data=json.loads(args.input.read_text(encoding='utf-8'))
        if not isinstance(data,dict):raise EvidenceError('Configuration must be an object')
        if data.get('kind','development')=='development':
            from .experience_development import Development
            loop=Development(args.root)
        elif data.get('kind')=='evaluation':
            from .experience_evaluation import Evaluation
            loop=Evaluation(args.root)
        else:raise EvidenceError('Choose development or evaluation')
        result=loop.prepare_config(data)
    elif action in ('docker-check','docker-calibrate'):
        from .docker_backend import offline
        result=offline(json.loads(args.input.read_text(encoding='utf-8')),args.root,
                       calibrate=action=='docker-calibrate')
    else:
        version=json.loads((args.root/'protocol.json').read_text())['schema_version']
        if version=='experience-development-v2':
            from .experience_development import Development
            loop=Development(args.root)
        elif version=='experience-evaluation-v2':
            from .experience_evaluation import Evaluation
            loop=Evaluation(args.root)
        elif action not in ('status','report'):
            raise EvidenceError('Historical v1 batches remain readable; prepare a new v2 batch rather than resuming them')
        if action=='run':result=loop.run(execute=args.execute)
        elif action=='review-analysis':result=loop.review_analysis(json.loads(args.input.read_text(encoding='utf-8')))
        elif action=='review-candidate':
            if version!='experience-development-v2':raise EvidenceError('Evaluation never learns')
            result=loop.review_candidate(json.loads(args.input.read_text(encoding='utf-8')))
        else:
            loop.verify()
            if action=='report':loop.report()
            result=loop.sync_review()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 1 if result['status'] in ('stopped','cancelled','reflection_incomplete') else 0
