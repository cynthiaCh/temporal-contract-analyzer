import importlib.util,json,subprocess,sys,tempfile,unittest,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('incremental_queue',ROOT/'tools/tempoevo-docker/run_incremental.py');queue=importlib.util.module_from_spec(spec);spec.loader.exec_module(queue)
class IncrementalQueueTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'split.json').write_text('{}')
 def auth(self):return dict(execute_training=True,execute_new20_test=True,automatic_accept_new_experiences=True,reviewer='Silas',kind='explicit_user_authorization',review_is_automatic=True,split_sha256=hashlib.sha256((self.root/'split.json').read_bytes()).hexdigest())
 def write(self,x):(self.root/'authorization.json').write_text(json.dumps(x))
 def test_named_automatic_review_requires_explicit_authorization(self):
  a=self.auth();self.write(a);self.assertEqual(queue.check_authorization(self.root),a)
  for field,value in [('automatic_accept_new_experiences',False),('reviewer','another name'),('review_is_automatic',False),('execute_new20_test',False)]:
   a=self.auth();a[field]=value;self.write(a)
   with self.assertRaises(AssertionError):queue.check_authorization(self.root)
 def test_split_change_invalidates_execution_authorization(self):
  self.write(self.auth());(self.root/'split.json').write_text('{"changed":true}')
  with self.assertRaises(AssertionError):queue.check_authorization(self.root)
 def test_testing_command_cannot_carry_training_feedback_or_online_pool(self):
  (self.root/'plan.json').write_text(json.dumps(dict(benchmark='bench',solver_image='solver',grader_image='grader')))
  cmd=queue.arguments(self.root,Path('cases.csv'),self.root/'new-batch','testing',count=20)
  self.assertNotIn('--online-memory',cmd);self.assertNotIn('--training-recipe',cmd);self.assertNotIn('--public-checks-docs',cmd)
  self.assertEqual(cmd[cmd.index('--retrieval-profile')+1],'business-source-v1')
  train=queue.arguments(self.root,Path('train.csv'),self.root/'train-batch','learning')
  self.assertEqual(train[train.index('--training-recipe')+1],'v8-compatible-v1')
 def test_public_smoke_reports_valid_and_invalid_python_without_scorer(self):
  p=self.root/'main.py';p.write_text('value = 1\n')
  def invoke():return json.loads(subprocess.check_output([sys.executable,str(ROOT/'tools/tempoevo-docker/public_syntax.py'),str(self.root)],text=True))
  self.assertTrue(invoke()['passed']);p.write_text('def broken(\n');self.assertFalse(invoke()['passed'])
if __name__=='__main__':unittest.main()
