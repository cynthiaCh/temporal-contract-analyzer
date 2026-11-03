"""Run trusted bench oracles after agent work, outside agent-visible inputs."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

from . import archive
from .case_catalog import bench_root, case_root, inside, read
from .core import EvidenceError, sha

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
    raise EvidenceError('未找到满足该案例版本要求的 ' + ('Python' if adapter == 'python' else 'Node.js'))


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
                raise EvidenceError('行为验证已取消' if stop.is_set() else '行为验证超时')
            stop.wait(.1)
    receipt = dict(command=command, exit_code=process.returncode)
    archive.atomic_json(directory/'execution.json', receipt)
    try:
        report = read(directory/'stdout.json')
    except (ValueError, OSError):
        raise EvidenceError('验证程序未返回有效 JSON，请查看验证日志')
    if not isinstance(report, dict) or report.get('case_id') != expected_id or report.get('verdict') not in VERDICTS:
        raise EvidenceError('验证程序的案例或结果协议不匹配')
    if process.returncode not in (0, 1) or (process.returncode == 0) != (report['verdict'] == 'PASS'):
        raise EvidenceError('验证程序异常退出或结果与退出码不一致')
    schedules = report.get('schedules', {})
    nested_error = isinstance(schedules, dict) and any(isinstance(row, dict) and row.get('runtimeError')
                                                      for row in schedules.values())
    if report.get('runtime_errors') or nested_error:
        raise EvidenceError('验证环境报告运行错误，请查看验证日志')
    return report


def evaluate(manifest, folder, node, stop, terminate):
    from .workbench import capture, file_modes, inventory, write_files
    evaluation_id = 'v-' + uuid.uuid4().hex[:16]
    directory = folder/'evaluations'/evaluation_id
    directory.mkdir(parents=True)
    local = (manifest.get('case') or {}).get('source') == 'local'
    provenance = 'current trusted analyzer-local oracle; post-run evaluation' if local else 'current trusted bench oracle; post-run evaluation'
    summary = dict(id=evaluation_id, created_at=archive.now(), provenance=provenance, jobs={})
    jobs = summary['jobs']
    for job in manifest['jobs']:
        jobs[job['id']] = dict(status='not_evaluated', reason='Codex 未正常完成')
    completed = [j for j in manifest['jobs'] if j['status'] == 'completed']
    try:
        record = manifest.get('case')
        if not record or record['adapter'] not in ('legacy-js', 'python'):
            raise EvidenceError('该记录没有可用的 bench 行为验证器')
        case_path = inside(case_root(record), record['manifest'])
        case = read(case_path)
        if case['id'] != record['id'] or record.get('authorization') != 'ungranted':
            raise EvidenceError('案例或授权条件与运行记录不匹配')
        root = case_path.parent
        probe = inside(root, case['oracle']['probe'])
        reference = inside(root, case['reference'] if record['adapter'] == 'python' else case['references']['bounded'])
        oracle_dir = probe.parent
        summary.update(case_id=case['id'], runtime=runtime(case, record['adapter'], node),
                       manifest_sha256=sha(case_path.read_bytes()),
                       oracle_files={str(p.relative_to(oracle_dir)):sha(p.read_bytes()) for p in sorted(oracle_dir.rglob('*'))
                                     if p.is_file() and '__pycache__' not in p.parts})
        def command(candidate):
            return ([summary['runtime']['path'], '-B', str(probe), str(candidate)] if record['adapter'] == 'python'
                    else [summary['runtime']['path'], str(probe), str(candidate), 'ungranted'])
        # Calibrate the same environment on the benchmark's known passing repair.
        reference_files, _ = capture(inside(root, 'base'))
        reference_modes = file_modes(inside(root, 'base'), reference_files)
        overlay_files, _ = capture(reference)
        reference_files.update(overlay_files)
        reference_modes.update(file_modes(reference, overlay_files))
        reference_copy = directory/'reference'
        write_files(reference_copy, reference_files, reference_modes)
        calibration = invoke(command(reference_copy), directory/'calibration', stop, terminate, case['id'])
        summary['calibration_verdict'] = calibration['verdict']
        if calibration['verdict'] != 'PASS':
            raise EvidenceError('参考修复未通过验证，当前环境无法判定修改成败')
        for job in completed:
            job_id = job['id']
            try:
                if stop.is_set():
                    raise EvidenceError('行为验证已取消')
                workspace = folder/'jobs'/job_id/'workspace'
                files, skipped = capture(workspace)
                subject = directory/job_id/'candidate'
                write_files(subject, files, file_modes(workspace, files))
                outcome = invoke(command(subject), directory/job_id/'oracle', stop, terminate, case['id'])
                schedules = outcome.get('schedules', {})
                jobs[job_id] = dict(status='passed' if outcome['verdict'] == 'PASS' else 'failed',
                                   verdict=outcome['verdict'], missing_required_effects=outcome.get('missing_required_effects', []),
                                   observed_forbidden_effects=outcome.get('observed_forbidden_effects', []),
                                   schedules=len(schedules), candidate_files=inventory(files), excluded=skipped,
                                   result_path=str((directory/job_id/'oracle/stdout.json').relative_to(folder)))
            except (OSError, ValueError, KeyError, TypeError, EvidenceError, subprocess.SubprocessError) as error:
                jobs[job_id] = dict(status='error', reason=str(error))
    except (OSError, ValueError, KeyError, TypeError, EvidenceError, subprocess.SubprocessError) as error:
        summary['error'] = str(error)
        for job in completed:
            jobs[job['id']] = dict(status='error', reason=str(error))
    summary['completed_at'] = archive.now()
    archive.atomic_json(directory/'summary.json', summary)
    return summary
