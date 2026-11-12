"""Explicit prepare/run/review entry points; no background model startup."""
import json
from pathlib import Path

from .core import EvidenceError
from .experience_evolution import Evolution


def register(sub):
    parser=sub.add_parser('experience-evolution',help='Bounded automation with unified memory review')
    actions=parser.add_subparsers(dest='evolution_action',required=True)
    for name in ('prepare','run','work','cancel','status','report','review-analysis','review-candidate','docker-check','docker-calibrate'):
        action=actions.add_parser(name)
        action.add_argument('--root',type=Path,required=True)
        if name in ('prepare','review-analysis','review-candidate','docker-check','docker-calibrate'):action.add_argument('input',type=Path)
        if name in ('run','work'):action.add_argument('--execute',action='store_true')
        if name=='work':
            action.add_argument('--watch',action='store_true')
            action.add_argument('--poll-seconds',type=float,default=2)


def run(args):
    loop=Evolution(args.root)
    action=args.evolution_action
    if action=='prepare':
        data=json.loads(args.input.read_text(encoding='utf-8'))
        if not isinstance(data,dict):raise EvidenceError('Configuration must be an object')
        if data.get('kind','development')=='development':
            from .experience_workflow import Workflow
            loop=Workflow(args.root)
        elif data.get('kind')=='evaluation':
            from .experience_workflow import FrozenEvaluation
            loop=FrozenEvaluation(args.root)
        else:raise EvidenceError('Choose development or evaluation')
        result=loop.prepare_config(data)
    elif action in ('docker-check','docker-calibrate'):
        from .docker_backend import offline
        result=offline(json.loads(args.input.read_text(encoding='utf-8')),args.root,
                       calibrate=action=='docker-calibrate')
    else:
        version=json.loads((args.root/'protocol.json').read_text())['schema_version']
        if version in ('experience-development-v3','experience-evaluation-v3'):
            from .experience_workflow import Workflow,FrozenEvaluation
            loop=Workflow(args.root) if version=='experience-development-v3' else FrozenEvaluation(args.root)
        elif version=='experience-development-v2':
            from .experience_development import Development
            loop=Development(args.root)
        elif version=='experience-evaluation-v2':
            from .experience_evaluation import Evaluation
            loop=Evaluation(args.root)
        elif action not in ('status','report'):
            raise EvidenceError('Historical v1 batches remain readable; prepare a new v2 batch rather than resuming them')
        if action in ('run','work'):
            if action=='work' and version!='experience-development-v3':raise EvidenceError('The worker requires a v3 development root')
            if action=='work' and not .1<=args.poll_seconds<=60:raise EvidenceError('Poll interval must be 0.1..60 seconds')
            result=loop.run(execute=args.execute)
            if action=='work' and args.watch:
                import time
                while result['status'] not in ('no_update','cancelled','infrastructure_error','budget_exhausted','ai_contract_failed','ai_candidate_failed','ai_check_incomplete'):
                    time.sleep(args.poll_seconds);result=loop.run(execute=True)
        elif action=='cancel':
            if version!='experience-development-v3':raise EvidenceError('Persistent cancellation requires a v3 development root')
            from . import experience_lifecycle
            result=experience_lifecycle.cancel(args.root)
        elif action=='review-analysis':
            if version in ('experience-development-v3','experience-evaluation-v3'):raise EvidenceError('V3 semantic checks execute automatically; manual review files cannot bypass them')
            result=loop.review_analysis(json.loads(args.input.read_text(encoding='utf-8')))
        elif action=='review-candidate':
            if version!='experience-development-v2':raise EvidenceError('Evaluation never learns')
            result=loop.review_candidate(json.loads(args.input.read_text(encoding='utf-8')))
        else:
            loop.verify()
            if action=='report':loop.report()
            result=loop.sync_review()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 1 if result['status'] in ('stopped','cancelled','reflection_incomplete','infrastructure_error',
        'budget_exhausted','ai_contract_failed','ai_candidate_failed','ai_check_incomplete') else 0
