"""CLI registration kept separate from the original research commands."""
import json
import webbrowser

from . import archive
from .core import EvidenceError


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
    for command in (init, scan, listing, show, check, compare, server, opening, stop, mcp):
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
