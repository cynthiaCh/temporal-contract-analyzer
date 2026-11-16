"""One Contract correction opportunity, with the original budgets and isolation."""
from copy import deepcopy
import unittest

import test_tempoevo_v4 as fixtures
import test_model_profiles_and_retries as retry_fixtures
from temporal_contract_analyzer.stage_retry import contract_write_denial
from temporal_contract_analyzer.tempoevo_v4 import LIMITS, read

PATCH = '*** Begin Patch\n*** Update File: /workspace/main.py\n@@\n-value = 0\n+value = 1\n*** End Patch'


def denied(model, patch=PATCH):
    return dict(valid=False, model=model, requests=1, tokens=dict(total_tokens=3),
        failure_type='tool_policy_denied', error='Blocked patch in read-only Contract stage',
        native_receipt=dict(archive_failure_requires_stop=False,patch_delivered=False,native=dict(blocked_tools=1)),
        policy_denial=dict(tool_name='apply_patch',command=patch))


class ContractBackend(fixtures.Backend):
    def __init__(self, failures=1):
        super().__init__();self.failures=failures;self.contract_calls=[];self.on_failure=None;self.request_count=1
    def execute(self,kind,payload,model,limits,directory):
        if kind=='contract' and 'version' not in payload:
            self.contract_calls.append((deepcopy(payload),deepcopy(limits),directory))
            if len(self.contract_calls)<=self.failures:
                if self.on_failure:self.on_failure()
                result=denied(model);result['requests']=self.request_count
                payload['sources']['main.py']='value = 999\n'  # Failed sessions cannot poison the next input.
                return result
        result=super().execute(kind,payload,model,limits,directory);result['model']=model;return result


class ContractToolRecoveryTests(unittest.TestCase):
    setUp=fixtures.V4Tests.setUp
    prepare=fixtures.V4Tests.prepare
    config_file=retry_fixtures.ModelRetryTests.config_file

    def test_one_correction_succeeds_even_with_transport_retries_disabled(self):
        loop=self.prepare(model_config=str(self.config_file(retries=0)));backend=ContractBackend()
        state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'))
        self.assertEqual(len(backend.contract_calls),2)
        first,second=backend.contract_calls
        self.assertEqual([c[1]['requests'] for c in backend.contract_calls],[12,11])
        self.assertLess(second[1]['seconds'],first[1]['seconds'])
        self.assertNotIn('tool_policy_feedback',first[0])
        self.assertIn('Do not call apply_patch',second[0]['tool_policy_feedback']['instruction'])
        self.assertEqual(second[0]['sources']['main.py'],'value = 0\n')
        self.assertEqual(read(second[2]/'input.json'),second[0])
        self.assertEqual(len(state['attempts']),1)
        self.assertEqual(len([s for s in state['stages'] if s['kind']=='gold']),1)
        summary=read(loop.root/'summary.json')
        self.assertEqual(summary['tool_policy_recoveries'],1)
        self.assertEqual(summary['transport_retries'],0)
        stage=next(s for s in state['stages'] if s['key']=='contract')
        self.assertEqual(stage['requests'],2)
        self.assertEqual(stage['tokens']['total_tokens'],13)
        self.assertEqual(stage['executions'][1]['restart_reason'],'contract_write_recovery')

    def test_repeated_patch_attempt_stops_after_one_extra_chance(self):
        loop=self.prepare();backend=ContractBackend(failures=99)
        state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'execution_invalid')
        self.assertEqual(len(backend.contract_calls),2)
        self.assertEqual(state['attempts'],[])
        self.assertFalse((loop.root/'expert-summary-task.json').exists())

    def test_no_extra_request_when_stage_budget_is_already_spent(self):
        limits=deepcopy(LIMITS);limits['contract']['requests']=1
        loop=self.prepare(limits=limits);backend=ContractBackend()
        self.assertEqual(loop.run(backend,execute=True)['status'],'execution_invalid')
        self.assertEqual(len(backend.contract_calls),1)
        self.assertEqual(read(loop.root/'summary.json')['tool_policy_recoveries'],0)

    def test_cancel_and_unknown_usage_prevent_correction(self):
        loop=self.prepare();backend=ContractBackend();backend.on_failure=loop.cancel
        self.assertEqual(loop.run(backend,execute=True)['status'],'cancelled')
        self.assertEqual(len(backend.contract_calls),1)
        loop=self.prepare();backend=ContractBackend();backend.request_count=None
        self.assertEqual(loop.run(backend,execute=True)['status'],'execution_invalid')
        self.assertEqual(len(backend.contract_calls),1)

    def test_deadline_and_frozen_binding_drift_prevent_correction(self):
        import time
        limits=deepcopy(LIMITS);limits['contract']['seconds']=.01
        loop=self.prepare(limits=limits);backend=ContractBackend();backend.on_failure=lambda:time.sleep(.02)
        self.assertEqual(loop.run(backend,execute=True)['status'],'execution_invalid')
        self.assertEqual(len(backend.contract_calls),1)
        loop=self.prepare();backend=ContractBackend()
        backend.on_failure=lambda:(loop.root/'original/main.py').write_text('changed = True\n')
        self.assertEqual(loop.run(backend,execute=True)['status'],'execution_invalid')
        self.assertEqual(len(backend.contract_calls),1)

    def test_outside_files_other_tools_and_unclean_archives_are_not_recovered(self):
        result=denied(fixtures.MODEL)
        self.assertTrue(contract_write_denial(result,'contract',{'main.py':''}))
        self.assertFalse(contract_write_denial(result,'action',{'main.py':''}))
        for patch in [PATCH.replace('/workspace/main.py','/etc/passwd'),PATCH.replace('/workspace/main.py','../main.py'),
                      PATCH.replace('/workspace/main.py','/workspace/unknown.py'), 'not a patch']:
            self.assertFalse(contract_write_denial(denied(fixtures.MODEL,patch),'contract',{'main.py':''}))
        for field,value in [('archive_failure_requires_stop',True),('patch_delivered',True),('preanalysis_error','Workspace changed')]:
            result=denied(fixtures.MODEL);result['native_receipt'][field]=value
            self.assertFalse(contract_write_denial(result,'contract',{'main.py':''}))
        result=denied(fixtures.MODEL);result['policy_denial']['tool_name']='Bash'
        self.assertFalse(contract_write_denial(result,'contract',{'main.py':''}))

    def test_testing_still_has_only_one_action_and_one_final_gold(self):
        from temporal_contract_analyzer.experience_approval import freeze
        loop=self.prepare(mode='testing',max_attempts=1,gold_evaluator=dict(command=['synthetic-gold']),memory_snapshot=freeze(self.store))
        backend=ContractBackend();state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'scored',state.get('error'))
        self.assertEqual(len(state['attempts']),1)
        self.assertEqual(len([s for s in state['stages'] if s['kind']=='gold']),1)
        self.assertFalse((loop.root/'candidate-pool').exists())

    def test_transport_retry_and_tool_correction_have_separate_counts_and_shared_budget(self):
        class MixedBackend(ContractBackend):
            def execute(inner,kind,payload,model,limits,directory):
                if kind=='contract' and len(inner.contract_calls)==1:
                    inner.contract_calls.append((deepcopy(payload),deepcopy(limits),directory))
                    return dict(valid=False,model=model,requests=1,tokens=dict(total_tokens=2),
                        failure_type='transient_transport_error',error='Connection reset')
                return super().execute(kind,payload,model,limits,directory)
        loop=self.prepare(model_config=str(self.config_file(retries=1)));backend=MixedBackend()
        state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'))
        self.assertEqual([c[1]['requests'] for c in backend.contract_calls],[12,11,10])
        self.assertIn('tool_policy_feedback',backend.contract_calls[-1][0])
        summary=read(loop.root/'summary.json')
        self.assertEqual(summary['tool_policy_recoveries'],1)
        self.assertEqual(summary['transport_retries'],1)
