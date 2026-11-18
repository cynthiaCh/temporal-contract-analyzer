"""V4 isolated native LLM stages and deterministic host evaluator commands."""
import json
from pathlib import Path
import subprocess
import time
from . import archive
from .candidate_files import capture, inventory, write_files
from .core import EvidenceError, canonical
from .tempoevo_v4 import VERSION


class NativeV4Backend:
    def __init__(self, protocol):self.protocol=protocol

    def execute(self, kind, payload, model, limits, directory):
        from .execution_backend import NativeBackend
        from ._session_runtime.model_settings import resolve_profile,validate_settings,identity
        settings=validate_settings(self.protocol.get('model_settings') or resolve_profile())
        if model!=identity(settings):raise EvidenceError('Native model drift')
        role='repair' if kind=='action' else 'analysis'
        readonly_no_tools=kind!='action' and self.protocol.get('analysis_tools') is False
        source=directory/'public-input';write_files(source,{k:v.encode() for k,v in payload.get('candidate_sources',payload['sources']).items()})
        protocol=dict(binary=self.protocol['binary'],node=self.protocol.get('node','/usr/bin/node'),case=dict(id=self.protocol.get('task_id','v4-task')),
            execution_policy=VERSION,model_settings=settings,visible=dict(task=payload['task']),input_path=str(source),
            candidate_files=inventory(capture(source)[0]),session_limits=limits,boundary_preflight_complete=True,readonly_no_tools=readonly_no_tools)
        from .prompt_context import compact
        wire_payload,context_report=compact(payload)
        if readonly_no_tools and context_report.get('compacted'):
            raise EvidenceError('Read-only tools are disabled but full public context requires workspace reads; no model call made')
        archive.atomic_json(directory/'prompt-context.json',context_report)
        prompt=('Use only the original task and supplied public code/documents as normative evidence. '
            'Experience and automatic Contract are fallible guidance. Evaluation observations do not create business requirements. '
            'Never access a scorer, reference implementation or hidden tests. '
            'For evidence cite the original task as file TASK; use exact public source paths and copy the quoted wording. '
            'For Action edit only business code in /workspace; preserve tests/configuration. '
            'Put compiled binaries/classes and caches in /tmp, not the submitted workspace. '
            'Analysis tools permit workspace reads with cat, rg, nl, head, tail and sed -n N,Mp; '
            'the public workspace may not be a Git repository, so prefer these readers to Git probes. '
            'Other stages return structured output without modifying files.\n'+canonical(wire_payload))
        if kind!='action' and not readonly_no_tools:
            prompt=('Runtime tool boundary for this read-only stage: read only /workspace public files. '
                'Use rg --files or find . -maxdepth 3 -type f; exclude folders with rg --files -g "!node_modules/**" '
                'or find . -type f -not -path "*/node_modules/*". find permits depth/type/name/path predicates, '
                '-not/-and/-or, balanced parentheses, -print and only -printf "%p\\n", "%P\\n", "%f\\n". '
                'sort permits read-only sorting flags, never -o or helper programs. rg permits ordinary pattern, glob and context flags, '
                'never --pre, pattern files or symlink following. test -f/-d/-e accepts one workspace path. '
                'Reader pipelines and &&/|| composition are permitted; no redirects, writes, scripts, command substitution, '
                'credentials, network, installations or agents. Unsupported tool syntax terminates this stage; do not try an alternative '
                'after a denial or request extra attempts. TASK is the supplied task text, not a guaranteed workspace file.\n'+prompt)
        if readonly_no_tools:
            prompt='READ-ONLY STAGE: Tools are disabled. Use the complete supplied public context and return only the requested JSON. Do not fix the candidate or call tools.\n'+prompt
        # DeepSeek accepted json_schema on wire but returned invalid JSON strings.
        # This is a format instruction, not answer repair or schema relaxation.
        if settings['provider'].get('name')=='DeepSeek':
            prompt+=('\nFINAL OUTPUT FORMAT: Return exactly one valid JSON object conforming to the supplied schema. '
                'Do not wrap it in Markdown fences or add prose outside the JSON object. '
                'Inside JSON strings, escape line breaks as \\n, quotes as \\" and backslashes as \\\\. '
                'Do not put literal line breaks inside a quoted JSON string. '
                'Formatting example only: {"report":"First line\\nSecond line with a \\"quoted\\" word."}. '
                'Use the actual stage schema and your actual findings, not the example content.')
        (directory/'native-stage').mkdir()
        backend=NativeBackend()
        if self.protocol.get('backend',{}).get('kind')=='docker':
            from .docker_backend import DockerBackend
            protocol['backend']=self.protocol['backend']
            protocol['node']=self.protocol['backend'].get('solver_node','/runtime/node16/bin/node')
            backend=DockerBackend()
        result=backend.execute(protocol,role,prompt,payload.get('schema'),directory/'native-stage')
        usage=result.get('usage') or {};tokens=usage.get('total_usage')
        valid=result.get('completed') is True and result.get('infrastructure_valid') is True
        out=dict(valid=valid,model=identity(settings),requests=usage.get('requests_started'),tokens=tokens,output=result.get('output'),
            observed_tokens=usage.get('observed_usage_subtotal'),usage_incomplete=usage.get('usage_incomplete',False),
            unknown_usage_requests=usage.get('usage_unknown_requests',0),
            failure_type=None if valid else ('timeout' if result.get('receipt',{}).get('stop_reason')=='timeout' else result.get('receipt',{}).get('failure_class') or 'invalid_output'),
            error=result.get('bridge_error') or result.get('output_parse_error'),native_receipt=result.get('receipt'))
        if not valid:
            errors=directory/'native-stage/native/archive/service-errors.json'
            if errors.exists():
                events=json.loads(errors.read_text()).get('raw_cli_errors',[])
                if events:
                    event=events[-1]['event'];out['error']=event.get('message') or (event.get('error') or {}).get('message') or out['error']
            from .stage_retry import transient_transport
            if transient_transport(result,out['error']):out['failure_type']='transient_transport_error'
            if (result.get('receipt') or {}).get('native',{}).get('blocked_tools',0):
                out['failure_type']='tool_policy_denied'
                out['output_parse_error']=result.get('output_parse_error')
                out['error']='Tool policy denied an operation; session stopped before a final answer'
                meter=directory/'native-stage/native/archive/meter/events.jsonl'
                if meter.exists():
                    denied=[json.loads(line) for line in meter.read_text().splitlines() if line.strip()]
                    denied=[row for row in denied if row.get('denied') and row.get('event',{}).get('hook_event_name') in ('PreToolUse','PermissionRequest')]
                    if denied:
                        event=denied[-1]['event'];inp=event.get('tool_input') or {}
                        out['policy_denial']=dict(tool_name=event.get('tool_name'),reason=denied[-1].get('reason'),
                            command=inp.get('command',inp.get('cmd')) if isinstance(inp,dict) else None)
                        out['error']+=': '+str(out['policy_denial']['command'] or out['policy_denial']['tool_name'])
        if kind=='action' and valid:
            if result.get('scoring_admissible') is not True:out.update(valid=False,error='Candidate or archive validation failed')
            out['candidate_sources']={k:v.decode() for k,v in capture(Path(result['final_candidate']))[0].items()}
        return out

    def evaluate(self, kind, payload, directory):
        if payload['evaluator'].get('image'):
            from .tempoevo_docker import evaluate
            return evaluate(payload,directory)
        command=payload['evaluator']['command']+[payload['candidate']]
        archive.atomic_json(directory/'command.json',command)
        try:
            run=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                timeout=payload['evaluator'].get('seconds',60),cwd=directory)
            (directory/'stdout.log').write_text(run.stdout);(directory/'stderr.log').write_text(run.stderr)
            result=json.loads(run.stdout)
            allowed=(0,1) if kind=='gold' else (0,)
            if run.returncode not in allowed or not isinstance(result,dict) or (run.returncode==1 and (result.get('passed') is True or result.get('verdict')=='PASS' or (isinstance(result.get('full_score'),dict) and result['full_score'].get('verdict')=='PASS'))):raise ValueError('Invalid evaluator process output')
            if result.get('valid') is False:return result
            return dict(result,valid=True)
        except (subprocess.TimeoutExpired,ValueError,OSError) as error:
            return dict(valid=False,error=repr(error),failure_type='timeout' if isinstance(error,subprocess.TimeoutExpired) else 'invalid_output' if isinstance(error,ValueError) else 'infrastructure_error')
