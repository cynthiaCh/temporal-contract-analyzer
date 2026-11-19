"""Run trusted bench oracles after agent work, outside agent-visible inputs."""
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

from . import archive
from .case_catalog import bench_root, case_root, inside, read
from .core import EvidenceError, sha
from .candidate_files import capture

VERDICTS = {'PASS', 'UNDERREACH', 'OVERREACH', 'UNDERREACH_AND_OVERREACH'}


def runtime(manifest, adapter, node):
    if adapter == 'python':
        minimum = tuple(int(n) for n in manifest.get('runtime', {}).get('minimum_version', '3.9').split('.'))
        candidates = [os.environ.get('TCA_PYTHON_BIN'), sys.executable,
                      shutil.which('python3.13'), shutil.which('python3.12'), shutil.which('python3.11'), shutil.which('python3')]
    else:
        config_path = bench_root()/'.bench.local.json'
        config = read(config_path) if config_path.is_file() else {}
        candidates = [config.get('node_binary'), node, os.environ.get('NODE_BIN'), shutil.which('node')]
    for value in candidates:
        if not value:
            continue
        binary = shutil.which(str(value)) or str(Path(value).expanduser())
        try:
            if adapter == 'python':
                version = subprocess.check_output([binary, '-c', 'import sys; print(".".join(map(str,sys.version_info[:3])))'], text=True, timeout=5).strip()
                if tuple(int(n) for n in version.split('.')) < minimum:
                    continue
            else:
                version = subprocess.check_output([binary, '--version'], text=True, timeout=5).strip()
                framework = manifest.get('framework', {})
                if framework.get('runtime') == 'vanilla-js' and version.lstrip('v') != framework['version'].lstrip('v'):
                    continue
            return dict(path=str(Path(binary).resolve()), version=version)
        except (OSError, ValueError, subprocess.SubprocessError):
            continue
    raise EvidenceError('No executable meeting the version requirements of this case was found for ' + ('Python' if adapter == 'python' else 'Node.js'))


def invoke(command, directory, stop, terminate, expected_id):
    directory.mkdir(parents=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    with (directory/'stdout.json').open('wb') as stdout, (directory/'stderr.log').open('wb') as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL,
                                   cwd=str(directory), env=env, start_new_session=True)
        deadline = time.monotonic() + 60
        while process.poll() is None:
            if stop.is_set() or time.monotonic() >= deadline:
                terminate(process)
                raise EvidenceError('Behavior validation cancelled' if stop.is_set() else 'Behavior validation timed out')
            stop.wait(.1)
    receipt = dict(command=command, exit_code=process.returncode)
    archive.atomic_json(directory/'execution.json', receipt)
    try:
        report = read(directory/'stdout.json')
    except (ValueError, OSError):
        raise EvidenceError('Validator did not return valid JSON; see the validation log')
    if not isinstance(report, dict) or report.get('case_id') != expected_id or report.get('verdict') not in VERDICTS:
        raise EvidenceError('Validator case or result protocol does not match')
    if process.returncode not in (0, 1) or (process.returncode == 0) != (report['verdict'] == 'PASS'):
        raise EvidenceError('Validator exited abnormally or its result conflicts with the exit code')
    schedules = report.get('schedules', {})
    nested_error = isinstance(schedules, dict) and any(isinstance(row, dict) and row.get('runtimeError')
                                                      for row in schedules.values())
    if report.get('runtime_errors') or nested_error:
        raise EvidenceError('Validation environment reported a runtime error; see the validation log')
    return report


def terminate(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass
    finally:
        # The CLI may exit before descendants that ignore SIGTERM do.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=3)


def scoring_inputs(record):
    manifest = inside(case_root(record), record['manifest'])
    case = read(manifest)
    root = manifest.parent
    reference = case['reference'] if record['adapter'] == 'python' else case['references']['bounded']
    files = {str(manifest): sha(manifest.read_bytes())}
    for path in (inside(root, 'base'), inside(root, reference), inside(root, case['oracle']['probe']).parent):
        content, _ = capture(path)
        files.update({str(path/name): sha(raw) for name, raw in content.items()})
    return files


def relation_states(outcome):
    if 'behavior_states' in outcome:
        states=outcome['behavior_states']
        if not isinstance(states,dict) or not states or any(not isinstance(k,str) or not k
                or (v is not None and type(v) is not bool) for k,v in states.items()):
            raise EvidenceError('Invalid derived behavior vector')
        return dict(states)
    effects = outcome.get('observed_effects')
    if not isinstance(effects, dict) or not effects:
        raise EvidenceError('Scorer did not provide complete observed_effects; cannot assess the experience improvement gate')
    failed = set(outcome.get('missing_required_effects', [])) | set(outcome.get('observed_forbidden_effects', []))
    return {key: (key not in failed if type(value) is bool else None) for key, value in effects.items()}


def delta(before, after):
    left, right = relation_states(before), relation_states(after)
    if set(left) != set(right):
        raise EvidenceError('Behavior vectors differ; comparison rejected')
    return dict(gained=[k for k in left if left[k] is False and right[k] is True],
                lost=[k for k in left if left[k] is True and right[k] is False],
                retained=[k for k in left if left[k] is True and right[k] is True],
                unknown=[k for k in left if left[k] is None or right[k] is None])
