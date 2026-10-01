"""CLI registration kept separate from the original research commands."""
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
    mt = commands.add_parser('measurement-template', help='Create a source-bound semantic measurement draft')
    mt.add_argument('report_id'); mt.add_argument('--finding-id'); mt.add_argument('--output', required=True)
    ma = commands.add_parser('measurement-add', help='Validate and append a semantic measurement')
    ma.add_argument('report_id'); ma.add_argument('document')
    mrt = commands.add_parser('measurement-review-template', help='Create an independent review form')
    mrt.add_argument('report_id'); mrt.add_argument('measurement_record_id'); mrt.add_argument('--reviewer', required=True); mrt.add_argument('--output', required=True)
    mra = commands.add_parser('measurement-review-add', help='Validate and append an independent review')
    mra.add_argument('report_id'); mra.add_argument('measurement_record_id'); mra.add_argument('review')
    mi = commands.add_parser('measurement-import-v06', help='Append a read-only MeasurementBench 0.6 compatibility view')
    mi.add_argument('report_id'); mi.add_argument('measurement_report')
    for command in (init, scan, listing, show, check, compare, server, opening, stop, mcp, mt, ma, mrt, mra, mi):
        command.add_argument('--store', help='Shared report directory (default: configured store)')


def _read_json(path):
    try:
        value = json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=_json_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise EvidenceError(str(path) + ': ' + str(error)) from error
    if not isinstance(value, dict):
        raise EvidenceError(str(path) + ': expected a JSON object')
    return value


def _write_new(path, value):
    target = Path(path)
    if target.exists():
        raise EvidenceError('输出已存在，请使用新路径，保留旧记录')
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write('\n')


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
    elif name == 'measurement-template':
        from .measurement import template
        value = template(args.report_id, store, args.finding_id)
        _write_new(args.output, value)
        value = {'output': str(Path(args.output)), 'schema_version': value['schema_version'],
                 'source_binding': value['source_binding'], 'workflow_status': 'draft'}
    elif name == 'measurement-add':
        value = archive.add_measurement(args.report_id, _read_json(args.document), store)
    elif name == 'measurement-review-template':
        from .measurement import review_template
        item = archive.measurement_record(args.report_id, args.measurement_record_id, store)
        value = review_template(item['measurement'], args.reviewer)
        _write_new(args.output, value)
        value = {'output': str(Path(args.output)), 'schema_version': value['schema_version'],
                 'measurement_sha256': value['measurement_sha256'], 'reviewer_id': value['reviewer_id']}
    elif name == 'measurement-review-add':
        value = archive.add_measurement_review(args.report_id, args.measurement_record_id,
                                               _read_json(args.review), store)
    elif name == 'measurement-import-v06':
        value = archive.add_legacy_measurement(args.report_id, args.measurement_report, store)
    else:
        raise EvidenceError('Unknown report command')
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return status
