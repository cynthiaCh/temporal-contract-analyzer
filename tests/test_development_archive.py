"""Archive projection and HTTP checks; no CLI, scorer or model is executed."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import build_opener, ProxyHandler, Request

from temporal_contract_analyzer import hub
from temporal_contract_analyzer.core import EvidenceError
from temporal_contract_analyzer.development import DevelopmentArchive


class DevelopmentArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.research = self.root/'research'
        self.research.mkdir()
        self.view = DevelopmentArchive(self.research)

    def write(self, batch, name, value):
        path = self.research/batch/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value if isinstance(value, str) else json.dumps(value), encoding='utf-8')
        return path

    def comparison(self, batch='comparison-1', reused=False):
        self.write(batch, 'summary.json', dict(case='synthetic-case', experience='E2',
                   experience_frozen_no_revision=reused, groups={
                       'A': dict(condition='AUTO', started=1, valid_denominator=1, complete_passed=0),
                       'B': dict(condition='AUTO_EXP', started=1, valid_denominator=1, complete_passed=1)},
                   per_slot=[dict(slot='A1', condition='AUTO', valid=True, verdict='UNDERREACH',
                                  passed_items=1, total_items=2, original_correct_losses=['keep']),
                             dict(slot='B1', condition='AUTO_EXP', valid=True, verdict='PASS',
                                  passed_items=2, total_items=2)]))
        self.write(batch, 'cohort.json', dict(case='synthetic-case'))
        self.write(batch, 'NEW_EXPERIENCE.md', 'Preserve shared ownership.\n')
        self.write(batch, 'experience-freeze.json', dict(candidate='E2', before_any_maintenance=True))
        return batch

    def test_source_feedback_is_not_relabelled_as_current_baseline_and_reuse_is_not_training(self):
        source = self.comparison()
        self.write(source, 'E1.md', 'Cancel everything.\n')
        self.write(source, 'training-feedback.json', dict(source_batch='/old/research/prior',
                                                        runs=[dict(slot='prior-B', verdict='UNDERREACH')]))
        self.write(source, 'reflection-receipt.json', dict(infrastructure_valid=True, output_format_valid=True))
        detail = self.view.read(source)
        stages = {row['id']: row for row in detail['stages']}
        self.assertEqual(stages['baseline']['rows'][0]['slot'], 'prior-B')
        self.assertEqual([r['slot'] for r in stages['validation']['rows']], ['A1', 'B1'])
        self.assertIn('-Cancel everything.', detail['experience_diff']['text'])
        self.assertEqual(stages['freeze']['status'], 'frozen')
        reused = self.comparison('comparison-2', reused=True)
        self.write(reused, 'summary.json', dict(json.loads((self.research/reused/'summary.json').read_text()),
                                               source_batch='/other-machine/research/comparison-1'))
        detail = self.view.read(reused)
        stages = {row['id']: row for row in detail['stages']}
        self.assertEqual(stages['reflection']['status'], 'not_performed')
        self.assertEqual(detail['links'][0]['id'], source)
        self.assertEqual(detail['groups'][0]['valid_denominator'], 1)

    def test_preparation_stop_is_not_an_empty_frozen_library_or_test_failure(self):
        batch = 'pilot-stop'
        self.write(batch, 'summary.json', dict(status='STOPPED', development=[],
                   frozen_library=None, preparation_failure=dict(material_valid=False),
                   tests={'T1': dict(runs=[dict(slot='T1-A', started=False, valid_score=False,
                                                 execution_status='NOT_STARTED')])},
                   costs=[dict(usage=None)], stop=dict(reason='invalid material')))
        self.write(batch, 'cohort.json', [dict(alias='D1', role='train', case='synthetic')])
        detail = self.view.read(batch)
        stages = {row['id']: row for row in detail['stages']}
        self.assertEqual(stages['case']['status'], 'blocked')
        for key in ('baseline', 'reflection', 'validation', 'freeze'):
            self.assertEqual(stages[key]['status'], 'not_started')
        self.assertFalse(detail['decision']['frozen'])
        self.assertIsNone(detail['test_runs'][0]['runs'][0]['verdict'])
        self.assertIsNone(detail['cost'][0]['usage'])

    def test_pilot_preserves_false_requirements_losses_and_generation_decisions(self):
        batch = 'pilot-complete'
        state = dict(baseline_slots=['base'], revalidation_slot='reval', candidate_generated=True)
        self.write(batch, 'summary.json', dict(development={'D1':dict(state=state, admission={'admitted':True})},
                                             tests={}, frozen_library=[{'version':'E1'}]))
        self.write(batch, 'actual-schedule.json', [dict(slot='base', score_result=dict(score_valid=True,
                   verdict='UNDERREACH', effects={'must_not_happen':False, 'keep':False})),
                   dict(slot='reval', score_result=dict(score_valid=True, verdict='PASS',
                        effects={'must_not_happen':False, 'keep':True}))])
        self.write(batch, 'development/D1/feedback.json', dict(standards=[
            dict(effect='must_not_happen', expected=False), dict(effect='keep', expected=True)]))
        self.write(batch, 'development/D1/experience-original.md', 'Synthetic experience')
        self.write(batch, 'experience-freeze.json', dict(entries=1))
        self.write(batch, 'frozen-library.json', [{'version':'E1'}])
        detail = self.view.read(batch)
        stages = {row['id']: row for row in detail['stages']}
        self.assertEqual(stages['baseline']['rows'][0]['passed'], 1)
        self.assertEqual(stages['validation']['rows'][0]['passed'], 2)
        self.assertTrue(detail['decision']['frozen'])
        self.assertEqual(detail['experiences'][0]['text']['text'], 'Synthetic experience')

    def test_missing_effects_and_infrastructure_failure_are_not_semantic_verdicts(self):
        row = self.view.run(dict(infrastructure_valid=False, valid=True, verdict='PASS'))
        self.assertFalse(row['valid'])
        self.assertIsNone(row['verdict'])
        row = self.view.run(dict(valid=True, effects={'known':False}), {'known':False, 'missing':True})
        self.assertEqual(row['passed'], 1)
        self.assertEqual(row['unknown'], 1)

    def test_only_allowlisted_files_are_read_and_no_runner_is_executed(self):
        batch = self.comparison()
        self.write(batch, 'auth.json', 'DO NOT EXPOSE')
        self.write(batch, 'prepare.py', 'raise RuntimeError("MUST NOT RUN")')
        before = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in self.research.rglob('*') if p.is_file()}
        self.view.list()
        detail = self.view.read(batch)
        self.assertNotIn('auth.json', [r['name'] for r in detail['artifacts']])
        with self.assertRaises(EvidenceError):
            self.view.artifact(batch, 'auth.json')
        for invalid in ('../outside', '/tmp/outside', 'comparison-1/..'):
            with self.subTest(invalid=invalid), self.assertRaises(EvidenceError):
                self.view.read(invalid)
        outside = self.root/'secret.md'
        outside.write_text('outside')
        (self.research/batch/'E1.md').symlink_to(outside)
        with self.assertRaises(EvidenceError):
            self.view.artifact(batch, 'E1.md')
        (self.research/batch/'E1.md').unlink()
        after = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in self.research.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_bad_summary_does_not_hide_other_batches(self):
        self.comparison()
        self.write('broken', 'summary.json', '{incomplete')
        data = self.view.list()
        self.assertEqual([r['id'] for r in data['items']], ['comparison-1'])
        self.assertEqual(data['warnings'][0]['id'], 'broken')

    def test_http_navigation_artifacts_and_get_only_access(self):
        batch = self.comparison()
        with patch.dict(os.environ, {'TCA_CONFIG':str(self.root/'config.json'),
                                    'TCA_DEVELOPMENT_ROOT':str(self.research)}):
            server = hub.ReportServer(self.root/'reports')
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        opener = build_opener(ProxyHandler({}))
        try:
            for asset in ('/development', '/development.js', '/development.css'):
                with opener.open(server.url+asset, timeout=5) as response:
                    self.assertEqual(response.status, 200)
            with opener.open(server.url+'/api/development', timeout=5) as response:
                self.assertEqual(len(json.load(response)['items']), 1)
            path = '/api/development/'+batch+'/artifact?'+urlencode({'name':'NEW_EXPERIENCE.md'})
            with opener.open(server.url+path, timeout=5) as response:
                self.assertIn('shared ownership', json.load(response)['text'])
            request = Request(server.url+'/api/development/'+batch+'/start', data=b'{}',
                              headers={'Content-Type':'application/json','X-TCA-Request':'local'})
            with self.assertRaises(HTTPError) as error:
                opener.open(request, timeout=5)
            self.assertEqual(error.exception.code, 404)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(3)


if __name__ == '__main__':
    unittest.main()
