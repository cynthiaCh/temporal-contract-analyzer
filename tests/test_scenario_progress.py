"""Scenario counts are descriptive views of explicit archived oracle evidence."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from temporal_contract_analyzer import archive
from temporal_contract_analyzer.case_evaluation import scenario_progress
from temporal_contract_analyzer.workbench import Workbench


class ScenarioProgressTests(unittest.TestCase):
    def test_mixed_scenarios_and_assertions(self):
        outcome={'verdict':'UNDERREACH','schedules':{
            'one':{'passed':True,'assertions':[{'id':'check-1','passed':True}]},
            'two':{'passed':False,'assertions':[{'id':'check-2','passed':False},{'id':'check-3','passed':True}]},
            'three':{'assertions':[{'id':'check-4','passed':True}]},
            'four':{'events':['observed']},
            'five':{'passed':False,'runtimeError':'missing runtime'},
        }}
        value=scenario_progress(outcome)
        self.assertEqual({k:value[k] for k in ('total','passed','failed','unknown','error')},
                         dict(total=5,passed=2,failed=1,unknown=1,error=1))
        self.assertEqual(value['items'][1]['failed_assertions'],['check-2'])
        self.assertEqual(value['items'][1]['assertions'],dict(total=2,passed=1,failed=1,unknown=0))

    def test_does_not_infer_passes_from_missing_effect_names_or_overall_verdict(self):
        outcome={'verdict':'PASS','missing_required_effects':[],
                 'schedules':{'one':{'events':[]},'two':{'assertions':[{'passed':True},{}]}}}
        value=scenario_progress(outcome)
        self.assertEqual(value['passed'],0)
        self.assertEqual(value['unknown'],2)
        for raw in ({},{'schedules':{}},{'schedules':[]}):self.assertIsNone(scenario_progress(raw))

    def test_partial_assertions_and_inconsistent_producer(self):
        value=scenario_progress({'schedules':{
            'one':{'passed':True,'assertions':[{'passed':False}]},
            'two':{'assertions':[{'passed':True},'untyped']},
            'three':True,'four':1}})
        self.assertEqual(value['passed'],1)
        self.assertEqual(value['unknown'],3)
        self.assertEqual(scenario_progress({'schedules':{'one':{'assertions':[{'passed':False},{}]}}})['failed'],1)

    def test_legacy_evaluation_is_enriched_without_rewriting_or_changing_verdict(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            with patch.dict(os.environ,{'TCA_CONFIG':str(root/'config.json')}):
                bench=Workbench(root/'reports',codex='/nonexistent')
                folder=bench.root/'e-0123456789abcdef'
                manifest=dict(id=folder.name,status='completed',label='Synthetic partial success',created_at='2026-11-04T00:00:00Z',
                              model='SYNTHETIC_ONLY',conditions=['none'],jobs=[dict(id='j-001',condition='none',status='completed')])
                archive.atomic_json(folder/'manifest.json',manifest)
                evaluation=folder/'evaluations/v-test'
                archive.atomic_json(evaluation/'summary.json',dict(id='v-test',completed_at='2026-11-04T00:00:01Z',
                    jobs={'j-001':dict(status='failed',verdict='OVERREACH',schedules=2)}))
                archive.atomic_json(evaluation/'j-001/oracle/stdout.json',dict(verdict='OVERREACH',
                    schedules={'one':{'passed':True},'two':{'passed':True}},observed_forbidden_effects=['forbidden-change']))
                paths=list(folder.rglob('*.json')); before={p:p.read_bytes() for p in paths}
                job=bench.read(folder.name)['jobs'][0]
                self.assertEqual(job['evaluation']['scenario_progress']['passed'],2)
                self.assertEqual(job['task_success'],'failed')
                self.assertEqual(job['evaluation']['verdict'],'OVERREACH')
                self.assertEqual(bench.list()['items'][0]['jobs'][0]['evaluation']['scenario_progress']['total'],2)
                self.assertEqual({p:p.read_bytes() for p in paths},before)
                (evaluation/'j-001/oracle/stdout.json').unlink()
                self.assertIsNone(bench.read(folder.name)['jobs'][0]['evaluation']['scenario_progress'])
