"""Same-origin loopback JSON transport for the report and experience review UIs."""
import json
from pathlib import Path
import subprocess
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlsplit

from .core import EvidenceError

WEB = Path(__file__).parent/'web'


def strict_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise EvidenceError('JSON contains duplicate key: ' + key)
        value[key] = item
    return value


class LocalHandler(BaseHTTPRequestHandler):
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

    def get(self):
        self.send({'error': 'Not found'}, 404)

    def post(self, data):
        self.send({'error': 'Not found'}, 404)
