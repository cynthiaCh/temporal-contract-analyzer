"""Offline training acceptance/held-out separation; synthetic models only."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import patch
import test_compact_experience as compact_fixtures
import json
from pathlib import Path
import unittest
import test_tempoevo_v4 as fixtures
Backend=fixtures.Backend
from temporal_contract_analyzer.tempoevo_v4 import read
from temporal_contract_analyzer.training_acceptance import normalize
from temporal_contract_analyzer.core import EvidenceError
from temporal_contract_analyzer import experience_approval as approval, compact_experience as compact, experience_memory as memory, taxonomy
from temporal_contract_analyzer.tempoevo_docker import evaluate


class AcceptanceBackend(Backend):
 def __init__(self,gold_at=2,visible_at=1,invalid=False):
  super().__init__(visible_at);self.gold_at=gold_at;self.invalid_gold=invalid;self.evaluations=[]
 def evaluate(self,kind,payload,directory):
  self.evaluations.append((kind,deepcopy(payload)))
  if kind!='gold':return super().evaluate(kind,payload,directory)
  if self.invalid_gold:return dict(valid=False,error='Synthetic environment unavailable',failure_type='infrastructure_error')
  n=int((Path(payload['candidate'])/'main.py').read_text().split('=')[1])
  return dict(valid=True,verdict='PASS' if n>=self.gold_at else 'UNDERREACH',
      observed_effects={'private-id':n>=self.gold_at},reference_implementation='SECRET_REFERENCE',gold_patch='SECRET_PATCH',
      schedules={'SECRET_SCENARIO':dict(assertions=[dict(expected='/oracle/SECRET.py',actual='SECRET')])})


class AcceptanceTests(unittest.TestCase):
 setUp=fixtures.V4Tests.setUp
 prepare=fixtures.V4Tests.prepare
 def test_public_pass_gold_fail_continues_using_previous_candidate(self):
  loop=self.prepare(training_feedback={'private-id':dict(summary='Preserve accepted work.',expected=True)});b=AcceptanceBackend();s=loop.run(b,execute=True)
  self.assertEqual(s['status'],'passed',s.get('error'));self.assertEqual(len(s['attempts']),2)
  self.assertEqual([a['acceptance_passed'] for a in s['attempts']],[False,True]);self.assertTrue(all(a['visible_passed'] for a in s['attempts']))
  self.assertEqual([k for k,_ in b.evaluations],['visible','gold','visible','gold'])
  actions=[p for k,p,_,_ in b.calls if k=='action'];self.assertEqual(actions[1]['candidate_sources']['main.py'],'value = 1\n')
  self.assertFalse(actions[1]['feedback']['oracle_acceptance']['passed']);self.assertEqual(s['stop_reason'],'oracle_accepted')
  for _,payload,_,_ in b.calls:
   serialized=json.dumps(payload);self.assertNotIn('SECRET',serialized);self.assertNotIn('private-id',serialized);self.assertNotIn('/oracle/',serialized)
  self.assertIn('SECRET', (loop.root/'stages/acceptance-1/raw-result.json').read_text())
 def test_gold_pass_public_fail_stops_in_training(self):
  loop=self.prepare();s=loop.run(AcceptanceBackend(gold_at=1,visible_at=99),execute=True)
  self.assertEqual(len(s['attempts']),1);self.assertTrue(s['attempts'][0]['acceptance_passed']);self.assertFalse(s['attempts'][0]['visible_passed'])
 def test_optional_public_failure_does_not_block_gold_acceptance(self):
  loop=self.prepare(required_visible_checks=False);s=loop.run(AcceptanceBackend(gold_at=1,visible_at=99),execute=True)
  self.assertTrue(s['training_accepted']);self.assertEqual(len(s['attempts']),1);self.assertFalse(s['attempts'][0]['visible_passed'])
 def test_three_gold_failures_require_real_expert_not_success_extraction(self):
  loop=self.prepare();b=AcceptanceBackend(gold_at=99);s=loop.run(b,execute=True)
  self.assertEqual(s['status'],'awaiting_expert_summary',s.get('error'));self.assertEqual(len(s['attempts']),3)
  self.assertNotIn('extract',[x[0] for x in b.calls]);self.assertFalse((loop.root/'candidate-pool/success.json').exists())
  self.assertIsNone(read(loop.root/'expert-summary-task.json')['expert']);self.assertFalse(s['training_accepted'])
 def test_scorer_error_not_a_behavior_failure(self):
  loop=self.prepare();s=loop.run(AcceptanceBackend(invalid=True),execute=True)
  self.assertEqual(s['status'],'execution_invalid');self.assertEqual(s['attempts'],[]);self.assertFalse((loop.root/'expert-summary-task.json').exists())
  self.assertFalse((loop.root/'candidate-pool').exists());self.assertEqual(s['stages'][-1]['failure_type'],'infrastructure_error')
 def test_missing_acceptance_rejected_before_root_created(self):
  with self.assertRaisesRegex(EvidenceError,'training_evaluator'):self.prepare(training_evaluator=None)
 def test_old_protocol_cannot_resume_even_if_binding_matches(self):
  from temporal_contract_analyzer.core import sha
  loop=self.prepare();p=read(loop.root/'protocol.json');p['schema_version']='tempoevo-trajectory-v4';loop.save('protocol.json',p)
  binding=read(loop.root/'binding.json');binding['protocol']=sha((loop.root/'protocol.json').read_bytes());loop.save('binding.json',binding)
  b=Backend()
  with self.assertRaisesRegex(EvidenceError,'read-only'):loop.run(b,execute=True)
  self.assertEqual(b.calls,[])
  self.assertFalse((loop.root/'execution.lock').exists())
  before=(loop.root/'summary.json').read_bytes();loop.report();self.assertEqual(before,(loop.root/'summary.json').read_bytes())
  with self.assertRaisesRegex(EvidenceError,'read-only'):loop.cancel()
 def test_known_training_exposure_cannot_be_declared_independent_testing(self):
  from temporal_contract_analyzer import experience_approval as approval
  with self.assertRaisesRegex(EvidenceError,'Training-exposed'):
   self.prepare(mode='testing',training_feedback_used=True,memory_snapshot=approval.freeze(self.store),gold_evaluator=dict(command=['gold']))


class NormalizationTests(unittest.TestCase):
 def test_actual_probe_shape_and_wrapper_are_supported(self):
  score=dict(verdict='UNDERREACH',observed_effects={'x':False},schedules={'one':{'runtimeError':None}})
  self.assertFalse(normalize(score)['passed']);self.assertFalse(normalize(dict(full_score=score,passed=False,valid=True))['passed'])
  self.assertTrue(normalize({'passed':True})['passed'])
 def test_invalid_outputs_and_runtime_errors_are_not_fail_verdicts(self):
  for raw in [{},{'exit_code':0},{'verdict':'UNKNOWN'},{'verdict':'PASS','passed':False},
              {'verdict':'FAIL','runtime_errors':['bad']},{'verdict':'PASS','schedules':{'x':{'runtimeError':'crash'}}}]:
   with self.subTest(raw=raw):self.assertFalse(normalize(raw)['valid'])

class BoundaryTests(unittest.TestCase):
 setUp=fixtures.V4Tests.setUp
 prepare=fixtures.V4Tests.prepare
 def test_testing_scores_one_submission_without_learning(self):
  from temporal_contract_analyzer import experience_approval as approval
  loop=self.prepare(mode='testing',memory_snapshot=approval.freeze(self.store),gold_evaluator=dict(command=['synthetic-gold']))
  b=AcceptanceBackend(gold_at=99,visible_at=2);before={str(p):p.read_bytes() for p in self.store.rglob('*') if p.is_file()}
  state=loop.run(b,execute=True)
  self.assertEqual([k for k,_ in b.evaluations],['visible','gold']);self.assertEqual(len(state['attempts']),1);self.assertFalse(state['gold_result']['passed'])
  self.assertEqual(state['status'],'scored')
  self.assertFalse((loop.root/'candidate-pool').exists());self.assertFalse((loop.root/'expert-summary-task.json').exists());self.assertNotIn('extract',[x[0] for x in b.calls])
  self.assertEqual(before,{str(p):p.read_bytes() for p in self.store.rglob('*') if p.is_file()})
  self.assertTrue(all('training_acceptance' not in json.dumps(x[1]) and 'SECRET' not in json.dumps(x[1]) for x in b.calls))
 def test_exception_and_timeout_are_archived_invalid_execution(self):
  for error in (TimeoutError('synthetic timeout'),RuntimeError('synthetic environment')):
   loop=self.prepare()
   class Broken(AcceptanceBackend):
    def evaluate(inner,kind,*args):
     if kind=='gold':raise error
     return super().evaluate(kind,*args)
   state=loop.run(Broken(),execute=True)
   self.assertEqual(state['status'],'execution_invalid');self.assertEqual(len(state['attempts']),0)
   raw=read(loop.root/'stages/acceptance-1/raw-result.json');self.assertFalse(raw['valid'])
 def test_success_materialization_rechecks_acceptance(self):
  loop=self.prepare();state=loop.run(AcceptanceBackend(gold_at=1),execute=True)
  self.assertTrue(state['training_accepted']);state['training_accepted']=False;loop.save('state.json',state)
  with self.assertRaisesRegex(EvidenceError,'requires training acceptance'):loop.publish_candidate('success')
 def test_stored_accepted_attempt_resume_does_not_generate_extra_action(self):
  loop=self.prepare();b=AcceptanceBackend(gold_at=1);state=loop.run(b,execute=True)
  state.update(status='evaluation_running',finalized=False);loop.save('state.json',state);count=len(b.calls)
  loop.run(b,execute=True);self.assertEqual(len(b.calls),count)
 def test_extraction_failure_preserves_accepted_assessment(self):
  loop=self.prepare();s=loop.run(Backend(invalid='extract'),execute=True)
  self.assertEqual(s['status'],'execution_invalid');self.assertTrue(s['training_accepted']);self.assertEqual(s['repair_stop_reason'],'oracle_accepted')
  self.assertFalse((loop.root/'candidate-pool/success.json').exists())
 def test_raw_probe_exit_one_is_a_behavior_failure_not_transport_error(self):
  import sys
  from temporal_contract_analyzer.tempoevo_backend import NativeV4Backend
  d=self.root/'probe';d.mkdir()
  ev=dict(command=[sys.executable,'-c','import json,sys; print(json.dumps({"verdict":"UNDERREACH"})); sys.exit(1)'])
  raw=NativeV4Backend({}).evaluate('gold',dict(candidate=str(self.source),evaluator=ev,purpose='training_acceptance'),d)
  self.assertTrue(raw['valid']);self.assertFalse(normalize(raw)['passed'])
 def test_docker_accepts_raw_verdict_without_a_passed_field(self):
  from unittest.mock import patch
  from types import SimpleNamespace
  from temporal_contract_analyzer.tempoevo_docker import evaluate
  d=self.root/'probe';d.mkdir();payload=dict(candidate=str(self.source),purpose='training_acceptance',evaluator=dict(image='sha256:'+'a'*64,command=['node','/probe']))
  with patch('temporal_contract_analyzer.tempoevo_docker.image_identity'),patch('temporal_contract_analyzer.tempoevo_docker.subprocess.run',return_value=SimpleNamespace(returncode=1,stdout='{"verdict":"UNDERREACH"}',stderr='')),patch('temporal_contract_analyzer._session_runtime.docker_transport.stop'):
   raw=evaluate(payload,d)
  self.assertTrue(raw['valid']);self.assertFalse(normalize(raw)['passed'])

 def test_unknown_public_verdict_is_allowed_but_missing_verdict_is_invalid(self):
  candidate=self.root/'candidate';candidate.mkdir()
  for value,valid in [({'passed':None},True),({},False)]:
   with self.subTest(value=value),patch('temporal_contract_analyzer.tempoevo_docker.image_identity'),patch('temporal_contract_analyzer.tempoevo_docker.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps(value),stderr='')),patch('temporal_contract_analyzer._session_runtime.docker_transport.stop'):
    result=evaluate(dict(candidate=str(candidate),evaluator=dict(image='sha256:'+'a'*64,command=['python3','/checks/project.py'])),self.root)
    self.assertIs(result['valid'],valid)
    if valid:self.assertIsNone(result['passed'])

 def test_final_gold_accepts_the_scorer_failure_exit_code(self):
  candidate=self.root/'candidate';candidate.mkdir()
  with patch('temporal_contract_analyzer.tempoevo_docker.image_identity'),patch('temporal_contract_analyzer.tempoevo_docker.subprocess.run',return_value=SimpleNamespace(returncode=1,stdout='{"passed": false}',stderr='')),patch('temporal_contract_analyzer._session_runtime.docker_transport.stop'):
   result=evaluate(dict(candidate=str(candidate),purpose='final_scoring',evaluator=dict(image='sha256:'+'a'*64,command=['python3','/checks/gold.py'])),self.root)
  self.assertTrue(result['valid']);self.assertFalse(result['passed'])


class IndependentTestingTests(unittest.TestCase):
    setUp=fixtures.V4Tests.setUp

    def prepare(self, **changes):
        config=dict(mode='testing',memory_snapshot=approval.freeze(self.store),gold_evaluator=dict(command=['synthetic-gold']))
        config.update(changes)
        return fixtures.V4Tests.prepare(self,**config)


    def test_no_public_checker_submits_once_even_when_gold_fails(self):
        loop=self.prepare(visible_evaluator=None)
        backend=AcceptanceBackend(gold_at=2);state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'scored',state.get('error'))
        self.assertFalse(state['gold_result']['passed'])
        self.assertEqual(len(state['attempts']),1)
        self.assertEqual([k for k,_ in backend.evaluations],['gold'])
        self.assertEqual([k for k,_,_,_ in backend.calls],['contract','action'])
        self.assertIsNone(state['attempts'][0]['visible_passed'])
        self.assertNotIn('oracle_acceptance',state['attempts'][0]['feedback'])
        self.assertNotIn('feedback',state['gold_result'])


    def test_legacy_summary_remains_read_only(self):
        loop=self.prepare();summary=(loop.root/'summary.json').read_bytes()
        protocol=read(loop.root/'protocol.json');protocol['acceptance_policy']='oracle_pass_or_action_budget_exhausted';loop.save('protocol.json',protocol)
        self.assertEqual(loop.report(),json.loads(summary))
        self.assertEqual((loop.root/'summary.json').read_bytes(),summary)
        backend=AcceptanceBackend()
        with self.assertRaisesRegex(EvidenceError,'read-only'):loop.run(backend,execute=True)
        with self.assertRaisesRegex(EvidenceError,'read-only'):loop.cancel()
        self.assertFalse(backend.calls);self.assertFalse(backend.evaluations)

    def test_gold_and_public_verdicts_cannot_change_testing_submission(self):
        for condition in ('baseline','contract','bm25','structured','fixed_contract'):
            submissions=[]
            for gold_at,public in ((1,True),(99,True),(1,False),(99,False),(99,None)):
                with self.subTest(condition=condition,gold_at=gold_at,public=public):
                    loop=self.prepare(condition=condition,routing_analysis=dict(
                        taxonomy_version=taxonomy.VERSION,
                        contract='Preserve accepted work.',obligation_labels=[],facts=[],unknowns=[]))
                    class Backend(AcceptanceBackend):
                        def execute(inner,*args):
                            self.assertFalse(any(k=='gold' for k,_ in inner.evaluations))
                            return super().execute(*args)
                        def evaluate(inner,kind,payload,directory):
                            if kind=='gold':
                                self.assertEqual(loop.state()['status'],'submitted')
                                self.assertEqual(len(loop.state()['attempts']),1)
                                self.assertEqual(payload['purpose'],'final_scoring')
                            value=super().evaluate(kind,payload,directory)
                            if kind=='visible':value['passed']=public
                            return value
                    backend=Backend(gold_at=gold_at);state=loop.run(backend,execute=True)
                    self.assertEqual(state['status'],'scored',state.get('error'))
                    self.assertEqual(state['gold_result']['passed'],gold_at==1)
                    self.assertEqual(state['stop_reason'],'single_submission')
                    self.assertEqual(len(state['attempts']),1)
                    self.assertEqual([k for k,_ in backend.evaluations],['visible','gold'])
                    self.assertNotIn('SECRET',json.dumps(backend.calls))
                    self.assertFalse(any(k in ('diagnosis','extract') for k,_,_,_ in backend.calls))
                    self.assertIsNone(state['attempts'][0]['acceptance_passed'])
                    self.assertIsNone(state['attempts'][0]['oracle_result'])
                    self.assertFalse((loop.root/'candidate-pool').exists())
                    self.assertFalse((loop.root/'expert-summary-task.json').exists())
                    submissions.append(([(kind,payload,model,limits['requests']) for kind,payload,model,limits in backend.calls],
                        state['attempts'][0]['candidate_sources']))
                    summary=read(loop.root/'summary.json')
                    self.assertIsNone(summary['final_acceptance']);self.assertIsNone(summary['first_pass_attempt'])
                    self.assertEqual(summary['per_attempt_oracle'],[None])
                    self.assertEqual(loop.verify()['evaluation_budget'],dict(visible=1,oracle=0,gold=1))
                    before=(deepcopy(backend.calls),deepcopy(backend.evaluations))
                    loop.run(backend,execute=True)
                    self.assertEqual((backend.calls,backend.evaluations),before)
            self.assertTrue(all(s==submissions[0] for s in submissions))

    def test_invalid_final_score_never_restarts_solving(self):
        loop=self.prepare();backend=AcceptanceBackend(invalid=True)
        state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'execution_invalid')
        self.assertEqual(state['repair_stop_reason'],'single_submission')
        self.assertEqual(len(state['attempts']),1)
        self.assertEqual([k for k,_,_,_ in backend.calls],['contract','action'])
        self.assertIsNone(read(loop.root/'summary.json')['gold_result'])
        before=(deepcopy(backend.calls),deepcopy(backend.evaluations))
        loop.run(backend,execute=True)
        self.assertEqual((backend.calls,backend.evaluations),before)

    def test_testing_rejects_multiple_submissions_before_creating_a_root(self):
        for attempts in (2,3):
            with self.assertRaisesRegex(EvidenceError,'exactly one'):self.prepare(max_attempts=attempts)
        self.assertFalse(list(self.root.glob('run-*')))

    def test_new_runs_reject_legacy_stop_policies_in_either_mode(self):
        for mode in ('learning','testing'):
            with self.subTest(mode=mode):
                with self.assertRaisesRegex(EvidenceError,'read-only'):self.prepare(mode=mode,acceptance_policy='visible_stop_then_independent_gold')
                with self.assertRaisesRegex(EvidenceError,'advisory'):self.prepare(mode=mode,required_visible_checks=True)

class CompactPublicationTests(unittest.TestCase):
    prepare=fixtures.V4Tests.prepare

    def setUp(self):
        fixtures.V4Tests.setUp(self)
        example=compact_fixtures.CompactExperienceTests();example.setUp();self.addCleanup(example.doCleanups)
        self.store=self.root/'library';self.store.mkdir()
        self.category=self.store/'mechanisms.json'
        self.category.write_text(json.dumps(example.value))

    def trained(self):
        loop=self.prepare();state=loop.run(fixtures.Backend(),execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'))
        return loop

    def request(self, item):
        bundle=next(b for b in memory.records(self.store) if b['id']==item['id'])
        return dict(id=item['id'],expected_record=bundle['sha256'],expected_review=item['review'],reviewer='Synthetic reviewer',decision='accept')

    def test_publish_review_and_retry_preserve_approved_content_and_snapshot(self):
        before=self.category.read_bytes();snapshot=approval.freeze(self.store)
        loop=self.trained();code=loop.publish_candidate('success')
        self.assertEqual(self.category.read_bytes(),before)
        self.assertEqual(approval.freeze(self.store),snapshot)
        self.assertEqual(approval.validate_snapshot(self.store,snapshot),snapshot)
        self.assertEqual({p.name for p in self.store.iterdir()},{'mechanisms.json','candidates.json'})
        self.assertFalse((loop.root/'candidate-pool/success-evidence.json').exists())
        item=compact.load(self.store/'candidates.json')['experiences'][0]
        self.assertEqual(item['review'],dict(reviewer=None,decision='pending',at=None))
        self.assertEqual(item['proposal'],dict(operation='new',target_ids=[]))
        self.assertIn('Verify accepted identity',item['verification'])
        self.assertIn('Synthetic fixture',item['exclusion'])
        self.assertIn(item['id'],compact.page(self.store).decode())
        self.assertEqual(next(b for b in memory.records(self.store) if b['id']==item['id'])['sha256'],code)
        compact.save_review(self.store,self.request(item))
        self.assertEqual(len(approval.freeze(self.store)['entries']),2)
        # Recover from a lost local receipt, even after the reviewer has accepted it.
        record=read(loop.root/'candidate-pool/success.json');record.pop('published_sha256')
        loop.save('candidate-pool/success.json',record)
        self.assertEqual(loop.publish_candidate('success'),code)
        saved=compact.load(self.store/'candidates.json')['experiences']
        self.assertEqual(len(saved),1);self.assertEqual(saved[0]['review']['decision'],'accept')

    def test_single_file_publication_does_not_inherit_whole_file_acceptance(self):
        self.store=self.category
        snapshot=approval.freeze(self.store);loop=self.trained();loop.publish_candidate('success')
        value=compact.load(self.store)
        self.assertEqual(len(value['experiences']),2)
        self.assertEqual(compact.review_for(value,value['experiences'][1])['decision'],'pending')
        self.assertEqual(approval.freeze(self.store),snapshot)
        self.assertEqual({p.name for p in self.category.parent.iterdir()},{'mechanisms.json'})

    def test_revision_and_merge_remain_pending_and_identify_targets(self):
        value=compact.load(self.category)
        value['experiences'].append(dict(value['experiences'][0],id='other-binding'))
        self.category.write_text(json.dumps(value));before=self.category.read_bytes()
        for operation,count in [('revise',1),('merge',2)]:
            loop=self.trained();path=loop.root/'candidate-pool/success.json';record=read(path)
            targets=[entry['bundle'] for entry in approval.freeze(self.store)['entries']]
            record['related_experiences']=targets
            record['reflection_update'].update(operation=operation,target_sha256s=[t['sha256'] for t in targets[:count]],change_summary=['Synthetic guidance change'],supporting_attempts=[1])
            loop.save('candidate-pool/success.json',record);loop.publish_candidate('success')
        items=compact.load(self.store/'candidates.json')['experiences']
        self.assertEqual([i['proposal']['operation'] for i in items],['revise','merge'])
        self.assertEqual([len(i['proposal']['target_ids']) for i in items],[1,2])
        self.assertTrue(all(i['review']['decision']=='pending' for i in items))
        self.assertEqual(self.category.read_bytes(),before)

    def test_failure_summary_publishes_pending_without_claiming_success(self):
        snapshot=approval.freeze(self.store);loop=self.prepare()
        self.assertEqual(loop.run(fixtures.Backend(99),execute=True)['status'],'awaiting_expert_summary')
        summary=dict(expert='SYNTHETIC_HUMAN',confirmed_conclusions=[],unverified_hypotheses=[],
            unresolved_behaviors=['Still failing'],boundaries_counterexamples=[],suggested_checks=[],
            experience=dict(labels=['I'],requires=['entry_snapshot'],excludes=[],
                rules=[dict(category='verification',body='Check retained selection identity.')],limitations=['Not a successful repair']))
        loop.submit_expert(summary);code=loop.publish_candidate('expert')
        item=compact.load(self.store/'candidates.json')['experiences'][0]
        self.assertEqual(item['review']['decision'],'pending')
        self.assertIn('Not a successful repair',item['exclusion'])
        self.assertEqual(approval.freeze(self.store),snapshot)
        self.assertFalse(read(loop.root/'candidate-pool/expert.json')['effectiveness_verified'])
        self.assertEqual(loop.publish_candidate('expert'),code)

    def test_testing_cannot_publish_into_compact_library(self):
        loop=self.prepare(mode='testing',memory_snapshot=approval.freeze(self.store),gold_evaluator=dict(command=['synthetic-gold']))
        with self.assertRaisesRegex(EvidenceError,'Testing cannot write'):loop.publish_candidate('success')
        self.assertEqual({p.name for p in self.store.iterdir()},{'mechanisms.json'})

    def test_unchanged_evidence_creates_no_duplicate_or_legacy_sidecar(self):
        loop=self.trained();path=loop.root/'candidate-pool/success.json';record=read(path)
        target=memory.records(self.store)[0]
        record['experience']=dict(labels=target['labels'],requires=target['requires'],excludes=target['excludes'],
            rules=[dict(category=r['category'],body=r['body']) for r in target['rules']],limitations=[])
        record['related_experiences']=[target]
        record['reflection_update'].update(operation='evidence',target_sha256s=[target['sha256']])
        loop.save('candidate-pool/success.json',record)
        snapshot=approval.freeze(self.store);before=self.category.read_bytes()
        code=loop.publish_candidate('success')
        self.assertEqual(loop.publish_candidate('success'),code)
        self.assertEqual(read(path)['publication_kind'],'evidence_proposal')
        self.assertEqual({p.name for p in self.store.iterdir()},{'mechanisms.json'})
        self.assertEqual(self.category.read_bytes(),before);self.assertEqual(approval.freeze(self.store),snapshot)

    def test_invalid_or_edited_candidate_is_not_overwritten(self):
        loop=self.trained();path=loop.root/'candidate-pool/success.json';record=read(path)
        bad=deepcopy(record);bad['experience']['requires']=['invented-predicate']
        loop.save('candidate-pool/success.json',bad)
        before=self.category.read_bytes()
        with self.assertRaises(EvidenceError):loop.publish_candidate('success')
        self.assertEqual({p.name for p in self.store.iterdir()},{'mechanisms.json'})
        self.assertEqual(self.category.read_bytes(),before)
        loop.save('candidate-pool/success.json',record);loop.publish_candidate('success')
        candidates=self.store/'candidates.json';value=compact.load(candidates)
        value['experiences'][0]['verification']='Synthetic reviewer edit.'
        candidates.write_text(json.dumps(value));before=candidates.read_bytes()
        loop.save('candidate-pool/success.json',record)
        with self.assertRaisesRegex(EvidenceError,'refusing to overwrite'):loop.publish_candidate('success')
        self.assertEqual(candidates.read_bytes(),before)

    def test_concurrent_publication_keeps_both_candidates_without_lock_files(self):
        record=read(self.trained().root/'candidate-pool/success.json')
        other=deepcopy(record);other['experience']['rules'][0]['body']='A different synthetic verification rule.'
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures=[executor.submit(compact.publish_candidate,self.store,r) for r in (record,other)]
            receipts=[f.result(timeout=5) for f in futures]
        self.assertEqual(len({r['published_sha256'] for r in receipts}),2)
        self.assertEqual(len(compact.load(self.store/'candidates.json')['experiences']),2)
        self.assertEqual({p.name for p in self.store.iterdir()},{'mechanisms.json','candidates.json'})
