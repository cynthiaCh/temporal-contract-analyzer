"""Finite offline setup for the single authorized D1 reflection diagnostic."""
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

A = Path(__file__).resolve().parent
REPO = A.parent.parent
HANDOFF = REPO / 'research/reflection-evidence-handoff-20261108_234110'
RUNTIME = REPO / 'research/two-class-experience-pilot-v2r5-20261108_223418'
BASE = REPO / 'research/two-class-experience-pilot-v2r4-20261108_221657'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(p, value):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def read(p):
    return json.loads(Path(p).read_text())


def main():
    if (A / 'prepared.json').exists():
        raise ValueError('Setup already completed; immutable batch, no overwrites')
    started = time.time()
    initial = {'time': started,
         'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
         'status': subprocess.check_output(['git', 'status', '--short'], cwd=REPO, text=True),
         'diff': subprocess.check_output(['git', 'diff'], cwd=REPO, text=True)}
    if not (A / 'initial-state.json').exists():
        save(A / 'initial-state.json', initial)
    provenance = []
    def copy(src, dest, handling='reused_unmodified'):
        src, dest = Path(src), A / dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        provenance.append({'source': str(src), 'destination': str(dest.relative_to(A)),
                           'sha256': sha(src), 'handling': handling})
    def tree(src, dest):
        for p in Path(src).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                copy(p, str(Path(dest) / p.relative_to(src)))
    # Execute only runner.session. campaign.py and all test schedulers are absent.
    for name in ['runner.py', 'archive.py', 'usage.py', 'native_backend.py', 'guard_server.py',
                 'guard_client.py', 'request_guard.py', 'read_policy.py', 'structured.py',
                 'maintenance.schema.json', 'extraction.schema.json', 'research-config.toml',
                 'models-cache.snapshot.json', 'toolflow.py', 'feedback_v2.py']:
        copy(RUNTIME / name, name)
    for name in ['handoff.py', 'feedback.py', 'schema_validator.py', 'reflection.schema.json', 'test_handoff.py']:
        copy(HANDOFF / name, name)
    copy(RUNTIME / 'test_runtime_v2.py', 'test_runtime_v2.py')
    copy(RUNTIME / 'test_read_policy_real.py', 'test_read_policy_real.py')
    tree(HANDOFF / 'inputs', 'inputs')
    tree(HANDOFF / 'audit', 'audit')
    copy(HANDOFF / 'evidence-ledger.json', 'evidence-ledger.original.json')
    ledger = read(HANDOFF / 'evidence-ledger.json')
    # Minimal provenance-role addition for the explicitly authorized critique.
    hp = A / 'handoff.py'
    hp.write_text(hp.read_text().replace("'training_patch', 'training_public_delivery'}",
                 "'training_patch', 'training_public_delivery', 'training_rejection_review'}"))
    rejection = read(HANDOFF / 'audit/rejected-candidate-replay.json')
    critique = {'role': 'AI_assisted_execution_agent_review_not_human_approval',
                'purpose': 'Critique of the rejected prior candidate, not an experience seed.',
                'issues': rejection['issues'], 'causal_limit': rejection['causal_limit']}
    save(A / 'inputs/rejected-clauses.json', critique)
    ledger['files']['inputs/rejected-clauses.json'] = {'role': 'training_rejection_review',
                                                      'sha256': sha(A / 'inputs/rejected-clauses.json')}
    # Add raw schedule anchors for the specifically requested contrasts. These
    # are Python-extracted observations, not new normative rules or diagnoses.
    for effect in ['offline-detach-false', 'nonconsuming-flight-cache', 'retained-context-query-flag']:
        for run in ['original', 'auto1', 'auto2']:
            name = 'inputs/original-score.json' if run == 'original' else f'inputs/{run}/score.json'
            score = read(A / name)
            ledger['entries'].append({'id': f'O-{run}-{effect}', 'kind': 'observed_result',
               'statement': f'{run}: complete observed scenario; no causal inference.',
               'author': 'python_score_extraction', 'related': [], 'anchors': [
                   {'type': 'json', 'file': name, 'pointer': '/schedules/' + effect,
                    'value': score['schedules'][effect]}]})
    save(A / 'evidence-ledger.json', ledger)
    import sys
    sys.path.insert(0, str(A))
    import runner
    from handoff import verify_ledger, rebuild_feedback, assemble_payload, INSTRUCTIONS
    from archive import inventory
    from toolflow import maintenance_prompt
    case = read(RUNTIME / 'cohort.json')[0]
    assert case['case'] == 'query-paused-initial-fetch-10266-vanilla' and case['role'] == 'train'
    save(A / 'case.json', case)
    tree(RUNTIME / 'materials/D1/candidate', 'candidate')
    copy(RUNTIME / 'materials/D1/task.md', 'task.md')
    copy(RUNTIME / 'derived/D1/automatic-contract.md', 'automatic-contract.md')
    oracle = Path(case['source_case']) / 'oracle'
    assert runner.backend.hashes(oracle) == case['oracle_files'], 'Scoring version changed'
    assert runner.backend.hashes(A / 'candidate') == case['candidate_files']
    assert sha(A / 'task.md') == case['task_sha256']
    assert (A / 'automatic-contract.md').read_bytes() == (HANDOFF / 'inputs/automatic-contract.md').read_bytes()
    common = maintenance_prompt((A / 'task.md').read_text(), (A / 'automatic-contract.md').read_text())
    (A / 'AUTO-prompt.md').write_text(common)
    candidates = []
    for receipt in REPO.glob('research/*/runs/*/archive/receipt.json'):
        d = read(receipt)
        if d.get('alias') != 'D1' or d.get('phase') != 'repair' or d.get('condition') != 'AUTO':
            continue
        root = receipt.parent
        config = read(root / 'input/config.json')
        start = read(root / 'input/frozen-start.json')
        matches = (d.get('status') == 'VALID' and d.get('scoring_admissible') is True
                   and d.get('score_result', {}).get('score_valid') is True
                   and start['prompt_sha256'] == sha(A / 'AUTO-prompt.md')
                   and start['files'] == inventory(A / 'candidate')
                   and config.get('model') == 'gpt-5.6-terra' and config.get('effort') == 'low'
                   and config.get('requests_per_session') == 24
                   and config.get('seconds_per_session') == 600)
        candidates.append({'archive': str(root), 'slot': d['slot'], 'started_at': d['started_at'],
                           'same_conditions_and_valid': matches})
    eligible = sorted([r for r in candidates if r['same_conditions_and_valid']], key=lambda r: r['started_at'])
    if len(eligible) < 2:
        raise ValueError('Cannot confirm two matching baselines; no baseline rerun authorized')
    selected = eligible[-2:]
    for n, record in enumerate(selected, 1):
        root = Path(record['archive'])
        assert root == BASE / f'runs/D1-AUTO-v2r4-{n}/archive', 'Latest baseline differs from handoff inputs'
        assert (root / 'input/actual-prompt.md').read_text() == common
        assert sha(root / 'score/stdout.json') == sha(A / f'inputs/auto{n}/score.json')
        for name in ['runner.py', 'native_backend.py', 'request_guard.py', 'guard_server.py',
                     'guard_client.py', 'read_policy.py', 'maintenance.schema.json',
                     'research-config.toml', 'models-cache.snapshot.json']:
            assert sha(root.parents[2] / name) == sha(A / name), 'Baseline runtime mismatch: ' + name
        assert read(root / 'score/receipt.json')['oracle_sha256'] == case['oracle_files']
        tree(root, f'baselines/auto{n}/archive')
    save(A / 'baseline-selection.json', {'algorithm': 'Latest two matching valid D1 AUTO sessions by actual started_at, never score rank',
        'candidates': candidates, 'selected': selected, 'all_condition_checks_passed': True,
        'intentional_change': 'Maintenance prompt adds only the new raw experience text after review.',
        'global_profile_note': 'CLI low effort overrides research-config medium; command and request hooks are authoritative.'})
    assert runner.ROLE['reflect'] == ('gpt-5.6-terra', 'medium', 12, 'reflection')
    assert runner.ROLE['repair'] == ('gpt-5.6-terra', 'low', 24, 'maintenance')
    verify_ledger(A, ledger)
    fb = rebuild_feedback(A, ledger); save(A / 'feedback.json', fb)
    payload = assemble_payload(A, ledger, fb); save(A / 'reflection-input.json', payload)
    # The original generic instructions are preserved except for truthful
    # disclosure of the newly authorized rejected-clause critique.
    instructions = INSTRUCTIONS.replace('No reference patch, prior experience, test outcome or expected class is supplied.',
        'No reference patch, test outcome or expected class is supplied. Only rejected clauses of the previous candidate and their evidence are provided as critique, not as an experience seed.')
    instructions += ('\nUse only evidence IDs actually listed in the payload. Across your rules, explicitly include every mandatory_counterevidence ID below; preserve every constraint ID. '
                     'Unresolved items use statement and impact fields; harmless scope limits differ from unresolved policy.\n')
    prompt = instructions + '\nMandatory counterevidence IDs: ' + json.dumps(ledger['mandatory_counterevidence'])
    prompt += '\nTRAINING PAYLOAD (complete, not a pathname to read):\n' + json.dumps(payload, ensure_ascii=False)
    (A / 'reflection-prompt.md').write_text(prompt)
    (A / 'reflection-task.md').write_text('Reflect once on the frozen D1 training evidence; no tools, no alternative candidate, no old E2 seed.\n')
    (A / 'reflection-workspace').mkdir()
    save(A / 'reflection-workspace/payload.json', payload)
    protocol = {'schema': 'D1-evidence-handoff-development-diagnostic-1', 'created_at': started,
       'case': case['case'], 'scope': 'D1 development only; no test access',
       'roles': {'reflect': {'model': 'gpt-5.6-terra', 'effort': 'medium', 'requests': 12, 'seconds': 600, 'tools': False},
                 'repair': {'model': 'gpt-5.6-terra', 'effort': 'low', 'requests': 24, 'seconds': 600, 'tools': 'identical to selected AUTO'}},
       'maximum_sessions': 3, 'maximum_requests': 60, 'concurrency': 1,
       'stdout_bytes': 16777216, 'retry': False,
       'schedule': ['D1-reflection', 'D1-revalidation-1', 'D1-revalidation-2'],
       'stop_on': ['first infrastructure anomaly', 'invalid reflection output', 'confirmed unsupported policy or factual contradiction', 'input/isolation/meter drift'],
       'admission': 'Evidence-supported improvement in at least one target relation or overall repair; no confirmed unsupported policy; record all regressions; neither full passes required nor sufficient.',
       'no_test_or_next_reflection': True}
    save(A / 'protocol.json', protocol)
    save(A / 'provenance.json', {'copied': provenance, 'modified': ['handoff.py: add training_rejection_review role only'],
                               'regenerated': ['reflection-input.json', 'reflection-prompt.md', 'feedback.json', 'evidence-ledger.json'],
                               'old_E2_seed': False, 'model_outputs_modified': False})
    save(A / 'prepared.json', {'offline_setup_seconds': time.time() - started, 'model_requests': 0})
    print('Prepared matching baselines and complete training-only reflection payload', flush=True)


if __name__ == '__main__':
    main()
