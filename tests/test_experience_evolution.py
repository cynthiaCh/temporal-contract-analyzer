"""Synthetic lifecycle tests. No paid model, actual expert or real-case result."""
from copy import deepcopy
import difflib
from contextlib import redirect_stdout,redirect_stderr
from io import StringIO
import json
import os
from pathlib import Path
import tempfile
import threading
from urllib.request import build_opener, ProxyHandler, Request
import unittest
from unittest.mock import patch

import evolution_fixtures as fixtures
from temporal_contract_analyzer import experience_memory as memory, experience_approval as approval
from temporal_contract_analyzer import experience_routing as routing, taxonomy
from temporal_contract_analyzer.experience_evolution import Evolution, load
from temporal_contract_analyzer.core import EvidenceError, sha
from temporal_contract_analyzer.evolution_backend import NativeBackend


class SyntheticBackend:
    kind='synthetic_fixture_not_model_or_effectiveness_evidence'

    def __init__(self,fail=None,no_gain=False,invalid_rule=False):
        self.calls=[];self.scores=[];self.fail=fail;self.no_gain=no_gain;self.invalid_rule=invalid_rule

    def preflight(self,protocol):pass

    def execute(self,protocol,role,prompt,schema,directory):
        self.calls.append((directory.name,role,prompt))
        if directory.name==self.fail:
            (directory/'partial.txt').write_text('SYNTHETIC_STREAM_INTERRUPTION_PARTIAL')
            return dict(completed=False,infrastructure_valid=False,usage=None,output=None,
                        original_error='synthetic stream failure',partial='partial response')
        if role=='reflect':
            rules=[dict(category=key,body=body,support=['TASK'],causal_status='hypothesis') for key,body in [
                ('applicability','Use when accepted work has an entry snapshot.'),
                ('event_relation','Retire acceptance before invoking synchronous callbacks.'),
                ('preservation','Retain effects already accepted before retirement.'),
                ('exclusion','Do not discard legitimate background results.'),
                ('verification','Check retirement while startup has not returned.')]]
            if self.invalid_rule:rules[0]['support']=['NOT_IN_LEDGER']
            output=dict(requires=['entry_snapshot'],excludes=[],rules=rules,unresolved=['Synthetic fixture; cause unverified.'])
            return dict(completed=True,infrastructure_valid=True,output=output,
                        usage=dict(requests_started=1,total_usage=None,usage_unknown_requests=1),patch='')
        final=directory/'synthetic-final';final.mkdir()
        for name,text in protocol['visible']['sources'].items():
            path=final/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        fixed='Frozen experience guidance' in prompt and not self.no_gain
        path=final/'main.py';before=path.read_text();after=before+('\n# SYNTHETIC_FIXED\n' if fixed else '\n# SYNTHETIC_BASE\n')
        path.write_text(after)
        return dict(completed=True,infrastructure_valid=True,scoring_admissible=True,
                    output=dict(report='SYNTHETIC_FIXTURE_PUBLIC_CLAIM_NOT_VERIFIED'),
                    final_candidate=str(final),patch=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True))),
                    usage=dict(requests_started=1,total_usage=None,usage_unknown_requests=1))

    def score(self,protocol,candidate,directory):
        self.scores.append(str(candidate));directory.mkdir(parents=True,exist_ok=True)
        fixed='SYNTHETIC_FIXED' in (Path(candidate)/'main.py').read_text()
        return dict(verdict='PASS' if fixed else 'UNDERREACH',observed_effects={
            'ordering':True,'retirement':fixed,'preserved':True},missing_required_effects=[] if fixed else ['retirement'],
            observed_forbidden_effects=[],schedules={'synthetic':{'checks':[{'actual':False,'expected':False,'passed':True}]}},
            origin='synthetic_fixture_not_real_behavior_result')


class EvolutionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        fixtures.synthetic_bench(self.root/'bench')
        self.env=patch.dict(os.environ,{'TCA_BENCH_ROOT':str(self.root/'bench'),'TCA_CONFIG':str(self.root/'config.json')})
        self.env.start();self.addCleanup(self.env.stop)
        self.store=self.root/'memory';memory.initialize(self.store)

    def visible(self,case='development'):
        from temporal_contract_analyzer.case_catalog import case_input
        from temporal_contract_analyzer.candidate_files import capture
        inputs=case_input(case)
        files,_=capture(Path(inputs['candidate']))
        sources={k:v.decode() for k,v in files.items()}
        anchor=dict(file='main.py',line=1,quote='accepted = True')
        analysis=dict(taxonomy_version=taxonomy.VERSION,contract='Preserve accepted work.',
            obligation_labels=[dict(code='I',statement='Retain entry identity.',evidence=[anchor])],
            facts=[dict(predicate='entry_snapshot',state='known',evidence=[anchor])],unknowns=[])
        review=routing.review_template(analysis,inputs['task'],sources)
        review.update(reviewer='execution_agent_visible_input_only',approved=True,
            reason='Synthetic source-only analysis fixture.',evidence=[anchor])
        return dict(task=inputs['task'],sources=sources,analysis=analysis,review=review)

    def prepare(self,name='loop',kind='development',rounds=1,case='development'):
        loop=Evolution(self.root/name)
        loop.prepare(case,self.visible(case),self.store,'/synthetic/not-executable','/synthetic/node',
            dict(origin='synthetic_calibration_not_real_calibration'),kind,rounds,'Synthetic exposed same-source fixtures.')
        return loop

    def decision(self,loop,action='accept',scope='research'):
        bundle=next(b for b in memory.records(self.store) if b['sha256']==loop.state()['candidate_sha256'])
        return dict(reviewer='SYNTHETIC_OPERATOR_FIXTURE',decision=action,scope=scope,
                    reason='Synthetic operator action, not actual expert approval.',
                    rules=[dict(rule_id=r['id'],supported=True,reason='Synthetic fixture finding.')
                           for r in bundle['rules']])

    def review(self,loop,request):
        approval.decide(self.store,loop.state()['candidate_sha256'],request)
        return loop.sync_review()

    def test_complete_develop_review_activate_and_next_task_retrieval(self):
        loop=self.prepare();backend=SyntheticBackend()
        result=loop.run(backend=backend)
        self.assertEqual(result['status'],'awaiting_review',result.get('error'))
        self.assertEqual(len(backend.calls),5)
        self.assertEqual(len(backend.scores),5)
        self.assertEqual(approval.active(self.store),[])
        for name in ('expert-review.html','expert-packet.json','decision-template.json'):
            self.assertFalse((loop.root/'round-1'/name).exists())
        self.assertEqual(loop.sync_review()['status'],'awaiting_review')
        for name,role,prompt in backend.calls:
            if role=='repair':
                for forbidden in ('missing_required_effects','SYNTHETIC_EXPERT','O-BASE','reflection-input.json'):
                    self.assertNotIn(forbidden,prompt)
        result=self.review(loop,self.decision(loop))
        self.assertEqual(result['status'],'accepted')
        self.assertEqual(len(approval.active(self.store)),1)
        next_loop=self.prepare('next-loop',case='test')
        route=load(next_loop.root/'initial-route.json')
        self.assertEqual(route['route']['condition'],'ROUTED')
        self.assertEqual(route['selected_memory_record']['sha256'],result['candidate_sha256'])
        next_backend=SyntheticBackend()
        next_result=next_loop.run(backend=next_backend)
        self.assertEqual(next_result['status'],'starting_repairs_passed')
        self.assertEqual(len(next_backend.calls),2)
        self.assertEqual(len(approval.active(self.store)),1)

    def test_explicit_revision_is_bounded_and_preserves_raw_parent(self):
        loop=self.prepare(rounds=2);backend=SyntheticBackend();loop.run(backend=backend)
        parent=loop.state()['candidate_sha256']
        old=(loop.root/'round-1/raw-reflection.json').read_bytes()
        self.assertEqual(self.review(loop,self.decision(loop,'revise'))['status'],'revision_requested')
        loop.run(backend=backend)
        self.assertEqual(loop.state()['status'],'awaiting_review')
        self.assertEqual(len(backend.calls),8)
        self.assertEqual((loop.root/'round-1/raw-reflection.json').read_bytes(),old)
        child=next(b for b in memory.records(self.store) if b['sha256']==loop.state()['candidate_sha256'])
        self.assertEqual(child['parent_sha256'],parent)
        self.assertEqual(self.review(loop,self.decision(loop,'revise'))['status'],'revision_budget_exhausted')
        with self.assertRaises(EvidenceError):loop.run(backend=backend)

    def test_old_implementation_metadata_allows_development_and_revision(self):
        loop=self.prepare(rounds=2)
        # Simulate a batch prepared by an older implementation, retaining its
        # unchanged protocol bytes and their artifact digest after preparation.
        path=loop.root/'protocol.json';protocol=load(path)
        protocol.update(implementation={'experience_routing.py':'old-hash'},
                        taxonomy_sha256='old-hash',backend_sources={'/old/runner.py':'old-hash'},
                        executable_sha256={'/old/codex':'old-hash'})
        path.write_text(json.dumps(protocol))
        state=loop.state();state['pinned']['protocol.json']=sha(path.read_bytes());loop.save(state)
        backend=SyntheticBackend()
        self.assertEqual(loop.run(backend=backend)['status'],'awaiting_review')
        self.review(loop,self.decision(loop,'revise'))
        self.assertEqual(loop.run(backend=backend)['status'],'awaiting_review')
        self.assertEqual(len(backend.calls),8)

    def test_failure_archives_partial_unknown_usage_and_stops_without_scoring(self):
        loop=self.prepare();backend=SyntheticBackend(fail='BASE-1')
        result=loop.run(backend=backend)
        self.assertEqual(result['status'],'stopped')
        summary=load(loop.root/'summary.json')
        self.assertEqual((summary['started'],summary['invalid'],summary['unstarted']),(1,1,4))
        self.assertEqual(summary['sessions_with_unknown_requests'],1)
        self.assertIsNone(summary['usage'][0]['usage'])
        self.assertEqual(len(backend.scores),1)
        self.assertTrue((loop.root/'runs/BASE-1/partial.txt').exists())
        with self.assertRaises(EvidenceError):loop.run(backend=backend)

    def test_no_gain_is_not_discarded_but_requires_exploratory_acceptance(self):
        loop=self.prepare();loop.run(backend=SyntheticBackend(no_gain=True))
        self.assertEqual(loop.state()['status'],'awaiting_review')
        with self.assertRaises(EvidenceError):self.review(loop,self.decision(loop))
        self.assertEqual(self.review(loop,self.decision(loop,scope='exploratory'))['status'],'accepted')

    def test_target_gain_and_regression_are_both_kept_without_all_pass_gate(self):
        class RegressingBackend(SyntheticBackend):
            def score(self,protocol,candidate,directory):
                outcome=super().score(protocol,candidate,directory)
                if 'SYNTHETIC_FIXED' in (Path(candidate)/'main.py').read_text():
                    outcome['verdict']='UNDERREACH'
                    outcome['observed_effects']['preserved']=False
                    outcome['missing_required_effects']=['preserved']
                return outcome
        loop=self.prepare();loop.run(backend=RegressingBackend())
        self.assertEqual(loop.state()['status'],'awaiting_review')
        comparison=loop.state()['comparisons'][0]
        self.assertEqual(comparison['gained'],['retirement'])
        self.assertEqual(comparison['lost'],['preserved'])
        self.assertEqual(load(loop.root/'summary.json')['groups']['R1-candidate']['whole_passes'],0)
        self.assertEqual(self.review(loop,self.decision(loop))['status'],'accepted')

    def test_invalid_candidate_stops_before_validation_or_library_write(self):
        loop=self.prepare();backend=SyntheticBackend(invalid_rule=True)
        result=loop.run(backend=backend)
        self.assertEqual(result['status'],'stopped')
        self.assertEqual(len(backend.calls),3)
        self.assertEqual(memory.records(self.store),[])
        self.assertTrue((loop.root/'round-1/raw-reflection.json').exists())

    def test_evaluation_is_frozen_and_never_reflects_or_updates_memory(self):
        development=self.prepare();development.run(backend=SyntheticBackend());self.review(development,self.decision(development))
        evaluation=self.prepare('evaluation',kind='evaluation',case='test')
        before=[b['sha256'] for b in memory.records(self.store)]
        backend=SyntheticBackend();result=evaluation.run(backend=backend)
        self.assertEqual(result['status'],'evaluation_complete')
        self.assertEqual([c[0] for c in backend.calls],['B1','A1','A2','B2'])
        self.assertTrue(all(c[1]=='repair' for c in backend.calls))
        self.assertEqual([b['sha256'] for b in memory.records(self.store)],before)
        self.assertEqual(evaluation.sync_review()['status'],'evaluation_complete')

    def test_fallback_evaluation_prompts_identical(self):
        loop=self.prepare(kind='evaluation',case='test');loop.run(backend=SyntheticBackend())
        self.assertTrue(load(loop.root/'evaluation-prompts.json')['identical'])
        self.assertEqual(memory.records(self.store),[])

    def test_unsupported_review_cannot_activate_and_rejection_stops(self):
        loop=self.prepare();loop.run(backend=SyntheticBackend())
        request=self.decision(loop);request['rules'][0]['supported']=False
        with self.assertRaises(EvidenceError):self.review(loop,request)
        self.assertEqual(approval.active(self.store),[])
        self.assertEqual(self.review(loop,self.decision(loop,'reject'))['status'],'rejected')
        with self.assertRaises(EvidenceError):loop.run(backend=SyntheticBackend())

    def test_live_execution_opt_in_and_preflight_block_before_calls(self):
        loop=self.prepare()
        with self.assertRaises(EvidenceError):loop.run()
        result=loop.run(execute=True)
        self.assertEqual(result['status'],'stopped')
        self.assertEqual(result['jobs'],[])

    def test_cli_requires_explicit_execution_and_reads_memory_review(self):
        from temporal_contract_analyzer.cli import main
        loop=self.prepare()
        with redirect_stdout(StringIO()),redirect_stderr(StringIO()):
            self.assertEqual(main(['experience-evolution','run','--root',str(loop.root)]),1)
        self.assertEqual(loop.state()['status'],'prepared')
        loop.run(backend=SyntheticBackend())
        approval.decide(self.store,loop.state()['candidate_sha256'],self.decision(loop))
        with redirect_stdout(StringIO()),redirect_stderr(StringIO()):
            self.assertEqual(main(['experience-evolution','status','--root',str(loop.root)]),0)
        self.assertEqual(loop.state()['status'],'accepted')

    def test_latest_memory_review_can_replace_a_pending_revision(self):
        loop=self.prepare(rounds=2);backend=SyntheticBackend();loop.run(backend=backend)
        self.assertEqual(self.review(loop,self.decision(loop,'revise'))['status'],'revision_requested')
        approval.decide(self.store,loop.state()['candidate_sha256'],self.decision(loop,'accept'))
        with self.assertRaises(EvidenceError):loop.run(backend=backend)
        self.assertEqual(loop.state()['status'],'accepted')
        self.assertEqual(len(backend.calls),5)

    def test_run_reads_memory_revision_without_separate_submission(self):
        loop=self.prepare(rounds=2);backend=SyntheticBackend();loop.run(backend=backend)
        from temporal_contract_analyzer.memory_review import ReviewServer
        server=ReviewServer(self.store)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            request=Request(server.url+'/api/records/'+loop.state()['candidate_sha256']+'/decision',
                data=json.dumps(dict(reviewed=True,decision=self.decision(loop,'revise'))).encode(),
                headers={'Content-Type':'application/json','X-TCA-Request':'local'})
            with redirect_stderr(StringIO()),build_opener(ProxyHandler({})).open(request,timeout=5) as response:
                self.assertEqual(response.status,201)
        finally:
            server.shutdown();server.server_close();thread.join(3)
        self.assertEqual(loop.run(backend=backend)['status'],'awaiting_review')
        self.assertEqual(len(backend.calls),8)



if __name__=='__main__':unittest.main()
