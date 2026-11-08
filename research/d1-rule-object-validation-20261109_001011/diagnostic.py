"""One reflection, manual AI evidence review, at most two development sessions.

Explicit stages only. No baseline execution, legacy scheduler, retry or tests.
"""
import json
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
A = Path(__file__).resolve().parent
sys.path.insert(0, str(A))
import runner
from archive import save, sha, inventory, digest
from handoff import (verify_ledger, assemble_payload, validate_candidate, semantic_gate,
                     object_digest, render, numbered_rules, make_schema)
from toolflow import maintenance_prompt, PREDICATES


def read(p, default=None):
    return json.loads(Path(p).read_text()) if Path(p).exists() else default


def stop(reason, classification):
    save(A / 'stop.json', {'reason': reason, 'classification': classification, 'time': time.time(),
                           'no_retry': True, 'no_more_model_calls': True})
    raise RuntimeError(reason)


def preflight():
    assert not (A / 'freeze.json').exists(), 'Preflight frozen; do not rerun'
    ledger = read(A / 'evidence-ledger.json')
    verify_ledger(A, ledger)
    payload = read(A / 'reflection-input.json')
    assert assemble_payload(A, ledger, read(A / 'feedback.json')) == {k:v for k,v in payload.items() if k not in {'mechanism_predicates', 'output_protocol'}}
    assert read(A / 'reflection.schema.json') == make_schema(ledger, PREDICATES)
    assert payload['mechanism_predicates'] == PREDICATES
    import test_protocol, test_runtime_v2
    suite = unittest.TestLoader().loadTestsFromModule(test_protocol)
    for method in unittest.TestLoader().getTestCaseNames(test_runtime_v2.RuntimeV2):
        if method != 'test_real_v1_failure_replay':
            suite.addTest(test_runtime_v2.RuntimeV2(method))
    # Uses only synthetic offline failure fixtures; no test-case traces.
    with (A / 'offline-checks.log').open('w') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    if not result.wasSuccessful():
        stop('Offline checks failed', 'preflight')
    case = read(A / 'case.json')
    with tempfile.TemporaryDirectory(prefix='d1-namespace-offline-') as tmp:
        runtime = Path(tmp)
        folder = runtime / 'fixture'; folder.mkdir()
        (folder / 'workspace').mkdir(); (folder / 'archive').mkdir()
        (folder / 'workspace/src').mkdir()
        (folder / 'workspace/src/session.js').write_bytes((A / 'candidate/src/session.js').read_bytes())
        socket = runtime / 'control'; socket.mkdir()
        cmd = runner.command('offline-preview', folder, 'repair', case, runtime=runtime,
                             socket_dir=socket, copy_auth=False)
        # Run the exact namespace prefix with a non-model payload. Nothing is
        # sent to a service and no authentication file is copied.
        prefix = cmd[:cmd.index('/opt/codex')]
        script = 'set -eu\ncat /workspace/src/session.js\ntest ! -e /home/sribd\ntest ! -e /workspace/archive\n/runtime/node --version'
        z = subprocess.run(prefix + ['/bin/sh', '-c', script], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=30)
        if z.returncode or (A / 'candidate/src/session.js').read_bytes() not in z.stdout:
            stop('Actual namespace/source read failed: ' + z.stderr.decode(errors='replace'), 'preflight')
        save(A / 'namespace-check.json', {'exit_code': z.returncode, 'source_read_exact': True,
             'archive_and_repository_not_mounted': True, 'model_calls': 0,
             'node_version': z.stdout.decode().splitlines()[-1], 'command': prefix + ['/bin/sh', '-c', script]})
        baseline = read(A / 'baselines/auto1/archive/command.json')
        def inner(c):
            return c[c.index('/opt/codex'):]
        assert inner(cmd) == inner(baseline), 'Maintenance CLI flags differ from baseline'
        reflect_cmd = runner.command('offline-reflect-preview', folder, 'reflect', case,
                             runtime=runtime, socket_dir=socket, copy_auth=False)
        assert 'model_reasoning_effort="medium"' in reflect_cmd
        assert '--enable' not in reflect_cmd
    # Pin source/evaluation/config without importing any reference patches.
    protected = {}
    for p in (Path(case['source_case']) / 'oracle').rglob('*'):
        if p.is_file():
            protected[str(p)] = sha(p)
    for p in A.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.name not in {'freeze.json'}:
            protected[str(p)] = sha(p)
    global_config = Path.home() / '.codex/config.toml'
    protected[str(global_config)] = sha(global_config)
    save(A / 'freeze.json', {'time': time.time(), 'files': protected,
                            'baseline_runtime_flags_equal': True,
                            'offline_tests': result.testsRun, 'model_calls_in_preflight': 0})
    print('OFFLINE PASS', result.testsRun, 'checks; maintenance command flags match baselines', flush=True)


def check():
    assert not (A / 'stop.json').exists(), 'Batch stopped; no retry'
    runner.verify(read(A / 'freeze.json')['files'])


def scorer(final, out):
    case = read(A / 'case.json')
    command = [case['node'], str(Path(case['source_case']) / 'oracle/probe.cjs'), str(final), 'ungranted']
    with (out / 'stdout.json').open('wb') as stdout, (out / 'stderr.txt').open('wb') as stderr:
        z = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=90)
    s = read(out / 'stdout.json')
    rules = read(Path(case['source_case']) / 'oracle/effects.json')['variants']['ungranted']
    assert z.returncode in (0, 1) and s['case_id'] == case['case']
    effects = s['observed_effects']
    assert set(effects) == set(read(A / 'inputs/original-score.json')['observed_effects'])
    assert len(rules['required']) == 29 and not rules['forbidden']
    missing = [k for k in rules['required'] if effects.get(k) is not True]
    forbidden = [k for k in rules['forbidden'] if effects.get(k) is True]
    verdict = 'UNDERREACH_AND_OVERREACH' if missing and forbidden else 'UNDERREACH' if missing else 'OVERREACH' if forbidden else 'PASS'
    assert verdict == s['verdict'] and missing == s['missing_required_effects'] and forbidden == s['observed_forbidden_effects']
    assert not any(v.get('runtimeError') for v in s['schedules'].values())
    save(out / 'receipt.json', {'command': command, 'exit_code': z.returncode,
                               'oracle_sha256': case['oracle_files'], 'candidate_digest': digest(inventory(final))})
    return {'verdict': verdict, 'effects': effects, 'missing': missing,
            'forbidden': forbidden, 'score_valid': True}


def execute(slot, prompt, candidate, task):
    check()
    slots = read(A / 'actual-schedule.json', [])
    assert not any(r['slot'] == slot['slot'] for r in slots), 'Already dispatched, no retry'
    assert len(slots) < 3
    if slot['phase'] == 'reflect':
        assert not slots
    else:
        assert read(A / 'candidate-freeze.json') is not None
    slots.append({**slot, 'status': 'DISPATCHING', 'dispatched_at': time.time()})
    save(A / 'actual-schedule.json', slots)
    case = read(A / 'case.json')
    if slot['phase'] == 'reflect':
        case.pop('candidate_files'); case.pop('task_sha256')
    try:
        record = runner.session(slot, prompt, case=case, candidate=candidate, task=task,
           config={'seconds_per_session': 600, 'stdout_bytes': 16777216,
                   'frozen_files': read(A / 'freeze.json')['files']},
           run_dir=A / 'runs' / slot['slot'], score_fn=scorer if slot['phase'] == 'repair' else None,
           allow_model_execution=True)
    except Exception as exc:
        record = {**slot, 'status': 'INVALID', 'catastrophic_runner_exception': repr(exc)}
    slots[-1] = record; save(A / 'actual-schedule.json', slots)
    print(json.dumps({'slot': slot['slot'], 'status': record.get('status'), 'seconds': record.get('seconds'),
                      'requests': record.get('native', {}).get('started'), 'score': record.get('score_result')}, ensure_ascii=False), flush=True)
    if record.get('catastrophic_runner_exception'):
        stop(record['catastrophic_runner_exception'], 'infrastructure')
    root = A / 'runs' / slot['slot'] / 'archive'
    guard = read(root / 'guard-collector-status.json', {})
    meter = read(root / 'meter/ledger.json', {})
    native = record.get('native', {})
    if (record.get('archive_failure_requires_stop') or guard.get('errors')
        or not record.get('infrastructure_valid') or not record.get('turn_complete')):
        stop('Infrastructure or incomplete session: ' + slot['slot'], 'infrastructure')
    if meter.get('started') != native.get('started') or meter.get('completed') != native.get('completed'):
        stop('Meter counters disagree', 'measurement')
    if sum(r.get('native', {}).get('started', 0) for r in slots) > 60:
        stop('Request cap violated', 'measurement')
    check()
    if not record.get('output_format_valid'):
        stop('Invalid complete model output; raw bytes retained', 'invalid_output')
    if slot['phase'] == 'repair' and (record.get('scoring_status') != 'COLLECTED'
                                      or not record.get('scored_candidate_unchanged')):
        stop('Final candidate not validly scored', 'scoring_admission')
    return record


def reflect():
    record = execute({'slot': 'D1-reflection', 'phase': 'reflect', 'condition': 'EVIDENCE_HANDOFF_REPAIR', 'alias': 'D1'},
                     (A / 'reflection-prompt.md').read_text(), A / 'reflection-workspace', A / 'reflection-task.md')
    root = A / 'runs/D1-reflection/archive'
    raw = (root / 'raw-answer.txt').read_bytes()
    (A / 'reflection-raw.txt').write_bytes(raw)
    # Full raw response already saved by runner before parsing; no truncation.
    candidate = json.loads(raw)
    save(A / 'candidate-experience.json', candidate)
    try:
        structural = validate_candidate(candidate, read(A / 'evidence-ledger.json'), PREDICATES)
        text = render(candidate)
        (A / 'candidate-experience.md').write_text(text)
        save(A / 'rule-evidence.json', {'rules': numbered_rules(candidate), 'unresolved': candidate['unresolved'],
                                       'applicability': candidate['applicability'], 'origin': 'program-derived numbering; exact original model rule fields'})
        save(A / 'derivation.json', {'rendered_origin': 'program_derived_not_raw_model_text',
          'operations': ['number original list in order starting R01', 'add fixed category labels', 'join exact model bodies without alteration'],
          'raw_response_sha256': sha(A / 'reflection-raw.txt'),
          'model_object_sha256': object_digest(candidate), 'model_object_file_sha256': sha(A / 'candidate-experience.json'),
          'rendered_sha256': sha(A / 'candidate-experience.md'), 'rule_evidence_sha256': sha(A / 'rule-evidence.json'),
          'no_evidence_or_policy_completion': True})
        forbidden = [read(A / 'case.json')['case']] + list(read(A / 'inputs/original-score.json')['observed_effects'])
        forbidden += ['src/', '/workspace', 'q.consumed', 'a.consumed', 'retryCancelled', 'fetchStatus', 'queryFn', 'refetchOnReconnect']
        if any(word in text for word in forbidden) or '```' in text:
            raise ValueError('Experience text contains prohibited identifying/code material')
        save(A / 'structural-review.json', structural)
    except Exception as exc:
        save(A / 'candidate-rejection.json', {'reviewer': 'execution_agent_AI_assisted', 'reason': repr(exc), 'raw_preserved': True})
        stop('Candidate support protocol invalid: ' + repr(exc), 'candidate_rejected')
    print('Raw rule object and program-derived delivery saved; awaiting AI-assisted semantic review (no additional model)', flush=True)


def develop():
    check()
    candidate = read(A / 'candidate-experience.json')
    review = read(A / 'semantic-review.json')
    result = semantic_gate(candidate, read(A / 'evidence-ledger.json'), PREDICATES, review)
    save(A / 'content-review-result.json', result)
    if result['semantic_status'] != 'supported_by_execution_agent':
        stop('Candidate rejected in AI-assisted evidence review', 'candidate_rejected')
    text = render(candidate)
    assert sha(A / 'candidate-experience.md') == runner.backend.sha(text)
    prompt = (A / 'AUTO-prompt.md').read_text() + '\n\n以下为冻结经验，按当前证据核查适用性：\n' + text
    (A / 'revalidation-prompt.md').write_text(prompt)
    frozen = {'time': time.time(), 'candidate_sha256': object_digest(candidate), 'text_sha256': runner.backend.sha(text),
              'requires': candidate['requires'], 'excludes': candidate['excludes'],
              'review': 'semantic-review.json', 'AI_assisted_not_human_approval': True,
              'maintenance_prompt_sha256': sha(A / 'revalidation-prompt.md'),
              'text_origin': 'program-derived exact model rule bodies and mechanical headings',
              'files': {str(A / n): sha(A / n) for n in ['candidate-experience.json', 'candidate-experience.md',
                         'semantic-review.json', 'rule-evidence.json', 'derivation.json', 'revalidation-prompt.md']}}
    assert not (A / 'candidate-freeze.json').exists(), 'No repeat development execution'
    save(A / 'candidate-freeze.json', frozen)
    for n in (1, 2):
        runner.verify(frozen['files'])
        execute({'slot': f'D1-revalidation-{n}', 'phase': 'repair', 'condition': 'AUTO_NEW_EXPERIENCE', 'alias': 'D1'},
                prompt, A / 'candidate', A / 'task.md')
    save(A / 'completion.json', {'time': time.time(), 'completed_development_revalidations': 2,
                                'no_test_or_next_reflection': True})


if __name__ == '__main__':
    stage = sys.argv[1]
    try:
        {'preflight': preflight, 'reflect': reflect, 'develop': develop}[stage]()
    except Exception as exc:
        if not (A / 'stop.json').exists():
            save(A / 'stop.json', {'reason': repr(exc), 'classification': 'stage_exception',
                                   'time': time.time(), 'no_more_model_calls': True, 'no_retry': True})
        print('STOP', repr(exc), flush=True)
        raise
