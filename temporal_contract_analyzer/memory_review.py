"""Local review of the current categorized library. No models or version workflows."""
from http.server import ThreadingHTTPServer
from pathlib import Path
import threading
import webbrowser
from urllib.parse import urlsplit

from . import compact_experience as compact, experience_memory as memory
from .core import EvidenceError
from .http_common import LocalHandler, WEB


class ReviewServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, store, port=0):
        self.store = Path(store).expanduser().resolve()
        if not compact.is_library(self.store):
            raise EvidenceError('Choose the categorized experience library; archive stores are read-only')
        memory.records(self.store)
        self.review_lock = threading.Lock()
        super().__init__(('127.0.0.1', port), ReviewHandler)
        self.url = 'http://127.0.0.1:' + str(self.server_address[1])


class ReviewHandler(LocalHandler):
    def get(self):
        path = urlsplit(self.path).path
        if path == '/':
            self.send(compact.page(self.server.store), content_type='text/html; charset=utf-8')
            return
        assets = {'/memory-review.css': ('memory-review.css', 'text/css'),
                  '/compact-review.js': ('compact-review.js', 'text/javascript')}
        if path in assets:
            name, kind = assets[path]
            self.send((WEB/name).read_bytes(), content_type=kind+'; charset=utf-8')
        else:
            self.send({'error': 'Not found'}, 404)

    def post(self, data):
        action = {'/api/compact-summary': compact.save_summary,
                  '/api/compact-review': compact.save_review}.get(urlsplit(self.path).path)
        if action is None:
            self.send({'error': 'Not found'}, 404)
            return
        with self.server.review_lock:
            self.send(action(self.server.store, data))


def serve(store, port=0, open_browser=True):
    server = ReviewServer(store, port)
    print('Experience review: ' + server.url+'/', flush=True)
    print('Review the experience and its Abstract. Ctrl+C stops this page.', flush=True)
    try:
        if open_browser:
            try:
                webbrowser.open(server.url)
            except webbrowser.Error:
                print('Open the address above in your browser.', flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
