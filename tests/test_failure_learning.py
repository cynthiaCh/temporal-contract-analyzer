import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from temporal_contract_analyzer import archive
from temporal_contract_analyzer.core import ROOT, EvidenceError
from temporal_contract_analyzer.learning import learn, list_lessons, review_material
from temporal_contract_analyzer.workbench import Workbench, capture, inventory


class FailureLearningTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        env=patch.dict(os.environ,{'TCA_CONFIG':str(self.root/'config.json')});env.start();self.addCleanup(env.stop)
        self.store=self.root/'reports';self.bench=Workbench(self.store,codex='/nonexistent')
        self.folder=self.bench.root/'e-0123456789abcdef'
        self.manifest=dict(id=self.folder.name,status='completed',case={'id':'synthetic'},
                           task='Maintain this source.',
                           label='Synthetic learning test',model='SYNTHETIC_ONLY',conditions=['review'],created_at='2026-11-04T00:00:00Z',
                           input_files={'main.js':'synthetic-hash'},report_id='synthetic-report',
                           jobs=[dict(id='j-001',status='completed',condition='review')])
        self.evaluation=dict(id='v-synthetic',completed_at='2026-11-04T00:00:00Z',calibration_verdict='PASS',
                             jobs={'j-001':dict(status='failed',verdict='UNDERREACH')})
        self.outcome=dict(verdict='UNDERREACH',schedules={'synthetic-close':{
            'passed':False,'assertions':[{'id':'synthetic.audit-retained','passed':False,'expected':'SECRET_EXPECTED_VALUE'}]}})
        self.write()

    def write(self):
        archive.atomic_json(self.folder/'manifest.json',self.manifest)
        archive.atomic_json(self.folder/'evaluations/v-synthetic/summary.json',self.evaluation)
        archive.atomic_json(self.folder/'evaluations/v-synthetic/j-001/oracle/stdout.json',self.outcome)

    def test_cli_spine_and_idempotent_candidate_memory(self):
        before={p:p.read_bytes() for p in self.folder.rglob('*.json')}
        result=subprocess.run([sys.executable,'-B','-m','temporal_contract_analyzer','reports','learn',self.folder.name,
                               '--store',str(self.store)],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        lesson=json.loads(result.stdout)['lessons'][0]
        self.assertEqual(lesson['status'],'candidate')
        self.assertIn('effect-separation',lesson['recipes'])
        self.assertNotIn('SECRET_EXPECTED_VALUE',json.dumps(lesson))
        self.assertEqual(learn(self.bench,self.folder.name)['lessons'][0],lesson)
        self.assertEqual(len(list_lessons(self.store,'synthetic')),1)
        self.assertEqual({p:p.read_bytes() for p in self.folder.rglob('*.json')},before)

    def code(self):
        root=self.root/'candidate';root.mkdir()
        (root/'main.js').write_text('async function run() {\n await fetch();\n publish();\n}\n')
        (root/'queue.js').write_text('export function attach(state) {\n return {\n record(frame) { state.recordProgress(frame); },\n receive(frame) { state.showProgress(frame); },\n };\n}\n')
        self.manifest['input_files']=inventory(capture(root)[0]);self.write()
        return root

    def test_learned_condition_freezes_source_context_and_preserves_original_arms(self):
        root=self.code();lesson=learn(self.bench,self.folder.name)['lessons'][0]
        run=self.bench.prepare(dict(candidate=str(root),task='Maintain this source.',model='SYNTHETIC_ONLY',
            conditions=['none','review','learned_review'],learning_case_id='synthetic'))
        self.assertEqual(run['learning']['lesson_ids'],[lesson['id']])
        folder=self.bench.folder(run['id'])
        a=(folder/'jobs/j-001/prompt.md').read_text();d=(folder/'jobs/j-002/prompt.md').read_text()
        learned=(folder/'jobs/j-003/report.md').read_text()
        self.assertNotIn('Feedback-informed',a+d)
        self.assertEqual((folder/'jobs/j-002/report.md').read_text(),archive.layer_text(run['report_id'],'review',self.store))
        self.assertIn('Feedback-informed',learned)
        self.assertIn('queue.js',learned)
        self.assertIn('state.recordProgress',learned)
        self.assertIn('state.showProgress',learned)
        for secret in ('SECRET_EXPECTED_VALUE','synthetic-close','synthetic.audit-retained'):
            self.assertNotIn(secret,learned)
        packet=json.loads((folder/'learned-context.json').read_text())
        self.assertLessEqual(packet['code_chars'],6000)
        packet,text=review_material(run['report_id'],[lesson],self.store,max_chars=1)
        self.assertEqual(packet['snippets'],[]);self.assertTrue(packet['omitted'])
        self.bench.codex='/usr/bin/true'
        (folder/'jobs/j-003/report.md').write_text('tampered')
        with self.assertRaisesRegex(EvidenceError,'冻结提示词或报告'):
            self.bench.start(run['id'])

    def test_no_semantic_learning_from_errors_or_unfinished_jobs(self):
        self.evaluation['calibration_verdict']='UNDERREACH';self.write()
        with self.assertRaisesRegex(EvidenceError,'参考校准'):
            learn(self.bench,self.folder.name)
        self.evaluation['calibration_verdict']='PASS'
        self.manifest['jobs'][0]['status']='timed_out';self.write()
        self.assertEqual(learn(self.bench,self.folder.name)['lessons'],[])
        self.assertEqual(list_lessons(self.store),[])

    def test_no_cross_case_or_changed_input_lesson_reuse(self):
        root=self.code();learn(self.bench,self.folder.name)
        args=dict(candidate=str(root),task='Maintain this source.',model='SYNTHETIC_ONLY',conditions=['learned_review'])
        with self.assertRaisesRegex(EvidenceError,'同一案例'):
            self.bench.prepare(args)
        with self.assertRaisesRegex(EvidenceError,'没有匹配'):
            self.bench.prepare(dict(args,learning_case_id='another-case'))
        with self.assertRaisesRegex(EvidenceError,'没有匹配'):
            self.bench.prepare(dict(args,task='Different maintenance task.',learning_case_id='synthetic'))
        (root/'main.js').write_text('async function run() { await fetch(); publish(); }\n')
        with self.assertRaisesRegex(EvidenceError,'没有匹配'):
            self.bench.prepare(dict(args,learning_case_id='synthetic'))

    def test_automatic_extraction_does_not_change_evaluation(self):
        expected=json.loads(json.dumps(self.evaluation))
        with patch('temporal_contract_analyzer.case_evaluation.evaluate',return_value=self.evaluation):
            self.assertEqual(self.bench.evaluate_manifest(self.manifest),expected)
        self.assertEqual(len(list_lessons(self.store)),1)
        with patch('temporal_contract_analyzer.case_evaluation.evaluate',return_value=self.evaluation), \
                patch('temporal_contract_analyzer.learning.learn',side_effect=EvidenceError('synthetic learning failure')):
            self.assertEqual(self.bench.evaluate_manifest(self.manifest),expected)
        self.assertTrue((self.folder/'learning-error.json').is_file())

    def test_malformed_optional_memory_cannot_hide_original_runs(self):
        root=self.code();learn(self.bench,self.folder.name)
        bad=self.store/'lessons/l-bad.json';bad.write_text('{broken json')
        view=self.bench.read(self.folder.name)
        self.assertEqual(view['status'],'completed')
        self.assertEqual(view['jobs'][0]['task_success'],'failed')
        self.assertIn('l-bad.json',view['learning_warning'])
        self.assertEqual(len(self.bench.list()['items']),1)
        args=dict(candidate=str(root),task='Maintain this source.',model='SYNTHETIC_ONLY')
        self.assertEqual(self.bench.prepare(dict(args,conditions=['none','review']))['status'],'prepared')
        with self.assertRaisesRegex(EvidenceError,'无法读取候选经验'):
            self.bench.prepare(dict(args,conditions=['learned_review'],learning_case_id='synthetic'))
        # start() can persist a decorated view; recovered memory must clear
        # the prior view's derived warning on the next read.
        archive.atomic_json(self.folder/'manifest.json',view)
        bad.unlink()
        recovered=self.bench.read(self.folder.name)
        self.assertEqual(len(recovered['failure_lessons']),1)
        self.assertNotIn('learning_warning',recovered)

    def test_unexpected_learning_error_is_isolated_after_completed_scoring(self):
        (self.folder/'evaluations/v-synthetic/j-001/oracle/stdout.json').write_text('[]')
        with patch('temporal_contract_analyzer.case_evaluation.evaluate',return_value=self.evaluation):
            self.assertEqual(self.bench.evaluate_manifest(self.manifest),self.evaluation)
        self.assertIn('AttributeError',(self.folder/'learning-error.json').read_text())
        self.assertEqual(self.bench.read(self.folder.name)['status'],'completed')

    def test_frozen_learning_context_and_ids_are_checked_before_launch(self):
        root=self.code();learn(self.bench,self.folder.name)
        run=self.bench.prepare(dict(candidate=str(root),task='Maintain this source.',model='SYNTHETIC_ONLY',
            conditions=['learned_review'],learning_case_id='synthetic'))
        self.bench.codex='/usr/bin/true';folder=self.bench.folder(run['id'])
        source=folder/'learned-context.json';raw=source.read_bytes();source.write_text('{}')
        with patch('temporal_contract_analyzer.workbench.subprocess.run') as launch:
            with self.assertRaisesRegex(EvidenceError,'冻结失败经验上下文'):
                self.bench.start(run['id'])
            launch.assert_not_called()
        source.write_bytes(raw)
        run['learning']['lesson_ids']=['l-changed']
        archive.atomic_json(folder/'manifest.json',run)
        with patch('temporal_contract_analyzer.workbench.subprocess.run') as launch:
            with self.assertRaisesRegex(EvidenceError,'冻结失败经验 ID'):
                self.bench.start(run['id'])
            launch.assert_not_called()
