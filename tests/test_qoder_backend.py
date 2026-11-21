"""Synthetic CLI events test the Qoder boundary without model requests or Credits."""
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from temporal_contract_analyzer.qoder_backend import QoderBackend, cleanup_runtime, confirmed_refusals, parse_action_report, parse_events, parse_output, readable_candidate, tool_requests
from temporal_contract_analyzer._session_runtime.request_guard import account
from temporal_contract_analyzer._session_runtime.model_settings import resolve_profile, validate_settings
from temporal_contract_analyzer._session_runtime.read_policy import read_command

REPORT_SCHEMA = json.loads((Path(__file__).resolve().parents[1]/'temporal_contract_analyzer/_session_runtime/maintenance.schema.json').read_text())


def events(turns=1):
    return [dict(type='system', subtype='init', model='DeepSeek-Flash', apiKeySource='none', mcp_servers=[], plugins=[]),
            dict(type='assistant', message=dict(id='fixture-message', stop_reason='end_turn')),
            dict(type='result', subtype='success', is_error=False, num_turns=turns,
                 result='{"ready":true}', total_credits=0.125, permission_denials=[])]


class Parsing(unittest.TestCase):
    def test_literal_action_report_whitespace_is_preserved_and_warned(self):
        warnings=[]
        text='{"report":"first\nsecond\tcolumn\rend","extra":true}'
        report,extras=parse_action_report(text,REPORT_SCHEMA,format_warnings=warnings)
        self.assertEqual(report,{'report':'first\nsecond\tcolumn\rend'})
        self.assertEqual(extras,{'extra':True})
        self.assertEqual(warnings,[dict(code='action_report_literal_whitespace',characters=dict(newline=1,tab=1,carriage_return=1))])
        with self.assertRaises(ValueError):parse_output(text,REPORT_SCHEMA)
        warnings=[]
        parse_action_report(json.dumps(report),REPORT_SCHEMA,format_warnings=warnings)
        self.assertEqual(warnings,[])

    def test_report_whitespace_tolerance_rejects_other_corruption(self):
        for text in ['{"report":"bad\x00value"}', '{"report":"ok","extra":"bad\nvalue"}',
                     '{"rep\nort":"bad"}', '{"report":"unfinished\nvalue',
                     '{"report":"first\nvalue"} {"report":"second"}',
                     '{"report":"first\nvalue","extra":{"report":"bad\nvalue"}}']:
            with self.subTest(text=repr(text)),self.assertRaises(ValueError):parse_action_report(text,REPORT_SCHEMA)
        schema=dict(type='object',properties=dict(ready=dict(type='string')),required=['ready'],additionalProperties=False)
        with self.assertRaises(ValueError):parse_action_report('{"ready":"bad\nvalue"}',schema)

    def test_action_report_separates_extra_metadata_without_changing_report(self):
        text='{"report":"Original report","report_length_ok":true,"report_note":null}'
        output,extras=parse_action_report(text,REPORT_SCHEMA)
        self.assertEqual(output,{'report':'Original report'})
        self.assertEqual(extras,{'report_length_ok':True,'report_note':None})
        with self.assertRaises(ValueError):parse_output(text,REPORT_SCHEMA)

    def test_action_report_required_type_length_and_json_checks_remain_strict(self):
        for text in ['{"report_length_ok":true}','{"report":false,"extra":null}',
                     json.dumps({'report':'x'*6001,'extra':True}),'not JSON','["report"]',
                     '{"report":"one"} {"report":"two"}']:
            with self.subTest(text=text[:60]),self.assertRaises(ValueError):parse_action_report(text,REPORT_SCHEMA)

    def test_other_action_schemas_do_not_gain_extra_field_tolerance(self):
        schema=dict(type='object',properties=dict(ready=dict(type='boolean')),required=['ready'],additionalProperties=False)
        with self.assertRaises(ValueError):parse_action_report('{"ready":true,"extra":null}',schema)

    def test_transient_cleanup_permissions_are_retried_and_recorded(self):
        with patch('temporal_contract_analyzer.qoder_backend.shutil.rmtree',side_effect=[PermissionError(13,'Permission denied'),None]) as remove, \
                patch('temporal_contract_analyzer.qoder_backend.time.sleep'):
            result=cleanup_runtime(Path('/synthetic-owned-runtime'))
        self.assertTrue(result['complete'])
        self.assertEqual(result['attempts'],2)
        self.assertEqual(remove.call_count,2)
        self.assertIn('Permission denied',result['errors'][0])

    def test_persistent_cleanup_errors_are_bounded_and_not_hidden(self):
        with patch('temporal_contract_analyzer.qoder_backend.shutil.rmtree',side_effect=PermissionError(13,'Permission denied')) as remove, \
                patch('temporal_contract_analyzer.qoder_backend.time.sleep'):
            result=cleanup_runtime(Path('/synthetic-owned-runtime'))
        self.assertFalse(result['complete'])
        self.assertEqual(remove.call_count,4)

    def test_one_schema_valid_json_object_can_have_a_prose_or_fence_wrapper(self):
        schema=dict(type='object',properties=dict(report=dict(type='string')),required=['report'],additionalProperties=False)
        for text in ['{"report":"done"}', 'Implemented and verified.\n{"report":"done"}', '```json\n{"report":"done"}\n```']:
            self.assertEqual(parse_output(text,schema),{'report':'done'})
        for text in ['No JSON', '{"report":"one"}\n{"report":"two"}', '{"report":true}', '{"report":"one"} more prose']:
            with self.subTest(text=text),self.assertRaises(ValueError):parse_output(text,schema)

    def test_denial_recovery_requires_matching_host_and_cli_hook_proof(self):
        request=dict(type='assistant',message=dict(content=[dict(type='tool_use',id='blocked',name='Bash')]))
        result=dict(type='user',message=dict(content=[dict(type='tool_result',tool_use_id='blocked',is_error=True,
                    content='Error: /qoder_hook.py hook blocking error: Tool denied by the training role policy')]))
        ledger=dict(events=[dict(denied=True,event=dict(tool_use_id='blocked',tool_name='Bash'))])
        notice=dict(type='system',subtype='notification',message='A background task completed')
        self.assertEqual(confirmed_refusals([notice,request,result],ledger),{'blocked'})
        with self.assertRaises(ValueError):confirmed_refusals([request],ledger)
        result['message']['content'][0]['content']='Exit code 1: shell command failed'
        with self.assertRaises(ValueError):confirmed_refusals([request,result],ledger)

    def test_unavailable_request_needs_explicit_cli_rejection(self):
        requested=dict(type='assistant',message=dict(content=[dict(type='tool_use',id='unavailable',name='mcp_list',input={})]))
        denied=dict(type='user',message=dict(content=[dict(type='tool_result',tool_use_id='unavailable',is_error=True,content='Tool is unavailable')]))
        self.assertEqual(tool_requests([requested,denied]),(set(),{'unavailable':'mcp_list'}))
        with self.assertRaises(ValueError):tool_requests([requested])
        denied['message']['content'][0]['is_error']=False
        with self.assertRaises(ValueError):tool_requests([requested,denied])

    def test_confirmed_model_and_bounded_turns(self):
        self.assertEqual(parse_events(events(), 'DeepSeek-Flash', 2)['num_turns'], 1)
        for data, model in [(events(3), 'DeepSeek-Flash'), (events(), 'Auto'),
                            (events()+[events()[-1]], 'DeepSeek-Flash'), (events()[:-1], 'DeepSeek-Flash')]:
            with self.subTest(data=data, model=model), self.assertRaises(ValueError):
                parse_events(data, model, 2)

    def test_custom_key_and_external_tools_are_rejected(self):
        for key, value in [('apiKeySource', 'custom'), ('mcp_servers', ['fixture']), ('plugins', ['fixture'])]:
            data = events()
            data[0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                parse_events(data, 'DeepSeek-Flash', 2)

    def test_credits_profile_cannot_be_redirected_to_byok(self):
        settings = resolve_profile()
        settings.update(model='DeepSeek-Flash', reasoning_effort='low', service_tier=None,
                        provider=dict(name='Qoder Credits', wire_api='qoder_cli', requires_openai_auth=False))
        self.assertEqual(validate_settings(settings)['model'], 'DeepSeek-Flash')
        settings['provider']['env_key'] = 'DEEPSEEK_API_KEY'
        with self.assertRaises(ValueError):
            validate_settings(settings)


class Execution(unittest.TestCase):
    def run_stage(self, timeout=False, invalid_json=False, ungated_tool=False, action=False, stream=None, ledger=None, locked_file=False, schema=None):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'binary').touch()
            (root/'account/.auth').mkdir(parents=True)
            (root/'account/.auth/user').write_text('synthetic auth fixture, not a credential')
            stage = root/'stage'; stage.mkdir()
            data = events() if stream is None else stream
            if ungated_tool:
                data[1]['message']['content'] = [dict(type='tool_use', name='Bash' if ungated_tool is True else ungated_tool, id='fixture-tool', input=dict(command='pwd'))]
            if invalid_json:
                data[-1]['result'] = 'not JSON'

            class Process:
                def __init__(self, *args, **kwargs):
                    self.stdin = io.StringIO()
                    self.stdout = iter(json.dumps(e)+'\n' for e in data)
                    self.returncode = None if timeout else 0
                    if action:
                        (stage/'public-input/main.py').write_text('value = 43\n')
                    if locked_file:
                        (stage/'public-input/sedFixture').touch(mode=0)
                    if ledger is not None:
                        (stage/'tool-meter/ledger.json').write_text(json.dumps(ledger))
                def wait(self, timeout=None):
                    if self.returncode is None:
                        raise subprocess.TimeoutExpired('synthetic CLI', timeout)
                    return self.returncode
                def poll(self):
                    return self.returncode
                def terminate(self):
                    self.returncode = -15

            protocol = dict(binary=str(root/'binary'), qoder_auth_dir=str(root/'account'),
                            backend=dict(kind='docker', solver_image='sha256:'+'a'*64))
            payload = dict(task='Synthetic fixture', sources={'main.py':'value = 42\n'},
                           schema=schema if schema is not None else dict(type='object', properties=dict(ready=dict(type='boolean')), required=['ready']))
            with patch('temporal_contract_analyzer.tempoevo_docker.image_identity', side_effect=lambda x:x), \
                    patch('temporal_contract_analyzer._session_runtime.docker_transport.stop') as stop, \
                    patch('temporal_contract_analyzer.qoder_backend.subprocess.Popen', Process):
                result = QoderBackend(protocol).execute('action' if action else 'contract', payload,
                    dict(model='DeepSeek-Flash', reasoning_effort='low'), dict(requests=2, seconds=1), stage)
                self.assertTrue(stop.called)
                if result.get('format_warnings'):
                    self.assertEqual((stage/'raw-answer.txt').read_text(),data[-1]['result'])
                    self.assertEqual(json.loads((stage/'output-format.json').read_text())['extra_fields'],result['action_report_extra_fields'])
                command = json.loads((stage/'command.json').read_text())
                self.assertEqual(command[command.index('--max-turns')+1], '2')
                self.assertEqual(command[command.index('--max-model-request-retries')+1], '0')
                self.assertEqual(command[command.index('--setting-sources')+1], 'user')
                self.assertEqual(command[command.index('--tools')+1],'Bash,Read')
                self.assertEqual(command[command.index('--disallowed-tools')+1],'mcp_call,mcp_get,mcp_list')
                self.assertIn('Do not add undeclared fields',command[command.index('--append-system-prompt')+1])
                self.assertNotIn('DEEPSEEK_API_KEY', ' '.join(command))
                self.assertNotIn('synthetic auth fixture', ' '.join(command))
                mounts = [command[i+1] for i, x in enumerate(command) if x == '--mount']
                self.assertEqual(any('dst=/workspace,readonly' in x for x in mounts), not action)
                self.assertFalse(any('docker.sock' in x or 'experience-memory' in x for x in mounts))
                return result

    def test_json_and_credits_are_measured_without_inventing_http_requests(self):
        result = self.run_stage()
        self.assertTrue(result['valid'], result)
        self.assertEqual(result['requests'], 1)
        self.assertEqual(result['output'], dict(ready=True))
        self.assertEqual(result['credits'], 0.125)
        self.assertIsNone(result['http_requests'])
        self.assertIsNone(result['tokens'])

    def test_stopped_container_profile_cleanup_failure_does_not_discard_valid_output(self):
        def fail_after_cleanup(runtime):
            receipt=cleanup_runtime(runtime)
            receipt.update(complete=False,errors=['synthetic persistent cleanup permission failure'])
            return receipt
        with patch('temporal_contract_analyzer.qoder_backend.cleanup_runtime',side_effect=fail_after_cleanup):
            result=self.run_stage()
        self.assertTrue(result['valid'],result)
        self.assertEqual(result['requests'],1)
        self.assertTrue(result['turn_count_complete'])
        self.assertIsNone(result['failure_type'])
        self.assertEqual(result['output'],dict(ready=True))
        self.assertIn('runtime cleanup pending',result['cleanup_warning'])
        self.assertFalse(result['runtime_cleanup']['complete'])

    def test_undeclared_null_fields_are_still_rejected(self):
        schema=dict(type='object',properties=dict(report=dict(type='string')),required=['report'],additionalProperties=False)
        with self.assertRaises(ValueError):parse_output('{"report":"done","report_note":null}',schema)

    def test_action_report_metadata_does_not_block_candidate_delivery(self):
        data=events();data[-1]['result']='{"report":"done","report_length_ok":true}'
        result=self.run_stage(action=True,stream=data,schema=REPORT_SCHEMA)
        self.assertTrue(result['valid'],result)
        self.assertEqual(result['output'],{'report':'done'})
        self.assertEqual(result['candidate_sources'],{'main.py':'value = 43\n'})
        self.assertEqual(result['action_report_extra_fields'],{'report_length_ok':True})
        self.assertEqual(result['format_warnings'],[dict(code='action_report_extra_fields',fields=['report_length_ok'])])

    def test_literal_report_newline_does_not_block_action_candidate(self):
        data=events();data[-1]['result']='{"report":"first\nsecond"}'
        result=self.run_stage(action=True,stream=data,schema=REPORT_SCHEMA)
        self.assertTrue(result['valid'],result)
        self.assertEqual(result['output'],{'report':'first\nsecond'})
        self.assertEqual(result['format_warnings'],[dict(code='action_report_literal_whitespace',characters={'newline':1})])
        self.assertEqual(result['candidate_sources'],{'main.py':'value = 43\n'})

    def test_contract_keeps_strict_schema_and_invalid_report_blocks_action(self):
        for action,text in [(False,'{"report":"done","extra":true}'),(True,'{"report":false,"extra":true}')]:
            data=events();data[-1]['result']=text
            result=self.run_stage(action=action,stream=data,schema=REPORT_SCHEMA)
            self.assertFalse(result['valid'],result)
            self.assertEqual(result['failure_type'],'invalid_output')
            self.assertNotIn('candidate_sources',result)

    def test_network_failure_uses_existing_bounded_stage_retry_policy(self):
        data=events()
        data[-1].update(subtype='error_during_execution',is_error=True,error_code='network_failure',errors=['other side closed'],result='')
        result=self.run_stage(stream=data)
        self.assertFalse(result['valid'])
        self.assertEqual(result['failure_type'],'transient_transport_error')
        self.assertEqual(result['requests'],1)
        data[-1]['error_code']='authentication_error'
        self.assertEqual(self.run_stage(stream=data)['failure_type'],'model_or_cli_abnormal_exit')

    def test_blocked_tool_can_recover_without_weakening_the_gate(self):
        data=events()
        data.insert(1,dict(type='assistant',message=dict(content=[dict(type='tool_use',id='blocked',name='Bash',input=dict(command='find .'))])))
        data.insert(2,dict(type='user',message=dict(content=[dict(type='tool_result',tool_use_id='blocked',is_error=True,
                       content='/qoder_hook.py hook blocking error: Tool denied by the training role policy')])))
        data[-1]['permission_denials']=[dict(tool_use_id='blocked',tool_name='Bash')]
        ledger=dict(tool_attempts=1,events=[dict(denied=True,event=dict(tool_use_id='blocked',tool_name='Bash'))])
        result=self.run_stage(stream=data,ledger=ledger)
        self.assertTrue(result['valid'],result)
        self.assertEqual(result['blocked_tool_requests'],1)
        data[2]['message']['content'][0]['is_error']=False
        self.assertFalse(self.run_stage(stream=data,ledger=ledger)['valid'])

    def test_zero_permission_sed_temp_file_does_not_crash_candidate_capture(self):
        result=self.run_stage(action=True,locked_file=True)
        self.assertTrue(result['valid'],result)
        self.assertEqual(result['candidate_sources'],{'main.py':'value = 43\n','sedFixture':''})

    def test_permission_normalization_does_not_follow_external_symlinks(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'workspace';root.mkdir()
            outside=Path(temp)/'private';outside.write_text('private');outside.chmod(0)
            (root/'escape').symlink_to(outside)
            try:
                with self.assertRaises(ValueError):readable_candidate(root)
                self.assertEqual(outside.stat().st_mode & 0o777,0)
            finally:outside.chmod(0o600)

    def test_timeout_stops_owned_container(self):
        result = self.run_stage(timeout=True)
        self.assertFalse(result['valid'])
        self.assertEqual(result['failure_type'], 'timeout')

    def test_invalid_json_is_retained_and_rejected(self):
        result = self.run_stage(invalid_json=True)
        self.assertFalse(result['valid'])
        self.assertEqual(result['failure_type'], 'invalid_output')

    def test_missing_tool_gate_fails_closed(self):
        result = self.run_stage(ungated_tool=True)
        self.assertFalse(result['valid'])
        self.assertIn('mandatory tool gate', result['error'])

    def test_action_delivers_actual_candidate_files_after_cleanup(self):
        result = self.run_stage(action=True)
        self.assertTrue(result['valid'], result)
        self.assertEqual(result['candidate_sources'], {'main.py':'value = 43\n'})

    def test_rejected_mcp_discovery_does_not_abort_final_result_collection(self):
        data=events()
        data.insert(1,dict(type='assistant',message=dict(content=[dict(type='tool_use',id='not-enabled',name='mcp_list',input={})])))
        data.insert(2,dict(type='user',message=dict(content=[dict(type='tool_result',tool_use_id='not-enabled',is_error=True,content='Tool is unavailable')])) )
        data[-1]['permission_denials']=[dict(tool_use_id='not-enabled',tool_name='mcp_list')]
        result=self.run_stage(stream=data)
        self.assertTrue(result['valid'],result)
        self.assertEqual(result['output'],dict(ready=True))

    def test_unrejected_unknown_tool_is_not_accepted(self):
        data=events()
        data.insert(1,dict(type='assistant',message=dict(content=[dict(type='tool_use',id='not-enabled',name='mcp_list',input={})])))
        result=self.run_stage(stream=data)
        self.assertFalse(result['valid'])
        self.assertIn('did not confirm rejection',result['error'])

    def test_read_still_requires_host_gate_proof(self):
        result=self.run_stage(ungated_tool='Read')
        self.assertFalse(result['valid'])
        self.assertIn('mandatory tool gate',result['error'])

    def test_collector_failure_is_not_hidden_by_missing_final_result(self):
        result=self.run_stage(stream=['not an event object'])
        self.assertFalse(result['valid'])
        self.assertIn('event must be an object',result['error'])
        self.assertNotIn('exactly one final result',result['error'])


class ToolHook(unittest.TestCase):
    def test_action_can_read_scratch_files_but_analysis_and_escaping_links_cannot(self):
        hook=Path(__file__).resolve().parents[1]/'temporal_contract_analyzer/_session_runtime/qoder_hook.py'
        with patch.dict(sys.modules,{'guard_client':SimpleNamespace(forward=lambda value:dict(deny=False))}):
            normalize=runpy.run_path(str(hook))['guard_event']
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);workspace=root/'workspace';workspace.mkdir();scratch=root/'scratch';scratch.mkdir()
            generated=scratch/'check.py';generated.write_text('print(42)')
            private=root/'private';private.write_text('private');(scratch/'escape').symlink_to(private)
            event=dict(hook_event_name='PreToolUse',tool_name='Read',cwd='/workspace',tool_input=dict(file_path=str(generated)))
            normalized=normalize(event,workspace,action=True,scratch=scratch)
            self.assertIn(str(generated.resolve()),normalized['tool_input']['command'])
            with self.assertRaises(ValueError):normalize(event,workspace,scratch=scratch)
            event['tool_input']['file_path']=str(scratch/'escape')
            with self.assertRaises(ValueError):normalize(event,workspace,action=True,scratch=scratch)

    def test_read_is_confined_to_public_regular_workspace_files(self):
        hook=Path(__file__).resolve().parents[1]/'temporal_contract_analyzer/_session_runtime/qoder_hook.py'
        with patch.dict(sys.modules,{'guard_client':SimpleNamespace(forward=lambda value:dict(deny=False))}):
            normalize=runpy.run_path(str(hook))['guard_event']
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);workspace=root/'public';workspace.mkdir()
            (workspace/'main.py').write_text('value = 42\n')
            (root/'private.txt').write_text('synthetic private fixture')
            (workspace/'escape').symlink_to(root/'private.txt')
            event=dict(hook_event_name='PreToolUse',tool_name='Read',cwd='/workspace',tool_input=dict(file_path='main.py'))
            allowed=normalize(event,workspace)
            self.assertEqual(allowed['qoder_original_tool'],'Read')
            self.assertEqual(allowed['qoder_original_input'],event['tool_input'])
            self.assertTrue(read_command(allowed))
            self.assertTrue(read_command(normalize(dict(event,tool_input=dict(file_path='missing.py')),workspace)))
            for filename in ('../private.txt',str(root/'private.txt'),'escape','.'):
                with self.subTest(filename=filename),self.assertRaises(ValueError):
                    normalize(dict(event,tool_input=dict(file_path=filename)),workspace)

    def test_guard_rejection_is_recorded_even_for_an_action(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            (root/'config.json').write_text(json.dumps(dict(global_cap=2,calls=dict(fixture=dict(cap=2,mode='maintenance')))))
            denied=account(dict(hook_event_name='PreToolUse',tool_name='Read',qoder_guard_denied=True,
                                tool_input=dict(file_path='/private/fixture')),root,'fixture',terminate=False)
            self.assertTrue(denied)
            ledger=json.loads((root/'ledger.json').read_text())
            self.assertEqual(ledger['tool_attempts'],1)
            self.assertEqual(ledger['sessions']['fixture']['blocked_tools'],1)

    def test_workspace_prefix_preserves_closed_read_policy(self):
        hook = Path(__file__).resolve().parents[1]/'temporal_contract_analyzer/_session_runtime/qoder_hook.py'
        for command, denied in [('cd /workspace && cat main.py', False), ('cd /workspace && touch main.py', True),
                                ('cd /etc && cat passwd', True)]:
            event = dict(hook_event_name='PreToolUse', cwd='/workspace', tool_name='Bash', tool_input=dict(command=command))
            fake_client = SimpleNamespace(forward=lambda value:dict(deny=not read_command(value)))
            with self.subTest(command=command), patch.dict(sys.modules, {'guard_client':fake_client}), \
                    patch.object(sys, 'stdin', io.StringIO(json.dumps(event))), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                if denied:
                    with self.assertRaises(SystemExit) as error:
                        runpy.run_path(str(hook), run_name='__main__')
                    self.assertEqual(error.exception.code, 2)
                else:
                    runpy.run_path(str(hook), run_name='__main__')
