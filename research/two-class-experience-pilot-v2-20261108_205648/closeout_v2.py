"""Post-stop, no-model closeout. Never modifies frozen execution artifacts."""
import hashlib
import json
from pathlib import Path

A = Path(__file__).resolve().parent


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    assert (A / 'stop.json').exists(), 'only closes an already stopped batch'
    diagnostic = read(A / 'diagnostics/preanalysis-material-failure.json')
    summary = read(A / 'summary.json')
    summary['preparation_outcome'] = {
        'extraction_attempts': 1, 'transport_valid_sessions': 1,
        'material_valid_extractions': 0, 'material_invalid_extractions': 1,
        'not_started_reextractions': ['T1'], 'D1_baselines_started': 0,
        'new_reflections': 0, 'development_revalidations': 0,
        'test_freeze_created': False, 'frozen_library_created': False,
        'not_a_post_training_empty_library': True}
    summary['preparation_failure'] = diagnostic
    save(A / 'summary.json', summary)
    frozen = read(A / 'protocol.json')['files']
    protected = read(A / 'protected-files.json')
    changes = [p for p, h in {**protected, **frozen}.items()
               if not Path(p).is_file() or sha(Path(p)) != h]
    integrity = read(A / 'integrity-check.json')
    integrity.update(protected_or_frozen_changes=changes,
                     verified_source_artifacts=len({**protected, **frozen}),
                     v1_untouched=not any('two-class-experience-pilot-20261108_200017/' in p for p in changes),
                     runtime_valid_extraction=1, material_valid_extraction=0,
                     tests_started=0, tests_valid=0, tests_invalid_started=0, tests_unstarted=8)
    assert not changes
    save(A / 'integrity-check.json', integrity)
    message = '''research: fix null-safe archival and audit pilot semantic errors

Preserve partial responses and unknown usage on failed or malformed sessions.
Gate behavior scoring on complete candidates and stop v2 on runtime/material failure.
Audit raw task/source, patches, checks and reflection rather than trusting prior reports.
Normalize checks/assertions feedback and distinguish retained success from prior success.
Archive v2's invalid first extraction without retrying or launching A/B tests.
Disclose the bounded nested-JSON interface blocker and eight unstarted test slots.
Preserve all v1 history, original scoring, production registry and global configuration.
'''
    (A / 'COMMIT_MESSAGE.txt').write_text(message)
    save(A / 'code-summary.json', {p.name: sha(p) for p in A.glob('*.py')})
    save(A / 'final-source-manifest.json', {
        'pre_execution_manifest': 'source-manifest.json',
        'v1_preserved': True,
        'regeneration_actual': {'D1': 'one new raw automatic output; invalid, not accepted',
                                'T1': 'not started', 'D2': 'unchanged reuse', 'T2': 'unchanged reuse'},
        'v2_experience': 'not generated or frozen',
        'new_actual_outputs': {str(p.relative_to(A)): sha(p) for p in A.rglob('*')
                               if p.is_file() and p.name not in ['archive-manifest.json', 'final-source-manifest.json']
                               and '__pycache__' not in p.parts
                               and str(p) not in frozen}})
    save(A / 'code-summary.json', {p.name: sha(p) for p in A.glob('*.py')})
    save(A / 'archive-manifest.json', {
        'self_excluded': True, 'status': 'STOPPED_PREPARATION_INVALID_AUTOMATIC_MATERIAL',
        'files': {str(p.relative_to(A)): sha(p) for p in A.rglob('*')
                  if p.is_file() and p.name != 'archive-manifest.json' and '__pycache__' not in p.parts}})
    print(json.dumps({'status': 'STOPPED_PREPARATION_INVALID_AUTOMATIC_MATERIAL',
                      'sessions': summary['sessions_started'], 'requests': summary['cost_total']['requests_started'],
                      'known_total_tokens': summary['cost_total']['known_token_subtotal']['total_tokens'],
                      'test_valid_A': 0, 'test_valid_B': 0, 'integrity': integrity}, ensure_ascii=False))


if __name__ == '__main__':
    main()
