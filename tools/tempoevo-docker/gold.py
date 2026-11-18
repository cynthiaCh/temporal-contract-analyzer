"""Invoke unchanged, registered benchmark probes; reject incomplete/runtime scores."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('/opt/swe-tempoc')
sys.path.insert(0, str(ROOT))
import swe_tempoc


def evaluate():
    cfg = json.loads(Path('/checks/case.json').read_text())
    relative = Path(cfg['manifest'])
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Invalid benchmark manifest path')
    manifest_path = ROOT / relative
    manifest = json.loads(manifest_path.read_text())
    admitted = json.loads(Path('/opt/grader-build/inputs.json').read_text())['scoring_case_ids']
    if manifest['id'] not in admitted:
        raise ValueError('Case is outside this grader image scoring scope')
    case = manifest_path.parent
    oracle = manifest['oracle']
    probe = (case / oracle['probe']).resolve()
    if case.resolve() not in probe.parents:
        raise ValueError('Probe escapes registered case')
    python = manifest.get('language') == 'python'
    node = None if python else swe_tempoc.node_binary()
    command = [sys.executable, '-B'] if python else [str(node)]
    command += [str(probe), sys.argv[-1]]
    if not python:
        command.append('ungranted')
    run = subprocess.run(command, capture_output=True, text=True, timeout=150,
                         env=swe_tempoc.execution_env(node))
    sys.stderr.write(run.stderr)
    schedules = json.loads((case / oracle['schedules']).read_text())['schedules']
    aliases = swe_tempoc.roster().get(manifest['id'], {}).get('report_schedule_aliases', {})
    expected = [aliases.get(row['id'], row['id']) for row in schedules]
    summary, score = swe_tempoc.classify(run.stdout, run.returncode, manifest['id'], expected)
    valid = summary['valid_scored']
    if score is None:
        try:
            score = json.loads(run.stdout)
        except ValueError:
            pass
    return dict(valid=valid, passed=valid and summary['verdict'] == 'PASS',
                verdict=summary['verdict'], full_score=score,
                error=summary.get('error'), probe_exit_code=run.returncode,
                raw_stdout=run.stdout if score is None else None)


if __name__ == '__main__':
    try:
        result = evaluate()
    except Exception as error:
        result = dict(valid=False, passed=False, verdict=None, error=repr(error))
    print(json.dumps(result))
