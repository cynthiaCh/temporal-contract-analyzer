"""Human review transport and immutable evidence checks using a synthetic store."""
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import build_opener, ProxyHandler, Request

import test_experience_memory as fixtures
from temporal_contract_analyzer import experience_memory as memory, experience_approval as approval
from temporal_contract_analyzer.cli import main
from temporal_contract_analyzer.memory_review import ReviewServer


class MemoryReviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.MemoryTests('test_storage_preserves_single_source_body_and_evidence')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.store = self.fixture.store
        self.bundle = memory.add(self.store, self.fixture.payload, [self.fixture.source])
        self.server = ReviewServer(self.store)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close_server)
        self.opener = build_opener(ProxyHandler({}))

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(3)

    def call(self, path, body=None, headers=None):
        defaults = {} if body is None else {'Content-Type':'application/json','X-TCA-Request':'local'}
        defaults.update(headers or {})
        request = Request(self.server.url+path, data=None if body is None else json.dumps(body).encode(), headers=defaults)
        return self.opener.open(request, timeout=10)

    @property
    def base(self):
        return '/api/records/'+self.bundle['sha256']

    def decision(self, choice='accept'):
        return dict(reviewed=True, decision=dict(reviewer='SYNTHETIC_OPERATOR_FIXTURE', decision=choice,
            scope='exploratory', reason='Synthetic transport test, not real expert approval.',
            rules=[dict(rule_id=r['id'], supported=True, reason='Synthetic evidence checked.') for r in self.bundle['rules']]))

    def test_opening_page_and_sources_never_activates(self):
        for path in ('/', '/memory-review.js', '/memory-review.css'):
            with self.call(path) as response:
                self.assertEqual(response.status, 200)
                self.assertIn("script-src 'self'", response.headers['Content-Security-Policy'])
        with self.call('/api/library') as response:
            data = json.load(response)
        self.assertEqual(len(data['records']), 1)
        self.assertFalse(data['records'][0]['active'])
        with self.call(self.base) as response:
            self.assertEqual(json.load(response)['bundle'], self.bundle)
        source = self.bundle['audit']['sources'][0]['sha256']
        with self.call(self.base+'/sources/'+source+'?pointer=/rules/0') as response:
            self.assertEqual(json.load(response)['value'], {'supported':True})
        self.assertFalse((self.store/'decisions').exists())

    def test_source_access_is_bound_to_record(self):
        for path in (self.base+'/sources/'+'f'*64, self.base+'/sources/../../memory.json',
                     '/api/records/not-a-digest', '/memory.json'):
            with self.subTest(path=path), self.assertRaises(HTTPError):
                self.call(path)
        source = self.bundle['audit']['sources'][0]['sha256']
        with self.call(self.base+'/sources/'+source+'?line=1') as response:
            self.assertTrue(json.load(response)['text'].startswith('1 | '))
        with self.assertRaises(HTTPError):
            self.call(self.base+'/sources/'+source+'?pointer=/rules/0&line=1')

    def test_incomplete_or_unconfirmed_review_is_rejected(self):
        original = (self.store/'records'/(self.bundle['sha256']+'.json')).read_bytes()
        for change in ('confirmation', 'name', 'reason_type', 'unsupported', 'missing_rule'):
            body = self.decision()
            if change == 'confirmation': body['reviewed'] = False
            elif change == 'name': body['decision']['reviewer'] = ''
            elif change == 'reason_type': body['decision']['rules'][0]['reason'] = None
            elif change == 'unsupported': body['decision']['rules'][0]['supported'] = False
            else: body['decision']['rules'].pop()
            with self.subTest(change=change), self.assertRaises(HTTPError):
                self.call(self.base+'/decision', body)
        self.assertEqual(approval.active(self.store), [])
        self.assertFalse((self.store/'decisions').exists())
        self.assertEqual((self.store/'records'/(self.bundle['sha256']+'.json')).read_bytes(), original)

    def test_explicit_synthetic_accept_creates_decision_and_active_version(self):
        with self.call(self.base+'/decision', self.decision()) as response:
            self.assertEqual(response.status, 201)
            self.assertTrue(json.load(response)['active'])
        self.assertEqual(len(list((self.store/'decisions').glob('*.json'))), 1)
        self.assertEqual(approval.active(self.store)[0]['bundle'], self.bundle)

    def test_empty_reasons_are_accepted_without_fabricated_text(self):
        body = self.decision()
        body['decision']['reason'] = ''
        for finding in body['decision']['rules']:
            finding['reason'] = ''
        with self.call(self.base+'/decision', body) as response:
            saved = json.load(response)['decision']
        self.assertEqual(saved['reason'], '')
        self.assertTrue(all(finding['reason'] == '' for finding in saved['rules']))

    def test_revision_records_decision_without_activation(self):
        with self.call(self.base+'/decision', self.decision('revise')) as response:
            self.assertFalse(json.load(response)['active'])
        self.assertEqual(approval.active(self.store), [])
        self.assertEqual(len(approval.decisions(self.store)), 1)

    def test_same_origin_and_local_header_required(self):
        for headers in ({'Origin':'https://example.invalid'}, {'X-TCA-Request':''}, {'Host':'evil.invalid'}):
            with self.subTest(headers=headers), self.assertRaises(HTTPError) as error:
                self.call(self.base+'/decision', self.decision(), headers)
            self.assertEqual(error.exception.code, 403)
        self.assertFalse((self.store/'decisions').exists())

    def test_cli_output_reports_saved_path_and_preserves_existing_file(self):
        output = self.fixture.root/'review.json'
        args = ['experience-memory','review-template',self.bundle['sha256'],
                '--store',str(self.store),'--output',str(output)]
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            self.assertEqual(main(args), 0)
        self.assertEqual(stdout.getvalue(), '')
        self.assertIn(str(output), stderr.getvalue())
        original = output.read_bytes()
        with redirect_stderr(StringIO()):
            self.assertEqual(main(args), 1)
        self.assertEqual(output.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
