"""Actual historical tool-input corpus, plus a bounded read/write distinction."""
import json,unittest
from pathlib import Path
from read_policy import allowed,read_command
R=Path(__file__).resolve().parent.parent
BASES=['two-class-experience-pilot-20261108_200017','two-class-experience-pilot-v2-20261108_205648','two-class-experience-pilot-v2r1-20261108_215007']
def corpus():
 rows=[]
 for name in BASES:
  a=R/name
  for rec in json.loads((a/'actual-schedule.json').read_text()):
   if rec['phase']!='extract':continue
   ledger=json.loads((a/'runs'/rec['slot']/'archive/meter/ledger.json').read_text())
   for x in ledger['events']:
    if x['event'].get('hook_event_name')=='PreToolUse':rows.append((name,rec['slot'],x['event']))
 return rows

class ReadPolicyReal(unittest.TestCase):
 def test_all_real_extraction_read_commands(self):
  rows=corpus();self.assertTrue(rows)
  for name,slot,event in rows:
   with self.subTest(batch=name,slot=slot,command=event.get('tool_input')):self.assertTrue(read_command(event))
 def test_exact_previously_denied_command(self):
  cmd='rg -n "signal|offline|reconnect|unsubscribe|consum|cancel" README* docs 2>/dev/null'
  self.assertTrue(allowed(cmd));self.assertTrue(allowed(cmd+' || true'))
 def test_non_null_redirection_and_unsafe_operations_stay_blocked(self):
  for cmd in ['cat README.md 2>/tmp/out','cat README.md > src/output','cat /etc/passwd 2>/dev/null','rg --pre bash term .','cat README.md; rm src/a.py','python3 -c "print(1)"','curl https://example.com','cat $(pwd)/README.md','true arbitrary_argument']:
   with self.subTest(command=cmd):self.assertFalse(allowed(cmd))
 def test_safe_fallback_does_not_authorize_unsafe_next_command(self):
  self.assertTrue(allowed('rg term docs 2>/dev/null || true'))
  self.assertFalse(allowed('rg term docs 2>/dev/null || rm src/a.py'))
  self.assertFalse(read_command({'tool_name':'Bash','tool_input':{'command':'cat README.md','workdir':'/tmp'}}))

if __name__=='__main__':unittest.main()
