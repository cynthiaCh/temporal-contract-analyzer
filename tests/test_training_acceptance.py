"""Offline training acceptance/held-out separation; synthetic models only."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
import test_tempoevo_v4 as fixtures
Backend=fixtures.Backend
from temporal_contract_analyzer.tempoevo_v4 import read
from temporal_contract_analyzer.training_acceptance import normalize
from temporal_contract_analyzer.core import EvidenceError


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
  self.assertFalse(actions[1]['feedback']['training_acceptance']['passed']);self.assertEqual(s['stop_reason'],'training_accepted')
  for _,payload,_,_ in b.calls:
   serialized=json.dumps(payload);self.assertNotIn('SECRET',serialized);self.assertNotIn('private-id',serialized);self.assertNotIn('/oracle/',serialized)
  self.assertIn('SECRET', (loop.root/'stages/acceptance-1/raw-result.json').read_text())
 def test_gold_pass_required_public_fail_continues(self):
  loop=self.prepare();s=loop.run(AcceptanceBackend(gold_at=1,visible_at=2),execute=True)
  self.assertEqual(len(s['attempts']),2);self.assertFalse(s['attempts'][0]['acceptance_passed']);self.assertTrue(s['attempts'][0]['training_result']['passed'])
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
 def test_testing_only_one_final_gold_no_feedback_or_learning(self):
  from temporal_contract_analyzer import experience_approval as approval
  loop=self.prepare(mode='testing',memory_snapshot=approval.freeze(self.store),gold_evaluator=dict(command=['synthetic-gold']))
  b=AcceptanceBackend(gold_at=99,visible_at=2);before={str(p):p.read_bytes() for p in self.store.rglob('*') if p.is_file()}
  state=loop.run(b,execute=True)
  self.assertEqual([k for k,_ in b.evaluations],['visible','visible','gold']);self.assertEqual(len(state['attempts']),2);self.assertFalse(state['gold_result']['passed'])
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
  self.assertEqual(s['status'],'execution_invalid');self.assertTrue(s['training_accepted']);self.assertEqual(s['repair_stop_reason'],'training_accepted')
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
