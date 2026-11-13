"""Local review of immutable memory records and their retained evidence. No models."""
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
import re
from uuid import uuid4
import webbrowser
from urllib.parse import parse_qs, urlsplit

from . import experience_memory as memory, experience_approval as approval, taxonomy
from .core import EvidenceError
from .http_common import LocalHandler, WEB


def presentation(store, bundle, workflow, decision):
    """Display-only metadata. Never edits a sealed record or implies approval."""
    from .experience_lifecycle import load
    catalog=load(Path(store)/'display.json',{})
    if catalog and (catalog.get('schema_version')!='experience-display-v1' or
                    not isinstance(catalog.get('titles'),dict) or
                    any(not memory.text(v) for v in catalog['titles'].values())):
        raise EvidenceError('Invalid experience display metadata')
    title=catalog.get('titles',{}).get(bundle['id'])
    if title is None:
        title=bundle['rules'][0]['body'].split('. ',1)[0]
        if len(title)>100:title=title[:97].rsplit(' ',1)[0]+'…'
    ai=(workflow or {}).get('ai_status','not_recorded')
    state='Awaiting human content review'
    if decision:state={'accept':'Content accepted','reject':'Rejected','revise':'Revision requested'}[decision['decision']]
    if (workflow or {}).get('status')=='enabled':state='Enabled'
    origin=(workflow or {}).get('origin_root')
    source_batch=load(Path(origin)/'protocol.json',{}).get('batch_id') if origin else None
    origin_note=next((n for n in bundle['audit']['notes'] if n.startswith('V4 origin: ')),None)
    return dict(learning_origin=None if origin_note is None else origin_note.split(': ',1)[1],title=title,title_source='display.json' if bundle['id'] in catalog.get('titles',{}) else 'derived_rule_excerpt',
        state=state,ai_status=ai,source_batch=source_batch,
        parent_sha256=bundle['parent_sha256'],
        parent_description=bundle['parent_sha256'] or 'None (parentless proposal; novelty not implied)')


def record(store, code):
    if not isinstance(code, str) or not re.fullmatch(r'[0-9a-f]{64}', code):
        raise EvidenceError('Invalid experience digest')
    result = next((b for b in memory.records(store) if b['sha256'] == code), None)
    if result is None:
        raise EvidenceError('Unknown experience version')
    return result


def revise(store, bundle, data):
    """Save operator wording as a new candidate, retaining source evidence."""
    from .experience_lifecycle import edit
    required={'actor','reason','rules'}
    if not isinstance(data,dict) or not required<=set(data) or set(data)-required-{'request_id','labels','requires','excludes'}:
        raise EvidenceError('Invalid manual revision fields')
    request=dict(data)
    request.setdefault('request_id',uuid4().hex)
    for key in ('labels','requires','excludes'):request.setdefault(key,bundle[key])
    return edit(store,bundle['sha256'],request)


class ReviewServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, store, port=0):
        self.store = Path(store).expanduser().resolve()
        if not (self.store/'memory.json').is_file():
            raise EvidenceError('Choose an existing experience memory store')
        memory.records(self.store)
        super().__init__(('127.0.0.1', port), ReviewHandler)
        self.url = 'http://127.0.0.1:' + str(self.server_address[1])


class ReviewHandler(LocalHandler):
    def get(self):
        url = urlsplit(self.path)
        parts = url.path.strip('/').split('/')
        query = parse_qs(url.query)
        assets = {'/': 'memory-review.html', '/memory-review.js': 'memory-review.js',
                  '/memory-review.css': 'memory-review.css'}
        if url.path in assets:
            name = assets[url.path]
            kind = 'text/html' if name.endswith('.html') else ('text/javascript' if name.endswith('.js') else 'text/css')
            self.send((WEB/name).read_bytes(), content_type=kind+'; charset=utf-8')
        elif parts == ['api', 'library']:
            bundles = memory.records(self.server.store)
            decisions = {d['candidate_sha256']: d for d in approval.decisions(self.server.store)}
            active = {r['bundle']['sha256'] for r in approval.active(self.server.store)}
            eligible = {row['bundle']['sha256'] for row in approval.approved(self.server.store)}
            tips = {r['sha256'] for r in memory.tips(bundles)}
            from .experience_lifecycle import metadata
            self.send(dict(review_api_version='experience-review-v3',store=str(self.server.store), records=[dict(
                id=b['id'], version=b['version'], sha256=b['sha256'], labels=b['labels'],
                status=b['review']['status'], active=b['sha256'] in active,
                default_eligible=b['sha256'] in eligible,
                latest=b['sha256'] in tips, rules=len(b['rules']),
                display=presentation(self.server.store,b,metadata(self.server.store,b['sha256']),decisions.get(b['sha256'])),
                reviewed=b['sha256'] in decisions,
                last_decision=None if b['sha256'] not in decisions else {
                    key: decisions[b['sha256']][key] for key in ('decision', 'reviewer', 'at', 'sequence')}
                ) for b in bundles]))
        elif len(parts) >= 3 and parts[:2] == ['api', 'records']:
            bundle = record(self.server.store, parts[2])
            if len(parts) == 3:
                from .experience_lifecycle import view
                self.send(dict(bundle=bundle, predicates=taxonomy.definition()['mechanism_predicates'],
                    display=presentation(self.server.store,bundle,view(self.server.store,bundle['sha256']),
                        next((d for d in reversed(approval.decisions(self.server.store)) if d['candidate_sha256']==bundle['sha256']),None)),
                    workflow=view(self.server.store,bundle['sha256']),
                    activation=approval.activation_options(self.server.store, bundle['sha256']),
                    review_plan=approval.review_plan(self.server.store, bundle['sha256']),
                    decisions=[d for d in approval.decisions(self.server.store)
                    if d['candidate_sha256'] == bundle['sha256']]))
            elif len(parts) == 5 and parts[3] == 'sources':
                code = parts[4]
                source = next((s for s in bundle['audit']['sources'] if s['sha256'] == code), None)
                if source is None:
                    raise EvidenceError('Evidence must belong to this experience version')
                raw = (self.server.store/'sources'/code).read_text(encoding='utf-8')
                pointer = query.get('pointer', [''])[0]
                value = memory.json_pointer(raw, pointer)
                text = raw if pointer == '' else json.dumps(value, ensure_ascii=False, indent=2)
                if 'line' in query:
                    line = int(query['line'][0])
                    lines = raw.splitlines()
                    if pointer or not 1 <= line <= len(lines):
                        raise EvidenceError('Invalid source line')
                    start, end = max(1, line-4), min(len(lines), line+4)
                    text = '\n'.join(f'{n} | {lines[n-1]}' for n in range(start, end+1))
                    value = None
                self.send(dict(name=Path(source['path']).name, sha256=code, pointer=pointer,
                    value=value if pointer else None, text=text[:500000], truncated=len(text)>500000))
            elif len(parts) == 4 and parts[3] == 'screening':
                from .experience_screening import read, evaluate
                report = read(self.server.store, bundle['sha256'])
                self.send(dict(report=report, gate=None if report is None else evaluate(report)))
            else:
                self.send({'error': 'Not found'}, 404)
        else:
            self.send({'error': 'Not found'}, 404)

    def post(self, data):
        parts = urlsplit(self.path).path.strip('/').split('/')
        if len(parts) != 4 or parts[:2] != ['api', 'records'] or parts[3] not in ('decision', 'activate', 'rollback', 'revise','revoke-enable'):
            self.send({'error': 'Not found'}, 404)
            return
        bundle = record(self.server.store, parts[2])
        if parts[3]=='revoke-enable':
            from .experience_lifecycle import revoke
            self.send(revoke(self.server.store,bundle['sha256'],data),201);return
        if parts[3] == 'revise':
            saved = revise(self.server.store, bundle, data)
            self.send(dict(sha256=saved['sha256']), 201)
            return
        if parts[3] in ('activate', 'rollback'):
            if set(data) != {'actor', 'reason', 'expected_current'}:
                raise EvidenceError('Activation needs actor, reason and expected_current')
            index = approval.activate(self.server.store, bundle['sha256'], data['expected_current'],
                data['actor'], data['reason'], rollback=parts[3] == 'rollback')
            self.send(dict(active=index['versions'].get(bundle['id']) == bundle['sha256'],
                           directory=str(self.server.store/'active.json')), 201)
            return
        if set(data) != {'reviewed', 'decision', 'activate', 'expected_current'} \
                or data['reviewed'] is not True:
            raise EvidenceError('Confirm review of the exact rules, labels, premises and evidence')
        decision = approval.decide(self.server.store, bundle['sha256'], data['decision'],
            activate_version=data['activate'], expected_current=data['expected_current'])
        active = any(r['bundle']['sha256'] == bundle['sha256'] for r in approval.active(self.server.store))
        eligible = {row['bundle']['sha256'] for row in approval.approved(self.server.store)}
        self.send(dict(decision=decision, active=active, default_active=bundle['sha256'] in eligible,
            directory=str(self.server.store/'decisions')), 201)


def serve(store, code=None, port=0, open_browser=True):
    if code is not None:
        record(store, code)
    server = ReviewServer(store, port)
    url = server.url + ('/?record='+code if code else '/')
    print('Experience review: ' + url, flush=True)
    print('Read rules and retained evidence, then submit your own decision. Ctrl+C stops this page.', flush=True)
    try:
        if open_browser:
            try:
                webbrowser.open(url)
            except webbrowser.Error:
                print('Open the address above in your browser.', flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
