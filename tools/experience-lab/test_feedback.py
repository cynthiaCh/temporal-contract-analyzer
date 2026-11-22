"""Progress reads real ledgers without treating a repair verdict as batch completion."""
import json
from pathlib import Path
import tempfile
import unittest

from records import case_status


class Progress(unittest.TestCase):
    def test_live_counts_and_extraction_after_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = root/'stages/extract/executions/1/native-stage/native/archive/meter/ledger.json'
            ledger.parent.mkdir(parents=True)
            ledger.write_text(json.dumps(dict(started=2, completed=1)))
            state = dict(status='passed', attempts=[{}], stages=[
                dict(key='action-1', status='complete', requests=6),
                dict(key='extract', status='started', requests=None)], final_acceptance=dict(passed=True))
            (root/'state.json').write_text(json.dumps(state))
            job = dict(case_id='fixture', trajectory=root)
            result = case_status(job)
            self.assertFalse(result['finished'])
            self.assertEqual(result['current_stage'], 'extract')
            self.assertEqual(result['completed_requests'], 7)
            self.assertEqual(result['pending_requests'], 1)
            ledger.write_text('{')
            self.assertEqual(case_status(job)['completed_requests'], 6)
            state['finalized'] = True
            (root/'state.json').write_text(json.dumps(state))
            self.assertTrue(case_status(job)['finished'])
            self.assertIsNone(case_status(job)['current_stage'])

    def test_execution_error_is_finished_with_no_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'state.json').write_text(json.dumps(dict(status='execution_invalid', attempts=[], error='fixture error')))
            result = case_status(dict(case_id='fixture', trajectory=root))
            self.assertTrue(result['finished'])
            self.assertIsNone(result['passed'])
            self.assertEqual(result['error'], 'fixture error')

    def test_qoder_turns_read_live_progress_without_synthetic_request_hooks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            progress = root/'stages/action-1/executions/1/qoder-progress.json'
            progress.parent.mkdir(parents=True)
            progress.write_text(json.dumps(dict(completed_turns=3, http_requests=None)))
            state = dict(status='action_running', attempts=[], stages=[dict(key='contract', status='complete', requests=1),
                         dict(key='action-1', status='started', requests=None)])
            (root/'state.json').write_text(json.dumps(state))
            result = case_status(dict(case_id='fixture', trajectory=root))
            self.assertEqual(result['completed_requests'], 4)
            self.assertEqual(result['pending_requests'], 0)
            self.assertEqual(result['current_stage'], 'action-1')
