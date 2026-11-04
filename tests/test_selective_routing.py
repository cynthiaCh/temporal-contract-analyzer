"""Candidate routing checks with synthetic execution, not model efficacy data."""
import copy
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_hypothesis_repair as fixtures
from temporal_contract_analyzer import archive
from temporal_contract_analyzer.core import ROOT, EvidenceError, analyze_sources
from temporal_contract_analyzer.routing import decide, prefilter

TASK='The preparation service is pending before ready. Keep checking preparation until ready.'
CODE='''export function preparation() {
 const state = { visible: true, loading: false };
 const check = () => checkPreparation().then(status => {
   state.loading = false;
   if (state.visible) publish(status);
 });
 return { start: check, close() { state.visible = false; } };
}
// kept=true
// fixed=false
// parent-patch
'''


def report(path='src/preparation.js',rules=('continuation-lifecycle-boundaries','continuation-guard-state-review')):
    from pathlib import PurePosixPath
    return dict(status='parsed',files=[dict(path=path,functions=[dict(name=PurePosixPath(path).stem,parent='<module>',line=1,end_line=5)],events=[
        dict(id='e1',path=path,line=2),dict(id='e2',path=path,line=5)])],
        findings=[dict(id='f'+str(i),rule=rule,path=path,scope='preparation',evidence=['e1','e2']) for i,rule in enumerate(rules)])


class RoutingDecisionTests(unittest.TestCase):
    def test_abstains_before_scan_for_unknown_and_multi_effect_composition(self):
        with patch('temporal_contract_analyzer.routing.parse_sources',side_effect=AssertionError('unnecessary parser')):
            for task in ['Optimize integer parsing.',
                         'Restore progress; preserve audit and retry, frames decode out of order.']:
                d=decide(task)
                self.assertEqual(d['condition'],'none');self.assertFalse(d['needs_scan'])
        self.assertEqual(decide(TASK)['reason'],'source-evidence-required')
        self.assertTrue(decide(TASK)['needs_scan'])

    def test_requires_matched_concrete_evidence_not_generic_finding_count(self):
        self.assertEqual(decide(TASK,report())['action'],'D')
        partial=report();partial['status']='partial'
        self.assertEqual(decide(TASK,partial)['action'],'A')
        broken=report();broken['findings'][0]['evidence']=['missing']
        self.assertEqual(decide(TASK,broken)['action'],'A')
        generic=report(rules=('effect-after-await',))
        self.assertEqual(decide(TASK,generic)['action'],'A')
        unrelated=report(path='src/analytics.js')
        self.assertEqual(decide(TASK,unrelated)['reason'],'no-task-source-alignment')

    def test_results_case_model_and_oracle_metadata_do_not_change_decision(self):
        a=report();b=copy.deepcopy(a)
        b.update(case_id='SECRET_CASE',model='SECRET_MODEL',task_success='passed',oracle={'verdict':'PASS'},feedback=['SECRET_CHECK'])
        self.assertEqual(decide(TASK,a),decide(TASK,b))

    def test_initial_state_requires_registration_evidence(self):
        task='Initial presence state is missing after opening; later updates work.'
        r=report(path='src/presence.js',rules=('connect-before-listen',))
        self.assertEqual(decide(task,r)['action'],'D')
        r['findings'][0]['rule']='continuation-guard-state-review'
        self.assertEqual(decide(task,r)['action'],'A')

    def test_requires_reachable_local_dependency_for_indirect_evidence(self):
        task='The initial presence state is missing.'
        r=report(path='src/notification.js',rules=('connect-before-listen',))
        r['files'].append(dict(path='src/presence.js',functions=[dict(name='presence',parent='<module>',line=1,end_line=5)],events=[]))
        sources={'src/presence.js':'import { connect } from "./notification.js";\nexport function presence(){\n connect();\n}\n',
                 'src/notification.js':'export function connect(){\n channel.start();\n let a=1;\n return a;\n}\n'}
        self.assertEqual(decide(task,r,sources)['action'],'D')
        sources['src/presence.js']='export function presence(){ return 1; }'
        self.assertEqual(decide(task,r,sources)['action'],'A')

    def test_same_file_protected_consumer_is_not_task_evidence(self):
        task='Initial presence state is missing after opening. Fix the presence panel while preserving workspace navigation. Do not change the metrics consumer.'
        sources={
            'src/presence-panel.js':'import { subscribeChannel } from "./subscription.js";\nimport { createPresenceChannel } from "./channel.js";\nexport function renderPresence(){ const channel=createPresenceChannel(); return subscribeChannel(channel); }\n',
            'src/channel.js':'export function createPresenceChannel(){ return {}; }\nexport function observeChannel(channel){\n channel.connect();\n channel.target.addEventListener("presence", receive);\n}\n',
            'src/subscription.js':'export function subscribeChannel(channel){\n channel.target.addEventListener("presence", receive);\n channel.connect();\n}\n'}
        r=analyze_sources(sources)
        self.assertTrue(any(f['rule']=='connect-before-listen' for f in r['findings']))
        self.assertEqual(decide(task,r,sources)['action'],'A')
        sources['src/subscription.js']=sources['src/subscription.js'].replace(' channel.target.addEventListener("presence", receive);\n channel.connect();',' channel.connect();\n channel.target.addEventListener("presence", receive);')
        r=analyze_sources(sources)
        self.assertEqual(decide(task,r,sources)['action'],'D')


class SelectiveIntegrationTests(unittest.TestCase):
    setUp=fixtures.HypothesisRepairTests.setUp

    def inputs(self,task):
        return dict(candidate=str(self.code),task=task,label='synthetic',case_record=self.parent['case'])

    def prepare(self,task):
        (self.code/'main.js').write_text(CODE)
        with patch('temporal_contract_analyzer.case_catalog.case_input',return_value=self.inputs(task)):
            return self.wb.prepare_selective_case(dict(case_id='synthetic',model='SYNTHETIC_ONLY',timeout=10))

    def test_a_fallback_is_exact_original_prompt_and_one_model_job(self):
        task='Refactor numeric parsing without changing behavior.'
        m=self.prepare(task);folder=self.wb.folder(m['id'])
        prompt=(folder/'jobs/j-001/prompt.md').read_text()
        expected=('Work only on the candidate-visible files in this workspace. '
                  'Do not inspect sibling experiment jobs, original repositories or report stores.\n\n'+task+'\n')
        self.assertEqual(prompt,expected);self.assertEqual(m['conditions'],['none'])
        self.assertEqual((folder/'jobs/j-001/report.md').read_text(),'')
        self.assertNotIn(m['routing']['policy'],prompt);self.assertEqual(len(m['jobs']),1)
        self.wb.start(m['id']);self.wb.thread.join(15)
        self.assertFalse(self.wb.thread.is_alive())
        self.assertEqual(self.wb.read(m['id'])['jobs'][0]['status'],'completed')

    def test_d_is_exact_frozen_layer_and_frozen_decision_is_checked(self):
        m=self.prepare(TASK);folder=self.wb.folder(m['id'])
        self.assertEqual(m['routing']['action'],'D')
        material=archive.layer_text(m['report_id'],'review',self.wb.store)
        self.assertEqual((folder/'jobs/j-001/report.md').read_text(),material)
        prompt=(folder/'jobs/j-001/prompt.md').read_text()
        self.assertTrue(prompt.endswith('\n<temporal-review-material>\n'+material+'\n</temporal-review-material>\n'))
        self.assertNotIn(m['routing']['policy'],prompt)
        (folder/'routing.json').write_text('{}')
        with self.assertRaisesRegex(EvidenceError,'门控决定'):self.wb.start(m['id'])

    def test_route_cli_is_read_only_and_rejects_user_condition_override(self):
        task=self.root/'task.md';task.write_text('Optimize integer parsing.')
        result=subprocess.run([sys.executable,'-m','temporal_contract_analyzer','reports','route',
            '--task-file',str(task),'--store',str(self.wb.store)],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        d=json.loads(result.stdout);self.assertEqual(d['action'],'A');self.assertFalse(d['needs_scan'])
        with self.assertRaisesRegex(EvidenceError,'own A/D'):
            self.wb.prepare_selective_case(dict(case_id='synthetic',conditions=['review']))

    def test_selective_cli_runs_exactly_one_synthetic_job(self):
        case=self.benchroot/'synthetic';metadata=json.loads((case/'case.json').read_text())
        metadata['prompt']='task.md';archive.atomic_json(case/'case.json',metadata)
        (case/'task.md').write_text('Refactor numeric parsing without changing behavior.')
        (case/'base/main.js').write_text(CODE)
        archive.atomic_json(self.benchroot/'experiments/temporal-diagnostics-v1/corpus.json',dict(cases=[
            dict(id='synthetic',manifest='synthetic/case.json',adapter='python',conditions=['latent-maintenance'])]))
        result=subprocess.run([sys.executable,'-B','-m','temporal_contract_analyzer','reports','selective',
            '--case-id','synthetic','--store',str(self.wb.store),'--timeout','10','--run'],
            cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        m=json.loads(result.stdout)
        self.assertEqual(m['conditions'],['none']);self.assertEqual(len(m['jobs']),1)
        self.assertEqual(m['jobs'][0]['status'],'completed')


if __name__=='__main__':unittest.main()
