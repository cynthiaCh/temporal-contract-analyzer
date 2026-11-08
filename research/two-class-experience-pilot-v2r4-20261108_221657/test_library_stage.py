import unittest,tempfile,json
from pathlib import Path
import campaign
import runner

class LibraryStage(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.old_a=campaign.A;self.old_check=campaign.check
  campaign.A=self.root;campaign.check=lambda:None
 def tearDown(self):campaign.A=self.old_a;campaign.check=self.old_check;self.tmp.cleanup()
 def test_lock_empty_library_and_close_learning(self):
  (self.root/'development').mkdir();(self.root/'development/state.json').write_text(json.dumps({'new_reflection_needed':False}))
  campaign.lock_library();self.assertEqual(json.loads((self.root/'frozen-library.json').read_text()),[])
  lock=json.loads((self.root/'library-lock.json').read_text());runner.verify(lock['files'])
  for fn in [campaign.baselines,campaign.reflect,campaign.develop]:
   with self.assertRaises(AssertionError):fn()
  (self.root/'frozen-library.json').write_text('["changed"]')
  with self.assertRaises(ValueError):runner.verify(lock['files'])
 def test_test_extraction_requires_prior_library_lock(self):
  with self.assertRaises(AssertionError):campaign.extract('T1')

if __name__=='__main__':unittest.main()
