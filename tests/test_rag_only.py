"""Feedback-free retrieval and real fake-CLI/scorer integration; no model calls."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_hypothesis_repair as fixtures
from temporal_contract_analyzer import archive
from temporal_contract_analyzer.core import EvidenceError
from temporal_contract_analyzer.rag import build_rag_context


class RagOnlyTests(unittest.TestCase):
    setUp=fixtures.HypothesisRepairTests.setUp

    def test_task_retrieval_includes_public_docs_and_import_definitions(self):
        root=self.root/'retrieval';root.mkdir()
        files={'main.js':b'import { policy } from "./shared.js";\nexport function run() { publish(policy); }\n',
               'shared.js':b'export const policy = { enabled: true };\n',
               'README.md':b'Publish policy documentation for the public task.\n'}
        for name,data in files.items():(root/name).write_bytes(data)
        report=archive.scan_path(root,self.wb.store)['archive']
        packet,text=build_rag_context(report['report_id'],'publish policy',files,self.wb.store,top_k=2)
        self.assertEqual(packet['query'],'publish policy')
        self.assertIn('README.md',{s['file'] for s in packet['snippets']})
        self.assertIn('main.js',{s['file'] for s in packet['snippets']})
        self.assertIn('shared.js',{s['file'] for s in packet['snippets']})
        self.assertIn('import-definition',json.dumps(packet['snippets']))
        self.assertLessEqual(packet['code_chars'],12000)
        p,_=build_rag_context(report['report_id'],'publish policy',files,self.wb.store,max_chars=1,seed_chars=1)
        self.assertFalse(p['snippets']);self.assertTrue(p['omitted'])
        empty,_=build_rag_context(report['report_id'],'zzznomatch',files,self.wb.store)
        self.assertFalse(empty['selected']);self.assertFalse(empty['snippets'])

    def test_single_rag_job_has_no_feedback_or_d_and_retains_regression_evaluation(self):
        original=archive.layer_text
        calls=[]
        def layer(report,condition,store):
            calls.append(condition)
            self.assertNotEqual(condition,'review')
            return original(report,condition,store)
        with patch('temporal_contract_analyzer.repair.hypothesis_material',side_effect=AssertionError('must not use hypotheses')), \
                patch('temporal_contract_analyzer.archive.layer_text',side_effect=layer):
            run=self.wb.prepare_rag(self.parent['id'],'j-001')
        self.assertEqual(run['conditions'],['rag_only']);self.assertEqual(len(run['jobs']),1)
        folder=self.wb.folder(run['id']);prompt=(folder/'jobs/j-001/prompt.md').read_text()
        for forbidden in ('decode-after-close','PRIVATE_EXPECTED_PAYLOAD','Failure-specific repair hypotheses','Candidate cause:','Selected candidate-source locations','<temporal-review-material>'):
            self.assertNotIn(forbidden,prompt)
        self.assertIn('<retrieved-candidate-context>',prompt)
        self.assertFalse((folder/'hypotheses.json').exists())
        packet=json.loads((folder/'rag-context.json').read_text())
        self.assertEqual(packet['query'],self.parent['task'])
        self.assertNotIn('checks',packet)
        self.wb.start(run['id']);self.wb.thread.join(15)
        self.assertFalse(self.wb.thread.is_alive())
        result=self.wb.read(run['id'])['jobs'][0]
        self.assertEqual(result['status'],'completed')
        self.assertEqual(result['evaluation']['regression']['status'],'regressed')
        self.assertFalse(result['evaluation']['regression']['eligible'])

    def test_reject_modified_retrieval_packet_and_condition(self):
        run=self.wb.prepare_rag(self.parent['id'],'j-001');folder=self.wb.folder(run['id'])
        packet=folder/'rag-context.json';raw=packet.read_bytes();packet.write_text('{}')
        with self.assertRaisesRegex(EvidenceError,'冻结修复反馈'):self.wb.start(run['id'])
        packet.write_bytes(raw)
        run['jobs'][0]['condition']='review';archive.atomic_json(folder/'manifest.json',run)
        with self.assertRaisesRegex(EvidenceError,'对照条件改变'):self.wb.start(run['id'])


if __name__=='__main__':unittest.main()
