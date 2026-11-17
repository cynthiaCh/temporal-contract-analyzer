"""Replay accounting excludes interrupted repair, preserves completed acceptance."""
import importlib.util
from pathlib import Path
import unittest
SPEC=importlib.util.spec_from_file_location('training_replay',Path(__file__).resolve().parents[1]/'tools/tempoevo-docker/run_training_replay.py')
replay=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(replay)

class ReplayAccounting(unittest.TestCase):
    def test_accepted_repair_is_not_lost_to_later_extraction_error(self):
        s=dict(status='execution_invalid',training_accepted=True,final_acceptance=dict(valid=True,passed=True),attempts=[dict(acceptance_passed=True)],error='extract unavailable')
        row=replay.score_state(s)
        self.assertIs(row['final_passed'],True);self.assertTrue(row['extraction_error'])

    def test_interrupted_second_action_is_unscored_not_prior_failure(self):
        s=dict(status='execution_invalid',attempts=[dict(acceptance_passed=False)],error='transport unavailable')
        row=replay.score_state(s)
        self.assertIsNone(row['final_passed']);self.assertIs(row['first_passed'],False)
        result=replay.summarize([row],70)
        self.assertEqual(result['failed'],0);self.assertEqual(result['unscored'],1);self.assertIsNone(result['pass_rate'])

    def test_mixed_valid_denominator(self):
        def state(accepted):return dict(status='passed' if accepted else 'repair_exhausted',training_accepted=accepted,final_acceptance=dict(valid=True),attempts=[dict(acceptance_passed=accepted)])
        rows=[replay.score_state(state(True)),replay.score_state(state(False)),replay.score_state(dict(status='execution_invalid'))]
        result=replay.summarize(rows,70)
        self.assertEqual((result['passed'],result['failed'],result['unscored']),(1,1,1));self.assertEqual(result['pass_rate'],0.5)

if __name__=='__main__':unittest.main()
