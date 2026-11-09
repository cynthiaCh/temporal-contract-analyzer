"""Small offline denominator and duplicate-integrity regressions."""
import copy,io,json,unittest
import analyze as a
from read_inventory import array_items

class AnalysisTests(unittest.TestCase):
 def setUp(self):
  self.r={'model':'gpt-5.6-terra','case_id':'synthetic-fixture','status':'COMPLETED','verdict':'PASS','receipt_sha256':'identical','path':'/synthetic/one/run.json','started_at_utc':'2026-01-01T00:00:00Z'}
  self.s={'case_id':'synthetic-fixture','verdict':'PASS','runtime_error_schedules':[],'receipt_sha256':'score1'}
 def valid(self,r=None,s=None,outer=None):return a.evaluate(r or self.r,[('/synthetic/score.json',s or self.s)],[outer or {}])[0]
 def test_contaminated_pass_is_not_admitted(self):
  self.r['status']='CONTAMINATED';self.assertFalse(self.valid())
 def test_outer_contamination_is_not_overridden_by_inner_pass(self):self.assertFalse(self.valid(outer={'status':'CONTAMINATED'}))
 def test_normal_behavior_failure_is_valid(self):
  self.r['verdict']=self.s['verdict']='UNDERREACH';self.assertTrue(self.valid())
 def test_missing_or_mismatched_score_is_not_behavior_failure(self):
  self.assertFalse(a.evaluate(self.r,[(None,None)],[])[0]);self.s['verdict']='UNDERREACH';self.assertFalse(self.valid())
 def test_explicit_invalid_and_runtime_error_are_excluded(self):
  self.r['valid_scored']=False;self.assertFalse(self.valid());del self.r['valid_scored'];self.s['runtime_error_schedules']=['fixture'];self.assertFalse(self.valid())
 def test_completed_runtime_failure_is_not_automatically_infrastructure(self):
  self.r['verdict']=self.s['verdict']='UNDERREACH';self.s['runtime_error_schedules']=['fixture'];self.assertTrue(self.valid())
 def test_fake_model_is_excluded(self):self.r['model']='protocol-stub-no-model';self.assertFalse(self.valid())
 def test_exact_copy_needs_execution_identity(self):
  r=copy.deepcopy(self.r);r['path']='/synthetic/two/run.json';self.assertEqual(a.duplicate_key(r),a.duplicate_key(self.r))
  self.r.pop('started_at_utc');r.pop('started_at_utc');self.assertNotEqual(a.duplicate_key(r),a.duplicate_key(self.r))
 def test_zero_denominator_stays_null(self):
  r={**self.r,'source_unit':'','raw_copies':1,'valid_score':False,'effort':'low','condition':'latent-maintenance','variant':'ungranted','workflow_profile':'fixture','timeout_seconds':600,'version_hash':None}
  row=a.aggregate([r],['case_id'])[0];self.assertIsNone(row['pass_rate']);self.assertIsNone(a.rank([row])[0]['rank_easiest'])
 def test_stream_handles_nested_unicode_and_chunk_boundaries(self):
  original=[{'a':[1,{'b':'sample'+chr(0x4e2d)}]},{'long':'x'*1100000}]
  self.assertEqual(list(array_items(io.StringIO(json.dumps(original)))),original)
 def test_stream_rejects_incomplete_array(self):
  with self.assertRaises(ValueError):list(array_items(io.StringIO('[{"a":1}')))

if __name__=='__main__':unittest.main(verbosity=2)
