"""Zero-model JSX source binding and English rules/feedback boundary checks."""
import json,tempfile,unittest
from pathlib import Path
import runner
from citations import catalog,schema,normalize,fingerprint
from schema_validator import validate
from toolflow import PREDICATES
from handoff import make_schema,render
from locked_scope import revision_schema
from review_training_adapter import reference_view,INSTRUCTIONS
A=Path(__file__).resolve().parent

class ExtensionTests(unittest.TestCase):
 def test_jsx_source_body_read_is_recognized(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);body='import React from "react";\nconst originalVisit = null;\nexport default function Source(){return <div/>;}\n';(root/'Source.jsx').write_text(body)
   events=[{'type':'item.completed','item':{'type':'command_execution','exit_code':0,'command':'cat Source.jsx','aggregated_output':body}}]
   self.assertEqual(runner.source_proof(events,root)[0]['source'],'Source.jsx')
 def test_jsx_span_catalog_keeps_source_and_contract_unchanged(self):
  src={'Source.jsx':'const currentSource = <div/>;\n','TASK':'Repair the current component.'};cat=catalog(src);sid=cat['entries'][0]['id']
  raw={'contract':'Synthetic fixture; not a model result.','primary_class':'T1','secondary_tags':[],'evidence_ids':[sid],'facts':[{'predicate':p,'state':'unknown','evidence_ids':[]} for p in PREDICATES],'claims':[{'kind':'source_fact','statement':'Synthetic source-binding fixture.','record_owner':'unknown','owner_expression':'','evidence_ids':[sid]}],'consistency':{'conflicts':[],'unknowns':[],'checked_dimensions':['negation','conditions','event_order','ownership','history_vs_ui','cancellation_vs_completion']}}
  value,_=normalize(raw,src,json.loads((A/'extraction.schema.json').read_text()),fingerprint(cat));self.assertEqual(value['contract'],raw['contract']);self.assertTrue(any(e['file']=='Source.jsx' for e in cat['entries']))
 def test_rules_object_schema_has_no_repeated_full_body(self):
  ledger={'entries':[{'id':'E-source','kind':'source_fact'}],'constraints':[{'id':'C-preserve'}]};s=revision_schema(ledger,PREDICATES)
  self.assertEqual(set(s['properties']),{'rules','unresolved'});self.assertNotIn('text',s['properties']);self.assertIn('body',s['properties']['rules']['items']['properties']);self.assertNotIn('rule_quote',s['properties']['rules']['items']['properties'])
 def test_repeated_subtree_serialization_is_lossless(self):
  long={'value':'x'*600,'nested':[1,2,3]};obj={'one':long,'two':long,'expected':False,'unknown':None,'successes':['s'],'regressions':['r']};view=reference_view(obj)
  def expand(x):
   if isinstance(x,dict) and set(x)=={'$same'}:return expand(view['shared_values'][x['$same']])
   if isinstance(x,dict):return {k:expand(v) for k,v in x.items()}
   if isinstance(x,list):return [expand(v) for v in x]
   return x
  self.assertEqual(expand(view['payload']),obj)
 def test_rule_renderer_and_instructions_are_English(self):
  text=render({'rules':[{'category':'preservation','body':'Keep the accepted result.'}]});self.assertEqual(text,'R01 [Preservation]\nKeep the accepted result.\n');self.assertIn('English',INSTRUCTIONS)

if __name__=='__main__':unittest.main(verbosity=2)
