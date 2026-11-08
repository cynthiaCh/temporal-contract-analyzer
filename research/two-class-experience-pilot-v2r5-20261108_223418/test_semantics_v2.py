import unittest,json
from pathlib import Path
from toolflow import route,digest,canonical,freeze_entry,validate_analysis
from feedback_v2 import checks,feedback
V=Path(__file__).resolve().parent.parent/'two-class-experience-pilot-20261108_200017'

class SemanticV2(unittest.TestCase):
 def test_real_false_contract_citations_do_not_override_veto(self):
  a=json.loads((V/'derived/T1/analysis.json').read_text());task=(V/'materials/T1/task.md').read_text();root=V/'materials/T1/candidate'
  sources={str(p.relative_to(root)):p.read_text() for p in root.rglob('*') if p.is_file() and p.suffix in ['.md','.py']};sources['TASK']=task
  review={'contract_sha256':digest(a['contract']),'task_sha256':digest(task),'sources_sha256':digest(canonical(sources)),
   'reviewer':'execution_agent_visible_input_only','approved':False,'conflicts':['reported defect was rewritten as required behavior'],'unknowns':[],'evidence':[{'file':'TASK','line':1,'quote':task.splitlines()[0]}],'findings':[]}
  library=json.loads((V/'frozen-library.json').read_text())
  self.assertEqual(route(a,sources,library,task=task,review=review)['reason'],'unresolved_semantic_conflict')
 def test_source_task_and_contract_hash_binding(self):
  a={'contract':'fixture','primary_class':'unknown','secondary_tags':[],'evidence':[],'facts':[]}
  r={'contract_sha256':'wrong','task_sha256':'wrong','sources_sha256':'wrong','reviewer':'execution_agent_visible_input_only','approved':True,'conflicts':[],'unknowns':[],'evidence':[],'findings':[]}
  self.assertEqual(route(a,{},[],task='task',review=r)['reason'],'semantic_review_input_drift')
 def test_real_checks_not_omitted(self):
  score=json.loads((V/'runs/D1-AUTO-1/archive/score/stdout.json').read_text());rows,unknown=checks(score)
  self.assertTrue(rows);self.assertFalse(unknown)
  matches=[r for r in rows if r['check']['id']=='no-live-at-entry']
  self.assertTrue(matches);self.assertFalse(matches[0]['check']['actual']);self.assertTrue(matches[0]['check']['expected'])
 def test_original_success_not_called_retained_when_lost(self):
  original={'observed_effects':{'one':True}};after={'observed_effects':{'one':False},'verdict':'FAIL','schedules':{}}
  r=feedback(original,[after],[{'effect':'one','expected':True,'description':'preserve'}])['runs'][0]
  self.assertEqual(len(r['original_successes']),1);self.assertEqual(r['actual_successes'],[])
  self.assertEqual(r['retained_original_successes'],[]);self.assertEqual(len(r['regressions']),1)
 def test_both_scorer_shapes(self):
  s={'schedules':{'a':{'checks':[{'passed':False,'actual':0,'expected':1}]},'b':{'assertions':[{'passed':True,'actual':1,'expected':1}]}}}
  r,u=checks(s);self.assertEqual(len(r),2);self.assertEqual(u,[])

class StructuredClaimsV2(unittest.TestCase):
 def test_same_call_claims_and_task_evidence(self):
  src={'TASK':'Repair a reported defect.'}
  a={'contract':'fixture','primary_class':'unknown','secondary_tags':[],'evidence':[],'facts':[],
     'claims':[{'kind':'reported_defect','statement':'reported behavior requires change','evidence':[{'file':'TASK','line':1,'quote':'Repair a reported defect.'}]}],
     'consistency':{'conflicts':[],'unknowns':[],'checked_dimensions':['negation']}}
  self.assertIsNone(validate_analysis(a,src))
  a['consistency']['conflicts']=['unresolved contradiction']
  self.assertIsNone(validate_analysis(a,src))  # semantic veto, not a free-text label, decides core conflict
 def test_unbound_claim_rejected(self):
  a={'contract':'fixture','primary_class':'unknown','secondary_tags':[],'evidence':[],'facts':[],
     'claims':[{'kind':'source_fact','statement':'unsupported','evidence':[]}],
     'consistency':{'conflicts':[],'unknowns':[],'checked_dimensions':[]}}
  self.assertEqual(validate_analysis(a,{}),'unbound_semantic_claim')

if __name__=='__main__':unittest.main()
