"""Qoder Credits stages in isolated solver containers, with explicit turn accounting."""
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import threading
import time
import uuid

from . import archive
from .candidate_files import EXCLUDED, capture, write_files
from .core import EvidenceError, canonical
from ._session_runtime.schema_validator import validate

REPO = Path(__file__).resolve().parents[1]
RUNTIME = Path(__file__).with_name('_session_runtime')
MEASUREMENT = 'qoder_model_turns'
ALLOWED_TOOLS = {'Bash', 'Read'}


def cleanup_runtime(runtime):
    """Retry transient host permissions only after the owned container stops."""
    errors = []
    for attempt, delay in enumerate((0, 0.1, 0.5, 1), 1):
        if delay:
            time.sleep(delay)
        try:
            shutil.rmtree(runtime)
        except FileNotFoundError:
            if runtime.exists():
                errors.append('A runtime child disappeared during cleanup')
                continue
        except OSError as error:
            errors.append(str(error))
            if isinstance(error, PermissionError):
                continue
            return dict(complete=False, attempts=attempt, errors=errors)
        return dict(complete=True, attempts=attempt, errors=errors)
    return dict(complete=False, attempts=4, errors=errors)


def confirmed_refusals(events, ledger):
    """Recover only requests proven blocked by our hook, never executed tools."""
    requests, blocked = {}, set()
    for event in events:
        if event.get('type') not in ('assistant', 'user'):
            continue
        for item in (event.get('message') or {}).get('content', []):
            if event.get('type') == 'assistant' and item.get('type') == 'tool_use':
                requests[item.get('id')] = item.get('name')
            if event.get('type') == 'user' and item.get('type') == 'tool_result' and item.get('is_error') is True:
                text = str(item.get('content', ''))
                if 'hook blocking error' in text and '/qoder_hook.py' in text:
                    blocked.add(item.get('tool_use_id'))
    confirmed = set()
    for row in ledger.get('events', []):
        if not row.get('denied'):
            continue
        event = row.get('event') or {}
        key = event.get('tool_use_id')
        name = event.get('qoder_original_tool', event.get('tool_name'))
        if key not in blocked or requests.get(key) != name or name not in ALLOWED_TOOLS:
            raise ValueError('Tool denial lacks matching CLI proof that the hook blocked execution')
        confirmed.add(key)
    return confirmed


def decode_output(text):
    """Decode one JSON value, with the existing unambiguous wrapper support."""
    try:
        output = json.loads(text)
    except json.JSONDecodeError:
        start = text.find('{')
        if start < 0:
            raise ValueError('Qoder did not return a JSON object')
        output, end = json.JSONDecoder().raw_decode(text, start)
        if text[end:].strip() not in ('', '```'):
            raise ValueError('Qoder returned ambiguous content after its JSON object')
    return output


def parse_output(text, schema):
    return validate(decode_output(text), schema)


def escape_report_whitespace(text):
    """Escape literal whitespace only in a top-level report string, losslessly."""
    start = text.find('{')
    if start < 0:
        raise ValueError('Qoder did not return a JSON object')
    chunks, counts = [text[:start]], {}
    depth, key, previous, i = 0, None, None, start
    escapes = {'\n': ('\\n', 'newline'), '\r': ('\\r', 'carriage_return'), '\t': ('\\t', 'tab')}
    while i < len(text):
        char = text[i]
        if char == '"':
            value, end = json.decoder.scanstring(text, i+1, False)
            body = text[i+1:end-1]
            controls = [c for c in body if ord(c) < 32]
            is_key = depth == 1 and text[end:].lstrip().startswith(':')
            if controls:
                if depth != 1 or key != 'report' or previous != ':' or is_key or any(c not in escapes for c in controls):
                    raise ValueError('Literal control characters are allowed only as report whitespace')
                for control in controls:
                    name = escapes[control][1]
                    counts[name] = counts.get(name, 0)+1
                body = ''.join(escapes[c][0] if c in escapes else c for c in body)
            chunks.append('"'+body+'"')
            key = value if is_key else None
            previous, i = '"', end
            continue
        chunks.append(char)
        if char in '{[':
            depth += 1
        elif char in '}]':
            depth -= 1
        if not char.isspace():
            previous = char
        i += 1
    return ''.join(chunks), counts


def parse_action_report(text, schema, *, format_warnings=None):
    """Separate Action report metadata; all declared fields remain validated."""
    report_schema = json.loads((RUNTIME/'maintenance.schema.json').read_text())
    counts = {}
    try:
        output = decode_output(text)
    except json.JSONDecodeError as error:
        if schema != report_schema or not error.msg.startswith('Invalid control character'):
            raise
        normalized, counts = escape_report_whitespace(text)
        output = decode_output(normalized)
    if schema != report_schema or not isinstance(output, dict):
        return validate(output, schema), {}
    extras = {key:value for key,value in output.items() if key not in schema['properties']}
    report = {key:value for key,value in output.items() if key in schema['properties']}
    checked = validate(report, schema)
    if counts and format_warnings is not None:
        format_warnings.append(dict(code='action_report_literal_whitespace', characters=counts))
    return checked, extras


def readable_candidate(root):
    """Restore owner access to stopped candidate files, including sed temp files."""
    changed = []
    def restore(path, directory=False):
        mode = path.lstat()
        if stat.S_ISLNK(mode.st_mode) or not (stat.S_ISDIR(mode.st_mode) if directory else stat.S_ISREG(mode.st_mode)):
            raise EvidenceError('Candidate inputs must be regular files/directories: '+str(path))
        required = 0o700 if directory else 0o400
        if mode.st_mode & required != required:
            if mode.st_uid != os.getuid():
                raise EvidenceError('Candidate file is not owned by the workspace user: '+str(path))
            new_mode = stat.S_IMODE(mode.st_mode) | required
            path.chmod(new_mode)
            changed.append(dict(path=path.relative_to(root).as_posix(), before=stat.S_IMODE(mode.st_mode), after=new_mode))
    restore(root, True)
    def onerror(error):
        raise error
    for current, dirs, names in os.walk(root, followlinks=False, onerror=onerror):
        for name in list(dirs):
            if name.startswith('.') or name in EXCLUDED:
                dirs.remove(name)
            else:
                restore(Path(current)/name, True)
        for name in names:
            if not name.startswith('.'):
                restore(Path(current)/name)
    return changed


def tool_requests(events):
    """A rejected request is not an executed tool; require CLI error evidence."""
    requested, rejected, results = {}, set(), {}
    interrupted = ('Error: Tool was not executed because the model response was interrupted '
                   'before its arguments were fully received. Reissue the call with complete arguments.')
    for event in events:
        message = event.get('message') or {}
        if event.get('type') == 'assistant':
            for content in message.get('content', []):
                if content.get('type') == 'tool_use':
                    key = content['id']
                    if key in requested and requested[key] != content.get('name'):
                        raise ValueError('Conflicting Qoder tool request identity')
                    requested[key] = content.get('name')
        elif event.get('type') == 'user':
            for content in message.get('content', []):
                if content.get('type') == 'tool_result':
                    results.setdefault(content['tool_use_id'], []).append(content)
                    if content.get('is_error') is True:rejected.add(content['tool_use_id'])
    unsupported = {key:name for key,name in requested.items() if name not in ALLOWED_TOOLS}
    if set(unsupported)-rejected:
        raise ValueError('Qoder did not confirm rejection of unavailable tools: '+', '.join(sorted(set(unsupported.values()))))
    not_executed = {key for key,rows in results.items()
                    if all(row.get('is_error') is True and row.get('content') == interrupted for row in rows)}
    return {key for key,name in requested.items() if name in ALLOWED_TOOLS}-not_executed, unsupported


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
                  'Use only Bash and Read. Read is limited to public files in /workspace; MCP, external discovery, subagents and other tools are unavailable. '
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
        events, problems, observed = [], [], set()
        process = None
        stopped = False
        started = time.monotonic()
        failure = None
        completed = None
        refusals = set()
        runtime_cleanup = None
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
                    '--env', 'TCA_QODER_STAGE='+kind,
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
                    '--permission-mode', 'bypass_permissions', '--tools', 'Bash,Read',
                    '--disallowed-tools', 'mcp_call,mcp_get,mcp_list', '-p', '--output-format', 'stream-json',
                    '--append-system-prompt', 'Return exactly one JSON object matching the OUTPUT_SCHEMA in the task. '
                    'Do not add undeclared fields, including null-valued fields. Do not add prose or Markdown fences.']
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
            if problems:
                raise ValueError('; '.join(problems))
            completed = parse_events(events, model['model'], limits['requests'])
            tool_calls, rejected_tools = tool_requests(events)
            archive.atomic_json(directory/'tool-requests.json', dict(
                allowed_request_ids=sorted(tool_calls), rejected_unavailable_requests=rejected_tools))
            if len(observed) > completed['num_turns']:
                problems.append('Qoder final turn count is smaller than observed completions')
            if failure:
                pass
            elif problems or guard.errors:
                failure = ('infrastructure_error', '; '.join(problems+guard.errors))
            elif process.returncode != 0 or completed.get('is_error') or completed.get('subtype') != 'success':
                failure = ('model_or_cli_abnormal_exit', str(completed.get('result') or completed.get('errors')))
            meter = directory/'tool-meter/ledger.json'
            ledger = json.loads(meter.read_text()) if meter.is_file() else {}
            refusals = confirmed_refusals(events, ledger)
            accepted_denials = dict(rejected_tools)
            for row in ledger.get('events', []):
                event = row.get('event') or {}
                if row.get('denied') and event.get('tool_use_id') in refusals:
                    accepted_denials[event['tool_use_id']] = event.get('qoder_original_tool', event.get('tool_name'))
            if any(not isinstance(d,dict) or d.get('tool_use_id') not in accepted_denials
                   or accepted_denials[d['tool_use_id']] != d.get('tool_name')
                   for d in completed.get('permission_denials', [])):
                failure = ('tool_policy_denied', 'Qoder reported an unconfirmed tool denial')
            if tool_calls and ledger.get('tool_attempts', 0) < len(tool_calls) and not failure:
                failure = ('infrastructure_error', 'Qoder did not run the mandatory tool gate for every tool call')
            if (failure and failure[0] == 'model_or_cli_abnormal_exit'
                    and completed.get('error_code') == 'network_failure'
                    and not guard.errors and not refusals):
                failure = ('transient_transport_error', failure[1])
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
                runtime_cleanup = cleanup_runtime(runtime)
                archive.atomic_json(directory/'runtime-cleanup.json', runtime_cleanup)
        turns = completed.get('num_turns') if completed else len(observed)
        output = None
        report_extras = {}
        format_warnings = []
        if completed and isinstance(completed.get('result'), str):
            (directory/'raw-answer.txt').write_text(completed['result'])
        if not failure:
            try:
                if kind == 'action':
                    output, report_extras = parse_action_report(completed['result'], schema, format_warnings=format_warnings)
                    if report_extras:
                        format_warnings.append(dict(code='action_report_extra_fields', fields=sorted(report_extras)))
                    if format_warnings:
                        archive.atomic_json(directory/'output-format.json', dict(
                            policy='action-report-format-v2', warnings=format_warnings, extra_fields=report_extras))
                else:
                    output = parse_output(completed['result'], schema)
            except (ValueError, TypeError, KeyError) as error:
                failure = ('invalid_output', str(error))
        final_sources = None
        if stopped:
            try:
                if kind == 'action':
                    archive.atomic_json(directory/'candidate-permissions.json', readable_candidate(workspace))
                final_sources = {k:v.decode() for k,v in capture(workspace)[0].items()}
            except (OSError, ValueError, EvidenceError) as error:
                failure = ('infrastructure_error', 'Candidate snapshot failed: '+str(error))
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
        result['blocked_tool_requests'] = len(refusals)
        result['runtime_cleanup'] = runtime_cleanup
        result['format_warnings'] = format_warnings
        result['action_report_extra_fields'] = report_extras
        result['cleanup_warning'] = ('Qoder host runtime cleanup pending: '+runtime_cleanup['errors'][-1]
            if runtime_cleanup and not runtime_cleanup['complete'] else None)
        if kind == 'action' and not failure:
            result['candidate_sources'] = final_sources
        archive.atomic_json(directory/'qoder-progress.json', dict(measurement=MEASUREMENT,
            completed_turns=turns, http_requests=None, credits=result['credits']))
        return result
