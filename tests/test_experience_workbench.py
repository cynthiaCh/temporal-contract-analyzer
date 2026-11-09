"""Synthetic workflow verification, never live model evidence."""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import build_opener, ProxyHandler, Request

from temporal_contract_analyzer import archive, hub
from temporal_contract_analyzer.core import EvidenceError
from temporal_contract_analyzer.experience_workbench import ExperienceWorkbench, delta
from temporal_contract_analyzer.workbench import Workbench


def synthetic_bench(root):
    """Real evaluator protocol over explicitly synthetic source/effects."""
    entries = []
    for name in ('development', 'test'):
        case = root/'cases'/name
        for part in ('base', 'reference', 'oracle', 'prompts'):
            (case/part).mkdir(parents=True)
        (case/'base/main.py').write_text('accepted = True\n# '+name+'\n')
        (case/'reference/main.py').write_text('accepted = True\n# FIXED\n')
        (case/'prompts/task.md').write_text('Preserve accepted work and correct the synthetic ordering.\n')
        (case/'case.json').write_text(json.dumps(dict(id=name, title='Synthetic '+name,
            prompt='prompts/task.md', reference='reference', oracle=dict(probe='oracle/probe.py'))))
        (case/'oracle/probe.py').write_text('''import json, pathlib, sys
text=(pathlib.Path(sys.argv[1])/'main.py').read_text()
fixed='FIXED' in text
effects={'ordering': fixed or 'AUTO' in text, 'retirement': fixed, 'preserved': True}
missing=[k for k,v in effects.items() if not v]
passed=not missing
print(json.dumps({'case_id':pathlib.Path(__file__).parent.parent.name,
'verdict':'PASS' if passed else 'UNDERREACH','observed_effects':effects,
'missing_required_effects':missing,'observed_forbidden_effects':[],
'schedules':{k:{'assertions':[{'id':k,'actual':v,'expected':True,'passed':v}]} for k,v in effects.items()}}))
sys.exit(0 if passed else 1)
''')
        entries.append(dict(id=name, manifest='cases/'+name+'/case.json', adapter='python',
                            language='python', conditions=['latent-maintenance'], prior_exposure='synthetic'))
    index = root/'experiments/temporal-diagnostics-v1'
    index.mkdir(parents=True)
    (index/'corpus.json').write_text(json.dumps(dict(cases=entries)))


def synthetic_codex(path):
    path.write_text('#!'+sys.executable+'\n'+'''import json, os, pathlib, sys, time
args=sys.argv[1:]
if args==['--version']:
 print('SYNTHETIC_WORKFLOW_ONLY 0.0');sys.exit(0)
prompt=sys.stdin.read()
root=pathlib.Path(args[args.index('-C')+1]);answer=pathlib.Path(args[args.index('-o')+1])
if os.environ.get('TCA_SYNTHETIC_SLEEP') or pathlib.Path(__file__).with_name('sleep-next').exists():time.sleep(30)
if os.environ.get('TCA_SYNTHETIC_FAIL'):
 print('synthetic service error',file=sys.stderr);sys.exit(2)
if '--output-schema' in args:
 schema=json.loads(pathlib.Path(args[args.index('--output-schema')+1]).read_text())
 if 'contract' in schema['properties']:
  result={'taxonomy_version':'temporal-obligation-taxonomy-7-v1','contract':'Preserve accepted work.',
  'obligation_labels':[{'code':'I','statement':'Bind the entry snapshot.',
    'evidence':[{'file':'main.py','line':1,'quote':'accepted = True'}]}],
  'facts':[{'predicate':'entry_snapshot','state':'known',
    'evidence':[{'file':'main.py','line':1,'quote':'accepted = True'}]}],'unknowns':[]}
 else:
  result={'requires':['entry_snapshot'],'excludes':[], 'rules':[{
   'body':'Invalidate logical acceptance before synchronous callbacks return a cleanup handle.',
   'evidence_ids':['AUTO-1','AUTO-2'],'preservation':'Retain audit for work accepted before retirement.',
   'verification':'Deliver a new event during synchronous start after retirement.', 'causal_status':'hypothesis'}]}
 answer.write_text(json.dumps(result))
else:
 text='AUTO' if '冻结经验正文' not in prompt or os.environ.get('TCA_SYNTHETIC_NO_GAIN') else 'FIXED'
 root.joinpath('main.py').write_text('accepted = True\\n# '+text+'\\n')
 answer.write_text('SYNTHETIC_WORKFLOW_ONLY')
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':11,'output_tokens':3}}),flush=True)
''')
    path.chmod(0o755)


class ExperienceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        synthetic_bench(self.root/'bench')
        self.fake = self.root/'fake-codex'
        synthetic_codex(self.fake)
        env = patch.dict(os.environ, {'TCA_BENCH_ROOT':str(self.root/'bench'),
                        'TCA_CONFIG':str(self.root/'config.json')})
        env.start()
        self.addCleanup(env.stop)
        self.runner = Workbench(self.root/'reports', codex=str(self.fake))
        self.addCleanup(self.runner.close)
        self.workflow = ExperienceWorkbench(self.runner)

    def create(self, **extra):
        return self.workflow.create(dict(case_id='development', model='SYNTHETIC', timeout=10,
                                         source_relationship='Synthetic exposed fixtures only.', **extra))

    def action(self, item, action, **data):
        result = self.workflow.action(item['id'], action, data)
        thread = self.runner.thread
        if thread and thread is not threading.current_thread():
            thread.join(15)
            self.assertFalse(thread.is_alive())
        return self.workflow.read(result['id'])

    def analysis(self, item):
        item = self.action(item, 'analyze')
        self.assertEqual(item['status'], 'analysis_review', item.get('error'))
        return self.action(item, 'review-analysis', approved=True, reason='Checked against visible task and exact source.')

    def develop(self):
        item = self.analysis(self.create())
        item = self.action(item, 'train')
        self.assertEqual(item['status'], 'candidate_review', item.get('error'))
        return item

    def freeze(self):
        item = self.develop()
        item = self.action(item, 'review-candidate', approved=True, reason='All rules, preservation and references checked.')
        item = self.action(item, 'revalidate')
        self.assertEqual(item['status'], 'ready_to_freeze', item.get('error'))
        return self.action(item, 'freeze')

    def test_spine_http_persists_visible_snapshot_without_launching(self):
        server = hub.ReportServer(self.runner.store)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            opener = build_opener(ProxyHandler({}))
            request = Request(server.url+'/api/experience', data=json.dumps(dict(case_id='development',
                model='SYNTHETIC', source_relationship='Synthetic')).encode(),
                headers={'Content-Type':'application/json', 'X-TCA-Request':'local'})
            with opener.open(request) as response:
                self.assertEqual(response.status, 201)
                item = json.load(response)
            with opener.open(server.url+'/api/experience/'+item['id']) as response:
                self.assertEqual(json.load(response), item)
            self.assertEqual(item['jobs'], [])
            self.assertEqual(item['status'], 'prepared')
            with opener.open(server.url+'/experience') as response:
                self.assertIn('七类', response.read().decode())
            with self.assertRaises(HTTPError) as error:
                opener.open(Request(server.url+'/api/experience', data=b'{}', headers={'Content-Type':'application/json'}))
            self.assertEqual(error.exception.code, 403)
        finally:
            server.shutdown();server.server_close();thread.join(3)

    def test_development_review_freeze_and_full_test(self):
        item = self.freeze()
        self.assertEqual(item['status'], 'frozen')
        self.assertEqual([j['role'] for j in item['jobs']],
                         ['analysis','AUTO-1','AUTO-2','reflection','REVALIDATE-1','REVALIDATE-2'])
        self.assertTrue(item['admission']['eligible'])
        self.assertEqual(item['comparisons'][0]['gained'], ['retirement'])
        self.assertEqual(item['comparisons'][0]['lost'], [])
        self.assertEqual(len(item['reviews']), 2)
        test = self.workflow.create(dict(
            kind='test', case_id='test', parent_id=item['id'], model='SYNTHETIC', timeout=10,
            source_relationship='Same synthetic source; no independent generalization.'))
        test = self.analysis(test)
        test = self.action(test, 'test')
        self.assertEqual(test['status'], 'completed', test.get('error'))
        self.assertEqual([j['role'] for j in test['jobs']], ['analysis','B1','A1','A2','B2'])
        self.assertEqual(test['route']['condition'], 'ROUTED')
        inputs = json.loads(self.workflow.artifact(test['id'], 'test-inputs.json')['text'])
        self.assertTrue(inputs['B'].startswith(inputs['A']))
        self.assertTrue(inputs['B'].endswith(item['entry']['text']))
        analysis_prompt = self.workflow.artifact(test['id'], 'jobs/j-001/prompt.md')['text']
        for forbidden in ('AUTO-1', 'reflection-evidence', 'observed_effects', item['entry']['text'], item['id']):
            self.assertNotIn(forbidden, analysis_prompt)
        for job in test['jobs'][1:]:
            prompt = self.workflow.artifact(test['id'], job['artifact_root']+'/prompt.md')['text']
            self.assertNotIn('missing_required_effects', prompt)
            self.assertEqual(job['original_delta']['lost'], [])
            self.assertEqual(job['usage']['input_tokens'], 11)
        self.assertFalse((self.runner.store/'lessons').exists())
        self.workflow.verify(test)
        with self.assertRaises(EvidenceError):self.action(test, 'test')

    def test_no_improvement_stops_before_freeze_or_test(self):
        with patch.dict(os.environ, {'TCA_SYNTHETIC_NO_GAIN':'1'}):
            item = self.develop()
            item = self.action(item, 'review-candidate', approved=True, reason='Synthetic content reviewed.')
            item = self.action(item, 'revalidate')
        self.assertEqual(item['status'], 'no_improvement')
        self.assertFalse(item['admission']['eligible'])
        with self.assertRaises(EvidenceError):self.action(item, 'freeze')
        with self.assertRaises(EvidenceError):self.workflow.create(dict(kind='test', case_id='test',
            parent_id=item['id'], model='SYNTHETIC', source_relationship='Synthetic'))
        self.assertEqual(len(item['jobs']), 6)

    def test_review_gates_rejection_and_tamper_prevent_execution(self):
        item = self.action(self.create(), 'analyze')
        with self.assertRaises(EvidenceError):self.action(item, 'train')
        with self.assertRaises(EvidenceError):self.action(item, 'review-analysis', approved=True, reason='')
        rejected = self.action(item, 'review-analysis', approved=False, reason='Unsupported policy.')
        self.assertEqual(rejected['status'], 'rejected')
        with self.assertRaises(EvidenceError):self.action(rejected, 'train')
        item = self.analysis(self.create())
        (self.workflow.folder(item['id'])/'input/main.py').write_text('changed')
        with self.assertRaisesRegex(EvidenceError, '源码'):self.action(item, 'train')
        self.assertEqual(len(self.workflow.read(item['id'])['jobs']), 1)

    def test_incomplete_session_preserves_error_and_stops_no_retry(self):
        item = self.analysis(self.create())
        with patch.dict(os.environ, {'TCA_SYNTHETIC_FAIL':'1'}):
            item = self.action(item, 'train')
        self.assertEqual(item['status'], 'stopped')
        self.assertEqual(len(item['jobs']), 2)
        failed = item['jobs'][-1]
        self.assertEqual(failed['status'], 'failed')
        self.assertNotIn('outcome', failed)
        self.assertIn('synthetic service error', self.workflow.artifact(item['id'], failed['artifact_root']+'/stderr.log')['text'])
        with self.assertRaises(EvidenceError):self.action(item, 'train')

    def test_same_case_not_test_and_frozen_entry_tamper_rejected(self):
        item = self.freeze()
        with self.assertRaises(EvidenceError):self.workflow.create(dict(kind='test', case_id='development',
            parent_id=item['id'], model='SYNTHETIC', source_relationship='Same case'))
        (self.workflow.folder(item['id'])/'frozen-entry.json').write_text('{}')
        with self.assertRaises(EvidenceError):self.workflow.create(dict(kind='test', case_id='test',
            parent_id=item['id'], model='SYNTHETIC', source_relationship='Same cluster'))

    def test_unknowns_not_regressions_and_forbidden_false_is_success(self):
        before = dict(observed_effects={'a':True, 'b':False}, missing_required_effects=[], observed_forbidden_effects=[])
        after = dict(before, observed_effects={'a':None, 'b':False})
        self.assertEqual(delta(before, after), dict(gained=[],lost=[],retained=['b'],unknown=['a']))

    def test_unknown_premise_falls_back_to_identical_prompts(self):
        parent = self.freeze()
        item = self.workflow.create(dict(kind='test', case_id='test', parent_id=parent['id'],
            model='SYNTHETIC', timeout=10, source_relationship='Synthetic exposed same source.'))
        item = self.action(item, 'analyze')
        analysis = item['analysis']
        analysis['facts'][0].update(state='unknown', evidence=[])
        item = self.action(item, 'review-analysis', approved=True, reason='Mechanism cannot be established.', analysis=analysis)
        item = self.action(item, 'test')
        self.assertEqual(item['status'], 'completed', item.get('error'))
        self.assertEqual(item['route']['condition'], 'AUTO')
        self.assertTrue(item['prompts_identical'])
        self.assertEqual(item['test_summary']['A'], item['test_summary']['B'])
        self.assertEqual(len([j for j in item['jobs'] if j['role']=='reflection']), 0)

    def test_cancel_and_recovery_never_resume_or_start_other_slots(self):
        item = self.create()
        with patch.dict(os.environ, {'TCA_SYNTHETIC_SLEEP':'1'}):
            self.workflow.action(item['id'], 'analyze', {})
            deadline = time.monotonic()+5
            while not list(self.workflow.folder(item['id']).glob('jobs/*/execution/jobs/*/events.jsonl')):
                self.assertLess(time.monotonic(), deadline)
                time.sleep(.02)
            live = self.workflow.read(item['id'])['jobs'][0]
            self.assertEqual(live['status'], 'running')
            self.assertIn('started_at', live)
            with self.assertRaises(EvidenceError):self.workflow.action(item['id'], 'analyze', {})
            with self.assertRaises(EvidenceError):self.runner.execution_lock()
            self.runner.cancel(item['id'])
            self.runner.thread.join(6)
        stopped = self.workflow.read(item['id'])
        self.assertEqual(stopped['status'], 'cancelled')
        self.assertEqual(len(stopped['jobs']), 1)
        with self.assertRaises(EvidenceError):self.action(stopped, 'analyze')
        orphan = self.create()
        orphan['status'] = 'training'
        self.workflow.save(orphan)
        self.workflow.recover()
        self.assertEqual(self.workflow.read(orphan['id'])['status'], 'interrupted')
        self.assertEqual(self.workflow.read(orphan['id'])['jobs'], [])

    def test_rejected_candidate_never_starts_revalidation(self):
        item = self.develop()
        item = self.action(item, 'review-candidate', approved=False, reason='Rule extends unsupported policy.')
        self.assertEqual(item['status'], 'rejected')
        with self.assertRaises(EvidenceError):self.action(item, 'revalidate')
        self.assertEqual(len(item['jobs']), 4)

    def test_scoring_version_drift_blocks_before_paid_session(self):
        item = self.analysis(self.create())
        (self.root/'bench/cases/development/oracle/probe.py').write_text('changed')
        with self.assertRaisesRegex(EvidenceError, '评分版本'):self.action(item, 'train')
        self.assertEqual(len(self.workflow.read(item['id'])['jobs']), 1)
        stopped = self.workflow.read(item['id'])
        self.assertEqual(stopped['status'], 'stopped')
        self.assertEqual(stopped['stopped_from'], 'analysis_approved')


if __name__ == '__main__':
    unittest.main()
