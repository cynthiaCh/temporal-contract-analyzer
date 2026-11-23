"""Historical protocols are data-only; only current sessions may execute."""
from pathlib import Path
import tempfile
import unittest
import json
import importlib.util
from contextlib import redirect_stdout,redirect_stderr
from io import StringIO
from unittest.mock import patch
from temporal_contract_analyzer.cli import main
from temporal_contract_analyzer.history_cli import inspect
from temporal_contract_analyzer.execution_backend import NativeBackend
from temporal_contract_analyzer.core import EvidenceError

class HistoryTests(unittest.TestCase):
    def test_all_old_versions_are_read_without_writes_or_model_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for kind in ('evolution','development','evaluation'):
                for version in (1,2,3):
                    (root/'protocol.json').write_text(json.dumps(dict(schema_version=f'experience-{kind}-v{version}',implementation='arbitrary historical hash')))
                    (root/'state.json').write_text('{"status":"infrastructure_error"}')
                    (root/'summary.json').write_text('{"whole_passes":0}')
                    (root/'REPORT.md').write_text('Original report')
                    before={p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in root.iterdir()}
                    with patch('subprocess.Popen',side_effect=AssertionError('No execution')),redirect_stdout(StringIO()):
                        self.assertEqual(main(['history','status','--root',str(root)]),0)
                        self.assertEqual(main(['history','report','--root',str(root)]),0)
                    self.assertEqual(before,{p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in root.iterdir()})
                    self.assertFalse(inspect(root)['execution_supported'])
    def test_old_cli_no_longer_exposes_execution_or_preparation(self):
        for command in (['experience-evolution','prepare'],['experience-evolution','run'],['history','run']):
            with self.subTest(command=command),redirect_stderr(StringIO()),self.assertRaises(SystemExit):main(command)
    def test_old_modules_are_removed_and_shared_bridge_rejects_old_protocols(self):
        for name in ('experience_workflow','experience_development','experience_evaluation','experience_evolution','experience_candidate_handoff','evolution_cli','evolution_backend','semantic_retrieval','experience_recoding','experience_submission','experience_updates','failure_learning'):
            self.assertIsNone(importlib.util.find_spec('temporal_contract_analyzer.'+name))
        policies=[f'experience-development-v{version}' for version in (1,2,3)]
        policies += [f'tempoevo-trajectory-v{version}' for version in range(4,13)]
        for policy in policies:
            with self.subTest(policy=policy),self.assertRaisesRegex(EvidenceError,'only tempoevo-trajectory-v13'):
                NativeBackend().execute(dict(execution_policy=policy),'repair','',None,Path('/never-created'))
