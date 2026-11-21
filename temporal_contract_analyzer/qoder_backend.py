"""Qoder Credits stages in isolated solver containers, with explicit turn accounting."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
import uuid

from . import archive
from .candidate_files import capture, write_files
from .core import EvidenceError, canonical
from ._session_runtime.schema_validator import validate

REPO = Path(__file__).resolve().parents[1]
RUNTIME = Path(__file__).with_name('_session_runtime')
MEASUREMENT = 'qoder_model_turns'


def parse_events(events, model, cap):
    """Validate the pinned CLI's stream-json result, including model selection."""
    init = [e for e in events if e.get('type') == 'system' and e.get('subtype') == 'init']
    results = [e for e in events if e.get('type') == 'result']
    if len(init) != 1 or init[0].get('model') != model:
        raise ValueError('Qoder did not confirm the requested built-in model')
    if init[0].get('apiKeySource') != 'none' or init[0].get('mcp_servers') or init[0].get('plugins'):
        raise ValueError('Qoder must use built-in Credits with no custom API key, MCP servers or plugins')
    if len(results) != 1:
        raise ValueError('Qoder did not return exactly one final result')
    result = results[0]
    turns = result.get('num_turns')
    if type(turns) is not int or not 0 <= turns <= cap:
        raise ValueError('Missing or invalid Qoder model-turn count')
    return result


def configuration():
    return dict(hooks={'PreToolUse': [dict(hooks=[dict(type='command',
        command='/usr/local/bin/python3 -B /qoder_hook.py', timeout=10)])]})


class QoderBackend:
    def __init__(self, protocol):
        self.protocol = protocol

    def execute(self, kind, payload, model, limits, directory):
        return self._execute(kind, payload, model, limits, Path(directory))

    def _execute(self, kind, payload, model, limits, directory):
        from .tempoevo_docker import image_identity
        from ._session_runtime.docker_transport import stop
        from .prompt_context import compact
        from ._session_runtime.guard_server import GuardServer

        if self.protocol.get('backend', {}).get('kind') != 'docker':
            raise EvidenceError('Qoder training requires Docker isolation')
        if type(limits['requests']) is not int or not 1 <= limits['requests'] <= (24 if kind == 'action' else 12) or not 0 < limits['seconds'] <= 600:
            raise EvidenceError('Invalid Qoder model-turn or time limit')
        image = image_identity(self.protocol['backend']['solver_image'])
        binary = Path(self.protocol['binary']).resolve()
        if not binary.is_file():
            raise EvidenceError('Provision the Linux Qoder CLI before preparing a run')
        auth = Path(self.protocol.get('qoder_auth_dir', REPO/'.tempoevo/qoder/account')).resolve()
        if not (auth/'.auth/user').is_file():
            raise EvidenceError('Sign in to Qoder CLI before preparing a Credits run')
        workspace = directory/'public-input'
        sources = payload.get('candidate_sources', payload['sources'])
        write_files(workspace, {k:v.encode() for k,v in sources.items()})
        wire, report = compact(payload)
        archive.atomic_json(directory/'prompt-context.json', report)
        schema = payload.get('schema') or json.loads((RUNTIME/'maintenance.schema.json').read_text())
        prompt = ('Use only the original task and public sources as requirements. Experience and Auto-Contract are fallible guidance. '
                  'No scorer, reference, hidden tests or Docker socket is available. '
                  'For evidence cite the original task as file TASK; use exact public source paths and copy the quoted wording. '
                  'For Action edit business code in /workspace, preserve tests/configuration, and compile only under /tmp. '
                  'For other stages do not modify files; Bash is restricted to workspace reads. '
                  'Bash starts in /workspace: do not prefix commands with cd. For analysis use only pwd, ls, rg, cat, nl, head, tail or sed -n N,Mp; never use find or write commands. '
                  'Return exactly one JSON object matching OUTPUT_SCHEMA, without markdown fences.\n'
                  'OUTPUT_SCHEMA='+canonical(schema)+'\nINPUT='+canonical(wire))
        (directory/'prompt.txt').write_text(prompt)
        runtime = Path(tempfile.mkdtemp(prefix='tca-qoder-', dir='/tmp'))
        profile = runtime/'profile'
        (profile/'.auth').mkdir(parents=True, mode=0o700)
        (profile/'settings.json').write_text(json.dumps(configuration()))
        name = 'tca-qoder-'+uuid.uuid4().hex
        events, problems, observed, tool_calls = [], [], set(), set()
        process = None
        stopped = False
        started = time.monotonic()
        failure = None
        completed = None
        guard = None
        try:
            with GuardServer(runtime/'hooks', directory/'tool-meter', name, limits['requests'],
                             'maintenance' if kind == 'action' else 'extraction',
                             docker_desktop=__import__('sys').platform == 'darwin') as guard:
                command = ['docker', 'run', '-i', '--pull=never', '--name', name, '--network', 'host',
                    '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                    '--memory', '8g', '--cpus', '4', '--pids-limit', '512', '--init',
                    '--user', str(os.getuid())+':'+str(os.getgid()), '--workdir', '/workspace',
                    '--tmpfs', '/tmp:rw,exec,mode=1777,size=4g', '--env', 'HOME=/home/agent',
                    '--env', 'PYTHONDONTWRITEBYTECODE=1', '--env', 'NODE_PATH=/runtime/frontend/node_modules',
                    '--env', 'GOCACHE=/tmp/go-cache', '--env', 'GO111MODULE=off']
                def mount(host, target, readonly=True):
                    if ',' in str(host):
                        raise EvidenceError('Commas in Docker mount paths are unsupported')
                    command.extend(['--mount', 'type=bind,src='+str(host)+',dst='+target+(',readonly' if readonly else '')])
                mount(binary, '/public-cli/qoder')
                mount(workspace, '/workspace', kind != 'action')
                mount(profile, '/home/agent/.qoder', False)
                # Share only the dedicated CLI account; Qoder locks its own token refreshes.
                mount(auth/'.auth', '/home/agent/.qoder/.auth', False)
                mount(guard.directory, '/hook-control')
                for file in ('qoder_hook.py', 'guard_client.py', 'request_guard.py', 'read_policy.py'):
                    mount(RUNTIME/file, '/'+file)
                for key in ('HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY', 'http_proxy', 'https_proxy', 'no_proxy'):
                    if key in os.environ:
                        command.extend(['--env', key])
                command += ['--entrypoint', '/public-cli/qoder', image,
                    '--model', model['model'], '--max-turns', str(limits['requests']),
                    '--max-model-request-retries', '0', '--setting-sources', 'user', '--strict-mcp-config',
                    '--no-session-persistence', '--settings', '/home/agent/.qoder/settings.json',
                    '--permission-mode', 'bypass_permissions', '--tools', 'Bash', '-p', '--output-format', 'stream-json']
                if model.get('reasoning_effort'):
                    command += ['--reasoning-effort', model['reasoning_effort']]
                archive.atomic_json(directory/'command.json', command)
                with (directory/'stderr.log').open('w') as stderr:
                    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                               stderr=stderr, text=True, start_new_session=True)
                    def collect():
                        size = 0
                        try:
                            with (directory/'events.jsonl').open('w') as stream:
                                for line in process.stdout:
                                    size += len(line.encode())
                                    if size > 16777216:
                                        problems.append('Qoder event archive exceeds 16 MiB')
                                        process.terminate()
                                        break
                                    stream.write(line); stream.flush()
                                    event = json.loads(line)
                                    if not isinstance(event, dict):
                                        raise ValueError('Qoder event must be an object')
                                    events.append(event)
                                    message = event.get('message') or {}
                                    if event.get('type') == 'assistant':
                                        for content in message.get('content', []):
                                            if content.get('type') == 'tool_use':
                                                if content.get('name') != 'Bash':
                                                    raise ValueError('Qoder attempted a tool outside the allowed Bash boundary')
                                                tool_calls.add(content['id'])
                                    if event.get('type') == 'assistant' and not event.get('parent_tool_use_id') and message.get('stop_reason'):
                                        observed.add(message['id'])
                                    archive.atomic_json(directory/'qoder-progress.json', dict(
                                        measurement=MEASUREMENT, completed_turns=len(observed), http_requests=None))
                        except Exception as error:
                            problems.append(str(error))
                            process.terminate()
                    collector = threading.Thread(target=collect, daemon=True)
                    collector.start()
                    process.stdin.write(prompt); process.stdin.close()
                    try:
                        process.wait(timeout=limits['seconds'])
                    except subprocess.TimeoutExpired:
                        failure = ('timeout', 'Qoder stage exceeded its time limit')
                    finally:
                        stop(name, directory/'container.json')
                        stopped = True
                        if process.poll() is None:
                            process.terminate()
                        process.wait(timeout=15)
                        collector.join(timeout=10)
                        if collector.is_alive():
                            problems.append('Qoder output collector did not finish')
            completed = parse_events(events, model['model'], limits['requests'])
            if len(observed) > completed['num_turns']:
                problems.append('Qoder final turn count is smaller than observed completions')
            if failure:
                pass
            elif problems or guard.errors:
                failure = ('infrastructure_error', '; '.join(problems+guard.errors))
            elif process.returncode != 0 or completed.get('is_error') or completed.get('subtype') != 'success':
                failure = ('model_or_cli_abnormal_exit', str(completed.get('result') or completed.get('errors')))
            elif completed.get('permission_denials'):
                failure = ('tool_policy_denied', 'Qoder reported denied tools')
            meter = directory/'tool-meter/ledger.json'
            ledger = json.loads(meter.read_text()) if meter.is_file() else {}
            if tool_calls and ledger.get('tool_attempts', 0) < len(tool_calls):
                failure = ('infrastructure_error', 'Qoder did not run the mandatory tool gate for every tool call')
            if any(e.get('denied') for e in ledger.get('events', [])):
                failure = ('tool_policy_denied', 'A tool was denied by the training role policy')
        except Exception as error:
            failure = failure or ('infrastructure_error', str(error))
        finally:
            if not stopped:
                try:
                    stop(name, directory/'container.json')
                    stopped = True
                except Exception as error:
                    failure = ('infrastructure_error', 'Qoder container cleanup unconfirmed: '+str(error))
            if stopped:
                shutil.rmtree(runtime)
        turns = completed.get('num_turns') if completed else len(observed)
        output = None
        if not failure:
            try:
                (directory/'raw-answer.txt').write_text(completed['result'])
                output = validate(json.loads(completed['result']), schema)
            except (ValueError, TypeError, KeyError) as error:
                failure = ('invalid_output', str(error))
        final_sources = {k:v.decode() for k,v in capture(workspace)[0].items()} if stopped else None
        if kind != 'action' and final_sources != sources:
            failure = ('infrastructure_error', 'Read-only Qoder stage modified public files')
        result = dict(valid=failure is None, model=model, requests=turns, request_measurement=MEASUREMENT,
            turn_count_complete=completed is not None,
            http_requests=None, credits=completed.get('total_credits') if completed else None,
            tokens=None, observed_tokens=None, usage_incomplete=True, unknown_usage_requests=turns,
            output=output, error=failure[1] if failure else None, failure_type=failure[0] if failure else None,
            seconds=time.monotonic()-started,
            native_receipt=dict(status='VALID' if not failure else 'INVALID',
                stop_reason=failure[0] if failure else None, measurement=MEASUREMENT))
        if kind == 'action' and not failure:
            result['candidate_sources'] = final_sources
        archive.atomic_json(directory/'qoder-progress.json', dict(measurement=MEASUREMENT,
            completed_turns=turns, http_requests=None, credits=result['credits']))
        return result
