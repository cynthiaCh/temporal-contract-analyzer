"""Synthetic fixtures and exact old failure replay, zero new model calls."""
import copy,json,unittest,tempfile
from pathlib import Path
from citations import catalog,schema,normalize,fingerprint,verify_catalog
from schema_validator import validate
from toolflow import validate_analysis,PREDICATES
from archive import sha
A=Path(__file__).resolve().parent

def read(p):return json.loads(Path(p).read_text())
def source(alias):
 root=A/'materials'/alias/'candidate'
 result={str(p.relative_to(root)):p.read_text() for p in root.rglob('*') if p.is_file() and p.suffix in ['.md','.js','.py']}
 result['TASK']=(A/'materials'/alias/'task.md').read_text();return result
def fixture(cat):
 # Synthetic complete shape, no claim of semantic endorsement.
 sid=cat['entries'][0]['id']
 return {'contract':'Synthetic fixture, not a model Contract.','primary_class':'T1','secondary_tags':[],
  'evidence_ids':[sid],'facts':[{'predicate':p,'state':'unknown','evidence_ids':[]} for p in PREDICATES],
  'claims':[{'kind':'source_fact','statement':'Synthetic fixture.','record_owner':'unknown','owner_expression':'','evidence_ids':[sid]}],
  'consistency':{'conflicts':[],'unknowns':[],'checked_dimensions':['negation','conditions','event_order','ownership','history_vs_ui','cancellation_vs_completion']}}

class CitationTests(unittest.TestCase):
 def test_catalog_deterministic_and_exact_spans(self):
  for alias in ['D','T']:
   src=source(alias);cat=catalog(src)
   self.assertEqual(cat,catalog(dict(reversed(list(src.items())))))
   self.assertEqual(cat,read(A/'materials'/alias/'source-catalog.json'))
   for row in cat['entries']:
    line=src[row['file']].splitlines()[row['line']-1]
    self.assertEqual(row['quote'],line[row['start_column']:row['end_column']]);self.assertLessEqual(len(row['quote']),80)
 def test_normalization_only_changes_reference_representation(self):
  src=source('D');cat=catalog(src);raw=fixture(cat);before=copy.deepcopy(raw)
  derived,meta=normalize(raw,src,read(A/'extraction.schema.json'),fingerprint(cat))
  self.assertEqual(raw,before);self.assertEqual(derived['contract'],raw['contract'])
  self.assertEqual(derived['primary_class'],raw['primary_class'])
  self.assertEqual([f['state'] for f in derived['facts']],[f['state'] for f in raw['facts']])
  self.assertIsNone(validate_analysis(derived,src));self.assertFalse(meta['semantic_entailment_checked'])
 def test_unknown_or_prose_id_rejected(self):
  src=source('D');cat=catalog(src)
  for invalid in ['S999999','README.md:47','quote copied here']:
   raw=fixture(cat);raw['evidence_ids']=[invalid]
   with self.assertRaises(ValueError):normalize(raw,src,read(A/'extraction.schema.json'),fingerprint(cat))
 def test_old_failed_output_not_rebound_or_salvaged(self):
  src=source('D');cat=catalog(src);raw=read(A/'audit-v1/preanalysis-object.json')
  with self.assertRaises(ValueError):normalize(raw,src,read(A/'extraction.schema.json'),fingerprint(cat))
  old=read(A/'audit-v1/source-evidence-audit.json')
  self.assertEqual(len(old['binding_errors']),2)
  self.assertEqual(old['binding_errors'][0]['exact_matching_lines_for_audit_only'],[47])
  self.assertEqual(old['binding_errors'][1]['exact_matching_lines_for_audit_only'],[])
 def test_shifted_source_and_digest_tamper_fail(self):
  src=source('D');cat=catalog(src);raw=fixture(cat);changed=copy.deepcopy(src);changed['README.md']='inserted\n'+changed['README.md']
  with self.assertRaises(ValueError):normalize(raw,changed,read(A/'extraction.schema.json'),fingerprint(cat))
  with self.assertRaises(ValueError):normalize(raw,src,read(A/'extraction.schema.json'),'0'*64)
  with self.assertRaises(ValueError):verify_catalog(cat,changed)
 def test_partial_or_string_encoded_object_rejected(self):
  cat=catalog(source('D'));raw=fixture(cat)
  with self.assertRaises(ValueError):json.loads(json.dumps(raw)[:-1])
  with self.assertRaises(ValueError):normalize(json.dumps(raw),source('D'),read(A/'extraction.schema.json'),fingerprint(cat))
 def test_existing_schema_has_no_quote_copying_fields(self):
  cat=catalog(source('D'));s=schema(cat,read(A/'extraction.schema.json'))
  for props in [s['properties'],s['properties']['facts']['items']['properties'],s['properties']['claims']['items']['properties']]:
   self.assertNotIn('evidence',props);self.assertIn('evidence_ids',props)
 def test_valid_id_does_not_automatically_certify_fact(self):
  src=source('D');cat=catalog(src);raw=fixture(cat)
  raw['facts'][0]['state']='known'  # Still lacks any supporting IDs.
  derived,_=normalize(raw,src,read(A/'extraction.schema.json'),fingerprint(cat))
  self.assertIsNotNone(validate_analysis(derived,src))
 def test_runner_normalizes_only_after_raw_archive(self):
  import sys,runner
  from archive import save
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);candidate=root/'candidate';candidate.mkdir()
   (candidate/'unit.py').write_text('first_source_line_for_evidence = 1\nsecond_source_line_for_evidence = 2\nthird_source_line_for_evidence = 3\n')
   task=root/'task.md';task.write_text('Synthetic read-only extraction fixture.\n')
   src={'unit.py':(candidate/'unit.py').read_text(),'TASK':task.read_text()};cat=catalog(src);raw=fixture(cat)
   fmt=root/'schema.json';save(fmt,schema(cat,read(A/'extraction.schema.json')))
   def factory(a,runtime,guard):
    events=[{'type':'item.completed','item':{'type':'command_execution','exit_code':0,'aggregated_output':src['unit.py']}},
            {'type':'item.completed','item':{'type':'agent_message','text':json.dumps(raw)}},{'type':'turn.completed'}]
    posts=[{'event':{'hook_event_name':'PreModelRequest','model':'gpt-6-sol'}},
           {'event':{'hook_event_name':'PostModelRequest','model':'gpt-6-sol','status':'completed','token_usage':None}}]
    save(guard.meter/'ledger.json',{'started':1,'completed':1,'events':posts,'sessions':{'fixture-extract':{'started':1,'completed':1,'blocked_requests':0,'tool_attempts':1,'blocked_tools':0}}})
    text=''.join(json.dumps(e)+'\n' for e in events)
    return [sys.executable,'-B','-c','import sys;sys.stdout.write('+repr(text)+')']
   rec=runner.session({'slot':'fixture-extract','phase':'extract'},'Synthetic fixture',case={'extraction_schema':str(fmt),'source_catalog_sha256':fingerprint(cat)},
      candidate=candidate,task=task,config={'seconds_per_session':5},run_dir=root/'run',command_factory=factory)
   self.assertTrue(rec['preanalysis_valid']);arc=root/'run/archive'
   self.assertEqual(read(arc/'raw-analysis-object.json'),raw)
   self.assertEqual(json.loads((arc/'raw-answer.txt').read_text()),raw)
   self.assertEqual(read(arc/'analysis.json')['contract'],raw['contract'])
   self.assertFalse(read(arc/'analysis-derivation.json')['statement_contract_category_or_fact_state_modified'])
 def test_exact_v1_failure_runner_replay_is_preserved_and_rejected(self):
  import sys,runner
  from archive import save
  old=A.parent/'transfer-progress-one-pair-pilot-20261109_085552/runs/session-01/archive'
  c=read(A/'cases.json')[0]
  with tempfile.TemporaryDirectory() as tmp:
   def factory(a,runtime,guard):
    ledger=read(old/'meter/ledger.json');ledger['sessions']={'fixture-old':next(iter(ledger['sessions'].values()))}
    save(guard.meter/'ledger.json',ledger)
    return [sys.executable,'-B','-c','import sys;sys.stdout.write('+repr((old/'events.jsonl').read_text())+')']
   rec=runner.session({'slot':'fixture-old','phase':'extract'},'Exact v1 replay; no model',case=c,candidate=A/'materials/D/candidate',task=A/'materials/D/task.md',
       config={'seconds_per_session':5},run_dir=Path(tmp)/'run',command_factory=factory)
   arc=Path(tmp)/'run/archive'
   self.assertEqual((arc/'raw-answer.txt').read_bytes(),(old/'raw-answer.txt').read_bytes())
   self.assertFalse(rec['preanalysis_valid']);self.assertFalse((arc/'analysis.json').exists())
   self.assertEqual(rec['archive_status']['status'],'OK')

if __name__=='__main__':unittest.main(verbosity=2)
