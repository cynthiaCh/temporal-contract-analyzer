"""Offline input/schema preparation; no model execution or legacy scheduler."""
import json
import subprocess
import sys
import time
from pathlib import Path
sys.dont_write_bytecode = True
A = Path(__file__).resolve().parent
sys.path.insert(0, str(A))
from archive import save, sha, inventory
from handoff import (make_schema, assemble_payload, verify_ledger, rebuild_feedback,
                     INSTRUCTIONS, VERSION, CATEGORIES)
from toolflow import PREDICATES, maintenance_prompt
import runner


def read(path):
    return json.loads(Path(path).read_text())


def main():
    assert not (A / 'prepared.json').exists(), 'No overwriting prepared inputs'
    start = time.time()
    case = read(A / 'case.json')
    assert case['case'] == 'query-paused-initial-fetch-10266-vanilla'
    assert runner.backend.hashes(A / 'candidate') == case['candidate_files']
    assert sha(A / 'task.md') == case['task_sha256']
    assert runner.backend.hashes(Path(case['source_case']) / 'oracle') == case['oracle_files']
    common = maintenance_prompt((A / 'task.md').read_text(), (A / 'automatic-contract.md').read_text())
    assert common == (A / 'AUTO-prompt.md').read_text()
    comparisons = []
    for n in (1, 2):
        root = A / f'baselines/auto{n}/archive'
        config, record = read(root / 'input/config.json'), read(root / 'receipt.json')
        assert inventory(root / 'input/original') == inventory(A / 'candidate')
        assert (root / 'input/actual-prompt.md').read_text() == common
        assert record['scoring_admissible'] and record['scored_candidate_unchanged']
        assert record['score_result']['score_valid'] and record['score_result']['verdict'] == 'UNDERREACH'
        assert config['model'] == 'gpt-5.6-terra' and config['effort'] == 'low'
        assert config['requests_per_session'] == 24 and config['seconds_per_session'] == 600
        assert sha(root / 'score/stdout.json') == sha(A / f'inputs/auto{n}/score.json')
        assert read(root / 'score/receipt.json')['oracle_sha256'] == case['oracle_files']
        score = read(root / 'score/stdout.json')
        assert sum(v is True for v in score['observed_effects'].values()) == 27
        assert score['observed_effects']['cached-paused-background'] is False
        assert score['observed_effects']['cached-later-consumption'] is False
        comparisons.append({'slot': record['slot'], 'started_at': record['started_at'],
                            'matching_conditions': True, 'valid_score': True, 'satisfied': 27})
    ledger = read(A / 'evidence-ledger.json')
    verify_ledger(A, ledger)
    feedback = rebuild_feedback(A, ledger)
    assert feedback == read(A / 'feedback.json')
    save(A / 'reflection.schema.json', make_schema(ledger, PREDICATES))
    save(A / 'predicates.json', PREDICATES)
    payload = assemble_payload(A, ledger, feedback)
    payload['mechanism_predicates'] = PREDICATES
    payload['output_protocol'] = {'version': VERSION, 'rule_categories': CATEGORIES,
        'mandatory_counterevidence': ledger['mandatory_counterevidence'],
        'preservation_constraint_ids': [c['id'] for c in ledger['constraints']]}
    save(A / 'reflection-input.json', payload)
    prompt = INSTRUCTIONS + '\nComplete frozen training payload:\n' + json.dumps(payload, ensure_ascii=False)
    (A / 'reflection-prompt.md').write_text(prompt)
    (A / 'reflection-task.md').write_text('Generate one single-source rule candidate from the frozen training evidence. No tools, old E2 seed or test feedback.\n')
    (A / 'reflection-workspace').mkdir()
    save(A / 'reflection-workspace/payload.json', payload)
    # The old raw output and rejection are immutable audit inputs, never seeds.
    old = read(A / 'audit/previous-run/candidate-experience.json')
    synthetic = {'provenance': {'kind': 'synthetic_derived_test_fixture', 'is_model_candidate': False,
                                'is_effect_evidence': False, 'source_sha256': sha(A / 'audit/previous-run/candidate-experience.json'),
                                'operation': 'Copy one old quotation into a synthetic single-rule body to test rendering only.'},
                 'candidate_fragment': {'rules': [{'category': 'event_relation', 'body': old['rules'][0]['quote']}]}}
    save(A / 'offline/derived-fixture.json', synthetic)
    save(A / 'condition-audit.json', {'baselines': comparisons, 'new_baseline_execution': False,
         'task_sha256': sha(A / 'task.md'), 'contract_sha256': sha(A / 'automatic-contract.md'),
         'common_prompt_sha256': sha(A / 'AUTO-prompt.md'), 'oracle_sha256': case['oracle_files'],
         'only_intended_maintenance_input_change': 'append deterministic rendering of frozen model rule bodies',
         'code_and_permission_equivalence': 'unchanged runner/backend/guard and CLI flags checked offline'})
    save(A / 'protocol.json', {'version': VERSION, 'scope': 'D1 same-case development diagnostic only',
         'case': case['case'], 'reflect': {'model': 'gpt-5.6-terra', 'effort': 'medium', 'cap': 12, 'seconds': 600, 'tools': False},
         'repair': {'model': 'gpt-5.6-terra', 'effort': 'low', 'cap': 24, 'seconds': 600, 'tools': 'same as AUTO'},
         'maximum_sessions': 3, 'maximum_requests': 60, 'concurrency': 1, 'stdout_bytes': 16777216,
         'schedule': ['D1-reflection', 'D1-revalidation-1', 'D1-revalidation-2'],
         'retry': False, 'stop_on': ['first infrastructure anomaly', 'invalid candidate', 'confirmed unsupported semantic policy/factual conflict', 'input or measurement distortion'],
         'text_origin': 'program-derived numbering, fixed category headings and exact model bodies; no other prose added',
         'admission': 'At least one supported target/overall improvement, no confirmed unsupported policy; report every regression, no both-pass requirement.',
         'no_test_or_next_reflection': True})
    save(A / 'prepared.json', {'time': time.time(), 'offline_setup_seconds': time.time()-start, 'model_requests': 0})
    print('Prepared ledger-derived schema, predicate dictionary and fixed D1 inputs', flush=True)


if __name__ == '__main__':
    main()
