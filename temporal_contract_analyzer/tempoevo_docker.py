"""V4 container preparation and network-isolated deterministic evaluations."""
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import uuid
from . import archive
from .core import EvidenceError


def image_identity(image):
    if not isinstance(image,str) or not re.fullmatch(r'sha256:[0-9a-f]{64}',image):
        raise EvidenceError('Docker execution requires an immutable image ID')
    actual=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',image],text=True,timeout=20).strip()
    if actual!=image:raise EvidenceError('Docker image identity mismatch')
    return image


def evaluator_inputs(evaluator):
    result=[]
    for host,target in evaluator.get('inputs',{}).items():
        path=Path(host).resolve();dest=PurePosixPath(target)
        if not path.is_file() or Path(host).is_symlink():raise EvidenceError('Evaluator inputs must be regular frozen files')
        if not dest.is_absolute() or len(dest.parts)<2 or '..' in dest.parts or dest.parts[1] in ('submission','proc','dev','tmp','etc','runtime','opt'):
            raise EvidenceError('Invalid evaluator input destination')
        result.append((path,str(dest)))
    if len({target for _,target in result})!=len(result):raise EvidenceError('Duplicate evaluator mount destination')
    return result


def evaluate(payload,directory):
    from .docker_backend import container_command
    from ._session_runtime.docker_transport import stop
    ev=payload['evaluator'];directory=Path(directory);name='tca-eval-'+uuid.uuid4().hex
    try:
        image_identity(ev['image']);mounts=[(Path(payload['candidate']),'/submission')]+evaluator_inputs(ev)
        args,image=container_command(ev['image'],name,mounts)
        # Native trusted adapters compile candidate code and retain wire logs.
        # These are disposable caches, never writable benchmark source.
        for target in ('/opt/swe-tempoc/results/student-case-expansion-runtime/builds',
                       '/opt/swe-tempoc/results/student-case-expansion-runtime/go-cache',
                       '/opt/swe-tempoc/results/transfer-v4-window-runtime'):
            args+=['--tmpfs',target+':rw,exec,mode=1777,size=1g']
        command=args+['--entrypoint',ev['command'][0],image]+ev['command'][1:]+['/submission']
        archive.atomic_json(directory/'command.json',command)
        try:
            process=subprocess.run(command,capture_output=True,text=True,timeout=ev.get('seconds',60),cwd=directory)
            (directory/'stdout.log').write_text(process.stdout);(directory/'stderr.log').write_text(process.stderr)
            value=json.loads(process.stdout)
            if isinstance(value,dict) and value.get('valid') is False:return value
            gold=payload.get('purpose') in ('training_acceptance','testing_acceptance')
            if process.returncode not in ((0,1) if gold else (0,)) or not isinstance(value,dict) or (not gold and ('passed' not in value or (value['passed'] is not None and type(value['passed']) is not bool))) or (process.returncode==1 and (value.get('passed') is True or value.get('verdict')=='PASS' or (isinstance(value.get('full_score'),dict) and value['full_score'].get('verdict')=='PASS'))):
                raise ValueError('Invalid Docker evaluator result')
            return dict(value,valid=True)
        finally:stop(name,directory/'container.json')
    except (OSError,ValueError,subprocess.SubprocessError) as error:
        return dict(valid=False,error=repr(error),failure_type='timeout' if isinstance(error,subprocess.TimeoutExpired) else 'infrastructure_error')


def analyze(sources,backend):
    """Run syntax analysis on public text, with no task/scorer mounts."""
    image_identity(backend['solver_image'])
    if not re.fullmatch(r'/runtime/node(?:16|18|24)/bin/node',backend.get('solver_node','/runtime/node16/bin/node')):
        raise EvidenceError('Unsupported solver Node path')
    package=Path(__file__).parent.resolve()
    script='import json,sys; from pathlib import Path; assert not any(Path(p).exists() for p in ("/opt/swe-tempoc","/evaluation","/var/run/docker.sock","/run/docker.sock")), "Solver contains trusted grader paths"; from temporal_contract_analyzer.preanalysis import analyze_candidate; print(json.dumps(analyze_candidate(json.load(sys.stdin),node="'+backend.get('solver_node','/runtime/node16/bin/node')+'")))'
    name='tca-ast-'+uuid.uuid4().hex
    command=['docker','run','--name',name,'-i','--pull=never','--network','none','--read-only','--cap-drop','ALL',
        '--security-opt','no-new-privileges','--memory','2g','--cpus','2','--pids-limit','128',
        '--tmpfs','/tmp:rw,mode=1777','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONPATH=/analyzer',
        '--env','NODE_PATH=/runtime/frontend/node_modules','--mount','type=bind,src='+str(package)+',dst=/analyzer/temporal_contract_analyzer,readonly',
        '--entrypoint','python3',backend['solver_image'],'-B','-c',script]
    from ._session_runtime.docker_transport import stop
    try:p=subprocess.run(command,input=json.dumps(sources),capture_output=True,text=True,timeout=60)
    finally:stop(name)
    if p.returncode:raise EvidenceError('Docker AST analysis failed: '+p.stderr[-2000:])
    return json.loads(p.stdout)
