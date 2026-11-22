"""Reserved test IDs, independent final scoring and no learning; synthetic models."""
import json,runpy,sys
from pathlib import Path
import unittest
from unittest.mock import patch
import test_tempoevo_v4 as fixtures
from temporal_contract_analyzer import experience_approval as approval
from temporal_contract_analyzer.tempoevo_v4 import read
from temporal_contract_analyzer.evaluation_split import assignment
from temporal_contract_analyzer.core import EvidenceError,canonical,sha

TRAIN='draft-autosave-handoff-precise-rule-vanilla-port-go'
TEST='draft-autosave-handoff-vue3-port-react'
class SplitTests(unittest.TestCase):
    setUp=fixtures.V4Tests.setUp
    prepare=fixtures.V4Tests.prepare

    def test_reserved_test_cannot_be_trained_or_online(self):
        with self.assertRaisesRegex(EvidenceError,'Reserved testing'):self.prepare(task_id=TEST)
        with self.assertRaises(EvidenceError):self.prepare(task_id=TEST,mode='testing',learning_policy='online',online_memory=str(self.root/'pool'))
        with self.assertRaises(EvidenceError):self.prepare(task_id=TRAIN,mode='testing')
        self.assertEqual(assignment(TEST)['role'],'testing')
        self.assertTrue(assignment(TEST)['independence']['historical_outcome_selected'])

    def test_exposed_training_replay_is_final_only_and_keeps_training_role(self):
        loop=self.prepare(task_id=TRAIN,mode='testing',condition='baseline',evaluation_purpose='training_replay',memory_snapshot=approval.freeze(self.store),gold_evaluator=dict(command=['synthetic-gold']))
        backend=fixtures.Backend(passes=2);state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'scored')
        self.assertEqual([s['kind'] for s in state['stages']],['action','gold'])
        protocol=read(loop.root/'protocol.json')
        self.assertEqual(protocol['evaluation_split']['role'],'training')
        self.assertFalse(protocol['held_out_eligible'])
        self.assertFalse((loop.root/'candidate-pool').exists())

    def test_real_reserved_id_is_scored_only_after_submission_without_learning(self):
        loop=self.prepare(task_id=TEST,mode='testing',memory_snapshot=approval.freeze(self.store),gold_evaluator=dict(command=['synthetic-gold']))
        class Backend(fixtures.Backend):
            def evaluate(inner,kind,payload,directory):
                if kind=='gold':
                    self.assertEqual(len([c for c in inner.calls if c[0]=='action']),1)
                    self.assertEqual(loop.state()['status'],'submitted')
                return super().evaluate(kind,payload,directory)
        b=Backend(passes=2);state=loop.run(b,execute=True)
        self.assertEqual(len(state['attempts']),1);self.assertEqual(state['status'],'scored');self.assertFalse(state['gold_result']['passed'])
        self.assertEqual(len([s for s in state['stages'] if s['kind']=='gold']),1)
        self.assertFalse((loop.root/'candidate-pool').exists());self.assertFalse((loop.root/'expert-summary-task.json').exists())
        self.assertFalse(read(loop.root/'protocol.json')['held_out_eligible'])
        self.assertEqual(read(loop.root/'protocol.json')['evaluation_split']['role'],'testing')
        self.assertNotIn('SECRET_GOLD',json.dumps(b.calls));self.assertEqual(approval.freeze(self.store)['entries'],[])

    def test_testing_preparation_has_no_extra_evaluation_or_reference_access(self):
        bench=self.root/'bench';bench.mkdir();manifest=bench/'case.json'
        manifest.write_text(json.dumps(dict(framework=dict(runtime='react18',version='18'),references=dict(bounded='FORBIDDEN_REFERENCE'),mutants=['FORBIDDEN_MUTANT'])))
        bank=dict(schema_version='experience-active-snapshot-v1',scope='research_only',entries=[]);bank['sha256']=sha(canonical(bank).encode())
        script=Path(__file__).resolve().parents[1]/'tools/tempoevo-docker/prepare_selected.py'
        with patch.object(sys,'argv',[str(script),'--root',str(self.root/'prepared'),'--start-rank','26','--limit','1','--mode','testing','--solver-image','unused','--grader-image','unused']),patch('temporal_contract_analyzer.case_catalog.bench_root',return_value=bench),patch('temporal_contract_analyzer.case_catalog.case_input',return_value=dict(candidate=str(self.source),task='Preserve accepted work.',case_record=dict(manifest='case.json'))),patch('temporal_contract_analyzer.experience_approval.freeze',return_value=bank),patch('temporal_contract_analyzer.tempoevo_backend.NativeV4Backend.evaluate') as ev,patch('temporal_contract_analyzer.tempoevo_v4.Trajectory.prepare') as prepared:
            runpy.run_path(str(script),run_name='__main__')
        ev.assert_not_called()
        cfg=prepared.call_args[0][0];self.assertEqual(cfg['mode'],'testing');self.assertIn('gold_evaluator',cfg)
        self.assertEqual(cfg['max_attempts'],1)
        self.assertNotIn('public_checks',cfg);self.assertFalse(cfg.get('required_visible_checks'))
        self.assertNotIn('visible_evaluator',cfg)
        self.assertEqual(Path(cfg['store']),script.parents[2]/'experience-memory/library')
        self.assertNotIn('training_evaluator',cfg);self.assertNotIn('training_feedback',cfg)
        self.assertFalse(list((self.root/'prepared').rglob('reference')))
        self.assertFalse(list((self.root/'prepared').rglob('VISIBLE_CHECKS.md')))
        progress=json.loads((self.root/'prepared/progress.json').read_text())
        self.assertEqual(progress[0]['controls'],[])

    def test_batch_rejects_gold_guided_testing_before_writing_or_launching(self):
        loop=self.prepare(mode='testing',memory_snapshot=approval.freeze(self.store),gold_evaluator=dict(command=['synthetic-gold']))
        protocol=read(loop.root/'protocol.json')
        protocol.update(acceptance_policy='oracle_pass_or_action_budget_exhausted',max_attempts=3)
        loop.save('protocol.json',protocol)
        progress=self.root/'progress.json'
        progress.write_text(json.dumps([dict(case_id=TEST,rank=26,root=str(self.root),status='prepared')]))
        # The batch launcher expects the trajectory under each case directory.
        trajectory=self.root/'trajectory';loop.root.rename(trajectory)
        before={str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        script=Path(__file__).resolve().parents[1]/'tools/tempoevo-docker/run_selected.py'
        with patch.object(sys,'argv',[str(script),'--root',str(self.root),'--execute']),patch('subprocess.run') as launch:
            with self.assertRaises(SystemExit) as error:runpy.run_path(str(script),run_name='__main__')
        self.assertEqual(error.exception.code,2);launch.assert_not_called()
        self.assertEqual(before,{str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
