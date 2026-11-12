"""Explicit offline entry points for the research experience library."""
import json
from pathlib import Path
import sys

from . import experience_memory as memory
from . import experience_approval as approval
from .core import EvidenceError


def register(sub):
    parser = sub.add_parser('experience-memory', help='Offline research experience library; no model calls')
    actions = parser.add_subparsers(dest='memory_action', required=True)
    for name in ('init', 'list', 'verify', 'freeze', 'add', 'show', 'search', 'retrieve', 'import-legacy',
                 'active', 'review-template', 'expert-review', 'recode', 'review',
                 'migrate-active', 'activate', 'rollback', 'submit'):
        action = actions.add_parser(name)
        action.add_argument('--store', type=Path, required=True)
        if name != 'review':
            action.add_argument('--output', type=Path, help='New file only; default is standard output')
        if name in ('add', 'retrieve', 'import-legacy','recode', 'migrate-active'):
            action.add_argument('input', type=Path)
        if name == 'add':
            action.add_argument('--source', type=Path, action='append', default=[])
        if name == 'show':
            action.add_argument('sha256')
            action.add_argument('--format', choices=('json', 'md'), default='json')
        if name == 'submit':
            action.add_argument('sha256')
            action.add_argument('--from-store', type=Path, required=True,
                                help='Isolated source store; copy the exact candidate into --store for review only')
        if name == 'search':
            action.add_argument('--query', required=True)
            action.add_argument('--taxonomy')
            action.add_argument('--limit', type=int, default=8)
        if name in ('list','search'):
            action.add_argument('--label',action='append',default=[],help='Native obligation label; repeat to require all')
        if name == 'retrieve':
            action.add_argument('--expected-snapshot')
            action.add_argument('--max-experiences',type=int,default=5)
            action.add_argument('--snapshot', type=Path)
        if name in ('review-template', 'expert-review'):
            action.add_argument('sha256')
        if name == 'review-template':
            action.add_argument('--full', action='store_true', help='Review every rule instead of referencing unchanged accepted parent findings')
        if name == 'expert-review':
            action.add_argument('--decision', type=Path, required=True)
            mode=action.add_mutually_exclusive_group()
            mode.add_argument('--review-only', action='store_true', help='Record acceptance only (the default)')
            mode.add_argument('--activate', action='store_true', help='Explicitly request activation after both gates pass')
            action.add_argument('--expected-current', help='Expected active digest, or none')
        if name in ('activate', 'rollback'):
            action.add_argument('sha256')
            action.add_argument('--expected-current', required=True, help='Expected active digest, or none')
        if name in ('activate', 'rollback', 'migrate-active'):
            action.add_argument('--actor', required=True, help='Actual operator or explicitly authorized technical actor')
            action.add_argument('--reason', default='')
        if name == 'review':
            action.add_argument('sha256', nargs='?', help='Optional exact experience version to open')
            action.add_argument('--port', type=int, default=0)
            action.add_argument('--no-browser', action='store_true')
        if name == 'recode':
            action.add_argument('--parent',required=True)
            action.add_argument('--version',required=True)
        if name == 'import-legacy':
            action.add_argument('--entry-sha256', required=True)
            action.add_argument('--id', required=True)
            action.add_argument('--review', type=Path, required=True)
            action.add_argument('--source', type=Path, action='append', default=[])
            action.add_argument('--research-admitted', action='store_true',
                                help='Explicitly retain an existing reviewed research admission; not a new review')


def run(args):
    if args.memory_action == 'review':
        from .memory_review import serve
        return serve(args.store, args.sha256, args.port, not args.no_browser)
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
    elif action == 'submit':
        from .experience_submission import submit
        value = submit(args.from_store, args.store, args.sha256)
    elif action == 'search':
        value = memory.search(args.store, args.query, args.taxonomy, args.limit,args.label)
    elif action == 'retrieve':
        value = memory.retrieve(args.store, json.loads(args.input.read_text(encoding='utf-8')),
                                args.expected_snapshot, None if args.snapshot is None else
                                json.loads(args.snapshot.read_text(encoding='utf-8')), max_experiences=args.max_experiences)
    elif action == 'active':
        value = approval.active(args.store)
    elif action == 'migrate-active':
        value = approval.migrate_active(args.store, json.loads(args.input.read_text(encoding='utf-8')),
                                        args.actor, args.reason)
    elif action in ('activate', 'rollback'):
        value = approval.activate(args.store, args.sha256,
            None if args.expected_current == 'none' else args.expected_current,
            args.actor, args.reason, rollback=action == 'rollback')
    elif action == 'expert-review':
        expected = approval.UNSPECIFIED if args.expected_current is None else (
            None if args.expected_current == 'none' else args.expected_current)
        value = approval.decide(args.store, args.sha256, json.loads(args.decision.read_text(encoding='utf-8')),
            activate_version=args.activate, expected_current=expected)
    elif action == 'recode':
        from .experience_recoding import candidate
        value=candidate(args.store,args.parent,args.input,args.version)
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
            value = approval.freeze(args.store)
        elif action == 'verify':
            value = dict(verified=True, records=len(bundles), lineage_tips=len(memory.tips(bundles)),
                         snapshot=memory.snapshot(bundles), active_versions=len(approval.active(args.store)),
                         default_active_versions=len(approval.freeze(args.store)['entries']),
                         semantic_validity='not_checked')
        elif action in ('show', 'review-template'):
            value = next((b for b in bundles if b['sha256'] == args.sha256), None)
            if value is None:
                raise EvidenceError('Unknown experience digest')
            if action == 'review-template':
                value = approval.review_template(args.store, args.sha256, full=args.full)
            elif args.format == 'md':
                value = memory.render(value)
        else:
            from . import taxonomy
            tips = {b['sha256'] for b in memory.tips(bundles)}
            required=taxonomy.labels(args.label)
            bundles=[b for b in bundles if set(required)<=set(b['labels'])]
            activated={row['bundle']['sha256'] for row in approval.active(args.store)}
            eligible = {row['bundle']['sha256'] for row in approval.approved(args.store)}
            value = [dict(id=b['id'], version=b['version'], sha256=b['sha256'],
                taxonomy_version=b['taxonomy_version'], labels=b['labels'],
                status=b['review']['status'], expert_active=b['sha256'] in activated,
                default_eligible=b['sha256'] in eligible,
                is_lineage_tip=b['sha256'] in tips) for b in bundles]
    content = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as stream:
            stream.write(content)
        print('Saved: ' + str(args.output.resolve()), file=sys.stderr)
    else:
        print(content.rstrip('\n'))
    return 0
