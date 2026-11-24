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
from temporal_contract_analyzer.mcp_server import Session


class ReportMCPTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root/'project'
        self.project.mkdir()
        (self.project/'Demo.vue').write_text('<script setup>async function load(){await fetch(); store.save();}</script>')
        self.store = self.root/'reports'
        env = patch.dict(os.environ, {'TCA_CONFIG':str(self.root/'config.json')})
        env.start()
        self.addCleanup(env.stop)

    def ready(self, **kwargs):
        session = Session(self.store, **kwargs)
        self.assertIn('result', session.handle(dict(jsonrpc='2.0',id=1,method='initialize',params=dict(protocolVersion='2025-06-18',clientInfo={'name':'test-client'}))))
        session.handle(dict(jsonrpc='2.0',method='notifications/initialized'))
        return session

    def test_agent_scan_returns_shared_report_id_and_paginated_exact_material(self):
        session = self.ready()
        meta = session.call('scan_project', {'path':str(self.project),'task_id':'agent-task'})
        self.assertEqual(meta['origin'], 'codex')
        self.assertEqual(archive.list_reports(self.store)['items'][0]['report_id'],meta['report_id'])
        first = session.call('read_report', {'report_id':meta['report_id'],'limit':100})
        self.assertEqual(first['next_offset'], 100)
        self.assertEqual(archive.records('deliveries',meta['report_id'],self.store)[0]['state'],'prepared_for_tool_response')
        session.written()
        second = session.call('read_report', {'report_id':meta['report_id'],'offset':100,'limit':20000})
        self.assertEqual(first['text']+second['text'],archive.layer_text(meta['report_id'],'full',self.store))
        self.assertTrue(any(r['state']=='transport_written' for r in archive.records('deliveries',meta['report_id'],self.store)))

    def test_research_binding_exposes_only_assigned_layer(self):
        meta = archive.scan_path(self.project,self.store)['archive']
        session = self.ready(report_id=meta['report_id'],layer='facts')
        self.assertEqual([d['name'] for d in session.definitions()],['read_report'])
        page = session.call('read_report',{})
        self.assertEqual(page['text'],archive.layer_text(meta['report_id'],'facts',self.store))
        self.assertNotIn('review_question',page['text'])
        for name,args in [('list_reports',{}),('scan_project',{'path':str(self.project)}),('read_source',{'report_id':meta['report_id'],'path':'Demo.vue'}),('read_report',{'layer':'review'}),('read_report',{'report_id':meta['report_id']})]:
            with self.subTest(name=name,args=args), self.assertRaises(EvidenceError):
                session.call(name,args)

    def test_initialization_errors_and_unknown_tools_are_protocol_results(self):
        session = Session(self.store)
        self.assertIn('error',session.handle(dict(jsonrpc='2.0',id=1,method='tools/list')))
        session = self.ready()
        self.assertEqual(session.handle(dict(jsonrpc='2.0',id=2,method='ping'))['result'],{})
        error = session.handle(dict(jsonrpc='2.0',id=3,method='tools/call',params={'name':'shell','arguments':{}}))
        self.assertTrue(error['result']['isError'])
        self.assertEqual(session.handle([])['error']['code'],-32600)

    def test_failed_scan_is_archived_without_claiming_a_successful_analysis(self):
        session = self.ready()
        meta = session.call('scan_project',{'path':str(self.root/'missing')})
        self.assertEqual(meta['status'],'failed')
        self.assertIn('Analysis failed',session.call('read_report',{'report_id':meta['report_id']})['text'])

    def test_none_condition_discloses_no_case_evidence(self):
        meta = archive.scan_path(self.project,self.store)['archive']
        session = self.ready(report_id=meta['report_id'],layer='none')
        result = session.call('read_report',{})
        self.assertEqual(result['text'],'')
        self.assertEqual(result['total_characters'],0)
        self.assertIsNone(result['next_offset'])

    def test_stdio_has_only_jsonrpc_and_runs_independently_of_cwd(self):
        messages = [dict(jsonrpc='2.0',id=1,method='initialize',params={'protocolVersion':'2025-06-18'}),
                    dict(jsonrpc='2.0',method='notifications/initialized'),
                    dict(jsonrpc='2.0',id=2,method='tools/list'),
                    dict(jsonrpc='2.0',id=3,method='tools/call',params={'name':'scan_project','arguments':{'path':str(self.project)}})]
        process = subprocess.run([sys.executable,'-I','-S','-B',str(ROOT/'temporal_contract_analyzer/hub_entry.py'),
                                  'reports','mcp','--store',str(self.store)],input='\n'.join(json.dumps(m) for m in messages)+'\n',
                                  text=True,capture_output=True,cwd=str(self.root),timeout=15)
        self.assertEqual(process.returncode,0,process.stderr)
        lines = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual([r['id'] for r in lines],[1,2,3])
        self.assertEqual({t['name'] for t in lines[1]['result']['tools']},
                         {'scan_project','list_reports','read_report','read_source','read_context','compare_reports',
                          'recall_experience','remember_correction','manage_experience'})
        self.assertFalse(lines[2]['result']['isError'])
        meta = json.loads(lines[2]['result']['content'][0]['text'])
        self.assertTrue(archive.verify(meta['report_id'],self.store)['verified'])


if __name__ == '__main__':
    unittest.main()
