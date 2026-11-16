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
        self.assertEqual(result['candidate'],str(self.case/'base'))
        self.assertEqual(result['case_record']['authorization'],'ungranted')
        self.assertNotIn('DO NOT LEAK',json.dumps(result))

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
