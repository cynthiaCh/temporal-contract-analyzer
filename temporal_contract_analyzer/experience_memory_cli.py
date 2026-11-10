"""Explicit offline entry points for the research experience library."""
import json
from pathlib import Path

from . import experience_memory as memory
from .core import EvidenceError


def register(sub):
    parser = sub.add_parser('experience-memory', help='Offline research experience library; no model calls')
    actions = parser.add_subparsers(dest='memory_action', required=True)
    for name in ('init', 'list', 'verify', 'freeze', 'add', 'show', 'search', 'retrieve', 'import-legacy'):
        action = actions.add_parser(name)
        action.add_argument('--store', type=Path, required=True)
        action.add_argument('--output', type=Path, help='New file only; default is standard output')
        if name in ('add', 'retrieve', 'import-legacy'):
            action.add_argument('input', type=Path)
        if name == 'add':
            action.add_argument('--source', type=Path, action='append', default=[])
        if name == 'show':
            action.add_argument('sha256')
            action.add_argument('--format', choices=('json', 'md'), default='json')
        if name == 'search':
            action.add_argument('--query', required=True)
            action.add_argument('--taxonomy')
            action.add_argument('--limit', type=int, default=8)
        if name == 'retrieve':
            action.add_argument('--expected-snapshot')
        if name == 'import-legacy':
            action.add_argument('--entry-sha256', required=True)
            action.add_argument('--id', required=True)
            action.add_argument('--review', type=Path, required=True)
            action.add_argument('--source', type=Path, action='append', default=[])
            action.add_argument('--research-admitted', action='store_true',
                                help='Explicitly retain an existing reviewed research admission; not a new review')


def run(args):
    if args.output and args.output.exists():
        raise EvidenceError('Output exists; use a new path')
    if args.output and (args.output.resolve() == args.store.resolve()
                       or args.store.resolve() in args.output.resolve().parents):
        raise EvidenceError('Write command output outside the memory store')
    action = args.memory_action
    if action == 'init':
        value = memory.initialize(args.store)
    elif action == 'add':
        value = memory.add(args.store, json.loads(args.input.read_text(encoding='utf-8')), args.source)
    elif action == 'search':
        value = memory.search(args.store, args.query, args.taxonomy, args.limit)
    elif action == 'retrieve':
        value = memory.retrieve(args.store, json.loads(args.input.read_text(encoding='utf-8')),
                                args.expected_snapshot)
    elif action == 'import-legacy':
        registry = json.loads(args.input.read_text(encoding='utf-8'))
        if not isinstance(registry, list):
            raise EvidenceError('Expected a historical registry list')
        matches = [entry for entry in registry if isinstance(entry, dict) and entry.get('sha256') == args.entry_sha256]
        if len(matches) != 1:
            raise EvidenceError('Historical entry digest must identify exactly one entry')
        payload = memory.legacy_payload(matches[0], args.id, args.input, args.review, args.source,
                                        admitted=args.research_admitted)
        value = memory.add(args.store, payload, [args.input, args.review]+args.source)
    else:
        bundles = memory.records(args.store)
        if action == 'freeze':
            value = memory.snapshot(bundles)
        elif action == 'verify':
            value = dict(verified=True, records=len(bundles), lineage_tips=len(memory.tips(bundles)),
                         snapshot=memory.snapshot(bundles), semantic_validity='not_checked')
        elif action == 'show':
            value = next((b for b in bundles if b['sha256'] == args.sha256), None)
            if value is None:
                raise EvidenceError('Unknown experience digest')
            if args.format == 'md':
                value = memory.render(value)
        else:
            tips = {b['sha256'] for b in memory.tips(bundles)}
            value = [dict(id=b['id'], version=b['version'], sha256=b['sha256'],
                taxonomy_version=b['taxonomy_version'], labels=b['labels'],
                status=b['review']['status'], is_lineage_tip=b['sha256'] in tips) for b in bundles]
    content = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as stream:
            stream.write(content)
    else:
        print(content.rstrip('\n'))
    return 0
