"""Typed boundary and actual runner lifecycle integration; all model events fake."""
import unittest,json,sys,tempfile,shutil
from pathlib import Path
A=Path(__file__).resolve().parent;P=A.parent/'two-class-experience-pilot-v2-20261108_205648'
from structured import parse_response,validate
from toolflow import PREDICATES,digest,canonical,route,freeze_entry,maintenance_prompt,valid_evidence
from archive import save,inventory
import runner

DIMS=['negation','conditions','event_order','ownership','history_vs_ui','cancellation_vs_completion']
def fixture():
 proof=[{'file':'src/unit.py','line':1,'quote':'shared_value = 1'}]
 return {'contract':'Preserve shared state and change the reported defect.','primary_class':'T4','secondary_tags':[],'evidence':proof,
 'facts':[{'predicate':k,'state':'known' if k=='shared_lifetime' else 'unknown','evidence':proof if k=='shared_lifetime' else []} for k in PREDICATES],
 'claims':[{'kind':'source_fact','statement':'value belongs to shared object','record_owner':'shared_state','owner_expression':'shared_value','evidence':proof}],
 'consistency':{'conflicts':[],'unknowns':[],'checked_dimensions':DIMS}}

class TypedPipeline(unittest.TestCase):
 def test_exact_broken_v2_output_rejected(self):
  raw=(P/'runs/D1-preanalysis-v2/archive/raw-answer.txt').read_text();outer=json.loads(raw)
  self.assertEqual(len(outer['report']),6000)
  with self.assertRaises(ValueError):parse_response('extract',raw)
 def test_top_level_roundtrip(self):
  a=fixture();self.assertEqual(parse_response('extract',json.dumps(a)),a)
 def test_hard_quote_boundaries(self):
  a=fixture();a['evidence'][0]['quote']='x'*80;parse_response('extract',json.dumps(a))
  a['evidence'][0]['quote']='x'*81
  with self.assertRaises(ValueError):parse_response('extract',json.dumps(a))
 def test_object_larger_than_old_wrapper_cap_is_still_valid(self):
  a=fixture();a['contract']='x'*1400;a['secondary_tags']=['x'*40]*4
  proof=[{'file':'x'*80,'line':100000,'quote':'x'*80}]
  a['evidence']=proof*3
  for f in a['facts']:f['state']='known';f['evidence']=proof
  a['claims']=[{'kind':'source_fact','statement':'x'*160,'record_owner':'shared_state','owner_expression':'x'*32,'evidence':proof}]*4
  raw=json.dumps(a);self.assertGreater(len(raw),6000);self.assertEqual(parse_response('extract',raw),a)
 def test_reflection_is_typed_and_maintenance_remains_prose(self):
  e={'text':'Use evidence to separate retained work from its current consumer.','requires':['shared_lifetime'],'excludes':[]}
  self.assertEqual(parse_response('reflect',json.dumps(e)),e)
  self.assertEqual(parse_response('repair','{"report":"done"}'),{'report':'done'})
  with self.assertRaises(ValueError):parse_response('reflect',json.dumps({'report':json.dumps(e)}))
 def test_missing_or_extra_fields_are_rejected(self):
  a=fixture();del a['consistency']
  with self.assertRaises(ValueError):parse_response('extract',json.dumps(a))
  a=fixture();a['case_id']='forbidden'
  with self.assertRaises(ValueError):parse_response('extract',json.dumps(a))
 def test_full_actual_runner_extract_route_repair_score_handoff(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);cand=root/'candidate';(cand/'src').mkdir(parents=True)
   body='shared_value = 1 # original candidate source\nsecond_source_expression = 2\nthird_source_expression = 3\n';(cand/'src/unit.py').write_text(body)
   task=root/'task.md';task.write_text('Change a reported defect; preserve shared behavior.')
   analysis=fixture();calls=[]
   def command(phase,answer):
    def build(a,runtime,guard):
     event={'hook_event_name':'PostModelRequest','model':runner.ROLE[phase][0],'status':'completed','token_usage':{k:1 for k in ['input_tokens','output_tokens','cached_input_tokens','cache_write_input_tokens','reasoning_output_tokens','total_tokens']}}
     save(guard.meter/'ledger.json',{'started':1,'completed':1,'blocked_requests':0,'tool_attempts':1,'sessions':{phase:{'started':1,'completed':1,'blocked_tools':0}},'events':[{'event':{'hook_event_name':'PreModelRequest','model':runner.ROLE[phase][0]}},{'event':event}]})
     events=[{'type':'item.completed','item':{'type':'command_execution','exit_code':0,'aggregated_output':body}},{'type':'item.completed','item':{'type':'agent_message','text':json.dumps(answer)}},{'type':'turn.completed'}]
     script='import json\n'+''.join('print('+repr(json.dumps(e))+')\n' for e in events)
     return [sys.executable,'-B','-c',script]
    return build
   ex=runner.session({'slot':'extract','phase':'extract'},'fixture',case={'node':'/usr/bin/true'},candidate=cand,task=task,config={'seconds_per_session':3},run_dir=root/'extract',command_factory=command('extract',analysis))
   self.assertTrue(ex['preanalysis_valid']);self.assertTrue(ex['candidate_complete'])
   src={'src/unit.py':body,'TASK':task.read_text()}
   review={'contract_sha256':digest(analysis['contract']),'task_sha256':digest(task.read_text()),'sources_sha256':digest(canonical(src)),'reviewer':'execution_agent_visible_input_only','approved':True,'conflicts':[],'unknowns':[],'evidence':analysis['evidence'],'findings':['synthetic fixture only']}
   entry=freeze_entry({'text':'Preserve shared state.','requires':['shared_lifetime'],'excludes':[]},'T4')
   decision=route(analysis,src,[entry],task=task.read_text(),review=review);self.assertEqual(decision['condition'],'ROUTED')
   a=maintenance_prompt(task.read_text(),analysis['contract']);b=maintenance_prompt(task.read_text(),analysis['contract'],entry['text']);self.assertTrue(b.startswith(a))
   def score(final,out):calls.append(final);save(out/'raw.json',{'fixture_only':True});return {'fixture_only':True,'verdict':'FAKE'}
   rep=runner.session({'slot':'repair','phase':'repair'},b,case={'node':'/usr/bin/true'},candidate=cand,task=task,config={'seconds_per_session':3},run_dir=root/'repair',command_factory=command('repair',{'report':'fixture completed'}),score_fn=score)
   self.assertTrue(rep['scoring_admissible']);self.assertEqual(rep['scoring_status'],'COLLECTED');self.assertEqual(len(calls),1)
   self.assertEqual(inventory(cand),inventory(root/'repair/archive/final-candidate'))
 def test_native_command_role_schema_and_budget_flags(self):
  from guard_server import GuardServer
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);candidate=root/'candidate';candidate.mkdir();(candidate/'source.py').write_text('value=1')
   task=root/'task.md';task.write_text('fixture')
   from archive import Archive
   for phase in ['extract','repair','reflect']:
    archive=Archive(root/phase).prepare(candidate,task,'fixture',{})
    with GuardServer(root/(phase+'-ipc'),archive.root/'meter',phase,runner.ROLE[phase][2],runner.ROLE[phase][3]) as g:
     cmd=runner.command(phase,archive.run_dir,phase,{'node':'/usr/bin/true'},runtime=root/(phase+'-runtime'),socket_dir=g.directory,copy_auth=False)
     schema=cmd[cmd.index('/format.json')-1]
     self.assertEqual(Path(schema).name,{'extract':'extraction.schema.json','repair':'maintenance.schema.json','reflect':'reflection.schema.json'}[phase])
     self.assertEqual(cmd[cmd.index('-m')+1],runner.ROLE[phase][0])
     self.assertIn('model_reasoning_effort="'+runner.ROLE[phase][1]+'"',cmd)
     self.assertIn('model_providers.experiment_no_retry.request_max_retries=0',cmd)
 def test_real_long_quote_does_not_fit_schema(self):
  a=fixture();a['evidence'][0]['quote']=(P/'materials/D1/candidate/src/session.js').read_text().splitlines()[8]
  with self.assertRaises(ValueError):parse_response('extract',json.dumps(a))

if __name__=='__main__':unittest.main()
