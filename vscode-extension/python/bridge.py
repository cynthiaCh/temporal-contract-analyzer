"""One JSON request per isolated process. Never import or execute workspace code."""
import json
from pathlib import Path
import sys

if sys.version_info < (3, 9):
    sys.exit('TempoEvo requires Python 3.9+')

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from temporal_contract_analyzer.core import EvidenceError, MAX_TOTAL, analyze_sources  # noqa: E402
from temporal_contract_analyzer import archive  # noqa: E402
from temporal_contract_analyzer.report import markdown  # noqa: E402


def run(request):
    if request.get('operation', '').startswith('experience_'):
        from temporal_contract_analyzer import owner_experience as owner
        operation = request['operation']
        if operation == 'experience_init': return owner.initialize(request['store'])
        if operation == 'experience_list': return owner.listing(request['store'])
        if operation == 'experience_history': return owner.history(request['store'])
        if operation == 'experience_change': return owner.change(request['store'], request['change'])
        raise EvidenceError('Unknown experience operation')
    node = archive.configuration().get('node') or request['node']
    if request.get('operation') == 'open_hub':
        from temporal_contract_analyzer.hub import ensure_server
        return dict(hub=ensure_server(request.get('store'), node))
    if request.get('archive'):
        return archive.scan_and_archive(request, request.get('store'), node, 'vscode')
    sources, skipped, _ = archive.capture(request)
    report = analyze_sources(sources, node=node, skipped=skipped)
    return dict(report=report, ranges=archive.editor_ranges(report, sources), markdown=markdown(report))


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
