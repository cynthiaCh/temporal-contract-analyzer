"""Local review of immutable memory records and their retained evidence. No models."""
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
import re
import webbrowser
from urllib.parse import parse_qs, urlsplit

from . import experience_memory as memory, experience_approval as approval, taxonomy
from .core import EvidenceError
from .hub import Handler, WEB


def record(store, code):
    if not isinstance(code, str) or not re.fullmatch(r'[0-9a-f]{64}', code):
        raise EvidenceError('Invalid experience digest')
    result = next((b for b in memory.records(store) if b['sha256'] == code), None)
    if result is None:
        raise EvidenceError('Unknown experience version')
    return result


class ReviewServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, store, port=0):
        self.store = Path(store).expanduser().resolve()
        if not (self.store/'memory.json').is_file():
            raise EvidenceError('Choose an existing experience memory store')
        memory.records(self.store)
        super().__init__(('127.0.0.1', port), ReviewHandler)
        self.url = 'http://127.0.0.1:' + str(self.server_address[1])


class ReviewHandler(Handler):
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
            active = {r['bundle']['sha256'] for r in approval.active(self.server.store)}
            tips = {r['sha256'] for r in memory.tips(bundles)}
            self.send(dict(store=str(self.server.store), records=[dict(
                id=b['id'], version=b['version'], sha256=b['sha256'], labels=b['labels'],
                status=b['review']['status'], active=b['sha256'] in active,
                latest=b['sha256'] in tips, rules=len(b['rules'])) for b in bundles]))
        elif len(parts) >= 3 and parts[:2] == ['api', 'records']:
            bundle = record(self.server.store, parts[2])
            if len(parts) == 3:
                self.send(dict(bundle=bundle, predicates=taxonomy.definition()['mechanism_predicates'],
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
            else:
                self.send({'error': 'Not found'}, 404)
        else:
            self.send({'error': 'Not found'}, 404)

    def post(self, data):
        parts = urlsplit(self.path).path.strip('/').split('/')
        if len(parts) != 4 or parts[:2] != ['api', 'records'] or parts[3] != 'decision':
            self.send({'error': 'Not found'}, 404)
            return
        bundle = record(self.server.store, parts[2])
        if set(data) != {'reviewed', 'decision'} or data['reviewed'] is not True:
            raise EvidenceError('Confirm review of the exact rules, labels, premises and evidence')
        decision = approval.decide(self.server.store, bundle['sha256'], data['decision'])
        active = any(r['bundle']['sha256'] == bundle['sha256'] for r in approval.active(self.server.store))
        self.send(dict(decision=decision, active=active,
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
