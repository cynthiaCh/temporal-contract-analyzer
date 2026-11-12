"""Explicit bounded adapter to the packaged single-session runner.

Only the named runner dependencies are copied. No scheduler is imported. Reading
this module never launches a model; NativeBackend.execute is an explicit action.
"""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading

from . import archive
from .core import EvidenceError, sha, canonical
from .candidate_files import capture, inventory, file_modes, write_files
from .case_evaluation import scoring_inputs, terminate

SOURCE = Path(__file__).resolve().parent/'_session_runtime'
DEPENDENCIES = ('runner.py','native_backend.py','archive.py','guard_server.py','guard_client.py',
                'request_guard.py','read_policy.py','usage.py','structured.py','schema_validator.py','docker_transport.py',
                'research-config.toml','maintenance.schema.json','extraction.schema.json')
ROLES = {
    'analysis':dict(model='gpt-6-sol', effort='low', requests=12, seconds=600),
    'repair':dict(model='gpt-5.6-terra', effort='low', requests=24, seconds=600),
    'reflect':dict(model='gpt-5.6-terra', effort='medium', requests=12, seconds=600)}
ROLES.update(contract_check=dict(model='gpt-6-sol',effort='low',requests=4,seconds=600),
             candidate_check=dict(model='gpt-5.6-terra',effort='medium',requests=4,seconds=600))
DRIVER = '''import json,sys
from pathlib import Path
import runner
v=json.load(sys.stdin)
runner.backend.BINARY=Path(v['binary'])
case={'node':v['node'],'task_sha256':v['task_sha256']}
case['reflection_readonly']=v['config'].get('reflection_readonly',False)
if v.get('candidate_files') is not None:case['candidate_files']=v['candidate_files']
r=runner.session(v['slot'],v['prompt'],case=case,candidate=Path(v['candidate']),
 task=v['task'],config=v['config'],run_dir=Path(v['run_dir']),allow_model_execution=True,transport=v.get('transport'))
print(json.dumps(r))
'''


def stop_tree(process):
    """Terminate only this bridge and its descendants after an outer timeout."""
    children={process.pid}
    pending=[]
    for entry in Path('/proc').iterdir():
        if entry.name.isdigit():
            try:
                parent=int((entry/'status').read_text().split('PPid:\t')[1].splitlines()[0])
                pending.append((int(entry.name),parent))
            except (OSError,ValueError,IndexError):pass
    while True:
        added={pid for pid,parent in pending if parent in children}-children
        if not added:break
        children.update(added)
    for pid in sorted(children,reverse=True):
        try:os.killpg(pid,signal.SIGKILL)
        except ProcessLookupError:
            try:os.kill(pid,signal.SIGKILL)
            except ProcessLookupError:pass


def validate_calibration(protocol, observed_runtime):
    if scoring_inputs(protocol['case']) != protocol['scoring_inputs']:
        raise EvidenceError('Evaluator or original candidate changed')
    calibration = protocol['calibration']
    required = {'case_id','candidate_sha256','scoring_inputs_sha256','runtime','evidence'}
    if not isinstance(calibration,dict) or set(calibration)!=required \
            or calibration['case_id']!=protocol['case']['id'] \
            or calibration['candidate_sha256']!=protocol['candidate_sha256'] \
            or calibration['scoring_inputs_sha256']!=sha(canonical(protocol['scoring_inputs']).encode()) \
            or calibration['runtime']!=observed_runtime \
            or not isinstance(calibration['evidence'],dict) \
            or set(calibration['evidence'])!={'original','reference','degenerate'}:
        raise EvidenceError('Missing version-bound reusable calibration evidence')
    for role, source in calibration['evidence'].items():
        if not isinstance(source,dict) or set(source)!={'path','sha256'} \
                or sha(Path(source['path']).read_bytes()) != source['sha256']:
            raise EvidenceError('Calibration evidence changed')
        outcome=json.loads(Path(source['path']).read_text(encoding='utf-8'))
        schedules=outcome.get('schedules',{}) if isinstance(outcome,dict) else {}
        nested_error=isinstance(schedules,dict) and any(isinstance(row,dict) and row.get('runtimeError')
                                                      for row in schedules.values())
        if not isinstance(outcome,dict) or outcome.get('case_id')!=protocol['case']['id'] \
                or outcome.get('verdict') not in ('PASS','UNDERREACH','OVERREACH','UNDERREACH_AND_OVERREACH') \
                or (role=='reference' and outcome['verdict']!='PASS') \
                or (role=='degenerate' and outcome['verdict']=='PASS') or outcome.get('runtime_errors') or nested_error:
            raise EvidenceError('Calibration outcomes are not trustworthy for their declared roles')


class NativeBackend:
    """Isolated native calls plus trusted external scoring; no fallback/retries."""
    kind = 'native_research_runner'

    def preflight(self, protocol):
        from .case_catalog import case_root, inside, read
        from .case_evaluation import runtime
        if not shutil.which('bwrap') or not Path(protocol['binary']).is_file() \
                or not Path(protocol['node']).is_file():
            raise EvidenceError('Native execution requires the explicit Codex binary, node and bwrap')
        manifest = read(inside(case_root(protocol['case']), protocol['case']['manifest']))
        observed_runtime=runtime(manifest, protocol['case']['adapter'], protocol['node'])
        validate_calibration(protocol, observed_runtime)

    def session_options(self, protocol):
        return {}

    def stop_external(self, request, directory):
        pass

    def execute(self, protocol, role, prompt, schema, directory):
        logical_role=role
        role={'contract_check':'analysis','candidate_check':'reflect'}.get(role,role)
        if not protocol.get('boundary_preflight_complete'):self.preflight(protocol)
        directory = Path(directory)
        backend = directory/'backend'
        backend.mkdir()
        for name in DEPENDENCIES:
            shutil.copyfile(Path(protocol.get('runtime_source',SOURCE))/name, backend/name)
        schema_name='analysis.schema.json' if role=='analysis' else 'reflection.schema.json'
        archive.atomic_json(backend/schema_name, schema or dict(type='object'))
        (backend/'driver.py').write_text(DRIVER, encoding='utf-8')
        lightweight=protocol.get('execution_policy') in ('experience-development-v2','experience-evaluation-v2',
            'experience-development-v3','experience-validation-v3','experience-evaluation-v3')
        frozen = {} if lightweight else {str(p.resolve()):sha(p.read_bytes()) for p in backend.iterdir() if p.is_file()}
        task_path=directory/'task.md'
        task_path.write_text(protocol['visible']['task'],encoding='utf-8')
        task_sha=sha(task_path.read_bytes())
        if not lightweight:frozen[str(task_path.resolve())]=task_sha
        limits=protocol.get('session_limits',ROLES[logical_role])
        if type(limits['requests']) is not int or not 0<limits['requests']<=ROLES[logical_role]['requests'] \
                or not 0<limits['seconds']<=ROLES[role]['seconds']:
            raise EvidenceError('Session limits cannot exceed the fixed role budget')
        evidence=protocol.get('reflection_evidence_path') if role=='reflect' else None
        request = dict(binary=protocol['binary'], node=protocol['node'],
            slot=dict(slot=directory.name, phase=role,logical_role=logical_role), prompt=prompt, task=str(task_path.resolve()),
            task_sha256=task_sha,candidate_files=None if evidence else protocol.get('candidate_files'),
            candidate=evidence or protocol['input_path'], run_dir=str((directory/'native').resolve()),
            config=dict(frozen_files=frozen,seconds_per_session=limits['seconds'],
                        requests_per_session=limits['requests'],protocol_schema=protocol.get('execution_policy'),
                        reflection_readonly=bool(evidence)))
        request.update(self.session_options(protocol))
        archive.atomic_json(directory/'native-request.json',request)
        cleanup_error=None
        process=subprocess.Popen([sys.executable,'-B',str(backend/'driver.py')],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
            cwd=str(backend),start_new_session=True)
        try:
            stdout,stderr=process.communicate(json.dumps(request),timeout=ROLES[role]['seconds']+90)
        except subprocess.TimeoutExpired as error:
            stop_tree(process)
            stdout,stderr=process.communicate()
            (directory/'bridge-partial.stdout').write_text(stdout or '',encoding='utf-8')
            (directory/'bridge-partial.stderr').write_text(stderr or '',encoding='utf-8')
            return self.invalid(directory,'Native bridge timeout; partial material retained, no retry')
        except BaseException:
            stop_tree(process)
            stdout,stderr=process.communicate()
            (directory/'bridge-partial.stdout').write_text(stdout or '',encoding='utf-8')
            (directory/'bridge-partial.stderr').write_text(stderr or '',encoding='utf-8')
            raise
        finally:
            try:self.stop_external(request, directory)
            except Exception as error:
                cleanup_error=repr(error)
                archive.atomic_json(directory/'bridge-cleanup-error.json',dict(error=cleanup_error,
                    original_service_material='bridge streams and native archive retained separately'))
        (directory/'bridge.stdout').write_text(stdout,encoding='utf-8')
        (directory/'bridge.stderr').write_text(stderr,encoding='utf-8')
        if cleanup_error:return self.invalid(directory,'Container cleanup unconfirmed; see bridge-cleanup-error.json')
        if process.returncode:
            return self.invalid(directory,'Native bridge failed; see retained stderr and native archive')
        try:receipt = json.loads(stdout)
        except ValueError:return self.invalid(directory,'Native bridge response could not be parsed')
        archive.atomic_json(directory/'native-receipt.json',receipt)
        native = directory/'native/archive'
        usage = json.loads((native/'usage.json').read_text()) if (native/'usage.json').is_file() else None
        raw = (native/'raw-answer.txt').read_text(encoding='utf-8')
        # The full raw response exists before parsing. No manual completion.
        try:output=json.loads(raw);parse_error=None
        except ValueError:output=None;parse_error='Incomplete or non-JSON answer; raw bytes retained'
        return dict(completed=receipt.get('candidate_complete') is True and parse_error is None,
            infrastructure_valid=receipt.get('infrastructure_valid') is True
                and not receipt.get('archive_failure_requires_stop'),
            scoring_admissible=receipt.get('scoring_admissible') is True if role=='repair' else True,
            output=output, output_parse_error=parse_error, final_candidate=receipt.get('final_candidate'),
            patch=(native/'patch.diff').read_text(encoding='utf-8') if (native/'patch.diff').is_file() else '',
            receipt=receipt, usage=usage)

    def invalid(self,directory,error):
        usage_path=Path(directory)/'native/archive/usage.json'
        try:usage=json.loads(usage_path.read_text())
        except (OSError,ValueError):usage=None
        return dict(completed=False,infrastructure_valid=False,scoring_admissible=False,
                    output=None,usage=usage,bridge_error=error)

    def score(self, protocol, candidate, directory):
        from .case_evaluation import invoke, runtime
        from .case_catalog import case_root, inside, read
        if not protocol.get('boundary_preflight_complete'):self.preflight(protocol)
        directory = Path(directory)
        files,_ = capture(Path(candidate))
        subject=directory/'candidate'
        write_files(subject,files,file_modes(Path(candidate),files))
        record=protocol['case'];case_path=inside(case_root(record),record['manifest']);manifest=protocol.get('frozen_manifest') or read(case_path)
        if record['authorization']!='ungranted':raise EvidenceError('Unsupported score authorization')
        probe=Path(protocol['frozen_probe']) if protocol.get('frozen_probe') else inside(case_path.parent,manifest['oracle']['probe'])
        environment=protocol['calibration']['runtime'] if protocol.get('boundary_preflight_complete') else runtime(manifest,record['adapter'],protocol['node'])
        command=([environment['path'],'-B',str(probe),str(subject)] if record['adapter']=='python'
                 else [environment['path'],str(probe),str(subject),'ungranted'])
        archive.atomic_json(directory/'evaluation.json',dict(command=command,runtime=environment,
            calibration='reused_frozen_original_reference_degenerate_evidence',candidate_files=inventory(files)))
        outcome=invoke(command,directory/'oracle',threading.Event(),terminate,record['id'])
        after,_=capture(subject)
        if inventory(after)!=inventory(files):raise EvidenceError('Scorer changed the frozen candidate')
        return outcome
