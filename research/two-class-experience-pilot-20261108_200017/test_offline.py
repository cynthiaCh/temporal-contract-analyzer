"""No models, no case scoring: tiny candidates, fake events/processes and local IPC."""
import importlib.util,json,os,shutil,subprocess,sys,tempfile,time,unittest
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent
sys.path.insert(0,str(A))
from archive import Archive,inventory,digest,save
from prompts import POLICY,OLD,adapt_maintenance_prompt,build_prompt
from runner import session,command,ROLE
from guard_server import GuardServer
from guard_client import forward

class OfflineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='archive-offline-');self.root=Path(self.tmp.name)
        self.candidate=self.root/'candidate';(self.candidate/'src').mkdir(parents=True)
        (self.candidate/'src/main.py').write_text('value = 1\n');(self.candidate/'business.patch').write_text('legitimate domain data\n')
        self.task=self.root/'task.md';self.task.write_text('Repair the candidate; validate relevant behavior.\n')
        self.prompt='原任务\n固定Contract\n结果格式说明'+OLD+'\n';self.case={'case':'offline-fixture','node':shutil.which('node') or '/usr/bin/true'}
    def tearDown(self):self.tmp.cleanup()
    def prepare(self,name='run'):
        return Archive(self.root/name).prepare(self.candidate,self.task,adapt_maintenance_prompt(self.prompt),{'model':'fixed','effort':'medium'})
    def fake(self,body):
        # The launched executable is Python interpreting a local fixture, never codex.
        def build(a,runtime,guard):return [sys.executable,'-B','-u','-c',body]
        return build
    def run_fake(self,name,body,**kwargs):
        return session({'slot':name,'phase':'repair','condition':'AUTO'},adapt_maintenance_prompt(self.prompt),case=self.case,candidate=self.candidate,task=self.task,config={'seconds_per_session':kwargs.pop('seconds',2)},run_dir=self.root/name,command_factory=self.fake(body),**kwargs)
    def test_no_change(self):
        a=self.prepare();before=inventory(a.original);state=a.finalize(model_stopped=True)
        self.assertEqual(state['status'],'OK');self.assertEqual(inventory(a.original),before);self.assertEqual(inventory(a.final),before)
        self.assertEqual((a.root/'patch.diff').read_bytes(),b'');self.assertEqual(json.loads((a.root/'diff-result.json').read_text())['exit_code'],0)
    def test_changes_add_delete_patch_applies(self):
        a=self.prepare();before=inventory(a.original)
        (a.workspace/'src/main.py').write_text('value = 2\n');(a.workspace/'business.patch').unlink();(a.workspace/'new.txt').write_text('new file\n')
        final=inventory(a.workspace);state=a.finalize(model_stopped=True);self.assertEqual(state['status'],'OK')
        self.assertEqual(inventory(a.original),before);self.assertEqual(inventory(a.final),final);self.assertEqual(inventory(a.workspace),final)
        changes=json.loads((a.root/'file-changes.json').read_text());self.assertIn('new.txt',changes['added']);self.assertIn('business.patch',changes['deleted'])
        self.assertEqual(json.loads((a.root/'diff-result.json').read_text())['exit_code'],1)
        applied=self.root/'apply';shutil.copytree(a.original,applied)
        z=subprocess.run(['patch','--batch','-p1','-d',str(applied),'-i',str(a.root/'patch.diff')],capture_output=True,text=True)
        self.assertEqual(z.returncode,0,z.stdout+z.stderr);self.assertEqual(inventory(applied),final)
    def test_extras_preserved_not_classified_by_suffix(self):
        a=self.prepare();(a.workspace/'backup').mkdir();(a.workspace/'backup/data.json').write_text('{}');(a.workspace/'extra.patch').write_text('not necessarily an archive\n')
        (a.root/'events.jsonl').write_text(json.dumps({'type':'item.completed','item':{'id':'fixture-write','type':'file_change','changes':[{'path':'/workspace/extra.patch'}]}})+'\n')
        state=a.finalize(model_stopped=True);self.assertEqual(state['status'],'OK')
        entry=next(x for x in json.loads((a.root/'file-changes.json').read_text())['extra_files'] if x['path']=='extra.patch');self.assertEqual(entry['event_evidence'][0]['item_id'],'fixture-write')
        for rel in ['business.patch','extra.patch','backup/data.json']:self.assertTrue((a.final/rel).is_file());self.assertTrue((a.workspace/rel).is_file())
        self.assertTrue(all(x['classification'].startswith('unclassified') for x in json.loads((a.root/'file-changes.json').read_text())['extra_files']))
    def test_timeout_keeps_partial_events_and_patch(self):
        body="import json,time,sys; from pathlib import Path; Path('src/main.py').write_text('partial = True\\n'); print(json.dumps({'type':'item.completed','item':{'type':'command_execution','exit_code':0,'aggregated_output':'partial tool output'}}),flush=True); print('fixture stderr',file=sys.stderr,flush=True); time.sleep(5)"
        rec=self.run_fake('timeout',body,seconds=.3);a=self.root/'timeout/archive'
        self.assertEqual(rec['failure_class'],'model_resource_limit');self.assertEqual(rec['stop_reason'],'timeout');self.assertEqual(rec['archive_status']['status'],'OK')
        self.assertIn('partial = True',(a/'patch.diff').read_text());self.assertIn('partial tool output',(a/'events.jsonl').read_text());self.assertIn('fixture stderr',(a/'stderr.log').read_text())
        self.assertFalse(json.loads((a/'collection.json').read_text())['answer_present']);self.assertIsNone(json.loads((a/'usage.json').read_text())['total_usage'])
    def test_abnormal_exit_and_diff_error_do_not_mask_model_failure(self):
        calls=[];scores=[]
        def broken(cmd,**kwargs):calls.append(cmd);kwargs['stderr'].write(b'fixture diff failed\n');return subprocess.CompletedProcess(cmd,2)
        rec=self.run_fake('abnormal',"import sys; from pathlib import Path; Path('src/main.py').write_text('changed = True\\n'); print('{invalid-json',flush=True); sys.exit(7)",diff_runner=broken,score_fn=lambda *x:scores.append(x))
        a=self.root/'abnormal/archive';self.assertEqual(rec['exit_code'],7);self.assertEqual(rec['failure_class'],'model_or_cli_abnormal_exit')
        self.assertEqual(rec['archive_status']['status'],'ERROR');self.assertTrue(rec['archive_failure_requires_stop']);self.assertEqual(rec['archive_stop_reason'],'archive_error');self.assertEqual(len(calls),1);self.assertEqual(scores,[])
        self.assertEqual(rec['scoring_status'],'BLOCKED_ARCHIVE_ERROR_OR_NON_REPAIR');self.assertTrue((a/'final-candidate/src/main.py').exists());self.assertEqual(json.loads((a/'diff-result.json').read_text())['status'],'ERROR')
        self.assertIn('fixture diff failed',(a/'diff.stderr').read_text());self.assertIn('{invalid-json',(a/'events.jsonl').read_text())
    def test_missing_diff_executable_records_error(self):
        a=self.prepare()
        def broken(*args,**kwargs):raise FileNotFoundError('fixture unavailable diff')
        before=inventory(a.workspace);state=a.finalize(model_stopped=True,diff_runner=broken)
        self.assertEqual(state['status'],'ERROR');self.assertTrue(any(e['stage']=='diff' for e in state['errors']));self.assertEqual(inventory(a.workspace),before);self.assertIsNone(json.loads((a.root/'diff-result.json').read_text())['exit_code'])
    def test_missing_cli_still_snapshots(self):
        rec=session({'slot':'missing-cli','phase':'repair'},adapt_maintenance_prompt(self.prompt),case=self.case,candidate=self.candidate,task=self.task,config={},run_dir=self.root/'missing-cli',command_factory=lambda *x:['/nonexistent/offline-fixture'])
        self.assertEqual(rec['failure_class'],'runner_exception');self.assertEqual(rec['archive_status']['status'],'OK');self.assertTrue(Path(rec['final_candidate']).is_dir())
    def test_completed_answer_and_explicit_trusted_score_boundary(self):
        # This callback only copies a PREEXISTING fake score, never runs an oracle.
        fixture=self.root/'existing-score.json';save(fixture,{'fixture_only':True,'verdict':'FAKE'})
        seen=[]
        def copy_existing(final,dest):
            seen.append(final);self.assertNotEqual(final,self.root/'completed/workspace');self.assertEqual(inventory(final),inventory(self.root/'completed/workspace'))
            shutil.copyfile(fixture,dest/'score.json');return {'fixture_only':True,'verdict':'FAKE'}
        body="import json; print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':json.dumps({'report':'fixture complete'})}})); print(json.dumps({'type':'turn.completed'}))"
        rec=self.run_fake('completed',body,score_fn=copy_existing);a=self.root/'completed/archive'
        self.assertEqual(len(seen),1);self.assertEqual(rec['scoring_status'],'COLLECTED');self.assertTrue(rec['scored_candidate_unchanged']);self.assertTrue(rec['output_format_valid'])
        self.assertEqual(json.loads((a/'raw-answer.txt').read_text()),{'report':'fixture complete'});self.assertEqual(json.loads((a/'score/score.json').read_text())['verdict'],'FAKE')
    def test_score_mutation_is_detected_without_cleanup(self):
        def untrusted(final,dest):(final/'new.txt').write_text('scorer changed it');return {'fixture_only':True}
        rec=self.run_fake('mutating-score','',score_fn=untrusted)
        self.assertEqual(rec['scoring_status'],'ERROR');self.assertFalse(rec['scored_candidate_unchanged']);self.assertTrue(Path(rec['final_candidate'],'new.txt').exists())
    def test_same_prompt_policy_both_arms_historical_bytes_preserved(self):
        H=A.parents[1]/'research/transfer-reflection-crosslang-20261108_202000';exp=(H/'NEW_EXPERIENCE.md').read_text()
        for source in (H/'prompts').glob('*/AUTO.md'):
            old=source.read_text();auto=build_prompt(old);enhanced=build_prompt(old,exp)
            self.assertEqual(enhanced,auto+'\n\n'+exp);self.assertEqual(auto.count(POLICY),1);self.assertNotIn(OLD,auto)
            self.assertEqual(auto.replace('。\n\n'+POLICY,OLD),old)
        for source in (H/'runs').glob('*/actual-prompt.md'):
            if OLD not in source.read_text():continue
            old=source.read_text();self.assertEqual(adapt_maintenance_prompt(old).replace('。\n\n'+POLICY,OLD),old)
    def test_guard_ipc_accounting_and_legal_shell_tools(self):
        with GuardServer(self.root/'ipc',self.root/'meter','fixture',2,'maintenance') as g:
            for i in range(2):
                self.assertFalse(forward({'hook_event_name':'PreModelRequest','model':'gpt-5.6-terra'},str(g.directory/'hook.sock'))['deny'])
                self.assertFalse(forward({'hook_event_name':'PreToolUse','tool_name':'Bash','tool_input':{'command':'for f in src/*; do cp "$f" /tmp/test; diff "$f" /tmp/test; done'}},str(g.directory/'hook.sock'))['deny'])
                self.assertFalse(forward({'hook_event_name':'PostModelRequest','status':'completed','token_usage':{'input_tokens':3,'output_tokens':1}},str(g.directory/'hook.sock'))['deny'])
            self.assertTrue(forward({'hook_event_name':'PreModelRequest'},str(g.directory/'hook.sock'))['deny'])
            ledger=json.loads((g.meter/'ledger.json').read_text());self.assertEqual(ledger['started'],2);self.assertEqual(ledger['blocked_requests'],1);self.assertEqual(ledger['tool_attempts'],2)
    def test_namespace_archive_invisible_with_legal_read_edit_loop(self):
        from runner import backend
        a=self.prepare();runtime=self.root/'runtime';runtime.mkdir()
        with GuardServer(runtime/'hook',a.root/'meter','offline',24,'maintenance') as g:
            cmd=command('offline',a.run_dir,'repair',self.case,runtime=runtime,socket_dir=g.directory,copy_auth=False)
            # Only run the exact namespace prefix; never execute its Codex command.
            prefix=cmd[:cmd.index('--')+1]
            self.assertNotIn('/output',prefix);self.assertNotIn('/meter',prefix);self.assertNotIn(str(a.root),prefix)
            body="""from pathlib import Path
import json,socket,subprocess
assert not Path('/output').exists() and not Path('/meter').exists() and not Path('/archive').exists()
assert not Path('/workspace/../archive').exists()
assert not Path("""+repr(str(a.root))+""").exists()
assert not Path('/workspace/archive-status.json').exists()
subprocess.run(['/bin/bash','-c','for f in /workspace/src/*; do cat "$f"; cp "$f" /tmp/copy; diff "$f" /tmp/copy; done'],check=True)
Path('/workspace/src/main.py').write_text('edited = True\\n')
s=socket.socket(socket.AF_UNIX);s.connect('/hook-control/hook.sock');s.sendall(json.dumps({'hook_event_name':'PreToolUse','tool_name':'Bash','tool_input':{'command':'for f in src/*; do cat "$f"; done'}}).encode()+b'\\n');assert not json.loads(s.recv(1024))['deny'];s.close()
print('archive hidden; legal read/edit/loop and hook IPC work')
"""
            z=subprocess.run(prefix+['/usr/bin/python3','-B','-c',body],capture_output=True,text=True,timeout=20)
            self.assertEqual(z.returncode,0,z.stderr);self.assertIn('archive hidden',z.stdout)
            # Parameter and tool flags remain the historical role settings.
            self.assertEqual(cmd[cmd.index('-m')+1],'gpt-5.6-terra');self.assertIn('model_reasoning_effort="low"',cmd)
            self.assertIn('code_mode_host',cmd);self.assertIn('model_providers.experiment_no_retry.request_max_retries=0',cmd)
    def test_symlink_binary_modes_retained(self):
        a=self.prepare();(a.workspace/'data.bin').write_bytes(b'\x00\xff');(a.workspace/'link').symlink_to('src/main.py');(a.workspace/'src/main.py').chmod(0o600)
        before=inventory(a.workspace);state=a.finalize(model_stopped=True);self.assertEqual(state['status'],'OK');self.assertEqual(inventory(a.final),before);self.assertTrue((a.final/'link').is_symlink())
    def test_native_execution_requires_explicit_opt_in_and_no_larger_limits(self):
        with self.assertRaises(RuntimeError):session({'slot':'disabled','phase':'repair'},'p',case=self.case,candidate=self.candidate,task=self.task,config={},run_dir=self.root/'disabled')
        with self.assertRaises(ValueError):session({'slot':'larger','phase':'repair'},'p',case=self.case,candidate=self.candidate,task=self.task,config={'seconds_per_session':601},run_dir=self.root/'larger',command_factory=self.fake(''))
        self.assertEqual(ROLE['repair'],('gpt-5.6-terra','low',24,'maintenance'));self.assertEqual(ROLE['extract'][2],12);self.assertEqual(ROLE['reflect'][2],12)
    def test_no_recursive_snapshot_layout(self):
        with self.assertRaises(ValueError):Archive(self.candidate/'bad-run').prepare(self.candidate,self.task,'p',{})

if __name__=='__main__':
    start=time.monotonic();suite=unittest.defaultTestLoader.loadTestsFromTestCase(OfflineTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    save(A/'offline-validation.json',{'status':'PASS' if result.wasSuccessful() else 'FAIL','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'seconds':time.monotonic()-start,'experiment_model_calls':0,'maintenance_model_executions':0,'case_score_reruns':0,'fixtures':'temporary tiny candidates, local fake CLI/event data; one existing fake score copied only','bwrap_namespace_executed_without_codex':True,'synthetic_ledger_not_real_usage':True})
    sys.exit(0 if result.wasSuccessful() else 1)
