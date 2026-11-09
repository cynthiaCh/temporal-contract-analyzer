"""Zero-model real failed-stream replay, incomplete-result admission and null cases."""
import unittest,tempfile,json,shutil,sys
from pathlib import Path
A=Path(__file__).resolve().parent;V=A.parent/'two-class-experience-pilot-20261108_200017'
sys.path.insert(0,str(A))
from archive import Archive,inventory,save
from usage import summarize_ledger
import runner

class RuntimeV2(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  self.candidate=self.root/'candidate';(self.candidate/'src').mkdir(parents=True)
  (self.candidate/'src/unit.py').write_text('first_complete_source_line = 1\nsecond_complete_source_line = 2\nthird_complete_source_line = 3\n')
  self.task=self.root/'task.md';self.task.write_text('Repair actual behavior, preserve the supported interface.')
  self.score_calls=[]
 def tearDown(self):self.tmp.cleanup()
 def run_fake(self,slot,events,ledger,*,code=0,sleep=0,seconds=2):
  def build(a,runtime,guard):
   x=json.loads(json.dumps(ledger));x['sessions']={slot:dict(started=x['started'],completed=x['completed'],blocked_requests=0,tool_attempts=1,blocked_tools=0)}
   save(guard.meter/'ledger.json',x)
   body='import sys,time\n'
   body+='sys.stdout.write('+repr(events)+');sys.stdout.flush()\n'
   body+='sys.stderr.write("original service stderr\\n");sys.stderr.flush()\n'
   body+='time.sleep('+repr(sleep)+')\nsys.exit('+repr(code)+')\n'
   return [sys.executable,'-B','-c',body]
  def scorer(final,out):self.score_calls.append(final);return {'fixture':True,'verdict':'FAKE'}
  rec=runner.session({'slot':slot,'phase':'repair','condition':'FIXTURE'},'offline fixture',case={'node':'/usr/bin/true'},candidate=self.candidate,task=self.task,config={'seconds_per_session':seconds},run_dir=self.root/slot,command_factory=build,score_fn=scorer)
  return rec,self.root/slot/'archive'
 def ledger(self,usage=None,complete=True):
  e=[{'event':{'hook_event_name':'PreModelRequest','model':'gpt-5.6-terra'}}]
  if complete:e.append({'event':{'hook_event_name':'PostModelRequest','model':'gpt-5.6-terra','status':'completed','token_usage':usage}})
  return {'started':1,'completed':int(complete),'events':e,'blocked_requests':0,'tool_attempts':1}
 def text(self,complete=True,report='fixture complete'):
  events=[{'type':'item.completed','item':{'type':'command_execution','exit_code':0,'aggregated_output':(self.candidate/'src/unit.py').read_text()}}, {'type':'item.completed','item':{'type':'agent_message','text':json.dumps({'report':report})}}]
  if complete:events.append({'type':'turn.completed'})
  return ''.join(json.dumps(e)+'\n' for e in events)
 def test_real_v1_failure_replay(self):
  src=V/'runs/T1-block-1-A/archive'
  shutil.rmtree(self.candidate);shutil.copytree(src/'input/original',self.candidate)
  ledger=json.loads((src/'meter/ledger.json').read_text())
  rec,out=self.run_fake('replay-v1', (src/'events.jsonl').read_text(),ledger,code=1)
  self.assertEqual(rec['archive_status']['status'],'OK')
  self.assertFalse(rec['scoring_admissible']);self.assertEqual(self.score_calls,[])
  self.assertFalse(rec['candidate_complete']);self.assertEqual(rec['failure_class'],'model_or_cli_abnormal_exit')
  usage=json.loads((out/'usage.json').read_text());self.assertEqual(usage['usage_unknown_requests'],1)
  self.assertIsNone(usage['total_usage']);self.assertEqual(usage['observed_usage_subtotal']['total_tokens'],34555)
  self.assertTrue((out/'partial-answer.txt').read_text());self.assertEqual((out/'raw-answer.txt').read_text(),'')
  self.assertIn('stream disconnected',(out/'service-errors.json').read_text())
  self.assertEqual((out/'events.jsonl').read_bytes(),(src/'events.jsonl').read_bytes())
 def test_complete_valid_candidate_scores_once(self):
  usage={k:1 for k in ['input_tokens','output_tokens','cached_input_tokens','cache_write_input_tokens','reasoning_output_tokens','total_tokens']}
  rec,out=self.run_fake('complete',self.text(),self.ledger(usage))
  self.assertTrue(rec['scoring_admissible']);self.assertEqual(len(self.score_calls),1)
  self.assertEqual(rec['scoring_status'],'COLLECTED')
 def test_timeout_keeps_partial_unscored(self):
  rec,out=self.run_fake('timeout',self.text(False),self.ledger(complete=False),sleep=3,seconds=.2)
  self.assertEqual(rec['stop_reason'],'timeout');self.assertEqual(rec['archive_status']['status'],'OK')
  self.assertFalse(rec['scoring_admissible']);self.assertEqual(self.score_calls,[])
  self.assertTrue((out/'partial-answer.txt').exists())
  self.assertEqual(json.loads((out/'usage.json').read_text())['usage_unknown_requests'],1)
 def test_malformed_event_unscored(self):
  rec,out=self.run_fake('malformed','null\nnot-json\n'+self.text(),self.ledger({}))
  self.assertEqual(rec['archive_status']['status'],'OK');self.assertFalse(rec['candidate_complete'])
  self.assertEqual(self.score_calls,[])
 def test_malformed_final_report_unscored(self):
  text=self.text().replace(json.dumps({'report':'fixture complete'}).replace('"','\\"'),'[]')
  # Construct directly so final message is a valid JSON array, invalid envelope.
  events=[{'type':'item.completed','item':{'type':'agent_message','text':'[]'}},{'type':'turn.completed'}]
  rec,out=self.run_fake('bad-envelope',''.join(json.dumps(e)+'\n' for e in events),self.ledger({}))
  self.assertEqual(rec['archive_status']['status'],'OK');self.assertFalse(rec['scoring_admissible'])
 def test_null_and_missing_fields_stay_unknown(self):
  for payload in [None,{}, {'input_tokens':0}]:
   u=summarize_ledger(self.ledger(payload))
   self.assertTrue(u['usage_incomplete']);self.assertIsNone(u['total_usage'])
   self.assertEqual(u['usage_unknown_requests'],1)
   self.assertIsNone(u['observed_usage_subtotal']['output_tokens'])
  u=summarize_ledger(self.ledger({'input_tokens':0}));self.assertEqual(u['observed_usage_subtotal']['input_tokens'],0)
 def test_ledger_missing_or_pending(self):
  self.assertIsNone(summarize_ledger(None)['usage_unknown_requests'])
  self.assertEqual(summarize_ledger(self.ledger(complete=False))['usage_unknown_requests'],1)
 def test_null_event_item_and_no_answer(self):
  rec,out=self.run_fake('null-item','{"type":"item.completed","item":null}\n',self.ledger(None),code=1)
  self.assertEqual(rec['archive_status']['status'],'OK');self.assertEqual(self.score_calls,[])

if __name__=='__main__':unittest.main()
