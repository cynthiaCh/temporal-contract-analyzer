"""Synthetic integration checks, never live model measurements."""
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import build_opener, ProxyHandler, Request

from temporal_contract_analyzer import archive, hub
from temporal_contract_analyzer.core import EvidenceError
from temporal_contract_analyzer.case_catalog import local_models
from temporal_contract_analyzer.workbench import Workbench, discover_codex, capture, file_modes, write_files


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.code = self.root/'candidate'; self.code.mkdir()
        (self.code/'panel.py').write_text('async def refresh():\n    await fetch()\n    publish()\n')
        (self.code/'README.md').write_text('Synthetic candidate-visible requirement.\n')
        self.fake = self.root/'fake-codex'
        self.fake.write_text('#!/usr/bin/python3\n' + '''
import json, pathlib, sys, time
args=sys.argv[1:]
if args==['--version']:
    print('SYNTHETIC_VERIFICATION_ONLY 0.0')
    sys.exit(0)
prompt=sys.stdin.read()
root=pathlib.Path(args[args.index('-C')+1])
answer=pathlib.Path(args[args.index('-o')+1])
print(json.dumps({'type':'thread.started','thread_id':'SYNTHETIC_VERIFICATION_ONLY'}), flush=True)
if 'SLEEP_TEST' in prompt: time.sleep(30)
if 'FAIL_TEST' in prompt:
    print('synthetic CLI error', file=sys.stderr)
    sys.exit(2)
if 'NO_TURN_TEST' in prompt: sys.exit(0)
assert root.joinpath('panel.py').read_text().startswith('async def refresh')
if args[args.index('--sandbox')+1]=='workspace-write':
    root.joinpath('panel.py').write_text('# SYNTHETIC_TEST_CHANGE\\n')
answer.write_text('SYNTHETIC_VERIFICATION_ONLY: ' + ('with report' if '<temporal-review-material>' in prompt else 'without report'))
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':11,'output_tokens':3}}), flush=True)
''')
        self.fake.chmod(0o755)
        env = patch.dict(os.environ, {'TCA_CONFIG':str(self.root/'config.json'),'CODEX_HOME':str(self.root/'codex-home')})
        env.start(); self.addCleanup(env.stop)
        self.workbench = Workbench(self.root/'reports', codex=str(self.fake))
        self.addCleanup(self.workbench.close)

    def prepare(self, **kwargs):
        data = dict(candidate=str(self.code), task='Review the code.', model='SYNTHETIC_VERIFICATION_ONLY',
                    conditions=['none','review'], mode='workspace-write', timeout=10)
        data.update(kwargs)
        return self.workbench.prepare(data)

    def wait(self, experiment_id):
        self.workbench.thread.join(15)
        self.assertFalse(self.workbench.thread.is_alive())
        return self.workbench.read(experiment_id)

    def test_frozen_layers_and_independent_jobs_start_from_identical_input(self):
        run = self.prepare(repeats=2)
        self.assertEqual(len(run['jobs']),4)
        self.assertEqual(run['status'],'prepared')
        self.assertEqual(self.workbench.artifact(run['id'],'j-001','report.md')['text'],'')
        report = archive.layer_text(run['report_id'],'review',self.workbench.store)
        self.assertEqual(self.workbench.artifact(run['id'],'j-002','report.md')['text'],report)
        self.assertIn(report,self.workbench.artifact(run['id'],'j-002','prompt.md')['text'])
        self.assertFalse((self.workbench.folder(run['id'])/'jobs/j-001/workspace').exists())
        (self.code/'panel.py').write_text('ORIGINAL CHANGED AFTER FREEZE')
        self.workbench.start(run['id'])
        finished = self.wait(run['id'])
        self.assertEqual(finished['status'],'completed')
        for job in finished['jobs']:
            self.assertEqual(job['status'],'completed')
            self.assertEqual(job['changed_files'],1)
            self.assertEqual(job['delivery'],'stdin_file_attached')
            self.assertEqual(job['task_success'],'unscored')
            self.assertEqual(job['usage']['input_tokens'],11)
            self.assertIn('--ignore-user-config',job['command'])
            self.assertNotIn('--dangerously-bypass-approvals-and-sandbox',job['command'])
        self.assertEqual((self.code/'panel.py').read_text(),'ORIGINAL CHANGED AFTER FREEZE')
        self.assertEqual(finished['codex_cli_version'],'SYNTHETIC_VERIFICATION_ONLY 0.0')
        with self.assertRaises(EvidenceError): self.workbench.start(run['id'])

    def test_reject_changed_prompt_and_symlinks_and_partial_input(self):
        run = self.prepare()
        (self.workbench.folder(run['id'])/'jobs/j-001/prompt.md').write_text('changed')
        with self.assertRaisesRegex(EvidenceError,'提示词'): self.workbench.start(run['id'])
        (self.code/'link.py').symlink_to(self.code/'panel.py')
        with self.assertRaisesRegex(EvidenceError,'普通文件'): self.prepare()
        (self.code/'link.py').unlink()
        (self.code/'panel.py').write_text('def invalid(')
        with self.assertRaisesRegex(EvidenceError,'未完整解析'): self.prepare()

    def test_preserves_executable_files_in_each_workspace(self):
        script=self.code/'run.sh'
        script.write_text('#!/bin/sh\nexit 0\n');script.chmod(0o755)
        run=self.prepare(conditions=['none'])
        self.assertEqual(run['file_modes']['run.sh'],0o755)
        self.workbench.start(run['id']);self.wait(run['id'])
        self.assertTrue((self.workbench.folder(run['id'])/'jobs/j-001/workspace/run.sh').stat().st_mode & 0o111)

    def test_hidden_files_excluded_and_invalid_conditions_rejected(self):
        (self.code/'.env').write_text('SYNTHETIC_SECRET')
        run = self.prepare()
        self.assertNotIn('.env',run['input_files'])
        self.assertIn('.env',run['skipped'])
        for conditions in ([], ['none','none'], ['full'], [None]):
            with self.subTest(conditions=conditions), self.assertRaises(EvidenceError): self.prepare(conditions=conditions)
        with self.assertRaises(EvidenceError): self.prepare(candidate=str(self.workbench.store.parent))
        for name in ('../manifest.json','workspace/panel.py'):
            with self.assertRaises(EvidenceError): self.workbench.artifact(run['id'],'j-001',name)

    def test_zero_exit_without_completed_turn_and_cli_errors_are_failures(self):
        for task in ('NO_TURN_TEST','FAIL_TEST'):
            run = self.prepare(task=task,conditions=['none'])
            self.workbench.start(run['id'])
            finished = self.wait(run['id'])
            self.assertEqual(finished['status'],'failed')
            self.assertFalse(finished['jobs'][0]['turn_completed'])
            self.assertEqual(finished['jobs'][0]['task_success'],'unscored')

    def test_cancellation_stops_process_and_prevents_queued_launch(self):
        run = self.prepare(task='SLEEP_TEST')
        self.workbench.start(run['id'])
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            if self.workbench.artifact(run['id'],'j-001','events.jsonl')['text']: break
            time.sleep(.05)
        other=Workbench(self.workbench.store,codex=str(self.fake))
        second=other.prepare(dict(candidate=str(self.code),task='review',model='SYNTHETIC_VERIFICATION_ONLY',conditions=['none']))
        with self.assertRaisesRegex(EvidenceError,'已有实验'): other.start(second['id'])
        self.workbench.cancel(run['id'])
        finished=self.wait(run['id'])
        self.assertEqual(finished['status'],'cancelled')
        self.assertEqual([j['status'] for j in finished['jobs']],['cancelled','cancelled'])
        self.assertFalse((self.workbench.folder(run['id'])/'jobs/j-002/workspace').exists())

    def test_timeout_retains_observations_without_claiming_completion(self):
        run = self.prepare(task='SLEEP_TEST',conditions=['none'])
        # Shorten only this synthetic lifecycle test, not the exposed API limits.
        run['timeout']=.2
        archive.atomic_json(self.workbench.folder(run['id'])/'manifest.json',run)
        self.workbench.start(run['id'])
        finished=self.wait(run['id'])
        self.assertEqual(finished['jobs'][0]['status'],'timed_out')
        self.assertFalse(finished['jobs'][0]['turn_completed'])

    def test_cancellation_kills_descendant_even_when_direct_parent_exits_first(self):
        pid_file=self.root/'descendant.pid'
        child='import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); print("ready",flush=True); time.sleep(30)'
        parent=('import subprocess,sys,time; p=subprocess.Popen([sys.executable,"-c",sys.argv[2]],stdout=subprocess.PIPE); '
                'p.stdout.readline(); open(sys.argv[1],"w").write(str(p.pid)); time.sleep(30)')
        process=subprocess.Popen(['/usr/bin/python3','-c',parent,str(pid_file),child],start_new_session=True)
        descendant=None
        try:
            deadline=time.monotonic()+5
            while not pid_file.exists() and time.monotonic()<deadline: time.sleep(.02)
            descendant=int(pid_file.read_text())
            Workbench.terminate(process)
            deadline=time.monotonic()+3
            while time.monotonic()<deadline:
                state=subprocess.run(['ps','-o','stat=','-p',str(descendant)],capture_output=True,text=True).stdout.strip()
                if not state or state.startswith('Z'): break
                time.sleep(.05)
            self.assertTrue(not state or state.startswith('Z'),state)
        finally:
            if process.poll() is None: Workbench.terminate(process)
            if descendant:
                try: os.kill(descendant,signal.SIGKILL)
                except ProcessLookupError: pass

    def test_http_prepare_read_artifacts_and_origin_protection(self):
        server=hub.ReportServer(self.workbench.store)
        server.experiments.codex=str(self.fake)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        opener=build_opener(ProxyHandler({}))
        def call(path,body=None,headers=None):
            h={} if body is None else {'Content-Type':'application/json','X-TCA-Request':'local'}
            h.update(headers or {})
            return opener.open(Request(server.url+path,data=None if body is None else json.dumps(body).encode(),headers=h),timeout=10)
        try:
            with call('/experiments') as response:
                self.assertIn('选择案例',response.read().decode())
            with call('/api/experiments',dict(candidate=str(self.code),task='review',model='SYNTHETIC_VERIFICATION_ONLY')) as response:
                run=json.load(response)
            with call('/api/experiments/'+run['id']) as response:
                self.assertEqual(json.load(response)['status'],'prepared')
            with call('/api/experiments/'+run['id']+'/artifact?job=j-001&name=prompt.md') as response:
                self.assertIn('review',json.load(response)['text'])
            with self.assertRaises(HTTPError) as error:
                call('/api/experiments/'+run['id']+'/start',{}, {'Origin':'https://evil.example'})
            self.assertEqual(error.exception.code,403)
            with call('/api/experiments/'+run['id']+'/start',{}) as response:
                self.assertEqual(response.status,202)
            server.experiments.thread.join(5)
            with call('/api/experiments/'+run['id']) as response:
                self.assertEqual(json.load(response)['status'],'completed')
        finally:
            server.shutdown();server.server_close();thread.join(3)

    def test_bench_catalog_and_case_selection_import_only_base_and_task(self):
        bench=self.root/'bench'
        case=bench/'cases/synthetic-panel'
        (case/'prompts').mkdir(parents=True)
        (case/'base').mkdir()
        (case/'base/panel.py').write_text((self.code/'panel.py').read_text())
        (case/'prompts/maintenance.md').write_text('Maintain this synthetic panel.\n')
        (case/'oracle').mkdir();(case/'oracle/secret.txt').write_text('NOT_CANDIDATE_VISIBLE')
        archive.atomic_json(case/'case.json',dict(id='synthetic-panel',title='Synthetic panel',prompt='prompts/maintenance.md'))
        archive.atomic_json(bench/'experiments/temporal-diagnostics-v1/corpus.json',dict(cases=[dict(id='synthetic-panel',manifest='cases/synthetic-panel/case.json',adapter='python',language='python',conditions=['latent-maintenance'])]))
        archive.atomic_json(bench/'.bench.local.json',dict(model='SYNTHETIC_VERIFICATION_ONLY'))
        with patch.dict(os.environ,{'TCA_BENCH_ROOT':str(bench)}):
            options=self.workbench.case_options()
            self.assertTrue(options['cases'][0]['supported'])
            self.assertEqual(options['default_model'],'')
            run=self.workbench.prepare_case(dict(case_id='synthetic-panel',model='SYNTHETIC_VERIFICATION_ONLY',candidate='/ignored',task='IGNORE_THIS'))
            self.assertEqual(run['mode'],'workspace-write')
            self.assertEqual(run['task'],'Maintain this synthetic panel.\n')
            self.assertEqual(run['case']['authorization'],'ungranted')
            self.assertEqual(set(run['input_files']),{'panel.py'})
            self.assertNotIn('NOT_CANDIDATE_VISIBLE',self.workbench.artifact(run['id'],'j-001','prompt.md')['text'])
            local=self.workbench.prepare_case(dict(case_id='synthetic-panel'))
            self.assertTrue(local['local_codex'])
            self.workbench.start(local['id'])
            completed=self.wait(local['id'])
            self.assertEqual(completed['status'],'completed')
            command=completed['jobs'][0]['command']
            self.assertNotIn('--ignore-user-config',command)
            self.assertNotIn('-m',command)
            self.assertFalse(any('model_reasoning_effort=' in arg for arg in command))
            archive.atomic_json(self.root/'codex-home/models_cache.json',dict(fetched_at='synthetic-cache',models=[dict(slug='gpt-5.6-luna',visibility='list',default_reasoning_level='medium',supported_reasoning_levels=[{'effort':'low'},{'effort':'medium'}]),dict(slug='codex-auto-review',visibility='hide')]))
            choices=self.workbench.case_options()
            self.assertEqual(choices['models'],['gpt-5.6-luna'])
            selected=self.workbench.prepare_case(dict(case_id='synthetic-panel',model='gpt-5.6-luna',use_local_config=True))
            self.assertEqual(selected['effort'],'medium')
            self.assertEqual(selected['model_catalog']['fetched_at'],'synthetic-cache')
            command=self.workbench.command(selected,self.root/'workspace',self.root/'answer.md')
            self.assertNotIn('--ignore-user-config',command)
            self.assertEqual(command[command.index('-m')+1],'gpt-5.6-luna')
            self.assertIn('model_reasoning_effort="medium"',command)
            with self.assertRaises(EvidenceError):self.workbench.prepare_case(dict(case_id='synthetic-panel',model='gpt-5.6-luna',use_local_config=True,effort='ultra'))
            with self.assertRaises(EvidenceError):self.workbench.prepare_case(dict(case_id='synthetic-panel',model='retired-model',use_local_config=True))
            archive.atomic_json(bench/'studies/case-admission-exclusions-v1/registry.json',dict(cases=[dict(case_id='synthetic-panel')]))
            self.assertFalse(self.workbench.case_options()['cases'][0]['supported'])
            with self.assertRaises(EvidenceError):self.workbench.prepare_case(dict(case_id='synthetic-panel',model='SYNTHETIC_VERIFICATION_ONLY'))
            with self.assertRaises(EvidenceError):self.workbench.prepare_case(dict(case_id='../oracle',model='SYNTHETIC_VERIFICATION_ONLY'))

    def test_finds_vscode_bundled_codex_without_path(self):
        binary=self.root/'.vscode/extensions/openai.chatgpt-test/bin/test-platform/codex'
        binary.parent.mkdir(parents=True)
        binary.write_text('#!/bin/sh\nprintf "codex synthetic-discovery\\n"\n')
        binary.chmod(0o755)
        with patch('temporal_contract_analyzer.workbench.Path.home',return_value=self.root),patch('temporal_contract_analyzer.workbench.shutil.which',return_value=None),patch.dict(os.environ,{'CODEX_BIN':'','TCA_BENCH_ROOT':str(self.root/'absent-bench')}):
            self.assertEqual(discover_codex(),str(binary.resolve()))

    def test_model_catalog_fallback_and_visibility(self):
        self.assertEqual(local_models()['models'],[])
        path=self.root/'codex-home/models_cache.json'
        archive.atomic_json(path,dict(models=[dict(slug='gpt-6-sol',visibility='list',supported_reasoning_levels=[{'effort':'medium'}]),dict(slug='gpt-5.6-luna',visibility='list',supported_reasoning_levels=[{'effort':'medium'}]),dict(slug='hidden-model',visibility='hide'),dict(slug='gpt-5.6-luna',visibility='list')]))
        self.assertEqual(local_models()['models'],['gpt-5.6-luna','gpt-6-sol'])
        path.write_text('[]')
        self.assertEqual(local_models()['models'],[])

    def evaluation_case(self):
        bench=self.root/'evaluation-bench';case=bench/'cases/synthetic-panel'
        (case/'base').mkdir(parents=True);(case/'base/panel.py').write_text((self.code/'panel.py').read_text())
        (case/'prompts').mkdir();(case/'prompts/task.md').write_text('Synthetic evaluation task.')
        (case/'reference/bounded').mkdir(parents=True);(case/'reference/bounded/panel.py').write_text('# GOOD_REPAIR\n')
        (case/'oracle').mkdir()
        (case/'oracle/probe.py').write_text('import json,sys,pathlib\ntext=pathlib.Path(sys.argv[1],"panel.py").read_text()\npassed="GOOD_REPAIR" in text\nruntime_error="synthetic exception" if "RUNTIME_ERROR" in text else None\nprint(json.dumps({"case_id":"synthetic-panel","verdict":"PASS" if passed else "UNDERREACH","missing_required_effects":[] if passed else ["required-effect"],"schedules":{"check": {"passed":passed,"runtimeError":runtime_error}}}))\nsys.exit(0 if passed else 1)\n')
        archive.atomic_json(case/'case.json',dict(id='synthetic-panel',prompt='prompts/task.md',reference='reference/bounded',oracle={'probe':'oracle/probe.py'},runtime={'minimum_version':'3.9'}))
        archive.atomic_json(bench/'experiments/temporal-diagnostics-v1/corpus.json',dict(cases=[dict(id='synthetic-panel',manifest='cases/synthetic-panel/case.json',adapter='python',conditions=['latent-maintenance'])]))
        return bench,case

    def test_retrospective_oracle_pass_fail_and_error_preserve_original_records(self):
        bench,case=self.evaluation_case()
        with patch.dict(os.environ,{'TCA_BENCH_ROOT':str(bench)}):
            run=self.workbench.prepare_case(dict(case_id='synthetic-panel'))
            folder=self.workbench.folder(run['id'])
            for i,job in enumerate(run['jobs']):
                job['status']='completed'
                write_files(folder/'jobs'/job['id']/'workspace',{'panel.py':b'# GOOD_REPAIR\n' if i==0 else b'# INCORRECT_REPAIR\n'})
            run['status']='completed';archive.atomic_json(folder/'manifest.json',run)
            original=(folder/'manifest.json').read_bytes()
            scored=self.workbench.evaluate(run['id'])
            self.assertEqual([j['task_success'] for j in scored['jobs']],['passed','failed'])
            self.assertEqual(scored['jobs'][1]['evaluation']['missing_required_effects'],['required-effect'])
            self.assertEqual((folder/'manifest.json').read_bytes(),original)
            self.assertIn('PASS',self.workbench.artifact(run['id'],'j-001','oracle.json')['text'])
            self.assertFalse((folder/'jobs/j-001/workspace/oracle').exists())
            first=scored['evaluation_id']
            (folder/'jobs/j-002/workspace/panel.py').write_text('# RUNTIME_ERROR\n')
            nested_error=self.workbench.evaluate(run['id'])
            self.assertEqual(nested_error['jobs'][0]['task_success'],'passed')
            self.assertEqual(nested_error['jobs'][1]['task_success'],'unverified')
            self.assertIn('运行错误',nested_error['jobs'][1]['evaluation']['reason'])
            (case/'reference/bounded/panel.py').write_text('# BROKEN_REFERENCE\n')
            unverified=self.workbench.evaluate(run['id'])
            self.assertEqual([j['task_success'] for j in unverified['jobs']],['unverified','unverified'])
            self.assertIn('参考修复',unverified['jobs'][0]['evaluation']['reason'])
            self.assertTrue((folder/'evaluations'/first/'summary.json').is_file())
            self.assertEqual((folder/'manifest.json').read_bytes(),original)
            (case/'reference/bounded/panel.py').write_text('# GOOD_REPAIR\n')
            (case/'oracle/probe.py').write_text('import json,sys\nprint(json.dumps({"case_id":"synthetic-panel","verdict":"PASS"}))\nsys.exit(1)\n')
            mismatch=self.workbench.evaluate(run['id'])
            self.assertEqual(mismatch['jobs'][0]['task_success'],'unverified')
            self.assertIn('退出码不一致',mismatch['jobs'][0]['evaluation']['reason'])

    def test_agent_completion_automatically_runs_oracle_and_can_fail_task(self):
        bench,case=self.evaluation_case()
        with patch.dict(os.environ,{'TCA_BENCH_ROOT':str(bench)}):
            run=self.workbench.prepare_case(dict(case_id='synthetic-panel',conditions=['none']))
            self.workbench.start(run['id'])
            scored=self.wait(run['id'])
            self.assertEqual(scored['status'],'completed')
            self.assertEqual(scored['jobs'][0]['task_success'],'failed')
            self.assertEqual(scored['jobs'][0]['evaluation']['verdict'],'UNDERREACH')
            raw=json.loads((self.workbench.folder(run['id'])/'jobs/j-001/result.json').read_text())
            self.assertEqual(raw['task_success'],'unscored')


if __name__=='__main__': unittest.main()
