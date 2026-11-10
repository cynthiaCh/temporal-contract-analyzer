"""Select source-derived AST evidence for the Auto Contract analysis prompt."""
from pathlib import PurePosixPath

from .core import CODE_EXT, EXCLUDED, analyze_sources


EVENT_FIELDS = ('id', 'path', 'scope', 'kind', 'line', 'column', 'end_line', 'end_column',
                'text', 'callee', 'receiver', 'arguments', 'target', 'operator', 'expression',
                'conditions', 'awaited', 'binding', 'import_name')


def select_ast_evidence(report):
    """Keep rule evidence and local relations, not the raw tree or hash metadata.

    This is a heuristic selection, not a complete inventory. Partial parser
    coverage remains visible; the analysis prompt also carries full source text.
    """
    events = {event['id']: event for file in report['files'] for event in file['events']}
    selected = {eid for finding in report['findings'] for eid in finding['evidence']}
    evidence = [{key: event[key] for key in EVENT_FIELDS if key in event}
                for eid, event in events.items() if eid in selected]
    findings = [{key: finding[key] for key in
                 ('rule', 'path', 'scope', 'evidence', 'message', 'condition', 'review_question', 'classification')
                 if key in finding} for finding in report['findings']]
    links = [link for link in report['call_links'] if link['call'] in selected]
    targets = {link['target'] for link in links}
    definitions = [dict(id=fn['id'], path=file['path'], line=fn['line'], scope=fn['local_id'])
                   for file in report['files'] for fn in file['functions'] if fn['id'] in targets]
    return dict(status=report['status'],
        selection='Rule-matched evidence only; an incomplete review aid, not a complete execution path.',
        coverage=[dict(path=file['path'], status=file['status'],
                       **{key: file[key] for key in ('analysis_scope', 'error') if key in file})
                  for file in report['files']],
        skipped=report['skipped'], limitations=report['limitations'],
        events=evidence, findings=findings,
        relations=[relation for relation in report['relations']
                   if relation['before'] in selected and relation['after'] in selected],
        call_links=links, target_definitions=definitions)


def analyze_candidate(sources, node=None):
    code = {}
    skipped = []
    for path, text in sorted(sources.items()):
        parts = PurePosixPath(path).parts
        if any(part in EXCLUDED or part.startswith('.') for part in parts):
            skipped.append(dict(path=path, reason='excluded_source_path'))
        elif PurePosixPath(path).suffix.lower() in CODE_EXT:
            code[path] = text
    report = analyze_sources(code, node=node, skipped=skipped)
    return report, select_ast_evidence(report)
