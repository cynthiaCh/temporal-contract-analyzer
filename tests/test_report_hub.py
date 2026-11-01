import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import build_opener, ProxyHandler, Request

from temporal_contract_analyzer import archive, hub


class ReportHubTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.store = self.root/'reports'
        self.project = self.root/'project'
        self.project.mkdir()
        (self.project/'Demo.vue').write_text('<script setup>async function load(){await fetch(); store.save();}</script>')
        env = patch.dict(os.environ, {'TCA_CONFIG': str(self.root/'config.json')})
        env.start()
        self.addCleanup(env.stop)
        self.server = hub.ReportServer(self.store)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close_server)
        self.opener = build_opener(ProxyHandler({}))

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(3)

    def call(self, path, body=None, headers=None):
        default = {} if body is None else {'Content-Type':'application/json', 'X-TCA-Request':'local'}
        default.update(headers or {})
        request = Request(self.server.url+path, data=None if body is None else json.dumps(body).encode(), headers=default)
        return self.opener.open(request, timeout=10)

    def test_browser_scan_list_read_snapshot_and_notes(self):
        with self.call('/api/scans', {'candidate':str(self.project), 'label':'Web run'}) as response:
            self.assertEqual(response.status, 201)
            meta = json.load(response)
        report_id = meta['report_id']
        with self.call('/api/reports') as response:
            self.assertEqual(json.load(response)['items'][0]['origin'], 'web')
        with self.call('/api/reports/'+report_id) as response:
            data = json.load(response)
        self.assertEqual(data['metadata']['label'], 'Web run')
        with self.call('/api/reports/'+report_id+'/source?path=Demo.vue') as response:
            self.assertIn('store.save()', json.load(response)['text'])
        with self.call('/api/reports/'+report_id+'/notes', dict(finding_id=data['report']['findings'][0]['id'],decision='uncertain',note='核查中')) as response:
            self.assertEqual(json.load(response)['actor'], 'human')
        with self.call('/api/reports/'+report_id+'/verify', {}) as response:
            self.assertTrue(json.load(response)['verified'])

    def test_cors_dns_rebinding_and_unprotected_posts_are_rejected(self):
        for path, body, headers in [
            ('/api/reports', None, {'Host':'evil.example'}),
            ('/api/reports', None, {'Origin':'https://evil.example'}),
            ('/api/scans', {}, {'X-TCA-Request':''}),
            ('/api/scans', {}, {'Content-Type':'text/plain'}),
        ]:
            with self.subTest(headers=headers), self.assertRaises(HTTPError) as error:
                self.call(path, body, headers)
            self.assertEqual(error.exception.code, 403)

    def test_serves_only_known_assets_and_artifacts_with_csp(self):
        with self.call('/') as response:
            self.assertIn("script-src 'self'", response.headers['Content-Security-Policy'])
            self.assertIn('报告库', response.read().decode())
        for path in ('/../../etc/passwd', '/api/reports/../../config', '/config.json'):
            with self.assertRaises(HTTPError):
                self.call(path)
        meta = archive.scan_path(self.project, self.store)['archive']
        with self.call('/api/reports/'+meta['report_id']+'/artifact?name=report.html') as response:
            self.assertIn("default-src 'none'", response.headers['Content-Security-Policy'])
            self.assertIn('时序源码', response.read().decode())
        with self.assertRaises(HTTPError):
            self.call('/api/reports/'+meta['report_id']+'/artifact?name=../../config.json')

    def test_failed_scan_is_returned_as_archived_record(self):
        with self.call('/api/scans', {'candidate':str(self.root/'missing')}) as response:
            meta = json.load(response)
        self.assertEqual(meta['status'], 'failed')
        with self.call('/api/reports/'+meta['report_id']) as response:
            self.assertIsNone(json.load(response)['report'])

    def test_measurement_template_and_append_api_remain_human_authored(self):
        meta = archive.scan_path(self.project, self.store)['archive']
        base = '/api/reports/' + meta['report_id']
        with self.call(base + '/measurement-template') as response:
            draft = json.load(response)
        self.assertEqual(draft['workflow_status'], 'draft')
        self.assertEqual(draft['obligations'], [])
        with self.call(base + '/measurements', draft) as response:
            saved = json.load(response)
        self.assertEqual(saved['measurement']['obligation_count'], 0)
        with self.call(base + '/measurement-review-template?record_id=' + saved['record_id'] + '&reviewer=reviewer-a') as response:
            review = json.load(response)
        self.assertEqual(review['reviewer_id'], 'reviewer-a')
        self.assertEqual(review['measurement_sha256'], saved['measurement']['measurement_sha256'])
        with self.call(base) as response:
            detail = json.load(response)
        self.assertEqual(len(detail['measurements']), 1)
        self.assertEqual(detail['measurements'][0]['document']['obligations'], [])

    def test_boundary_cards_reuse_evidence_and_keep_review_separate_from_measurements(self):
        meta = archive.scan_path(self.project, self.store)['archive']
        base = '/api/reports/' + meta['report_id']
        with self.call(base) as response:
            detail = json.load(response)
        card = next(row for row in detail['boundary_cards'] if row['rule'] == 'effect-after-await')
        events = {e['id']: e for f in detail['report']['files'] for e in f['events']}
        self.assertEqual(events[card['boundary']['evidence_ids'][0]]['kind'], 'await')
        self.assertIn('store.save()', events[card['effects']['evidence_ids'][0]]['text'])
        self.assertEqual(card['requirement_protection']['evidence_ids'], [])
        review = dict(protection='insufficient', requirement_basis='Demo.vue:1; API spec pending',
                      missing_evidence='Need callback reachability and cancellation trace')
        with self.call(base + '/notes', dict(finding_id=card['finding_id'], decision='confirmed',
                                            note='Relation confirmed; behavior still unknown', boundary_review=review)) as response:
            saved = json.load(response)
        self.assertEqual(saved['boundary_review'], review)
        with self.call(base + '/notes', dict(finding_id=card['finding_id'], decision='uncertain', note='Legacy note')):
            pass
        with self.call(base) as response:
            refreshed = json.load(response)
        self.assertEqual(refreshed['report'], detail['report'])
        self.assertEqual(refreshed['boundary_cards'], detail['boundary_cards'])
        self.assertEqual(refreshed['measurements'], [])
        self.assertEqual(refreshed['notes'][0]['boundary_review'], review)
        self.assertNotIn('boundary_review', refreshed['notes'][1])
        for malformed in ({}, dict(review, protection='passed'), dict(review, protection=[]),
                          dict(review, missing_evidence=42)):
            with self.subTest(malformed=malformed), self.assertRaises(HTTPError) as error:
                self.call(base + '/notes', dict(finding_id=card['finding_id'], decision='uncertain',
                                               note='', boundary_review=malformed))
            self.assertEqual(error.exception.code, 400)
        self.assertEqual(len(archive.records('notes', meta['report_id'], self.store)), 2)

    def test_background_service_is_reused_and_can_be_stopped(self):
        store = self.root/'background'
        self.addCleanup(lambda: hub.stop_server(store))
        first = hub.ensure_server(store)
        second = hub.ensure_server(store)
        self.assertEqual(first['instance'], second['instance'])
        self.assertEqual(first['url'], second['url'])
        self.assertTrue(hub.stop_server(store)['stopped'])


if __name__ == '__main__':
    unittest.main()
