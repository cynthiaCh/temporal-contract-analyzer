"""Exercise the actual .command Python payload without opening a browser/model."""
from contextlib import redirect_stdout, redirect_stderr
import io
import json
import unittest
from unittest.mock import patch

from temporal_contract_analyzer import hub
from temporal_contract_analyzer.core import ROOT


class WorkbenchLauncherTests(unittest.TestCase):
    def run_launcher(self, health, active=None):
        source=(ROOT/'启动Codex实验工作台.command').read_text()
        payload=source.split('<<\'PY\'\n',1)[1].split('\nPY\n',1)[0]
        old=dict(url='http://127.0.0.1:12345',instance='old')
        new=dict(url='http://127.0.0.1:12346',instance='new')
        replies=[io.StringIO(json.dumps(health)),io.StringIO(json.dumps(dict(active=active)))]
        with patch.object(hub,'ensure_server',side_effect=[old,new]) as ensure, \
                patch.object(hub._opener,'open',side_effect=replies), \
                patch.object(hub,'stop_server') as stop, \
                patch.object(hub,'running_server',return_value=None), \
                patch('webbrowser.open',return_value=True) as browser, \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            status=0
            try:exec(compile(payload,'启动Codex实验工作台.command','exec'),{})
            except SystemExit as error:status=error.code
            return status,ensure.call_count,stop.call_count,browser.call_args

    def test_upgrades_idle_service_missing_context_capability(self):
        status,starts,stops,browser=self.run_launcher({'experiment_ui':'local-codex-models-v1'})
        self.assertEqual((status,starts,stops),(0,2,1))
        self.assertEqual(browser.args[0],'http://127.0.0.1:12346/experiments')

    def test_reuses_current_service(self):
        status,starts,stops,browser=self.run_launcher(dict(experiment_ui='local-codex-models-v1',context_enrichment='snapshot-definitions-v1',scenario_progress='explicit-schedules-v1',failure_learning='candidate-memory-v1'))
        self.assertEqual((status,starts,stops),(0,1,0))
        self.assertEqual(browser.args[0],'http://127.0.0.1:12345/experiments')

    def test_refuses_to_interrupt_active_old_service(self):
        status,starts,stops,browser=self.run_launcher({'experiment_ui':'local-codex-models-v1'},active='running-experiment')
        self.assertEqual((status,starts,stops),(1,1,0))
        self.assertIsNone(browser)
