"""Loopback report browser with explicit, opt-in local Codex experiments."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit
from urllib.request import build_opener, ProxyHandler, Request

from . import archive
from .core import EvidenceError, ROOT, VERSION
from .workbench import Workbench

WEB = Path(__file__).parent/'web'
_opener = build_opener(ProxyHandler({}))


def strict_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise EvidenceError('JSON contains duplicate key: ' + key)
        value[key] = item
    return value


class ReportServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, store=None, port=0, node=None):
        self.store = archive.store_path(store)
        self.node = node
        self.instance = secrets.token_hex(24)
        self.experiments = Workbench(self.store, node)
        self.experiments.recover()
        super().__init__(('127.0.0.1', port), Handler)
        self.url = 'http://127.0.0.1:' + str(self.server_address[1])

    def server_close(self):
        self.experiments.close()
        super().server_close()


class Handler(BaseHTTPRequestHandler):
    server_version = 'TemporalReports/1'

    def log_message(self, format, *args):
        # Do not put source text or report content in service logs.
        pass

    def send(self, value, status=200, content_type='application/json; charset=utf-8', report=False):
        data = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Frame-Options', 'SAMEORIGIN')
        policy = "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'self'; base-uri 'none'" if report else \
                 "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'self'; base-uri 'none'; form-action 'self'"
        self.send_header('Content-Security-Policy', policy)
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def allowed(self):
        host = self.headers.get('Host', '')
        expected = urlsplit(self.server.url).netloc
        return host == expected and self.headers.get('Origin', self.server.url) == self.server.url

    def do_GET(self):
        if not self.allowed():
            self.send({'error': 'Loopback origin required'}, 403)
            return
        try:
            self.get()
        except (EvidenceError, ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
            self.send({'error': str(error)}, 400)

    def get(self):
        url = urlsplit(self.path)
        query = {k: values[0] for k, values in parse_qs(url.query).items()}
        parts = url.path.strip('/').split('/')
        store = self.server.store
        if url.path == '/api/health':
            self.send(dict(store=str(store), instance=self.server.instance, version=VERSION,
                           experiment_ui='local-codex-models-v1', context_enrichment='snapshot-definitions-v1',
                           scenario_progress='explicit-schedules-v1', failure_learning='candidate-memory-v1'))
        elif url.path == '/api/state':
            self.send(dict(store=str(store), version=VERSION, url=self.server.url))
        elif url.path == '/api/reports':
            allowed = {k: v for k, v in query.items() if k in {'search', 'status', 'origin', 'project', 'limit', 'offset'}}
            self.send(archive.list_reports(store, **allowed))
        elif url.path == '/api/compare':
            self.send(archive.compare_reports(query['before'], query['after'], store))
        elif parts == ['api', 'case-options']:
            self.send(self.server.experiments.case_options())
        elif parts == ['api', 'experiments']:
            self.send(self.server.experiments.list())
        elif len(parts) >= 3 and parts[:2] == ['api', 'experiments']:
            if len(parts) == 3:
                self.send(self.server.experiments.read(parts[2]))
            elif len(parts) == 4 and parts[3] == 'artifact':
                self.send(self.server.experiments.artifact(parts[2], query['job'], query['name']))
            else:
                self.send({'error': 'Not found'}, 404)
        elif len(parts) >= 3 and parts[:2] == ['api', 'reports']:
            report_id = parts[2]
            if len(parts) == 3:
                self.send(archive.read_report(report_id, store))
            elif len(parts) == 4 and parts[3] == 'source':
                self.send(archive.read_source(report_id, query['path'], store))
            elif len(parts) == 4 and parts[3] == 'context':
                from .context import build_context, markdown
                aliases = json.loads(query.get('aliases','{}'), object_pairs_hook=strict_object)
                packet = build_context(report_id, store, query.get('finding_id'),
                                       int(query.get('depth',1)), int(query.get('max_chars',12000)),
                                       aliases, self.server.node)
                self.send(dict(context=packet, markdown=markdown(packet)))
            elif len(parts) == 4 and parts[3] == 'artifact':
                name = query['name']
                data = archive.artifact(report_id, name, store)
                kind = {'html': 'text/html', 'md': 'text/plain', 'json': 'application/json'}[name.rsplit('.', 1)[-1]]
                self.send(data, content_type=kind+'; charset=utf-8', report=name.endswith('.html'))
            elif len(parts) == 4 and parts[3] == 'measurement-template':
                from .measurement import template
                self.send(template(report_id, store, query.get('finding_id')))
            elif len(parts) == 4 and parts[3] == 'measurement-review-template':
                from .measurement import review_template
                item = archive.measurement_record(report_id, query['record_id'], store)
                self.send(review_template(item['measurement'], query['reviewer']))
            else:
                self.send({'error': 'Not found'}, 404)
        elif url.path in {'/', '/app.js', '/style.css', '/experiments', '/experiments.js'}:
            name = {'/': 'index.html', '/experiments': 'experiments.html'}.get(url.path, url.path[1:])
            content_type = 'text/html' if name.endswith('.html') else ('text/javascript' if name.endswith('.js') else 'text/css')
            self.send((WEB/name).read_bytes(), content_type=content_type+'; charset=utf-8')
        else:
            self.send({'error': 'Not found'}, 404)

    def do_POST(self):
        if not self.allowed() or self.headers.get('X-TCA-Request') != 'local' or self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            self.send({'error': 'Same-origin JSON request required'}, 403)
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 1048576:
                raise EvidenceError('Request size invalid')
            data = json.loads(self.rfile.read(size), object_pairs_hook=strict_object)
            if not isinstance(data, dict):
                raise EvidenceError('Expected an object')
            self.post(data)
        except (EvidenceError, ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
            self.send({'error': str(error)}, 400)

    def post(self, data):
        parts = urlsplit(self.path).path.strip('/').split('/')
        store = self.server.store
        if parts == ['api', 'scans']:
            labels = {k: data[k] for k in ('project', 'label', 'task_id', 'parent_report_id') if k in data}
            if any(not isinstance(v, str) or len(v) > 1000 for v in labels.values()):
                raise EvidenceError('Invalid scan label')
            if not isinstance(data.get('candidate'), str) or not Path(data['candidate']).is_absolute():
                raise EvidenceError('请输入候选工程或源码文件的绝对路径')
            result = archive.scan_path(data['candidate'], store, self.server.node, 'web', **labels)
            self.send(result['archive'], 201)
        elif parts == ['api', 'experiments']:
            prepare = self.server.experiments.prepare_case if 'case_id' in data else self.server.experiments.prepare
            self.send(prepare(data), 201)
        elif len(parts) == 4 and parts[:2] == ['api', 'experiments']:
            if parts[3] == 'start':
                self.send(self.server.experiments.start(parts[2]), 202)
            elif parts[3] == 'cancel':
                self.send(self.server.experiments.cancel(parts[2]), 202)
            elif parts[3] == 'evaluate':
                self.send(self.server.experiments.evaluate(parts[2]))
            elif parts[3] == 'learn':
                from .learning import learn
                self.send(learn(self.server.experiments, parts[2]))
            else:
                self.send({'error': 'Not found'}, 404)
        elif len(parts) == 4 and parts[:2] == ['api', 'reports']:
            if parts[3] == 'verify':
                self.send(archive.verify(parts[2], store))
            elif parts[3] == 'notes':
                self.send(archive.annotate(parts[2], data['finding_id'], data['decision'], data.get('note', ''), store,
                                           boundary_review=data.get('boundary_review')), 201)
            elif parts[3] == 'measurements':
                self.send(archive.add_measurement(parts[2], data, store), 201)
            elif parts[3] == 'measurement-reviews':
                self.send(archive.add_measurement_review(parts[2], data['measurement_record_id'], data['review'], store), 201)
            else:
                self.send({'error': 'Not found'}, 404)
        elif parts == ['api', 'shutdown']:
            if data.get('instance') != self.server.instance:
                raise EvidenceError('Server identity mismatch')
            self.send({'stopped': True})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        else:
            self.send({'error': 'Not found'}, 404)


def running_server(store=None):
    root = archive.store_path(store)
    marker = root/'server.json'
    try:
        value = json.loads(marker.read_text(encoding='utf-8'))
        parsed = urlsplit(value['url'])
        if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or parsed.path or parsed.query or parsed.fragment or parsed.username:
            return None
        with _opener.open(value['url']+'/api/health', timeout=1) as response:
            health = json.load(response)
        if health['instance'] == value['instance'] and health['store'] == str(root):
            return value
    except (OSError, ValueError, KeyError):
        pass
    return None


def serve(store=None, port=0, node=None):
    server = ReportServer(store, port, node)
    server.store.mkdir(parents=True, exist_ok=True)
    value = dict(url=server.url, store=str(server.store), pid=os.getpid(), instance=server.instance, version=VERSION)
    archive.atomic_json(server.store/'server.json', value)
    print(json.dumps(value), flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        server.server_close()
        try:
            path = server.store/'server.json'
            if json.loads(path.read_text())['instance'] == server.instance:
                path.unlink()
        except (OSError, ValueError, KeyError):
            pass


def ensure_server(store=None, node=None):
    root = archive.store_path(store)
    root.mkdir(parents=True, exist_ok=True)
    current = running_server(root)
    if current:
        return current
    lock = root/'.server-start-lock'
    deadline = time.monotonic() + 12
    while True:
        try:
            lock.mkdir()
            break
        except FileExistsError:
            current = running_server(root)
            if current:
                return current
            if time.monotonic() > deadline:
                raise EvidenceError('报告中心启动锁未释放；请稍后重试或检查 .server-start-lock')
            try:
                stale = time.time() - lock.stat().st_mtime > 30
            except FileNotFoundError:
                continue
            if stale:
                try:
                    lock.rmdir()
                except OSError:
                    pass
            time.sleep(0.1)
    try:
        current = running_server(root)
        if current:
            return current
        args = [sys.executable, '-I', '-S', '-B', '-X', 'utf8', str(ROOT/'temporal_contract_analyzer/hub_entry.py'),
                'reports', 'serve', '--store', str(root), '--port', '0']
        if node:
            args += ['--node', node]
        with (root/'server.log').open('ab') as log:
            child = subprocess.Popen(args, cwd=str(ROOT), stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                     start_new_session=True)
        # Retain and reap the detached service while this parent is alive.
        threading.Thread(target=child.wait, daemon=True).start()
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            current = running_server(root)
            if current:
                return current
            if child.poll() is not None:
                raise EvidenceError('报告中心启动失败，请查看 ' + str(root/'server.log'))
            time.sleep(0.1)
        child.terminate()
        raise EvidenceError('报告中心启动超时')
    finally:
        lock.rmdir()


def stop_server(store=None):
    value = running_server(store)
    if not value:
        return dict(stopped=False, reason='not_running')
    request = Request(value['url']+'/api/shutdown', data=json.dumps({'instance': value['instance']}).encode(),
                      headers={'Content-Type': 'application/json', 'X-TCA-Request': 'local'})
    with _opener.open(request, timeout=3) as response:
        return json.load(response)
