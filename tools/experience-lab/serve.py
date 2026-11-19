#!/usr/bin/env python3
"""Local TempoEvo workbench. Prepare without models; execute only on explicit Start."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import secrets
import sys
from urllib.parse import parse_qs, urlsplit
import webbrowser

from runner import Controller, REPO, DEFAULT_GRADER, DEFAULT_SOLVER, PUBLIC_DOCS, default_benchmark, environment, read
from records import archived_runs, run_detail, case_detail
from model_profiles import Profiles

WEB = Path(__file__).resolve().parent/'web'


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port, root):
        self.controller = Controller(root)
        self.profiles = Profiles(self.controller.root.parent/'model-profiles.json')
        self.token = secrets.token_hex(24)
        super().__init__(('127.0.0.1', port), Handler)
        self.url = 'http://127.0.0.1:'+str(self.server_address[1])


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, value, status=200, content_type='application/json'):
        body = json.dumps(value).encode() if content_type == 'application/json' else value
        self.send_response(status)
        self.send_header('Content-Type', content_type+'; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.headers.get('Host') != urlsplit(self.server.url).netloc:
            self.send(dict(error='Use the local workbench address'), 403)
            return
        url = urlsplit(self.path)
        query = parse_qs(url.query)
        try:
            if url.path in ('/', '/style.css', '/app.js'):
                file = WEB/('index.html' if url.path == '/' else url.path[1:])
                self.send(file.read_bytes(), content_type={'.html':'text/html', '.css':'text/css', '.js':'text/javascript'}[file.suffix])
            elif url.path == '/api/bootstrap':
                config = self.server.profiles.snapshot()
                self.send(dict(token=self.server.token, repository=str(REPO), profiles=config['profiles'], default_profile=config['default_profile'], profile_config=config,
                               defaults=dict(benchmark=default_benchmark(), store='experience-memory/library', model_config=config['path'],
                                             solver_image=DEFAULT_SOLVER, grader_image=DEFAULT_GRADER, public_checks=PUBLIC_DOCS)))
            elif url.path == '/api/environment':
                self.send(environment())
            elif url.path == '/api/profiles':
                self.send(self.server.profiles.snapshot(query['path'][0]))
            elif url.path == '/api/runs':
                rows = []
                for file in sorted(self.server.controller.root.glob('run-*/lab.json'), reverse=True):
                    x = read(file)
                    rows.append(dict(id=x['id'], title=x['id'], mode=x['config']['mode'], status=x['status'], recorded=False, count=x['config']['count']))
                self.send(rows+archived_runs())
            elif url.path == '/api/run':
                self.send(run_detail(self.server.controller, query['id'][0]))
            elif url.path == '/api/case':
                self.send(case_detail(self.server.controller, query['run'][0], query['case'][0]))
            else:
                self.send(dict(error='Not found'), 404)
        except (ValueError, KeyError, OSError) as error:
            self.send(dict(error=str(error)), 400)

    def do_POST(self):
        if self.headers.get('Origin') != self.server.url or self.headers.get('X-TempoEvo-Token') != self.server.token:
            self.send(dict(error='This action must originate from this local workbench'), 403)
            return
        try:
            if self.headers.get('Content-Type') != 'application/json':
                raise ValueError('Send JSON')
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 32000:
                raise ValueError('Invalid request size')
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError('Expected an object')
            if self.path == '/api/profiles/save':
                self.send(self.server.profiles.save(body))
            elif self.path == '/api/prepare':
                ident = self.server.controller.prepare(body)
                self.send(dict(id=ident), 202)
            elif self.path == '/api/start':
                self.send(dict(id=self.server.controller.start(body['id'])), 202)
            elif self.path == '/api/stop':
                self.server.controller.stop(body['id'])
                self.send(dict(status='stopping'), 202)
            else:
                self.send(dict(error='Not found'), 404)
        except (ValueError, KeyError, OSError) as error:
            self.send(dict(error=str(error)), 400)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--runs', type=Path, default=REPO/'.tempoevo/runs')
    parser.add_argument('--open', action='store_true')
    args = parser.parse_args()
    server = Server(args.port, args.runs)
    print(json.dumps(dict(url=server.url, runs=str(server.controller.root))), flush=True)
    if args.open:
        webbrowser.open(server.url)
    try:
        server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
