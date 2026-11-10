"""Pinned SWE-TempoC runtimes behind the existing bounded session interface."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import uuid

from . import archive
from .core import EvidenceError, canonical, sha
from .candidate_files import capture, inventory, file_modes, write_files
from .case_catalog import case_input, case_root, inside, read
from .case_evaluation import scoring_inputs, invoke, terminate, relation_states
from .evolution_backend import NativeBackend, source_hashes, validate_calibration
from ._session_runtime.docker_transport import stop


def validate_config(value):
    if not isinstance(value, dict) or set(value) != {'kind','solver_image','grader_image','grader_node'} \
            or value['kind'] != 'docker':
        raise EvidenceError('Docker backend requires kind, solver_image, grader_image and grader_node')
    if any(not isinstance(value[k], str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', value[k])
           for k in ('solver_image','grader_image')):
        raise EvidenceError('Docker requires immutable locally present image IDs; tags/pulls are not accepted')
    if not isinstance(value['grader_node'], str) or not re.fullmatch(
            r'/opt/swe-tempoc/\.swe-tempoc/toolchains/node-v(?:16\.20\.2|18\.17\.0|24\.8\.0)(?:-linux-x64)?/bin/node', value['grader_node']):
        raise EvidenceError('Choose an explicit pinned SWE-TempoC grader Node path')
    return dict(value)


def project_score(outcome, raw_sha256):
    """Preserve scoring; expose literal schedule results with derivation identity."""
    if isinstance(outcome.get('observed_effects'),dict) and outcome['observed_effects']:
        relation_states(outcome)
        return outcome
    schedules=outcome.get('schedules')
    if not isinstance(schedules,dict) or not schedules:
        raise EvidenceError('Oracle supplies no complete behavior projection')
    states={}
    for key,row in schedules.items():
        if not isinstance(key,str) or not key or not isinstance(row,dict):
            raise EvidenceError('Malformed oracle schedule')
        value=row.get('passed')
        if value is not None and type(value) is not bool:raise EvidenceError('Invalid schedule passed value')
        states[key]=value
    return dict(outcome,behavior_states=states,behavior_projection=dict(
        kind='derived_explicit_schedule_passed',raw_sha256=raw_sha256,
        rule='Copy literal passed; missing/null remains unknown. No policy or cause inference.'))


def container_command(image, name, mounts=(), network='none'):
    args = ['docker','run','-i','--pull=never','--name',name,'--read-only','--cap-drop','ALL',
            '--security-opt','no-new-privileges','--network',network,'--init',
            '--user',str(os.getuid())+':'+str(os.getgid()),'--memory','8g','--cpus','4',
            '--pids-limit','512','--tmpfs','/tmp:rw,exec,mode=1777,size=4g',
            '--env','HOME=/tmp','--env','PYTHONDONTWRITEBYTECODE=1']
    for source, destination in mounts:
        source = str(Path(source).resolve())
        if ',' in source:raise EvidenceError('Commas in bind paths are unsupported')
        args += ['--mount','type=bind,src='+source+',dst='+destination+',readonly']
    return args, image


def captured(command, directory, name, payload=None, seconds=60):
    """Keep both streams and daemon cleanup evidence on every exit path."""
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    archive.atomic_json(directory/'command.json',command)
    process=None
    try:
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,text=True,start_new_session=True)
        try:out,err=process.communicate(payload,timeout=seconds)
        except BaseException:
            terminate(process)
            out,err=process.communicate()
            (directory/'stdout').write_text(out or '')
            (directory/'stderr').write_text(err or '')
            raise
        (directory/'stdout').write_text(out)
        (directory/'stderr').write_text(err)
        archive.atomic_json(directory/'execution.json',dict(exit_code=process.returncode))
        if process.returncode:raise EvidenceError('Docker command failed; see '+str(directory/'stderr'))
        return json.loads(out)
    finally:
        stop(name,directory/'container.json')


class DockerBackend(NativeBackend):
    kind='swe_tempoc_docker'

    def session_options(self, protocol):
        return dict(transport=dict(solver_image=protocol['backend']['solver_image'],
            node=protocol['node'],name='tca-session-'+uuid.uuid4().hex))

    def stop_external(self, request, directory):
        stop(request['transport']['name'],Path(directory)/'bridge-container.json')

    def _case(self, protocol):
        record=protocol['case'];root=case_root(record)
        manifest_path=inside(root,record['manifest']);manifest=read(manifest_path)
        if record['source']=='local':
            return manifest, '/evaluation/case', [(manifest_path.parent,'/evaluation/case')]
        # The trusted image supplies the benchmark, verified against host hashes.
        return manifest, str(Path('/opt/swe-tempoc')/Path(record['manifest']).parent), []

    def environment(self, protocol, directory):
        config=validate_config(protocol['backend']);directory=Path(directory)
        if not shutil.which('docker'):raise EvidenceError('Docker CLI is unavailable')
        if not re.fullmatch(r'/runtime/node(?:16|18|24)/bin/node',protocol['node']):
            raise EvidenceError('Choose a public solver Node path')
        for key in ('solver_image','grader_image'):
            observed=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',config[key]],
                                             text=True,timeout=20).strip()
            if observed!=config[key]:raise EvidenceError('Pinned Docker image mismatch')
        binary=Path(protocol['binary'])
        if not binary.is_file() or protocol['executable_sha256'].get(str(binary))!=sha(binary.read_bytes()):
            raise EvidenceError('Prepared public Codex executable changed')
        for path,code in protocol['backend_sources'].items():
            if sha(Path(path).read_bytes())!=code:raise EvidenceError('Runner changed')
        if scoring_inputs(protocol['case'])!=protocol['scoring_inputs']:
            raise EvidenceError('Original candidate, manifest or scorer changed')
        manifest, case, mounts=self._case(protocol)
        if protocol['case']['adapter'] not in ('legacy-js','python') or \
                (protocol['case']['adapter']=='legacy-js' and
                 manifest.get('framework',{}).get('runtime')!='vanilla-js'):
            raise EvidenceError('Docker admission currently requires self-contained vanilla-js or Python; frontend/upstream dependency setup is not validated')
        name='tca-check-'+uuid.uuid4().hex
        args,image=container_command(config['solver_image'],name,[(binary,'/opt/codex')])
        solver_code='''import json,pathlib,subprocess,sys
for path in ['/opt/swe-tempoc','/evaluation','/var/run/docker.sock','/run/docker.sock']:
 if pathlib.Path(path).exists():raise ValueError('Forbidden solver path: '+path)
print(json.dumps(dict(python=sys.version.split()[0],node=subprocess.check_output([sys.argv[1],'--version'],text=True).strip(),codex=subprocess.check_output(['/opt/codex','--version'],text=True).strip())))
'''
        solver=captured(args+['--entrypoint','python3',image,'-B','-c',solver_code,protocol['node']],
                        directory/'solver',name,seconds=30)
        if protocol['case']['adapter']=='python':
            minimum=tuple(int(n) for n in manifest.get('runtime',{}).get('minimum_version','3.9').split('.'))
            if tuple(map(int,solver['python'].split('.')))<minimum:
                raise EvidenceError('Solver Python does not meet the original case runtime')
        expected={}
        if protocol['case']['source']=='bench':
            root=case_root(protocol['case'])
            expected={str(Path('/opt/swe-tempoc')/Path(p).relative_to(root)):code
                      for p,code in protocol['scoring_inputs'].items()}
        name='tca-check-'+uuid.uuid4().hex
        args,image=container_command(config['grader_image'],name,mounts)
        grader_code='''import hashlib,json,pathlib,subprocess,sys
expected=json.load(sys.stdin)
for path,code in expected.items():
 if hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()!=code:raise ValueError('Image scorer/source mismatch: '+path)
python=sys.version.split()[0]
node=subprocess.check_output([sys.argv[1],'--version'],text=True).strip()
print(json.dumps(dict(python=python,node=node)))
'''
        grader=captured(args+['--entrypoint','python3',image,'-B','-c',grader_code,config['grader_node']],
                        directory/'grader',name,json.dumps(expected),seconds=30)
        if protocol['case']['adapter']=='python':
            if tuple(map(int,grader['python'].split('.')))<minimum:
                raise EvidenceError('Grader Python does not meet the original case runtime')
            executable='/usr/local/bin/python3';version=grader['python']
        else:
            framework=manifest.get('framework',{})
            if framework.get('runtime')=='vanilla-js' and grader['node'].lstrip('v')!=framework['version'].lstrip('v'):
                raise EvidenceError('Grader Node differs from original manifest')
            if solver['node']!=grader['node']:raise EvidenceError('Solver/grader Node mismatch')
            executable=config['grader_node'];version=grader['node']
        result=dict(path=executable,version=version,image_id=config['grader_image'],
                    solver_image_id=config['solver_image'],solver_runtime=solver)
        archive.atomic_json(directory/'runtime.json',result)
        return result

    def preflight(self, protocol):
        # Fresh checks are offline; no connection request or reference re-scoring.
        directory=Path(protocol['input_path']).parent/'preflight'/uuid.uuid4().hex
        observed=self.environment(protocol,directory)
        validate_calibration(protocol,observed)

    def raw_score(self, protocol, candidate, directory):
        """One unchanged trusted oracle invocation, also used for offline calibration."""
        directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
        files,_=capture(Path(candidate));subject=directory/'candidate'
        write_files(subject,files,file_modes(Path(candidate),files))
        record=protocol['case'];manifest,case,mounts=self._case(protocol)
        if record['authorization']!='ungranted':raise EvidenceError('Unsupported score authorization')
        config=protocol['backend'];name='tca-grade-'+uuid.uuid4().hex
        args,image=container_command(config['grader_image'],name,mounts+[(subject,'/submission')])
        probe=str(Path(case)/manifest['oracle']['probe'])
        if record['adapter']=='python':command=['--entrypoint','python3',image,'-B',probe,'/submission']
        else:command=['--entrypoint',config['grader_node'],image,probe,'/submission','ungranted']
        archive.atomic_json(directory/'evaluation.json',dict(command=args+command,
            candidate_files=inventory(files),image_id=config['grader_image']))
        try:outcome=invoke(args+command,directory/'oracle',threading.Event(),terminate,record['id'])
        finally:stop(name,directory/'container.json')
        after,_=capture(subject)
        if inventory(after)!=inventory(files):raise EvidenceError('Scorer changed candidate')
        projected=project_score(outcome,sha((directory/'oracle/stdout.json').read_bytes()))
        archive.atomic_json(directory/'projected-score.json',projected)
        return projected

    def score(self, protocol, candidate, directory):
        self.preflight(protocol)
        return self.raw_score(protocol,candidate,directory)


def offline(config, root, calibrate=False):
    """Explicit zero-model runtime check and optional three-control calibration."""
    required={'case_id','binary','node','backend'} | ({'degenerate_candidate'} if calibrate else set())
    if not isinstance(config,dict) or set(config)!=required:raise EvidenceError('Invalid Docker check/calibration fields')
    root=Path(root).resolve()
    if root.exists():raise EvidenceError('Use a new offline check directory')
    backend=validate_config(config['backend']);inputs=case_input(config['case_id'])
    files,_=capture(Path(inputs['candidate']));sources={k:v.decode('utf-8') for k,v in files.items()}
    binary=str(Path(config['binary']).resolve())
    protocol=dict(case=inputs['case_record'],binary=binary,node=config['node'],backend=backend,
                  backend_sources=source_hashes(),executable_sha256={binary:sha(Path(binary).read_bytes())},
                  candidate_sha256=sha(canonical(sources).encode()),scoring_inputs=scoring_inputs(inputs['case_record']))
    root.mkdir(parents=True)
    archive.atomic_json(root/'check-input.json',config)
    archive.atomic_json(root/'binding.json',protocol)
    implementation=DockerBackend()
    try:
        observed=implementation.environment(protocol,root/'environment')
        if not calibrate:
            result=dict(status='offline_check_passed',runtime=observed,model_calls=0)
        else:
            case=inside(case_root(protocol['case']),protocol['case']['manifest']).parent
            manifest=read(case/Path(protocol['case']['manifest']).name)
            ref=manifest['reference'] if protocol['case']['adapter']=='python' else manifest['references']['bounded']
            reference=root/'reference';shutil.copytree(inputs['candidate'],reference)
            shutil.copytree(inside(case,ref),reference,dirs_exist_ok=True)
            evidence={};vectors={}
            for role,candidate in [('original',inputs['candidate']),('reference',reference),('degenerate',config['degenerate_candidate'])]:
                outcome=implementation.raw_score(protocol,Path(candidate),root/role/'score')
                path=root/role/'score.json';archive.atomic_json(path,outcome)
                evidence[role]=dict(path=str(path),sha256=sha(path.read_bytes()))
                vectors[role]=relation_states(outcome)
            if any(set(v)!=set(vectors['reference']) for v in vectors.values()) \
                    or any(v is not True for v in vectors['reference'].values()):
                raise EvidenceError('Incomplete or conflicting calibration behavior vectors')
            calibration=dict(case_id=config['case_id'],candidate_sha256=protocol['candidate_sha256'],
                scoring_inputs_sha256=sha(canonical(protocol['scoring_inputs']).encode()),runtime=observed,evidence=evidence)
            protocol['calibration']=calibration
            validate_calibration(protocol,observed)
            archive.atomic_json(root/'calibration.json',calibration)
            result=dict(status='offline_calibration_passed',runtime=observed,model_calls=0,
                        calibration=str(root/'calibration.json'))
    except BaseException as error:
        archive.atomic_json(root/'result.json',dict(status='blocked',error=repr(error),model_calls=0))
        raise
    archive.atomic_json(root/'result.json',result)
    return result
