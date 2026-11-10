"""Native bridge/scorer interface checks with synthetic artifacts; no model calls."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import evolution_fixtures as fixtures
from temporal_contract_analyzer import case_evaluation
from temporal_contract_analyzer.case_catalog import case_input
from temporal_contract_analyzer.core import canonical, sha, EvidenceError
from temporal_contract_analyzer.case_evaluation import scoring_inputs
from temporal_contract_analyzer.evolution_backend import NativeBackend, source_hashes


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);fixtures.synthetic_bench(self.root/'bench')
        self.env=patch.dict(os.environ,{'TCA_BENCH_ROOT':str(self.root/'bench'),'TCA_CONFIG':str(self.root/'config')})
        self.env.start();self.addCleanup(self.env.stop)
        # These tests exercise scoring and calibration on a synthetic candidate.
        # No native session is launched; test the isolation prerequisite separately.
        which = shutil.which
        availability = patch('temporal_contract_analyzer.evolution_backend.shutil.which',
            side_effect=lambda name: '/synthetic/bwrap' if name == 'bwrap' else which(name))
        availability.start();self.addCleanup(availability.stop)
        path=self.root/'bench/cases/development/case.json'
        manifest=json.loads(path.read_text())
        manifest['runtime']={'minimum_version':'.'.join(map(str,sys.version_info[:2]))}
        path.write_text(json.dumps(manifest))
        inputs=case_input('development');record=inputs['case_record']
        native_runtime=case_evaluation.runtime(manifest,'python',None)
        evidence={}
        for role,verdict in [('original','UNDERREACH'),('reference','PASS'),('degenerate','UNDERREACH')]:
            source=self.root/(role+'.json');source.write_text(json.dumps(dict(case_id='development',
                verdict=verdict,origin='synthetic_fixture_not_real_calibration')))
            evidence[role]=dict(path=str(source),sha256=sha(source.read_bytes()))
        scoring=scoring_inputs(record)
        self.protocol=dict(case=record,backend_sources=source_hashes(),binary=sys.executable,
            node=shutil.which('node') or sys.executable,scoring_inputs=scoring,candidate_sha256='a'*64,
            executable_sha256={str(Path(p).resolve()):sha(Path(p).read_bytes())
                               for p in (sys.executable,shutil.which('node') or sys.executable)},
            calibration=dict(case_id='development',candidate_sha256='a'*64,
                scoring_inputs_sha256=sha(canonical(scoring).encode()),runtime=native_runtime,evidence=evidence),
            visible=dict(task=inputs['task']),input_path=inputs['candidate'])

    def test_version_bound_calibration_and_single_original_scorer_invocation(self):
        backend=NativeBackend();backend.preflight(self.protocol)
        with patch.object(case_evaluation,'invoke',wraps=case_evaluation.invoke) as invoked:
            outcome=backend.score(self.protocol,Path(self.protocol['input_path']),self.root/'scored')
        self.assertEqual(invoked.call_count,1)
        self.assertEqual(outcome['verdict'],'UNDERREACH')
        value=json.loads((self.root/'scored/evaluation.json').read_text())
        self.assertEqual(value['calibration'],'reused_frozen_original_reference_degenerate_evidence')

    def test_calibration_cannot_be_only_a_boolean_approval_or_wrong_runtime(self):
        backend=NativeBackend();self.protocol['calibration']['runtime']['version']='0.0'
        with self.assertRaises(EvidenceError):backend.preflight(self.protocol)

    def test_missing_isolation_blocks_before_native_execution(self):
        with patch('temporal_contract_analyzer.evolution_backend.shutil.which', return_value=None):
            with self.assertRaisesRegex(EvidenceError, 'requires the explicit Codex binary, node and bwrap'):
                NativeBackend().preflight(self.protocol)

    def test_runtime_error_is_not_a_credible_degenerate_failure(self):
        source=self.protocol['calibration']['evidence']['degenerate']
        path=Path(source['path']);value=json.loads(path.read_text())
        value['schedules']={'broken':{'runtimeError':'SYNTHETIC_ENVIRONMENT_ERROR'}}
        path.write_text(json.dumps(value));source['sha256']=sha(path.read_bytes())
        with self.assertRaises(EvidenceError):NativeBackend().preflight(self.protocol)

    def test_native_bridge_retains_null_usage_and_partial_response_without_parsing_success(self):
        directory=self.root/'session';directory.mkdir()
        protocol=self.protocol
        class FakeProcess:
            returncode=0
            def __init__(self,command,**kwargs):
                self.command=command
            def communicate(self,request,timeout):
                data=json.loads(request)
                archive=Path(data['run_dir'])/'archive';archive.mkdir(parents=True)
                (archive/'raw-answer.txt').write_text('')
                (archive/'partial-answer.txt').write_text('SYNTHETIC_PARTIAL_STREAM')
                (archive/'usage.json').write_text(json.dumps(dict(requests_started=1,
                    total_usage=None,observed_usage_subtotal=None,usage_unknown_requests=1)))
                return json.dumps(dict(candidate_complete=False,infrastructure_valid=False,
                    scoring_admissible=False,archive_failure_requires_stop=False,
                    stop_reason='SYNTHETIC_STREAM_FAILURE')), 'synthetic stderr'
        with patch('temporal_contract_analyzer.evolution_backend.subprocess.Popen',FakeProcess):
            # Preflight's runtime subprocess is already checked above; keep this
            # patch restricted to the bridge rather than faking runtime discovery.
            with patch.object(NativeBackend,'preflight',return_value=None):
                result=NativeBackend().execute(protocol,'reflect','Synthetic prompt',dict(type='object'),directory)
        self.assertFalse(result['completed'])
        self.assertIsNone(result['output'])
        self.assertIsNone(result['usage']['total_usage'])
        self.assertEqual(result['usage']['usage_unknown_requests'],1)
        self.assertTrue((directory/'native/archive/partial-answer.txt').exists())
        self.assertFalse((directory/'backend/study.py').exists())
        request=json.loads((directory/'native-request.json').read_text())
        self.assertEqual(request['slot']['phase'],'reflect')
        self.assertEqual(request['config']['seconds_per_session'],600)


if __name__=='__main__':unittest.main()
