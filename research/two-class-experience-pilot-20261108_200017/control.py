"""New staged pilot controller. No imports/start of any historical scheduler.

Commands: train D1|D2; freeze; test. Admission is a separately recorded
execution-agent review of actual evidence, never an extra model call.
"""
import json
from pathlib import Path
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True
A = Path(__file__).resolve().parent
sys.path.insert(0, str(A))
import runner
from archive import save, sha, inventory, digest
from toolflow import (PREDICATES, canonical, digest as text_digest, feedback, freeze_entry,
                      maintenance_prompt, reflection_prompt, route)


class Stop(RuntimeError):
    pass


def read(p):
    return json.loads(Path(p).read_text())


def cases():
    return {c['alias']: c for c in read(A / 'cohort.json')}


def material(alias):
    return A / 'materials' / alias


def sources(alias):
    root = material(alias) / 'candidate'
    return {str(f.relative_to(root)): f.read_text() for f in root.rglob('*')
            if f.is_file() and f.suffix in ['.md', '.py', '.js']}


def journal():
    return read(A / 'actual-schedule.json') if (A / 'actual-schedule.json').exists() else []


def check():
    if (A / 'stop.json').exists():
        raise Stop('batch already stopped; no retry')
    assert sha(A / 'protocol.json') == (A / 'protocol.sha256').read_text().strip()
    runner.verify(read(A / 'protocol.json')['files'])
    runner.verify(read(A / 'protected-files.json'))


def stop(reason):
    save(A / 'stop.json', {'reason': reason, 'time': time.time(), 'launched_slots': [r['slot'] for r in journal()],
                           'no_retry': True, 'no_more_model_calls': True})
    raise Stop(reason)


def score_for(alias):
    c = cases()[alias]

    def score(final, out):
        cmd = [c['node'], str(Path(c['source_case']) / 'oracle/probe.cjs'), str(final), 'ungranted']
        with (out / 'stdout.json').open('wb') as stdout, (out / 'stderr.txt').open('wb') as stderr:
            z = subprocess.run(cmd, stdout=stdout, stderr=stderr, timeout=90)
        s = read(out / 'stdout.json')
        assert z.returncode in [0, 1] and s['case_id'] == c['case']
        expected_effects = read(A / 'calibration' / alias / 'original/stdout.json')['observed_effects']
        assert set(s['observed_effects']) == set(expected_effects)
        rules = read(material(alias) / 'evaluation/effects.json')['variants']['ungranted']
        missing = [k for k in rules['required'] if s['observed_effects'].get(k) is not True]
        forbidden = [k for k in rules['forbidden'] if s['observed_effects'].get(k) is True]
        expected = 'UNDERREACH_AND_OVERREACH' if missing and forbidden else (
            'UNDERREACH' if missing else ('OVERREACH' if forbidden else 'PASS'))
        assert missing == s['missing_required_effects'] and forbidden == s['observed_forbidden_effects']
        assert expected == s['verdict']
        errors = {k: v['runtimeError'] for k, v in s['schedules'].items() if v.get('runtimeError')}
        assert not errors, errors
        save(out / 'receipt.json', {'command': cmd, 'exit_code': z.returncode, 'oracle_sha256': c['oracle_files'],
                                   'candidate_sha256': digest(inventory(final))})
        return {'verdict': s['verdict'], 'effects': s['observed_effects'], 'missing': missing,
                'forbidden': forbidden, 'runtime_errors': errors, 'score_valid': True}
    return score


def critical(rec, phase):
    if rec.get('catastrophic_runner_exception'):
        return 'runner failed before complete archival/accounting'
    if rec.get('archive_failure_requires_stop'):
        return 'archive integrity failure'
    root = A / 'runs' / rec['slot'] / 'archive'
    ledger = read(root / 'meter/ledger.json') if (root / 'meter/ledger.json').exists() else {}
    native = rec.get('native', {})
    if rec.get('guard_errors'):
        return 'hook collector error'
    if ledger and (ledger.get('started') != native.get('started', 0) or ledger.get('completed') != native.get('completed', 0)):
        return 'meter session/global counter distortion'
    model, effort, cap, mode = runner.ROLE[phase]
    events = [x['event'] for x in ledger.get('events', [])]
    model_events = [e for e in events if e.get('hook_event_name') in ['PreModelRequest', 'PostModelRequest']]
    if any(e.get('model') != model for e in model_events):
        return 'model identity distortion'
    if native.get('blocked_tools'):
        return 'isolation/tool-policy violation'
    if native.get('started', 0) > cap:
        return 'request budget distortion'
    if native.get('started', 0) - native.get('completed', 0) not in [0, 1]:
        return 'unaccounted request gap'
    if phase == 'repair' and (rec.get('scoring_status') != 'COLLECTED' or not rec.get('scored_candidate_unchanged')):
        return 'scoring capability or final-input integrity failure'
    return None


def execute(slot, alias, prompt, *, candidate=None, task=None):
    check()
    rows = journal()
    if any(r['slot'] == slot['slot'] for r in rows):
        raise Stop('slot already started; no retry')
    if len(rows) >= 20:
        stop('session limit')
    counts = {p: sum(r['phase'] == p for r in rows) for p in runner.ROLE}
    if counts[slot['phase']] >= {'extract': 4, 'repair': 14, 'reflect': 2}[slot['phase']]:
        stop('role session cap')
    if sum(r.get('native', {}).get('started', 0) for r in rows) > 408:
        stop('total request limit')
    slot = {**slot, 'alias': alias}
    # Record slot before dispatch, including any subsequent infrastructure failure.
    rows.append({**slot, 'status': 'LAUNCHING', 'time': time.time()})
    save(A / 'actual-schedule.json', rows)
    config = {'seconds_per_session': 600, 'stdout_bytes': 16777216,
              'frozen_files': read(A / 'protocol.json')['files']}
    c = dict(cases()[alias])
    if candidate is not None:
        c.pop('candidate_files', None)
        c.pop('task_sha256', None)
    try:
        rec = runner.session(slot, prompt, case=c, candidate=candidate or material(alias) / 'candidate',
                             task=task or material(alias) / 'task.md', config=config,
                             run_dir=A / 'runs' / slot['slot'],
                             score_fn=score_for(alias) if slot['phase'] == 'repair' else None,
                             allow_model_execution=True)
        collector = A / 'runs' / slot['slot'] / 'archive/guard-collector-status.json'
        rec['guard_errors'] = read(collector)['errors'] if collector.exists() else ['missing collector status']
    except Exception as exc:
        rec = {**slot, 'status': 'INVALID', 'native': {}, 'seconds': None,
               'exception': repr(exc), 'catastrophic_runner_exception': True, 'infrastructure_valid': False}
    rows[-1] = rec
    save(A / 'actual-schedule.json', rows)
    print(canonical({'slot': rec['slot'], 'status': rec['status'], 'infrastructure_valid': rec.get('infrastructure_valid'),
                     'requests': rec.get('native', {}).get('started'), 'seconds': rec.get('seconds'),
                     'score': rec.get('score_result', {}).get('verdict')}), flush=True)
    try:
        check()
    except Exception as exc:
        stop('frozen source/config drift: ' + repr(exc))
    issue = critical(rec, slot['phase'])
    if issue:
        stop(issue)
    if len(rows) >= 2 and all(not r.get('infrastructure_valid', False) for r in rows[-2:]):
        stop('two consecutive infrastructure anomalies')
    return rec


def analysis_for(alias):
    p = A / 'derived' / alias / 'analysis.json'
    if p.exists():
        return read(p)
    rec = execute({'slot': alias + '-preanalysis', 'phase': 'extract', 'condition': 'COMMON'}, alias,
                  (material(alias) / 'preanalysis-prompt.md').read_text())
    raw = A / 'runs' / rec['slot'] / 'archive/analysis.json'
    analysis = read(raw) if rec.get('preanalysis_valid') and raw.exists() else {
        'contract': '', 'primary_class': 'unknown', 'secondary_tags': [], 'evidence': [], 'facts': []}
    save(p, analysis)
    save(p.parent / 'preanalysis-status.json', {'valid': rec.get('preanalysis_valid', False),
         'error': rec.get('preanalysis_error'), 'raw_archive': str(raw.parent),
         'invalid_fallback': not rec.get('preanalysis_valid', False)})
    (p.parent / 'automatic-contract.md').write_text(analysis['contract'])
    return analysis


def candidate_violations(text, alias):
    # Structural checks supplement, never replace, the execution-agent policy review.
    violations = []
    for c in cases().values():
        if c['case'] in text:
            violations.append('case identity')
    for relation in read(material(alias) / 'standards.json'):
        if relation['effect'] in text:
            violations.append('scoring assertion name: ' + relation['effect'])
    if re.search(r'(?:src/|/workspace|\.js\b|\.py\b|```|\b[a-z]+[A-Z][A-Za-z]*\b|\b[a-z]+_[a-z_]+\b)', text):
        violations.append('code/path/identifier-like text')
    return violations


def train(alias):
    assert alias in ['D1', 'D2']
    assert not (A / 'experience-freeze.json').exists(), 'training closed'
    check()
    out = A / 'development' / alias
    assert not (out / 'state.json').exists(), 'case already developed; no retry'
    analysis = analysis_for(alias)
    common = maintenance_prompt((material(alias) / 'task.md').read_text(), analysis['contract'])
    out.mkdir(parents=True, exist_ok=True)
    (out / 'AUTO-prompt.md').write_text(common)
    baseline = []
    for number in [1, 2]:
        baseline.append(execute({'slot': f'{alias}-AUTO-{number}', 'phase': 'repair', 'condition': 'AUTO'}, alias, common))
    save(out / 'baseline-receipts.json', baseline)
    original = read(A / 'calibration' / alias / 'original/stdout.json')
    raw_scores = [read(A / 'runs' / r['slot'] / 'archive/score/stdout.json') for r in baseline]
    fb = feedback(original, raw_scores, read(material(alias) / 'standards.json'))
    fb['explanations'] = [{'source': 'policy-review.md', 'author': 'execution_agent',
        'kind': 'policy_and_existing_source_interpretation',
        'scope': 'source-bound policy review only, not inferred causal diagnosis of these repairs'}]
    save(out / 'feedback.json', fb)
    state = {'alias': alias, 'primary_class': analysis['primary_class'], 'baseline_slots': [r['slot'] for r in baseline],
             'baseline_passes': sum(s['verdict'] == 'PASS' for s in raw_scores), 'candidate_generated': False,
             'reflection_slot': None, 'revalidation_slot': None, 'reason': None}
    if state['baseline_passes'] == 2:
        state['reason'] = 'both_AUTO_pass_no_experience_generated'
    elif analysis['primary_class'] == 'unknown':
        state['reason'] = 'unknown_class_no_class_specific_reflection'
    elif any(r['phase'] == 'reflect' and r.get('primary_class') == analysis['primary_class'] for r in journal()):
        state['reason'] = 'one_reflection_per_class_already_used'
    else:
        payload = {'task': (material(alias) / 'task.md').read_text(), 'original_sources': sources(alias),
                   'source_supported_policy_review': (A / 'policy-review.md').read_text(),
                   'feedback': fb, 'baseline_deliveries': []}
        for r in baseline:
            root = A / 'runs' / r['slot'] / 'archive'
            payload['baseline_deliveries'].append({'patch': (root / 'patch.diff').read_text(),
                 'public_delivery': (root / 'raw-answer.txt').read_text(),
                 'score': {k:v for k,v in read(root / 'score/stdout.json').items() if k in ['verdict','observed_effects','missing_required_effects','observed_forbidden_effects']},
                 'raw_score_sha256': sha(root / 'score/stdout.json')})
        # The role is no-tools; candidate workspace contains only this training payload.
        refdir = out / 'reflection-input'
        refdir.mkdir()
        save(refdir / 'training-feedback.json', payload)
        (out / 'reflection-task.md').write_text('Reflect once from current training evidence. No tools. No old seed.')
        prompt = reflection_prompt(payload)
        (out / 'reflection-prompt.md').write_text(prompt)
        rec = execute({'slot': alias + '-reflection', 'phase': 'reflect', 'condition': 'LEARN',
                       'primary_class': analysis['primary_class']}, alias, prompt,
                      candidate=refdir, task=out / 'reflection-task.md')
        state['reflection_slot'] = rec['slot']
        raw = (A / 'runs' / rec['slot'] / 'archive/experience.md').read_text()
        (out / 'reflection-raw.txt').write_text(raw)
        try:
            if not rec.get('infrastructure_valid'):
                raise ValueError('invalid reflection infrastructure; no candidate admitted')
            candidate = json.loads(raw)
            entry = freeze_entry(candidate, analysis['primary_class'])
            violations = candidate_violations(entry['text'], alias)
            if violations:
                raise ValueError(violations)
            save(out / 'experience-candidate.json', entry)
            (out / 'experience-original.md').write_text(candidate['text'])
            state['candidate_generated'] = True
            dev_prompt = maintenance_prompt((material(alias) / 'task.md').read_text(), analysis['contract'], entry['text'])
            (out / 'revalidation-prompt.md').write_text(dev_prompt)
            dev = execute({'slot': alias + '-development-revalidation', 'phase': 'repair', 'condition': 'AUTO_NEW_EXPERIENCE'}, alias, dev_prompt)
            state['revalidation_slot'] = dev['slot']
            dev_score = read(A / 'runs' / dev['slot'] / 'archive/score/stdout.json')
            comparisons = [feedback(base, [dev_score], read(material(alias) / 'standards.json'))['runs'][0] for base in raw_scores]
            save(out / 'revalidation-comparison.json', {'vs_each_AUTO': comparisons,
                 'development_is_not_test': True, 'original_to_dev': feedback(original, [dev_score], read(material(alias) / 'standards.json'))})
            state['observed_relation_improvement'] = any(x['improvements'] for x in comparisons)
            state['reason'] = 'await_execution_agent_admission_review'
        except (ValueError, TypeError, KeyError) as exc:
            state['reason'] = 'candidate_invalid_no_second_candidate'
            state['candidate_error'] = repr(exc)
    save(out / 'state.json', state)
    print(canonical(state), flush=True)


def freeze():
    check()
    assert not (A / 'experience-freeze.json').exists()
    entries = []
    decisions = []
    for alias in ['D1', 'D2']:
        state = read(A / 'development' / alias / 'state.json')
        if state['candidate_generated']:
            decision = read(A / 'development' / alias / 'admission.json')
            assert decision['reviewer'] == 'execution_agent' and decision['candidate_text_unmodified']
            if decision['admitted']:
                assert state.get('observed_relation_improvement') and decision['no_confirmed_unsupported_policy']
                entry = read(A / 'development' / alias / 'experience-candidate.json')
                assert entry['text_sha256'] == sha(A / 'development' / alias / 'experience-original.md')
                assert entry['primary_class'] not in [x['primary_class'] for x in entries]
                entries.append(entry)
            decisions.append({'alias': alias, 'state': state, 'decision': decision})
        else:
            decisions.append({'alias': alias, 'state': state, 'decision': {'admitted': False, 'reason': state['reason']}})
    save(A / 'frozen-library.json', entries)
    frozen = dict(read(A / 'protocol.json')['files'])
    frozen[str(A / 'frozen-library.json')] = sha(A / 'frozen-library.json')
    for alias in ['D1', 'D2']:
        for f in (A / 'development' / alias).glob('*'):
            if f.is_file():
                frozen[str(f)] = sha(f)
    save(A / 'experience-freeze.json', {'time': time.time(), 'entries': len(entries), 'files': frozen,
         'decisions': decisions, 'test_cases': ['T1', 'T2'], 'test_schedule': read(A / 'schedule.json'),
         'no_test_learning': True, 'raw_text_only_delivered': True})
    if not entries:
        save(A / 'completion.json', {'status': 'STOPPED_AFTER_DEVELOPMENT_NO_DELIVERABLE_EXPERIENCE',
                                    'test_sessions': 0, 'time': time.time()})
    print('FROZEN', len(entries), 'entries', flush=True)


def test():
    check()
    frozen = read(A / 'experience-freeze.json')
    runner.verify(frozen['files'])
    library = read(A / 'frozen-library.json')
    assert library, 'no test when both classes empty'
    assert not (A / 'test-started.json').exists(), 'no test restart/retry'
    save(A / 'test-started.json', {'time': time.time(), 'freeze_sha256': sha(A / 'experience-freeze.json')})
    # Both independent test analyses/routes happen only after library freeze.
    prompts = {}
    for alias in ['T1', 'T2']:
        analysis = analysis_for(alias)
        decision = route(analysis, sources(alias), library)
        out = A / 'testing' / alias
        save(out / 'route.json', decision)
        chosen = next((e['text'] for e in library if decision['selected'] and e['sha256'] == decision['selected']['sha256']), None)
        task = (material(alias) / 'task.md').read_text()
        prompts[alias] = {'A': maintenance_prompt(task, analysis['contract']),
                          'B': maintenance_prompt(task, analysis['contract'], chosen)}
        for arm, prompt in prompts[alias].items():
            (out / (arm + '-prompt.md')).write_text(prompt)
        save(out / 'prompt-correspondence.json', {'identical': prompts[alias]['A'] == prompts[alias]['B'],
             'A_sha256': text_digest(prompts[alias]['A']), 'B_sha256': text_digest(prompts[alias]['B']),
             'same_contract_sha256': text_digest(analysis['contract']), 'selected_experience': decision['selected']})
    save(A / 'test-input-freeze.json', {str(p): sha(p) for p in (A / 'testing').rglob('*') if p.is_file()})
    for slot in read(A / 'schedule.json')['slots']:
        runner.verify(frozen['files'])
        runner.verify(read(A / 'test-input-freeze.json'))
        execute(slot, slot['alias'], prompts[slot['alias']][slot['arm']])
    save(A / 'completion.json', {'status': 'COMPLETED', 'test_maintenance_sessions': 8,
                                 'no_more_calls': True, 'time': time.time()})


def main():
    try:
        if sys.argv[1] == 'train':
            train(sys.argv[2])
        elif sys.argv[1] == 'freeze':
            freeze()
        elif sys.argv[1] == 'test':
            test()
        else:
            raise ValueError('unknown stage')
    except Stop as exc:
        print('STOP:', exc, flush=True)
        sys.exit(2)
    except Exception as exc:
        save(A / 'stop.json', {'reason': 'controller exception: ' + repr(exc), 'time': time.time(),
             'no_retry': True, 'no_more_model_calls': True, 'launched_slots': [r['slot'] for r in journal()]})
        raise


if __name__ == '__main__':
    main()
