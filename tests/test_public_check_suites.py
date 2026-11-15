"""Public suites accept synthetic good APIs and reject synthetic faulty APIs."""
import json,os,shutil,subprocess,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(shutil.which('node'),'Node required')
class PublicSuites(unittest.TestCase):
 def test_all_six_public_suites_have_positive_and_negative_witnesses(self):
  for family in ['autosave','query','transfer','generator','review','subscription']:
   for buggy in [False,True]:
    with self.subTest(family=family,buggy=buggy),tempfile.TemporaryDirectory() as temp:
     root=Path(temp);cfg=root/'case.json';cfg.write_text(json.dumps(dict(manifest='synthetic/case.json',runtime='react18',family=family)))
     script=(ROOT/'tools/tempoevo-docker/public_checks.cjs').read_text().replace('/checks/case.json',str(cfg)).replace('/checks/public_frontend.cjs',str(ROOT/'tests/public_api_fixture.cjs'))
     main=root/'checks.cjs';main.write_text(script)
     p=subprocess.run(['node',str(main),str(root)],capture_output=True,text=True,timeout=15,env=dict(os.environ,PUBLIC_FIXTURE_BUG='1' if buggy else '0'))
     self.assertEqual(p.returncode,0,p.stderr);data=json.loads(p.stdout)
     self.assertNotEqual(data.get('valid'),False,data);self.assertEqual(data['passed'],not buggy,data)
