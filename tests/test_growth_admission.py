"""Admission boundaries for the fresh 100-case experiment, with no providers."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

from temporal_contract_analyzer.frozen_benchmark import FrozenBenchmark, gold_evaluator
from temporal_contract_analyzer.swe_tempoc_inputs import project_public_files
from temporal_contract_analyzer.balance_budget import BalanceBudget


class FrozenInputsTests(unittest.TestCase):
    def fixture(self, cid, manifest, files):
        frozen = object.__new__(FrozenBenchmark)
        frozen.receipt = dict(case_manifests={cid:'cases/example/case.json'})
        frozen.files = {'cases/example/case.json':json.dumps(manifest).encode(),
                        **{'cases/example/'+k:v for k,v in files.items()}}
        return frozen

    def test_python_task_and_reference_use_own_schema(self):
        manifest=dict(schema_version='python-pilot-0.1',prompt='task.md',reference='reference',mutants=['negative'])
        frozen=self.fixture('python',manifest,{'task.md':b'Public task','base/main.py':b'original',
            'reference/main.py':b'correct','negative/main.py':b'negative','oracle/probe.py':b'secret'})
        self.assertEqual(frozen.task('python'),'Public task')
        self.assertEqual(frozen.candidate_files('python','reference')[0],{'main.py':b'correct'})
        self.assertNotIn(b'secret',frozen.candidate_files('python')[0].values())
        ev=gold_evaluator('/repo','sha256:x','/case.json',manifest,{})
        self.assertIn('/repo/tools/tempoevo-docker/python_gold.py',ev['inputs'])

    def test_rxjs_projection_keeps_upstream_target_and_original_identity(self):
        cid='rxjs-asyncsubject-clear-latent-maintenance-port-go'
        manifest=dict(references=dict(bounded='reference'),mutants=['negative'])
        base={'rxjs/src/internal/AsyncSubject.ts':b'original','src/workflow.go':b'product',
              'rxjs/spec/subjects/AsyncSubject-spec.ts':b'public test','rxjs/unneeded.txt':b'omitted'}
        frozen=self.fixture(cid,manifest,{**{'base/'+k:v for k,v in base.items()},
            'reference/rxjs/src/internal/AsyncSubject.ts':b'fixed','oracle/probe.cjs':b'secret'})
        original,proof=frozen.candidate_files(cid,project=True)
        reference,reference_proof=frozen.candidate_files(cid,'reference',project=True)
        self.assertEqual((original,proof),project_public_files(base))
        self.assertEqual(proof,reference_proof)
        self.assertEqual(reference['rxjs/src/internal/AsyncSubject.ts'],b'fixed')
        self.assertNotIn('rxjs/unneeded.txt',original)
        self.assertNotIn(b'secret',original.values())

    def test_unknown_behavior_family_is_not_autosave(self):
        frozen=self.fixture('download-example',dict(framework=dict(runtime='vue3',version='3')), {})
        with self.assertRaisesRegex(ValueError,'No legacy'):frozen.public_config('download-example')

    def test_grader_selection_rejects_aliases_duplicates_and_unknown_ids(self):
        source=Path(__file__).resolve().parents[1]/'tools/tempoevo-docker/prepare_grader_build.py'
        spec=importlib.util.spec_from_file_location('growth_grader_builder',source)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'selection.csv'
            path.write_text('case_id,manifest\na,cases/a.json\nb,cases/b.json\n')
            self.assertEqual(module.selection_ids(path,{'a':'cases/a.json','b':'cases/b.json'}),['a','b'])
            for body in ('a,cases/a.json\na,cases/a.json','a,wrong.json','unknown,cases/a.json'):
                path.write_text('case_id,manifest\n'+body+'\n')
                with self.assertRaises(ValueError):module.selection_ids(path,{'a':'cases/a.json'})


@unittest.skipIf(os.name=='nt','Linux accounting locks')
class BalancePolicyTests(unittest.TestCase):
    def test_explicit_balance_only_policy_has_no_legacy_250_cap(self):
        from tests.test_balance_budget import balance,usage
        with tempfile.TemporaryDirectory() as temp:
            amount=['400']
            guard=BalanceBudget(Path(temp)/'ledger.json',authorized_total_cny=None,
                max_inflight_stages=4,fetcher=lambda:balance(amount[0]))
            self.assertIsNone(guard.initialize()['allocated_new_cny'])
            self.assertTrue(guard.before_stage('one')['allowed'])
            amount[0]='100';guard.observe(usage(),'one')
            self.assertEqual(guard.summary()['observed_decrease_cny'],'300')
            self.assertTrue(guard.before_stage('two')['allowed'])

    def test_missing_request_ledger_cannot_restart_initialized_meter(self):
        import sys
        runtime=Path(__file__).resolve().parents[1]/'temporal_contract_analyzer/_session_runtime'
        sys.path.insert(0,str(runtime))
        from request_guard import account
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'config.json').write_text(json.dumps(dict(global_cap=2,calls={'stage':dict(cap=2,mode='maintenance')})))
            account(dict(hook_event_name='PreModelRequest'),root,'stage',False)
            line=json.loads((root/'events.jsonl').read_text())
            self.assertTrue(line['request_id'].endswith(':stage:1'))
            self.assertEqual(len(line['request_id'].split(':')[0]),64)
            (root/'ledger.json').unlink()
            with self.assertRaisesRegex(ValueError,'missing after initialization'):
                account(dict(hook_event_name='PreModelRequest'),root,'stage',False)


if __name__=='__main__':unittest.main()
