"""A controller-stop placeholder is distinguishable from an actual Gold call."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('recover_stage',Path(__file__).resolve().parents[1]/'experiments/experience-growth/train70-test30-20261118/recover_unlaunched.py')
recover=importlib.util.module_from_spec(spec);spec.loader.exec_module(recover)


class UnlaunchedGoldTests(unittest.TestCase):
    def test_only_pre_dispatch_placeholder_can_be_recovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);stage=dict(key='final-gold',kind='gold',status='invalid',requests=0)
            folder=root/'stages/final-gold';folder.mkdir(parents=True)
            value=dict(valid=False,failure_type='infrastructure_error',error=recover.STOP_ERROR)
            for name in ('input.json','raw-result.json','result.json'):(folder/name).write_text(json.dumps(value))
            self.assertTrue(recover.unlaunched_evaluation(stage,root))
            (folder/'command.json').write_text('[]')
            self.assertFalse(recover.unlaunched_evaluation(stage,root))
            (folder/'command.json').unlink()
            value['error']='Real grader failed';(folder/'raw-result.json').write_text(json.dumps(value))
            self.assertFalse(recover.unlaunched_evaluation(stage,root))


if __name__=='__main__':unittest.main()
