"""Explicit prepare/run/review entry points; no background model startup."""
import json
from pathlib import Path

from .core import EvidenceError
from .experience_evolution import Evolution


def register(sub):
    parser=sub.add_parser('experience-evolution',help='Bounded automation with an external expert activation gate')
    actions=parser.add_subparsers(dest='evolution_action',required=True)
    for name in ('prepare','run','status','report','expert','docker-check','docker-calibrate'):
        action=actions.add_parser(name)
        action.add_argument('--root',type=Path,required=True)
        if name in ('prepare','expert','docker-check','docker-calibrate'):action.add_argument('input',type=Path)
        if name in ('run','expert'):action.add_argument('--execute',action='store_true')


def run(args):
    loop=Evolution(args.root)
    action=args.evolution_action
    if action=='prepare':
        data=json.loads(args.input.read_text(encoding='utf-8'))
        required={'case_id','visible','store','binary','node','calibration','source_relationship'}
        if not isinstance(data,dict) or not required<=set(data) or set(data)-required-{'kind','max_rounds','backend'}:
            raise EvidenceError('Invalid evolution configuration fields')
        result=loop.prepare(**data)
    elif action in ('docker-check','docker-calibrate'):
        from .docker_backend import offline
        result=offline(json.loads(args.input.read_text(encoding='utf-8')),args.root,
                       calibrate=action=='docker-calibrate')
    elif action=='run':result=loop.run(execute=args.execute)
    elif action=='expert':result=loop.expert(json.loads(args.input.read_text(encoding='utf-8')),execute=args.execute)
    else:
        loop.verify()
        if action=='report':loop.report()
        result=loop.state()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 1 if result['status'] in ('stopped','cancelled') else 0
