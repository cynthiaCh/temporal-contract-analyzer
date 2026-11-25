"""Offline profile propagation and bounded transport recovery; no paid calls."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import test_tempoevo_v4 as fixtures
from temporal_contract_analyzer.core import EvidenceError
from temporal_contract_analyzer.tempoevo_v4 import MODEL, read
from temporal_contract_analyzer._session_runtime.model_settings import resolve_profile, identity, validate_settings
from temporal_contract_analyzer.stage_retry import transient_transport


class RetryBackend(fixtures.Backend):
    def __init__(self, failures=1, failure_type='transient_transport_error', **kw):
        super().__init__(**kw);self.failures=failures;self.failure_type=failure_type;self.trials=[];self.on_failure=None;self.request_count=1
    def execute(self,stage,payload,model,limits,directory):
        if stage=='action':
            self.trials.append((deepcopy(payload),deepcopy(limits),directory))
            if len(self.trials)<=self.failures:
                if self.on_failure:self.on_failure()
                payload['candidate_sources']['main.py']='value = 999\n'
                return dict(valid=False,error='Connection failed: error sending request',failure_type=self.failure_type,
                            model=model,requests=self.request_count,tokens=None,usage_incomplete=True,unknown_usage_requests=1)
        out=super().execute(stage,payload,model,limits,directory);out['model']=model;return out


class ModelRetryTests(unittest.TestCase):
    setUp=fixtures.V4Tests.setUp
    prepare=fixtures.V4Tests.prepare

    def config_file(self, retries=2, model='synthetic-other-model', effort=None):
        settings=resolve_profile();settings.update(profile='custom',model=model,reasoning_effort=effort,service_tier=None)
        settings['provider']=dict(name='Compatible',wire_api='responses',requires_openai_auth=False,base_url='https://provider.example/v1',env_key='TEMPOEVO_TEST_API_KEY')
        data=dict(schema_version='tempoevo-model-profiles-v1',default_profile='custom',retry_policy=dict(max_retries=retries,backoff_seconds=0),profiles={'custom':{k:settings[k] for k in ('model','reasoning_effort','service_tier','provider')}})
        path=self.root/'models.json';path.write_text(json.dumps(data));return path

    def test_network_failures_recover_without_extra_action_or_evaluation(self):
        loop=self.prepare(model_config=str(self.config_file()));backend=RetryBackend(failures=2)
        state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'));self.assertEqual(len(state['attempts']),1)
        self.assertEqual(len(backend.trials),3)
        self.assertEqual([p['candidate_sources']['main.py'] for p,_,_ in backend.trials],['value = 0\n']*3)
        self.assertEqual([limits['requests'] for _,limits,_ in backend.trials],[24,23,22])
        self.assertEqual(len([s for s in state['stages'] if s['kind']=='gold']),1)
        row=next(s for s in state['stages'] if s['key']=='action-1')
        self.assertEqual(row['requests'],3);self.assertEqual(row['unknown_usage_requests'],2);self.assertIsNone(row['tokens'])
        self.assertEqual(read(loop.root/'summary.json')['transport_retries'],2)
        self.assertTrue(all((d/'result.json').exists() for _,_,d in backend.trials))
        model=read(loop.root/'protocol.json')['model'];self.assertEqual(model,dict(model='synthetic-other-model',reasoning_effort=None))
        self.assertTrue(all(call[2]==model for call in backend.calls))

    def test_minimax_credits_profile_reaches_stages_without_an_explicit_effort(self):
        path=self.config_file(model='MiniMax-M3.1-Flash')
        data=json.loads(path.read_text())
        data['profiles']['custom']['provider']=dict(name='Qoder Credits',wire_api='qoder_cli',requires_openai_auth=False)
        path.write_text(json.dumps(data))
        loop=self.prepare(model_config=str(path));backend=RetryBackend(failures=0)
        state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'))
        self.assertTrue(all(call[2]==dict(model='MiniMax-M3.1-Flash',reasoning_effort=None) for call in backend.calls))
        settings=resolve_profile('custom',path);settings['reasoning_effort']='low'
        with self.assertRaisesRegex(ValueError,'reasoning effort'):validate_settings(settings)

    def test_efficient_tier_reaches_stages_and_rejects_explicit_effort(self):
        path=self.config_file(model='Efficient')
        data=json.loads(path.read_text())
        data['profiles']['custom']['provider']=dict(name='Qoder Credits',wire_api='qoder_cli',requires_openai_auth=False)
        path.write_text(json.dumps(data))
        loop=self.prepare(model_config=str(path));backend=RetryBackend(failures=0)
        state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'))
        self.assertTrue(all(call[2]==dict(model='Efficient',reasoning_effort=None) for call in backend.calls))
        settings=resolve_profile('custom',path);settings['reasoning_effort']='low'
        with self.assertRaisesRegex(ValueError,'reasoning effort'):validate_settings(settings)

    def test_retry_exhaustion_is_invalid_not_three_behavior_failures(self):
        loop=self.prepare(model_config=str(self.config_file()));b=RetryBackend(failures=9)
        state=loop.run(b,execute=True)
        self.assertEqual(state['status'],'execution_invalid');self.assertEqual(len(b.trials),3);self.assertEqual(state['attempts'],[])
        self.assertFalse((loop.root/'expert-summary-task.json').exists());self.assertFalse((loop.root/'candidate-pool').exists())
        before=len(b.trials);loop.run(b,execute=True);self.assertEqual(len(b.trials),before)

    def test_nontransport_failure_does_not_retry(self):
        for failure in ['timeout','invalid_output','authentication_error','infrastructure_error']:
            loop=self.prepare(model_config=str(self.config_file()));b=RetryBackend(failures=9,failure_type=failure)
            self.assertEqual(loop.run(b,execute=True)['status'],'execution_invalid');self.assertEqual(len(b.trials),1)

    def test_retry_shares_original_request_budget(self):
        from temporal_contract_analyzer.tempoevo_v4 import LIMITS
        limits=deepcopy(LIMITS);limits['action']['requests']=2
        loop=self.prepare(model_config=str(self.config_file()),limits=limits);b=RetryBackend(failures=9)
        self.assertEqual(loop.run(b,execute=True)['status'],'execution_invalid');self.assertEqual(len(b.trials),2)
        self.assertEqual(read(loop.root/'summary.json')['requests'],3)  # Contract 1 + Action 2.

    def test_unknown_or_overbudget_usage_prevents_retry(self):
        for value in [None,-1,25]:
            loop=self.prepare(model_config=str(self.config_file()));b=RetryBackend();b.request_count=value
            self.assertEqual(loop.run(b,execute=True)['status'],'execution_invalid');self.assertEqual(len(b.trials),1)

    def test_stage_deadline_and_cancel_stop_recovery(self):
        from temporal_contract_analyzer.tempoevo_v4 import LIMITS
        limits=deepcopy(LIMITS);limits['action']['seconds']=.01
        loop=self.prepare(model_config=str(self.config_file()),limits=limits);b=RetryBackend();b.on_failure=lambda:time.sleep(.02)
        self.assertEqual(loop.run(b,execute=True)['status'],'execution_invalid');self.assertEqual(len(b.trials),1)
        loop=self.prepare(model_config=str(self.config_file()));b=RetryBackend();b.on_failure=loop.cancel
        self.assertEqual(loop.run(b,execute=True)['status'],'cancelled');self.assertEqual(len(b.trials),1)

    def test_profile_is_frozen_external_edit_cannot_switch_model(self):
        config=self.config_file();loop=self.prepare(model_config=str(config));config.write_text('{}')
        state=loop.run(RetryBackend(failures=0),execute=True);self.assertEqual(state['status'],'passed',state.get('error'))
        self.assertEqual(read(loop.root/'protocol.json')['model']['model'],'synthetic-other-model')

    def test_model_drift_and_old_v5_are_blocked(self):
        loop=self.prepare(model_config=str(self.config_file()))
        self.assertEqual(loop.run(fixtures.Backend(),execute=True)['status'],'execution_invalid')
        for version in ['tempoevo-trajectory-v5','tempoevo-trajectory-v6','tempoevo-trajectory-v7','tempoevo-trajectory-v8']:
            loop=self.prepare();p=read(loop.root/'protocol.json');p['schema_version']=version;loop.save('protocol.json',p)
            with self.assertRaisesRegex(EvidenceError,'Historical protocol'):loop.run(RetryBackend(),execute=True)

    def test_interrupted_restart_is_archived_and_never_silently_replayed(self):
        loop=self.prepare(model_config=str(self.config_file()));b=RetryBackend(failures=9)
        original=b.execute
        def execute(stage,payload,model,limits,directory):
            if stage=='action' and len(b.trials)==1:raise RuntimeError('Synthetic interruption during restart')
            return original(stage,payload,model,limits,directory)
        b.execute=execute;state=loop.run(b,execute=True)
        self.assertEqual(state['status'],'execution_invalid')
        row=next(s for s in state['stages'] if s['kind']=='action')
        self.assertEqual([x['status'] for x in row['executions']],['complete','started'])
        self.assertTrue((loop.root/'stages/action-1/executions/1/result.json').exists())
        before=len(b.trials);loop.run(b,execute=True);self.assertEqual(len(b.trials),before)

    def test_retry_zero_and_invalid_profiles(self):
        loop=self.prepare(model_config=str(self.config_file(retries=0)));b=RetryBackend()
        self.assertEqual(loop.run(b,execute=True)['status'],'execution_invalid');self.assertEqual(len(b.trials),1)
        with self.assertRaises(EvidenceError):self.prepare(model_profile='missing')
        with self.assertRaises(EvidenceError):self.prepare(model={'model':'other','reasoning_effort':'medium'})
        s=resolve_profile();s['provider']['api_key']='SECRET'
        with self.assertRaises(ValueError):validate_settings(s)

    def test_transient_classifier_requires_archive_and_excludes_http_errors(self):
        r=dict(receipt=dict(failure_class='model_or_cli_abnormal_exit',archive_failure_requires_stop=False))
        self.assertTrue(transient_transport(r,'stream disconnected before completion: error sending request'))
        for message in ['Bad Request 400: error sending request','401 unauthorized: Connection failed','context length: Connection failed','Invalid output']:
            self.assertFalse(transient_transport(r,message))
        r['receipt']['archive_failure_requires_stop']=True
        self.assertFalse(transient_transport(r,'Connection failed'))

    def test_cli_and_docker_receive_profile_without_archiving_api_key(self):
        import subprocess
        import sys
        from temporal_contract_analyzer.execution_backend import SOURCE
        settings=resolve_profile('custom',self.config_file(model='configured-model',effort='high'))
        code='''import sys,json,os
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import native_backend as nb
from docker_transport import Launcher
root=Path(sys.argv[2]);settings=json.loads(sys.argv[3]);public=root/'public';public.mkdir()
for name in ['codex','codex-code-mode-host']:(public/name).write_text('fixture')
nb.BINARY=public/'codex';nb.global_snapshot=lambda:{}
native=nb.command('TEST',root/'session','extraction',copy_auth=False,runtime=root/'runtime',socket_dir=root/'socket',settings=settings)
assert native[native.index('-m')+1]=='configured-model'
assert 'model_reasoning_effort="high"' in native
assert 'model_providers.tempoevo_configured.base_url="https://provider.example/v1"' in native
assert 'model_providers.tempoevo_configured.request_max_retries=0' in native
assert 'SYNTHETIC_SECRET_VALUE' not in ' '.join(native)
config=dict(name='tca-session-'+'a'*32,solver_image='sha256:'+'b'*64,node='/runtime/node16/bin/node',credential_env=['TEMPOEVO_TEST_API_KEY'])
cmd=Launcher(config,root/'session/archive').command(native,root/'session',root/'runtime','TEST',root/'socket')
assert ['--env','TEMPOEVO_TEST_API_KEY'] == cmd[cmd.index('TEMPOEVO_TEST_API_KEY')-1:cmd.index('TEMPOEVO_TEST_API_KEY')+1]
assert 'SYNTHETIC_SECRET_VALUE' not in ' '.join(cmd)
settings['reasoning_effort']=None
again=nb.command('SECOND',root/'second','extraction',copy_auth=False,runtime=root/'runtime',socket_dir=root/'socket',settings=settings)
assert not any(x.startswith('model_reasoning_effort=') for x in again)
'''
        with patch.dict(os.environ,{'TEMPOEVO_TEST_API_KEY':'SYNTHETIC_SECRET_VALUE'}):
            p=subprocess.run([sys.executable,'-c',code,str(SOURCE),str(self.root),json.dumps(settings)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)

    def test_native_adapter_classifies_real_shape_connection_failure(self):
        from temporal_contract_analyzer.tempoevo_backend import NativeV4Backend
        directory=self.root/'native-test';directory.mkdir()
        native=directory/'native-stage/native/archive';native.mkdir(parents=True)
        (native/'service-errors.json').write_text(json.dumps({'raw_cli_errors':[{'event':{'message':'stream disconnected before completion: error sending request'}}]}))
        raw=dict(completed=False,infrastructure_valid=False,usage=dict(requests_started=1,total_usage=None,usage_unknown_requests=1,usage_incomplete=True),receipt=dict(failure_class='model_or_cli_abnormal_exit',archive_failure_requires_stop=False))
        # The public adapter owns native-stage creation, so retain only the error fixture on mocked dispatch.
        import shutil
        shutil.rmtree(directory/'native-stage')
        def dispatch(*args):
            p=directory/'native-stage/native/archive';p.mkdir(parents=True,exist_ok=True)
            (p/'service-errors.json').write_text(json.dumps({'raw_cli_errors':[{'event':{'message':'stream disconnected before completion: error sending request'}}]}))
            return raw
        backend=NativeV4Backend(dict(binary='/synthetic/codex'))
        with patch('temporal_contract_analyzer.execution_backend.NativeBackend.execute',side_effect=dispatch):
            out=backend.execute('action',dict(task='Public task',sources={'main.py':'value = 0\n'}),MODEL,dict(requests=24,seconds=60),directory)
        self.assertEqual(out['failure_type'],'transient_transport_error');self.assertEqual(out['requests'],1)

    def test_batch_launcher_rejects_history_without_overwriting_results(self):
        import subprocess
        import sys
        batch=self.root/'old-batch';trajectory=batch/'old-case/trajectory';trajectory.mkdir(parents=True)
        (trajectory/'protocol.json').write_text(json.dumps({'schema_version':'tempoevo-trajectory-v5'}))
        (batch/'progress.json').write_text(json.dumps([dict(status='prepared',rank=11,case_id='old-case',root=str(trajectory.parent))]))
        history=batch/'training-progress.json';history.write_text('historical result bytes\n')
        tool=Path(__file__).resolve().parents[1]/'tools/tempoevo-docker/run_selected.py'
        result=subprocess.run([sys.executable,str(tool),'--root',str(batch),'--execute'],capture_output=True,text=True)
        self.assertEqual(result.returncode,2);self.assertIn('Historical batch is read-only',result.stderr)
        self.assertEqual(history.read_text(),'historical result bytes\n')
