"""Commands for archived source reports, context, the report browser and MCP."""
import json
from pathlib import Path
import webbrowser

from . import archive
from .core import EvidenceError


def _json_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise EvidenceError('JSON contains duplicate key: ' + key)
        value[key] = item
    return value


def register(sub):
    parent = sub.add_parser('reports', help='Persistent reports, local browser and Codex MCP')
    commands = parent.add_subparsers(dest='report_command', required=True)
    init = commands.add_parser('init', help='Set the shared report store and optional Node executable')
    init.add_argument('--node')
    scan = commands.add_parser('scan', help='Scan a file/directory and save an immutable report plus source snapshot')
    scan.add_argument('candidate')
    scan.add_argument('--node')
    for label in ('project', 'label', 'task-id', 'parent-report-id'):
        scan.add_argument('--'+label)
    listing = commands.add_parser('list', help='List archived reports')
    for value in ('search', 'status', 'origin', 'project'):
        listing.add_argument('--'+value, default='')
    listing.add_argument('--limit', type=int, default=100)
    listing.add_argument('--offset', type=int, default=0)
    show = commands.add_parser('show', help='Read a saved report without rescanning')
    show.add_argument('report_id')
    show.add_argument('--layer', default='full')
    show.add_argument('--format', choices=['json', 'md'], default='md')
    check = commands.add_parser('verify', help='Verify archived bytes and snapshot binding')
    check.add_argument('report_id')
    context = commands.add_parser('context', help='Enrich finding evidence with definitions from the archived source snapshot')
    context.add_argument('report_id')
    context.add_argument('--finding-id')
    context.add_argument('--depth', type=int, default=1)
    context.add_argument('--max-chars', type=int, default=12000)
    context.add_argument('--aliases', default='{}', help='Explicit JSON mapping of import prefixes to snapshot-relative directories')
    context.add_argument('--node')
    context.add_argument('--format', choices=['json', 'md'], default='json')
    context.add_argument('--output', help='Write a new file; refuses overwrites')
    compare = commands.add_parser('compare', help='Compare two archived reports')
    compare.add_argument('before_id')
    compare.add_argument('after_id')
    server = commands.add_parser('serve', help='Run the local browser in the foreground')
    server.add_argument('--port', type=int, default=0)
    server.add_argument('--node')
    opening = commands.add_parser('open', help='Start/reuse the local browser and open it')
    opening.add_argument('--report-id')
    opening.add_argument('--no-browser', action='store_true')
    stop = commands.add_parser('stop', help='Stop the report browser')
    mcp = commands.add_parser('mcp', help='Serve MCP over stdio for Codex')
    mcp.add_argument('--node')
    mcp.add_argument('--report-id', help='Restrict this research session to one frozen report')
    mcp.add_argument('--layer', help='The only frozen layer exposed in a restricted research session')
    for command in (init, scan, listing, show, check, context, compare, server, opening, stop, mcp):
        command.add_argument('--store', help='Shared report directory (default: configured store)')


def run(args):
    name, store = args.report_command, args.store
    status = 0
    if name == 'init':
        value = archive.configure(store or archive.store_path(), args.node)
    elif name == 'scan':
        labels = {k: getattr(args, k) for k in ('project', 'label', 'task_id', 'parent_report_id') if getattr(args, k) is not None}
        value = archive.scan_path(args.candidate, store, args.node, **labels)['archive']
        status = 0 if value['status'] == 'parsed' else 2
    elif name == 'list':
        value = archive.list_reports(store, **{k: getattr(args, k) for k in ('search', 'status', 'origin', 'project', 'limit', 'offset')})
    elif name == 'show':
        if args.format == 'md':
            print(archive.layer_text(args.report_id, args.layer, store))
            return 0
        value = archive.read_report(args.report_id, store)
    elif name == 'verify':
        value = archive.verify(args.report_id, store)
    elif name == 'context':
        from .context import build_context, markdown
        aliases = json.loads(args.aliases, object_pairs_hook=_json_object)
        value = build_context(args.report_id, store, args.finding_id, args.depth,
                              args.max_chars, aliases, args.node)
        content = markdown(value) if args.format=='md' else json.dumps(value, ensure_ascii=False, indent=2)+'\n'
        if args.output:
            target = Path(args.output).expanduser().resolve()
            candidate = Path(archive.metadata(args.report_id, store)['candidate_root']).resolve()
            immutable = archive.store_path(store)/'runs'
            if target==immutable or immutable in target.parents:
                raise EvidenceError('Context output cannot be written inside an immutable report archive')
            if target==candidate or candidate in target.parents:
                raise EvidenceError('Context output must be outside the candidate project')
            if target.exists():
                raise EvidenceError('Output already exists; use a new path to preserve the previous record')
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('x', encoding='utf-8') as handle:
                handle.write(content)
            value = dict(output=str(Path(args.output)), schema_version=value['schema_version'], usage=value['usage'])
        else:
            print(content, end='')
            return 0
    elif name == 'compare':
        value = archive.compare_reports(args.before_id, args.after_id, store)
    elif name == 'serve':
        from .hub import serve
        serve(store, args.port, args.node)
        return 0
    elif name == 'open':
        from .hub import ensure_server
        value = ensure_server(store)
        if args.report_id:
            archive.metadata(args.report_id, store)
            value['url'] += '/#report=' + args.report_id
        if not args.no_browser:
            webbrowser.open(value['url'])
    elif name == 'stop':
        from .hub import stop_server
        value = stop_server(store)
    elif name == 'mcp':
        from .mcp_server import serve
        serve(store, args.node, args.report_id, args.layer)
        return 0
    else:
        raise EvidenceError('Unknown report command')
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return status
