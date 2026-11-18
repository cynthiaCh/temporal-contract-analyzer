"""Only completely measured bounded solver failures may be closed without rerun."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('close_invalid',Path(__file__).resolve().parents[1]/'experiments/experience-growth/train70-test30-20261118/close_bounded_invalid.py')
close=importlib.util.module_from_spec(spec);spec.loader.exec_module(close)


class InvalidClosureTests(unittest.TestCase):
    def setUp(self):
        self.state=dict(status='execution_invalid',stages=[dict(status='invalid',kind='contract')])
        self.result=dict(valid=False,failure_type='model_resource_limit',usage_incomplete=False,requests=12,
            native_receipt=dict(native=dict(started=12,completed=12),archive_status=dict(status='OK'),archive_failure_requires_stop=False))
        self.stages=[dict(state='settled',usage_incomplete=False)]
    def test_known_cap_failure_is_invalid_not_behavioral_score(self):
        self.assertEqual(close.classify(self.state,self.result,self.stages),'model_resource_limit')
    def test_unknown_usage_pending_or_cleanup_never_auto_closes(self):
        variants=[]
        row=deepcopy(self.result);row['usage_incomplete']=True;variants.append(row)
        row=deepcopy(self.result);row['native_receipt']['native']['completed']=11;variants.append(row)
        row=deepcopy(self.result);row['native_receipt']['transport_cleanup_error']='unknown';variants.append(row)
        for row in variants:
            with self.assertRaises(ValueError):close.classify(self.state,row,self.stages)
        with self.assertRaises(ValueError):close.classify(self.state,self.result,[dict(state='started',usage_incomplete=False)])
    def test_transport_and_gold_failure_need_individual_investigation(self):
        row=deepcopy(self.result);row['failure_type']='transient_transport_error'
        with self.assertRaises(ValueError):close.classify(self.state,row,self.stages)
        self.state['stages'][0]['kind']='gold'
        with self.assertRaises(ValueError):close.classify(self.state,self.result,self.stages)
    def test_policy_denial_requires_guard_evidence_and_complete_accounting(self):
        row=deepcopy(self.result);row['failure_type']='tool_policy_denied'
        with self.assertRaises(ValueError):close.classify(self.state,row,self.stages)
        row['native_receipt']['native']['blocked_tools']=1
        row['policy_denial']=dict(tool_name='Bash',reason='closed grammar',command='pwd && find .')
        self.assertEqual(close.classify(self.state,row,self.stages),'tool_policy_denied')
        row['usage_incomplete']=True
        with self.assertRaises(ValueError):close.classify(self.state,row,self.stages)


if __name__=='__main__':unittest.main()
