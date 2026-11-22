import json
from pathlib import Path
import tempfile
import unittest
from temporal_contract_analyzer.core import EvidenceError
from temporal_contract_analyzer.swe_tempoc_inputs import case_input


class SweTempocInputTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'benchmark').mkdir(); self.case = self.root/'cases/demo'; self.case.mkdir(parents=True)
        (self.case/'base').mkdir(); (self.case/'base/main.js').write_text('export const x = 1;')
        (self.case/'task.md').write_text('Public maintenance task')
        (self.case/'contract.md').write_text('DO NOT LEAK CONTRACT')
        self.manifest = dict(id='demo', diagnostic_tasks=dict(maintenance=dict(core_prompt='task.md',contract_suffix='contract.md')))
        (self.case/'case.json').write_text(json.dumps(self.manifest))
        self.roster('cases/demo/case.json')

    def roster(self, path):
        (self.root/'benchmark/swe-tempoc.json').write_text(json.dumps(dict(cases=[dict(case_id='demo',manifest=path)])))

    def test_only_public_latent_task_and_base(self):
        result = case_input('demo',self.root)
        self.assertEqual(result['task'],'Public maintenance task')
        self.assertEqual(result['candidate'],str((self.case/'base').resolve()))
        self.assertEqual(result['case_record']['authorization'],'ungranted')
        self.assertNotIn('DO NOT LEAK',json.dumps(result))

    def test_python_pilot_uses_original_public_prompt_without_contract(self):
        self.manifest=dict(id='demo',schema_version='python-pilot-0.1',prompt='task.md',reference='reference/bounded')
        (self.case/'case.json').write_text(json.dumps(self.manifest))
        result=case_input('demo',self.root)
        self.assertEqual(result['task'],'Public maintenance task')
        self.assertNotIn('DO NOT LEAK',json.dumps(result))

    def test_derived_projection_keeps_product_and_original_public_tests(self):
        from temporal_contract_analyzer.swe_tempoc_inputs import project_public_base
        base=self.case/'base'
        contents={'rxjs/src/internal/AsyncSubject.ts':'export class AsyncSubject {}',
                  'src/workflow.go':'package main',
                  'rxjs/spec/Subject-spec.ts':'original public test',
                  'rxjs/spec/other-spec.ts':'omitted original fixture',
                  'rxjs/package-lock.json':'large immutable dependency lock'}
        for name,text in contents.items():
            file=base/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_text(text)
        destination=self.root/'projection';_,meta=project_public_base(base,destination)
        self.assertEqual((destination/'src/workflow.go').read_text(),'package main')
        self.assertEqual((destination/'rxjs/src/internal/AsyncSubject.ts').read_text(),contents['rxjs/src/internal/AsyncSubject.ts'])
        self.assertIn('rxjs/spec/Subject-spec.ts',meta['paths'])
        self.assertFalse((destination/'rxjs/spec/other-spec.ts').exists())
        self.assertFalse((destination/'rxjs/package-lock.json').exists())
        self.assertIn('trusted scorer',meta['scope'])

    def test_rejects_unknown_and_escaping_manifest(self):
        with self.assertRaises(EvidenceError):case_input('unknown',self.root)
        self.roster('../outside.json')
        with self.assertRaises(EvidenceError):case_input('demo',self.root)

    def test_rejects_upstream_instead_of_silently_using_wrong_source(self):
        (self.case/'task.json').write_text(json.dumps(self.manifest)); self.roster('cases/demo/task.json')
        with self.assertRaisesRegex(EvidenceError,'source-archive adapter'):case_input('demo',self.root)

    def test_rejects_mismatched_identity_and_symlink_prompt(self):
        self.manifest['id']='wrong'; (self.case/'case.json').write_text(json.dumps(self.manifest))
        with self.assertRaises(EvidenceError):case_input('demo',self.root)
        self.manifest['id']='demo'; (self.case/'case.json').write_text(json.dumps(self.manifest))
        (self.case/'task.md').unlink(); (self.case/'task.md').symlink_to(self.case/'contract.md')
        with self.assertRaises(EvidenceError):case_input('demo',self.root)
