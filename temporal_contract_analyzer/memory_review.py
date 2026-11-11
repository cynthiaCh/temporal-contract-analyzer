"""Local review of immutable memory records and their retained evidence. No models."""
import json
from copy import deepcopy
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from uuid import uuid4
import webbrowser
from urllib.parse import parse_qs, urlsplit

from . import experience_memory as memory, experience_approval as approval, taxonomy
from .core import EvidenceError
from .http_common import LocalHandler, WEB


def record(store, code):
    if not isinstance(code, str) or not re.fullmatch(r'[0-9a-f]{64}', code):
        raise EvidenceError('Invalid experience digest')
    result = next((b for b in memory.records(store) if b['sha256'] == code), None)
    if result is None:
        raise EvidenceError('Unknown experience version')
    return result


def revise(store, bundle, data):
    """Save operator wording as a new candidate, retaining source evidence."""
    memory.object_fields(data, {'actor', 'reason', 'rules'}, 'manual revision')
    if not memory.text(data['actor']) or not memory.text(data['reason']):
        raise EvidenceError('Manual revision needs an editor name and reason')
    rules = data['rules']
    if not isinstance(rules, list) or len(rules) != len(bundle['rules']):
        raise EvidenceError('Manual revision must retain all rule identities')
    for old, new in zip(bundle['rules'], rules):
        memory.object_fields(new, {'id', 'category', 'body'}, 'edited rule')
        if new['id'] != old['id'] or not isinstance(new['category'], str) \
                or new['category'] not in memory.CATEGORIES or not memory.text(new['body']):
            raise EvidenceError('Invalid edited rule identity, category or body')
    changed = [new['id'] for old, new in zip(bundle['rules'], rules) if old != new]
    if not changed:
        raise EvidenceError('Change at least one rule before saving a revision')
    payload = deepcopy({key: bundle[key] for key in memory.FIELDS})
    payload.update(version='human-'+uuid4().hex, parent_sha256=bundle['sha256'], rules=rules)
    provenance = dict(kind='manual_revision', actor=data['actor'].strip(), reason=data['reason'].strip(),
        at=datetime.now(timezone.utc).isoformat(), parent_sha256=bundle['sha256'],
        changed_rule_ids=changed, rules=rules)
    with TemporaryDirectory() as directory:
        source = Path(directory)/'manual-revision.json'
        source.write_text(json.dumps(provenance, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        code = memory.digest(source.read_text(encoding='utf-8'))
        payload['audit']['sources'].append(dict(path='manual-revision.json', sha256=code))
        payload['audit']['notes'].append('Human wording revision; retained evidence requires review against edited rules.')
        payload['review'] = dict(status='candidate', kind='human', source_sha256=code,
            limitations=['Manual editing does not establish evidence support or content acceptance.'])
        return memory.add(store, payload, [source])


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
            from .experience_screening import qualified
            tips = {r['sha256'] for r in memory.tips(bundles)}
            self.send(dict(store=str(self.server.store), records=[dict(
                id=b['id'], version=b['version'], sha256=b['sha256'], labels=b['labels'],
                status=b['review']['status'], active=b['sha256'] in active,
                default_eligible=qualified(self.server.store, b['sha256']),
                latest=b['sha256'] in tips, rules=len(b['rules']),
                reviewed=b['sha256'] in decisions,
                last_decision=None if b['sha256'] not in decisions else {
                    key: decisions[b['sha256']][key] for key in ('decision', 'reviewer', 'at', 'sequence')}
                ) for b in bundles]))
        elif len(parts) >= 3 and parts[:2] == ['api', 'records']:
            bundle = record(self.server.store, parts[2])
            if len(parts) == 3:
                self.send(dict(bundle=bundle, predicates=taxonomy.definition()['mechanism_predicates'],
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
        if len(parts) != 4 or parts[:2] != ['api', 'records'] or parts[3] not in ('decision', 'activate', 'rollback', 'revise'):
            self.send({'error': 'Not found'}, 404)
            return
        bundle = record(self.server.store, parts[2])
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
        from .experience_screening import qualified
        self.send(dict(decision=decision, active=active, default_active=active and qualified(self.server.store,bundle['sha256']),
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
