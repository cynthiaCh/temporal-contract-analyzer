"""One JSON request per isolated process. Never import or execute workspace code."""
import json
from pathlib import Path, PurePosixPath
import sys

if sys.version_info < (3, 9):
    sys.exit('Temporal Contracts requires Python 3.9+')

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from temporal_contract_analyzer.core import (  # noqa: E402
    EvidenceError, EXCLUDED, MAX_FILE, MAX_TOTAL, analyze_sources, collect,
)
from temporal_contract_analyzer.report import markdown  # noqa: E402


def source_path(value):
    p = PurePosixPath(value)
    if not value or p.is_absolute() or '..' in p.parts or '\\' in value:
        raise EvidenceError('Invalid relative source path')
    if any(part in EXCLUDED or part.startswith('.') for part in p.parts):
        raise EvidenceError('Excluded source path: ' + value)
    return value


def run(request):
    mode = request.get('mode')
    skipped = []
    if mode == 'file':
        sources = {source_path(request['path']): request['text']}
    elif mode == 'folder':
        sources, skipped = collect(request['root'])
        # Only replace files in the collected inventory: no overlay can add an
        # excluded, external or symlinked input to a directory scan.
        for name, text in request.get('overlays', {}).items():
            if name in sources:
                sources[source_path(name)] = text
    else:
        raise EvidenceError('Unknown scan mode')
    if any(not isinstance(text, str) for text in sources.values()):
        raise EvidenceError('Expected source text')
    sizes = [len(text.encode('utf-8')) for text in sources.values()]
    if any(size > MAX_FILE for size in sizes) or sum(sizes) > MAX_TOTAL or len(sources) > 1000:
        raise EvidenceError('源码超过扫描范围（单文件 1 MiB / 合计 25 MiB / 1000 文件）')
    report = analyze_sources(sources, node=request['node'], skipped=skipped)
    ranges = {}
    for file in report['files']:
        # Python AST columns count UTF-8 bytes; VS Code and Babel count UTF-16.
        lines = sources[file['path']].splitlines()
        def column(line, offset):
            if file.get('column_unit') != 'utf8_bytes':
                return offset
            text = lines[line - 1] if 0 < line <= len(lines) else ''
            prefix = text.encode('utf-8')[:offset].decode('utf-8')
            return len(prefix.encode('utf-16-le')) // 2
        for event in file['events']:
            ranges[event['id']] = [event['line'] - 1, column(event['line'], event['column']),
                                   event['end_line'] - 1, column(event['end_line'], event['end_column'])]
    return dict(report=report, ranges=ranges, markdown=markdown(report))


if __name__ == '__main__':
    try:
        # JSON escaping can expand UTF-8 input; still bound the transport size.
        raw = sys.stdin.buffer.read(MAX_TOTAL * 6 + 1024)
        if len(raw) >= MAX_TOTAL * 6 + 1024:
            raise EvidenceError('Request exceeds input size limit')
        result = run(json.loads(raw))
        sys.stdout.write(json.dumps(result, ensure_ascii=False))
    except Exception as error:
        sys.stderr.write(str(error) + '\n')
        sys.exit(1)
