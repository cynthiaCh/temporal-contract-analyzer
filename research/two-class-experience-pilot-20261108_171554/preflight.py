"""Zero-model inspection/calibration only. No model or legacy scheduler imports."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import unittest

A = Path(__file__).resolve().parent
R = A.parents[1]
B = R.parent / 'temporal-contract-bench-git'
IDS = ['query-paused-initial-fetch-10266-vanilla', 'document-submit-snapshot-vanilla',
       'query-paused-initial-fetch-10266-python3', 'document-submit-snapshot-python3-eval-v2']


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(path):
    return {str(p.relative_to(path)): sha(p) for p in sorted(path.rglob('*')) if p.is_file()}


def main():
    started = time.monotonic()
    assert not (A / 'summary.json').exists(), 'inspection already closed; no implicit rerun'
    required = R / 'refine-logs/experience-toolflow-v1-20261108'
    specs = {name: (required / name).is_file() for name in
             ['METHOD.md', 'taxonomy.json', 'protocol.json', 'experience-registry.json']}
    save(A / 'spec-check.json', {'directory': str(required), 'files_present': specs,
                               'fallback_taxonomy_created': False})
    protected = {}
    for name in subprocess.check_output(['git', 'ls-files', '-z'], cwd=R).decode().split('\0'):
        if name and (R / name).is_file():
            protected[str(R / name)] = sha(R / name)
    node = B / 'results/student-case-expansion-runtime/node18/bin/node'
    runtimes = {}
    for name, command in [('node', [str(node), '--version']), ('python', ['python3', '--version']),
                          ('bwrap', ['bwrap', '--version'])]:
        try:
            p = subprocess.run(command, capture_output=True, text=True, timeout=10)
            runtimes[name] = {'command': command, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
        except Exception as e:
            runtimes[name] = {'error': repr(e)}
    save(A / 'runtime-check.json', runtimes)
    cases = []
    for index, cid in enumerate(IDS):
        srcs = list((B / 'case-clusters').glob('*/arms/' + cid + '/case.json'))
        assert len(srcs) == 1, (cid, srcs)
        manifest = srcs[0]
        src = manifest.parent
        m = json.loads(manifest.read_text())
        assert m['id'] == cid
        for f in src.rglob('*'):
            if f.is_file():
                protected[str(f)] = sha(f)
        dest = A / 'inputs' / cid
        shutil.copytree(src / 'base', dest / 'candidate')
        shutil.copytree(src / 'oracle', dest / 'evaluation')
        shutil.copyfile(manifest, dest / 'manifest.json')
        shutil.copyfile(src / m['diagnostic_tasks']['maintenance']['core_prompt'], dest / 'task.md')
        docs = [p for p in (src / 'base').rglob('*') if p.suffix == '.md']
        # Retain numbered candidate-visible evidence, separate from manifest labels.
        evidence = {}
        for f in sorted((src / 'base').rglob('*')):
            if f.is_file() and f.suffix in ('.md', '.js', '.py'):
                evidence[str(f.relative_to(src / 'base'))] = [
                    {'line': n, 'text': line} for n, line in enumerate(f.read_text().splitlines(), 1)]
        save(dest / 'visible-source-lines.json', evidence)
        c = {'case': cid, 'role': 'train' if index < 2 else 'test', 'source': str(src),
             'independent_unit_id': m['independent_unit_id'], 'framework': m['framework'],
             'provenance': m['provenance'], 'input_sha256': inventory(dest),
             'candidate_visible_documents': [str(p.relative_to(src / 'base')) for p in docs],
             'standard_adapter': 'manifest oracle probe.cjs, original ungranted effects; no scoring edits',
             'oracle_sha256': inventory(src / 'oracle'), 'calibration': []}
        variants = [('original', None)] + [('reference-' + key, src / value) for key, value in m['references'].items()]
        variants += [(name.replace('/', '-'), src / name) for name in m['mutants']]
        for label, overlay in variants:
            out = A / 'calibration' / cid / label
            shutil.copytree(src / 'base', out / 'candidate')
            if overlay:
                shutil.copytree(overlay, out / 'candidate', dirs_exist_ok=True)
            command = [str(node), str(src / m['oracle']['probe']), str(out / 'candidate'), 'ungranted']
            t = time.monotonic()
            rec = {'label': label, 'command': command, 'candidate_before': inventory(out / 'candidate')}
            try:
                proc = subprocess.run(command, capture_output=True, text=True, timeout=90,
                                      env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
                (out / 'stdout.json').write_text(proc.stdout)
                (out / 'stderr.txt').write_text(proc.stderr)
                score = json.loads(proc.stdout)
                errors = {k: v.get('runtimeError') for k, v in score['schedules'].items() if v.get('runtimeError')}
                rules = json.loads((src / m['oracle']['effects']).read_text())['variants']['ungranted']
                effects = score['observed_effects']
                missing = [k for k in rules['required'] if effects.get(k) is not True]
                forbidden = [k for k in rules['forbidden'] if effects.get(k) is True]
                expected = 'UNDERREACH_AND_OVERREACH' if missing and forbidden else (
                    'UNDERREACH' if missing else ('OVERREACH' if forbidden else 'PASS'))
                valid = (proc.returncode in [0, 1] and not errors and score['case_id'] == cid
                         and expected == score['verdict'] and rec['candidate_before'] == inventory(out / 'candidate'))
                rec.update(exit_code=proc.returncode, verdict=score['verdict'], effects=effects,
                           runtime_errors=errors, score_valid=valid)
            except Exception as e:
                rec.update(score_valid=False, error=repr(e))
            rec['seconds'] = time.monotonic() - t
            save(out / 'receipt.json', rec)
            c['calibration'].append(rec)
        c['calibration_trustworthy'] = (all(x['score_valid'] for x in c['calibration'])
            and next(x for x in c['calibration'] if x['label'] == 'original').get('verdict') != 'PASS'
            and next(x for x in c['calibration'] if x['label'] == 'reference-bounded').get('verdict') == 'PASS'
            and all(x.get('verdict') != 'PASS' for x in c['calibration'] if x['label'].startswith('mutants-')))
        cases.append(c)
        save(A / 'cohort.json', cases)
        print(cid, 'calibration:', c['calibration_trustworthy'], flush=True)
    from test_interfaces import OfflineInterfaces
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(OfflineInterfaces)
    with (A / 'interface-tests.log').open('w') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    save(A / 'offline-interfaces.json', {'tests': result.testsRun, 'failures': len(result.failures),
         'errors': len(result.errors), 'passed': result.wasSuccessful(), 'synthetic_fixtures_only': True,
         'semantic_evidence_validation': 'unimplemented; literal source binding only',
         'real_taxonomy_integration': 'blocked_missing_spec', 'runner_integration': 'not_executed'})
    save(A / 'protected-files.json', protected)
    changed = [p for p, h in protected.items() if not Path(p).is_file() or sha(Path(p)) != h]
    blockers = ['missing authoritative v1 specification: ' + ', '.join(k for k, v in specs.items() if not v)] if not all(specs.values()) else []
    blockers += [c['case'] + ': calibration failed' for c in cases if not c['calibration_trustworthy']]
    if changed:
        blockers.append('protected input drift')
    save(A / 'integrity-check.json', {'protected_files': len(protected), 'changed': changed,
         'model_sessions_started': 0, 'legacy_scheduler_started': False, 'existing_files_modified': bool(changed),
         'input_archive_digest': inventory(A / 'inputs')})
    save(A / 'summary.json', {'status': 'STOPPED_BEFORE_MODEL_CALLS', 'blockers': blockers,
         'training': {'status': 'not_started', 'baselines': [], 'reflections': [], 'revalidations': []},
         'library': {'status': 'not_generated_or_frozen', 'entries': []},
         'tests': {'status': 'not_started', 'classifications': [], 'routes': [], 'A': [], 'B': []},
         'test_denominator': 0, 'effect_estimate': None, 'model_sessions': 0, 'bottom_level_requests': 0,
         'model_tokens': 'not_applicable_no_calls', 'engineering_assistant_tokens': None,
         'engineering_monetary_cost': None, 'preflight_seconds': time.monotonic() - started,
         'source_design': 'two same-source cross-language pairs; previously exposed; not independent generalization',
         'completed_at': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()})


if __name__ == '__main__':
    main()
