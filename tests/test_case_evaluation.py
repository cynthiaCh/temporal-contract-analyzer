"""Trusted scoring rejects invalid observations and keeps regression evidence."""
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest

from temporal_contract_analyzer.case_evaluation import delta, invoke, terminate
from temporal_contract_analyzer.core import EvidenceError


class CaseEvaluationTests(unittest.TestCase):
    def test_relation_delta_keeps_gains_losses_and_unknowns(self):
        before = dict(observed_effects=dict(gain=False, loss=True, keep=True, uncertain=None),
                      missing_required_effects=['gain'])
        after = dict(observed_effects=dict(gain=True, loss=True, keep=True, uncertain=None),
                     observed_forbidden_effects=['loss'])
        self.assertEqual(delta(before, after), dict(gained=['gain'], lost=['loss'],
                         retained=['keep'], unknown=['uncertain']))
        with self.assertRaises(EvidenceError):
            delta(before, dict(observed_effects={'other': True}))
        with self.assertRaises(EvidenceError):
            delta(before, dict(verdict='PASS'))

    def test_scorer_exit_case_and_runtime_errors_are_not_valid_outcomes(self):
        rows = [
            (dict(case_id='fixture', verdict='PASS'), 0, True),
            (dict(case_id='fixture', verdict='UNDERREACH'), 1, True),
            (dict(case_id='wrong', verdict='PASS'), 0, False),
            (dict(case_id='fixture', verdict='PASS'), 1, False),
            (dict(case_id='fixture', verdict='UNDERREACH'), 2, False),
            (dict(case_id='fixture', verdict='UNDERREACH',
                  schedules={'broken': {'runtimeError': 'synthetic missing runtime'}}), 1, False),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            for number, (outcome, code, valid) in enumerate(rows):
                with self.subTest(outcome=outcome, code=code):
                    command = [sys.executable, '-B', '-c',
                               'import sys; print(sys.argv[1]); sys.exit(int(sys.argv[2]))',
                               json.dumps(outcome), str(code)]
                    directory = Path(temporary)/str(number)
                    if valid:
                        self.assertEqual(invoke(command, directory, threading.Event(), terminate, 'fixture'), outcome)
                    else:
                        with self.assertRaises(EvidenceError):
                            invoke(command, directory, threading.Event(), terminate, 'fixture')
                    self.assertTrue((directory/'stdout.json').is_file())
                    self.assertTrue((directory/'execution.json').is_file())
