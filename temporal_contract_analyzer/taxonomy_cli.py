"""Offline taxonomy and explicit-input routing commands; no experiment launch path."""
import json
from pathlib import Path

from .core import EvidenceError
from . import taxonomy, experience_routing

COMMANDS = ('taxonomy', 'experience-prompt', 'experience-review-template', 'route-experience', 'maintenance-prompt')


def register(sub):
    parser = sub.add_parser('taxonomy', help='Show the canonical seven obligation labels')
    parser.add_argument('--format', choices=['json', 'md', 'schema'], default='md')
    parser.add_argument('--output', type=Path)
    for command in COMMANDS[1:]:
        parser = sub.add_parser(command, help='Prepare or route explicit public inputs offline; never calls a model')
        parser.add_argument('input', type=Path)
        parser.add_argument('--output', type=Path)


def run(args):
    if args.output and args.output.exists():
        raise EvidenceError('Output exists; use a new path to preserve prior evidence')
    if args.command == 'taxonomy':
        value = taxonomy.markdown() if args.format == 'md' else (
            taxonomy.analysis_schema() if args.format == 'schema' else taxonomy.definition())
    else:
        data = json.loads(args.input.read_text(encoding='utf-8'))
        required = {'task', 'sources'}
        optional = set()
        if args.command == 'experience-prompt':
            optional = {'AST'}
        else:
            required.add('analysis')
        if args.command == 'route-experience':
            required.add('library')
            optional = {'review'}
        if not isinstance(data, dict) or not required <= set(data) or set(data) - required - optional:
            raise EvidenceError('Invalid explicit input fields; no case IDs, historical scores or legacy classes')
        if args.command == 'experience-prompt':
            value = experience_routing.analysis_prompt(data['task'], data['sources'], data.get('AST'))
        elif args.command == 'experience-review-template':
            value = experience_routing.review_template(data['analysis'], data['task'], data['sources'])
        elif args.command == 'maintenance-prompt':
            codes = experience_routing.validate_analysis(data['analysis'], data['task'], data['sources'])
            value = experience_routing.maintenance_prompt(data['task'], data['analysis']['contract'],
                                                          obligation_labels=codes)
        else:
            value = experience_routing.route(data['analysis'], data['sources'], data['library'],
                                             task=data['task'], review=data.get('review'))
    content = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as target:
            target.write(content.rstrip('\n') + '\n')
    else:
        print(content.rstrip('\n'))
    return 0
