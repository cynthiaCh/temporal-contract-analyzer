"""Append-only local reports shared by CLI, editor and MCP. No candidate execution."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
import uuid

from .core import (EvidenceError, EXCLUDED, MAX_FILE, MAX_TOTAL, ROOT, VERSION,
                   analyze_sources, canonical, collect, compare, sha)
from .layers import freeze_bundle, verify_bundle
from .report import markdown, html_report

ARCHIVE_SCHEMA = 'temporal-report-archive-1'
ID_PATTERN = re.compile(r'^r-[0-9]{8}T[0-9]{12}Z-[0-9a-f]{12}$')


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def config_path():
    return Path(os.environ.get('TCA_CONFIG', str(Path.home()/'.temporal-contract-analyzer/config.json'))).expanduser()


def configuration():
    path = config_path()
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise EvidenceError('Invalid report-center configuration')
    return value


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.write-', dir=str(path.parent))
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as target:
            json.dump(value, target, ensure_ascii=False, sort_keys=True, indent=2)
            target.write('\n')
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def configure(store, node=None):
    current = configuration()
    current['store'] = str(Path(store).expanduser().resolve())
    if node:
        current['node'] = str(Path(node).expanduser().resolve()) if os.path.sep in node else node
    atomic_json(config_path(), current)
    return current


def store_path(store=None):
    value = store or os.environ.get('TCA_REPORT_STORE') or configuration().get('store')
    return Path(value or Path.home()/'.temporal-contract-analyzer/reports').expanduser().resolve()


def source_path(value):
    if not isinstance(value, str) or not value or '\\' in value:
        raise EvidenceError('Invalid relative source path')
    p = PurePosixPath(value)
    if p.is_absolute() or '..' in p.parts or str(p) != value:
        raise EvidenceError('Invalid relative source path')
    if any(part in EXCLUDED or part.startswith('.') for part in p.parts):
        raise EvidenceError('Excluded source path: ' + value)
    return value


def check_sources(sources):
    if not isinstance(sources, dict) or len(sources) > 1000:
        raise EvidenceError('Expected at most 1000 source files')
    total = 0
    for name, text in sources.items():
        source_path(name)
        if not isinstance(text, str):
            raise EvidenceError('Expected source text')
        size = len(text.encode('utf-8'))
        total += size
        if size > MAX_FILE or total > MAX_TOTAL:
            raise EvidenceError('源码超过扫描范围（单文件 1 MiB / 合计 25 MiB / 1000 文件）')


def capture(request):
    """One input capture shared by analysis and archival, including dirty buffers."""
    mode = request.get('mode', 'folder')
    if mode == 'file':
        sources = {source_path(request['path']): request['text']}
        skipped = []
        overlays = list(sources) if request.get('input_kind') != 'disk' else []
    elif mode == 'folder':
        sources, skipped = collect(request['root'])
        overlays = []
        for name, text in request.get('overlays', {}).items():
            if name in sources:
                sources[source_path(name)] = text
                overlays.append(name)
    else:
        raise EvidenceError('Unknown scan mode')
    check_sources(sources)
    return sources, skipped, sorted(overlays)


def request_for_path(candidate):
    candidate = Path(candidate).expanduser()
    if candidate.is_symlink():
        raise EvidenceError('不能扫描符号链接')
    if candidate.is_file():
        if candidate.stat().st_size > MAX_FILE:
            raise EvidenceError('源码超过扫描范围（单文件 1 MiB）')
        # Preserve exclusion checks even for a directly supplied file path.
        if any(part in EXCLUDED or part.startswith('.') for part in candidate.absolute().parts[1:]):
            raise EvidenceError('Excluded source path')
        return dict(mode='file', root=str(candidate.parent.resolve()), path=candidate.name,
                    text=candidate.read_bytes().decode('utf-8'), input_kind='disk')
    return dict(mode='folder', root=str(candidate.absolute()), input_kind='disk')


def editor_ranges(report, sources):
    ranges = {}
    for file in report['files']:
        lines = sources[file['path']].splitlines()
        def column(line, offset):
            if file.get('column_unit') != 'utf8_bytes':
                return offset
            text = lines[line-1] if 0 < line <= len(lines) else ''
            return len(text.encode('utf-8')[:offset].decode('utf-8').encode('utf-16-le')) // 2
        for event in file['events']:
            ranges[event['id']] = [event['line']-1, column(event['line'], event['column']),
                                   event['end_line']-1, column(event['end_line'], event['end_column'])]
    return ranges


def _report_dir(store, report_id):
    if not isinstance(report_id, str) or not ID_PATTERN.fullmatch(report_id):
        raise EvidenceError('Invalid report ID')
    root = store_path(store)/'runs'/report_id
    if root.is_symlink() or not root.is_dir() or root.parent.is_symlink():
        raise EvidenceError('Report not found: ' + report_id)
    return root


def _read(path):
    if path.is_symlink() or not path.is_file():
        raise EvidenceError('Missing or symlinked archive file: ' + path.name)
    return json.loads(path.read_text(encoding='utf-8'))


def metadata(report_id, store=None):
    value = _read(_report_dir(store, report_id)/'metadata.json')
    if value.get('report_id') != report_id or value.get('schema_version') != ARCHIVE_SCHEMA:
        raise EvidenceError('Invalid archive metadata')
    return value


def verify(report_id, store=None):
    root = _report_dir(store, report_id)
    manifest = _read(root/'manifest.json')
    if manifest.get('schema_version') != ARCHIVE_SCHEMA or manifest.get('report_id') != report_id:
        raise EvidenceError('Invalid archive manifest')
    files = manifest.get('files', {})
    if not isinstance(files, dict) or not {'metadata.json', 'snapshot.json'}.issubset(files):
        raise EvidenceError('Incomplete archive manifest')
    actual = set()
    for path in root.rglob('*'):
        if path.is_symlink():
            raise EvidenceError('Archive contains symlink')
        if path.is_file() and path.name != 'manifest.json':
            actual.add(path.relative_to(root).as_posix())
        elif path.is_file() and path != root/'manifest.json':
            actual.add(path.relative_to(root).as_posix())
    if actual != set(files):
        raise EvidenceError('Archive inventory changed')
    for name, digest in files.items():
        p = PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or '\\' in name:
            raise EvidenceError('Invalid archive artifact path')
        if sha((root/name).read_bytes()) != digest:
            raise EvidenceError('Archive checksum mismatch: ' + name)
    snapshot = _read(root/'snapshot.json')
    check_sources(snapshot['sources'])
    meta = metadata(report_id, store)
    if meta['status'] != 'failed':
        report = _read(root/'report.json')
        inputs = [dict(path=p, sha256=sha(t.encode('utf-8'))) for p, t in sorted(snapshot['sources'].items())]
        if report['inputs'] != inputs or report['input_sha256'] != sha(canonical(inputs).encode('utf-8')):
            raise EvidenceError('Snapshot and report input binding differ')
        if report['skipped'] != snapshot['skipped']:
            raise EvidenceError('Snapshot exclusion inventory differs')
        if meta['input_sha256'] != report['input_sha256'] or meta['status'] != report['status']:
            raise EvidenceError('Metadata and report differ')
        if (root/'bundle').exists():
            verify_bundle(root/'bundle', report['input_sha256'])
    return dict(verified=True, report_id=report_id, files=len(files), analysis_validity='not_checked')


def persist(sources, skipped, report, request, store=None, origin='cli', error=None):
    archive = store_path(store)
    candidate = Path(request['root']).expanduser().resolve()
    if candidate == archive or candidate in archive.parents or archive in candidate.parents:
        raise EvidenceError('报告库与候选工程必须分开放置，不能互相包含')
    check_sources(sources)
    scope = dict(mode=request.get('mode', 'folder'), path=request.get('path') if request.get('mode') == 'file' else None)
    project_id = sha(str(candidate).encode('utf-8'))[:16]
    parent = request.get('parent_report_id') or None
    if parent:
        previous = metadata(parent, archive)
        if previous['project_id'] != project_id or previous['scope'] != scope:
            raise EvidenceError('前后报告必须属于同一项目和扫描范围')
    report_id = 'r-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:12]
    runs = archive/'runs'
    runs.mkdir(parents=True, exist_ok=True)
    if runs.is_symlink():
        raise EvidenceError('Archive runs directory must not be a symlink')
    stage = Path(tempfile.mkdtemp(prefix='.pending-', dir=str(runs)))
    try:
        atomic_json(stage/'snapshot.json', dict(sources=sources, skipped=skipped))
        layers = []
        if report:
            atomic_json(stage/'report.json', report)
            (stage/'report.md').write_text(markdown(report), encoding='utf-8')
            (stage/'report.html').write_text(html_report(report), encoding='utf-8')
            if report['status'] == 'parsed':
                bundle = freeze_bundle(report, stage/'bundle')
                layers = list(bundle['layers'])
        meta = dict(schema_version=ARCHIVE_SCHEMA, report_id=report_id, created_at=now(),
                    project_id=project_id, project=request.get('project') or (candidate.parent.name if candidate.name == 'base' else candidate.name),
                    candidate_root=str(candidate), scope=scope, origin=origin,
                    label=request.get('label', ''), task_id=request.get('task_id', ''),
                    parent_report_id=parent, input_kind=request.get('input_kind', 'disk'),
                    overlays=request.get('captured_overlays', []),
                    status=report['status'] if report else 'failed', error=error,
                    input_sha256=report['input_sha256'] if report else None,
                    tool_version=report['tool_version'] if report else VERSION,
                    tool_sha256=report['tool_sha256'] if report else None,
                    summary=report['summary'] if report else dict(files=0, parsed_files=0, events=0, review_hints=0),
                    rules=sorted({f['rule'] for f in report['findings']}) if report else [], layers=layers)
        atomic_json(stage/'metadata.json', meta)
        hashes = {p.relative_to(stage).as_posix(): sha(p.read_bytes()) for p in stage.rglob('*') if p.is_file()}
        atomic_json(stage/'manifest.json', dict(schema_version=ARCHIVE_SCHEMA, report_id=report_id, files=hashes,
                    qualification='Content consistency only; does not prove analysis correctness or tamper-proof provenance.'))
        os.rename(stage, runs/report_id)
        return dict(meta, archive_path=str(runs/report_id), store=str(archive))
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def scan_and_archive(request, store=None, node=None, origin='cli'):
    sources, skipped = {}, []
    request = dict(request)
    try:
        sources, skipped, overlays = capture(request)
        request.update(captured_overlays=overlays, input_kind='editor_snapshot' if overlays else 'disk')
        report = analyze_sources(sources, node=node or configuration().get('node'), skipped=skipped)
    except (EvidenceError, OSError, UnicodeError) as error:
        meta = persist(sources, skipped, None, request, store, origin, str(error))
        return dict(archive=meta, report=None, ranges={}, markdown='分析失败：' + str(error))
    meta = persist(sources, skipped, report, request, store, origin)
    return dict(archive=meta, report=report, ranges=editor_ranges(report, sources), markdown=markdown(report))


def scan_path(candidate, store=None, node=None, origin='cli', **labels):
    try:
        request = request_for_path(candidate)
    except (EvidenceError, OSError, UnicodeError) as error:
        path = Path(candidate).expanduser().absolute()
        root = path.parent if path.suffix else path
        request = dict(mode='file' if path.suffix else 'folder', root=str(root), path=path.name, **labels)
        meta = persist({}, [], None, request, store, origin, str(error))
        return dict(archive=meta, report=None, ranges={}, markdown='分析失败：' + str(error))
    request.update(labels)
    return scan_and_archive(request, store, node, origin)


def list_reports(store=None, search='', status='', origin='', project='', limit=100, offset=0):
    limit, offset = int(limit), int(offset)
    if not 1 <= limit <= 500 or offset < 0:
        raise EvidenceError('Invalid pagination (limit 1–500)')
    runs = store_path(store)/'runs'
    items, invalid = [], []
    for root in sorted(runs.glob('r-*'), reverse=True):
        try:
            meta = metadata(root.name, store)
            if status and meta['status'] != status or origin and meta['origin'] != origin:
                continue
            if project and project not in (meta['project_id'], meta['project']):
                continue
            if search and search.casefold() not in canonical(meta).casefold():
                continue
            items.append(meta)
        except (EvidenceError, OSError, ValueError, KeyError) as error:
            invalid.append(dict(report_id=root.name, error=str(error)))
    return dict(items=items[offset:offset+limit], total=len(items), limit=limit, offset=offset,
                invalid=invalid, store=str(store_path(store)))


def read_report(report_id, store=None):
    verify(report_id, store)
    root = _report_dir(store, report_id)
    return dict(metadata=metadata(report_id, store),
                report=_read(root/'report.json') if (root/'report.json').exists() else None,
                notes=records('notes', report_id, store), deliveries=records('deliveries', report_id, store))


def read_source(report_id, name, store=None):
    verify(report_id, store)
    sources = _read(_report_dir(store, report_id)/'snapshot.json')['sources']
    if name not in sources:
        raise EvidenceError('Source is not part of this archived snapshot')
    return dict(path=name, text=sources[name], sha256=sha(sources[name].encode('utf-8')))


def artifact(report_id, name, store=None):
    verify(report_id, store)
    root = _report_dir(store, report_id)
    allowed = {'report.json', 'report.md', 'report.html', 'snapshot.json', 'metadata.json', 'manifest.json'}
    if name not in allowed or not (root/name).is_file():
        raise EvidenceError('Artifact not found')
    return (root/name).read_bytes()


def layer_text(report_id, layer='full', store=None):
    verify(report_id, store)
    root = _report_dir(store, report_id)
    meta = metadata(report_id, store)
    if layer == 'full':
        if meta['status'] == 'failed':
            return '分析失败：' + meta['error']
        return (root/'report.md').read_text(encoding='utf-8')
    if layer not in meta['layers']:
        raise EvidenceError('This report has no complete frozen layer: ' + layer)
    return '' if layer == 'none' else (root/'bundle'/(layer+'.md')).read_text(encoding='utf-8')


def records(kind, report_id, store=None):
    if kind not in {'notes', 'deliveries'}:
        raise EvidenceError('Invalid record kind')
    _report_dir(store, report_id)
    result = []
    for path in sorted((store_path(store)/kind/report_id).glob('*.json')):
        result.append(_read(path))
    return result


def append_record(kind, report_id, value, store=None):
    _report_dir(store, report_id)
    if kind not in {'notes', 'deliveries'}:
        raise EvidenceError('Invalid record kind')
    item = dict(value, record_id=uuid.uuid4().hex, report_id=report_id, created_at=now())
    path = store_path(store)/kind/report_id/(item['created_at'].replace(':', '') + '-' + item['record_id'] + '.json')
    atomic_json(path, item)
    return item


def annotate(report_id, finding_id, decision, note, store=None):
    data = read_report(report_id, store)
    if not data['report'] or finding_id not in {f['id'] for f in data['report']['findings']}:
        raise EvidenceError('Unknown finding')
    if decision not in {'confirmed', 'dismissed', 'uncertain'} or not isinstance(note, str) or len(note) > 10000:
        raise EvidenceError('Invalid research annotation')
    return append_record('notes', report_id, dict(finding_id=finding_id, decision=decision, note=note,
                         actor='human', qualification='Researcher assessment, not an oracle label'), store)


def compare_reports(before_id, after_id, store=None):
    before, after = read_report(before_id, store), read_report(after_id, store)
    a, b = before['metadata'], after['metadata']
    if a['project_id'] != b['project_id'] or a['scope'] != b['scope']:
        raise EvidenceError('只能比较同一项目、同一扫描范围的报告')
    if not before['report'] or not after['report']:
        raise EvidenceError('扫描失败的记录无法计算规则变化')
    delta = compare(before['report'], after['report'])
    delta.pop('before')
    delta.pop('after')
    delta.update(before_id=before_id, after_id=after_id)
    return delta
