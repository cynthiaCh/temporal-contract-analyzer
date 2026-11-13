"""V4 isolated native LLM stages and deterministic host evaluator commands."""
import json
from pathlib import Path
import subprocess
import time
from . import archive
from .candidate_files import capture, inventory, write_files
from .core import EvidenceError, canonical
from .tempoevo_v4 import MODEL


class NativeV4Backend:
    def __init__(self, protocol):self.protocol=protocol

    def execute(self, kind, payload, model, limits, directory):
        from .execution_backend import NativeBackend
        from ._session_runtime.model_settings import MODEL as actual_model, EFFORT
        if model!=MODEL or (actual_model,EFFORT)!=('gpt-6.1-sol','medium'):raise EvidenceError('Native model drift')
        role='repair' if kind=='action' else 'analysis'
        source=directory/'public-input';write_files(source,{k:v.encode() for k,v in payload.get('candidate_sources',payload['sources']).items()})
        protocol=dict(binary=self.protocol['binary'],node=self.protocol.get('node','/usr/bin/node'),case=dict(id=self.protocol.get('task_id','v4-task')),
            execution_policy='tempoevo-trajectory-v4',visible=dict(task=payload['task']),input_path=str(source),
            candidate_files=inventory(capture(source)[0]),session_limits=limits,boundary_preflight_complete=True)
        prompt=('Use only the original task and supplied public code/documents as normative evidence. '
            'Experience and automatic Contract are fallible guidance. Evaluation observations do not create business requirements. '
            'Never access a scorer, reference implementation or hidden tests. '
            'For Action edit only business code in /workspace; preserve tests/configuration. Other stages return structured output without modifying files.\n'+canonical(payload))
        (directory/'native-stage').mkdir()
        result=NativeBackend().execute(protocol,role,prompt,payload.get('schema'),directory/'native-stage')
        usage=result.get('usage') or {};tokens=usage.get('total_usage') or usage.get('observed_usage_subtotal')
        valid=result.get('completed') is True and result.get('infrastructure_valid') is True
        out=dict(valid=valid,model=MODEL,requests=usage.get('requests_started'),tokens=tokens,output=result.get('output'),
            failure_type=('timeout' if result.get('receipt',{}).get('stop_reason')=='timeout' else result.get('receipt',{}).get('failure_class') or 'invalid_output'),
            error=result.get('bridge_error') or result.get('output_parse_error'),native_receipt=result.get('receipt'))
        if kind=='action' and valid:
            if result.get('scoring_admissible') is not True:out.update(valid=False,error='No admissible source-reading/candidate proof')
            out['candidate_sources']={k:v.decode() for k,v in capture(Path(result['final_candidate']))[0].items()}
        return out

    def evaluate(self, kind, payload, directory):
        command=payload['evaluator']['command']+[payload['candidate']]
        archive.atomic_json(directory/'command.json',command)
        try:
            run=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                timeout=payload['evaluator'].get('seconds',60),cwd=directory)
            (directory/'stdout.log').write_text(run.stdout);(directory/'stderr.log').write_text(run.stderr)
            result=json.loads(run.stdout)
            if run.returncode or not isinstance(result,dict):raise ValueError('Invalid evaluator process output')
            return dict(result,valid=True)
        except (subprocess.TimeoutExpired,ValueError,OSError) as error:
            return dict(valid=False,error=repr(error),failure_type='timeout' if isinstance(error,subprocess.TimeoutExpired) else 'invalid_output' if isinstance(error,ValueError) else 'infrastructure_error')
