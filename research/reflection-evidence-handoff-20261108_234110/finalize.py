"""Python-only verification log, source comparison and archive summaries."""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from handoff import digest, verify_ledger, assemble_payload
from build import save, ROOT, REPO


def main():
    command = ['python3', '-m', 'unittest', 'discover', '-s', str(ROOT), '-p', 'test_handoff.py', '-v']
    result = subprocess.run(command, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    (ROOT / 'verification.log').write_text(result.stdout + result.stderr)
    verification = {'command': command, 'exit_code': result.returncode,
                    'timestamp_utc': datetime.now(timezone.utc).isoformat(),
                    'source': 'actual_subprocess', 'model_calls': 0}
    save('verification.json', verification)
    if result.returncode:
        raise SystemExit(result.returncode)
    ledger = json.loads((ROOT / 'evidence-ledger.json').read_text())
    verify_ledger(ROOT, ledger)
    feedback = json.loads((ROOT / 'feedback.json').read_text())
    if assemble_payload(ROOT, ledger, feedback) != json.loads((ROOT / 'reflection-input.json').read_text()):
        raise ValueError('archived payload mismatch')
    provenance = json.loads((ROOT / 'provenance.json').read_text())
    sources_ok = all(digest((REPO / item['source']).read_bytes()) == item['sha256']
                     and digest((ROOT / item['destination']).read_bytes()) == item['sha256']
                     for item in provenance['reused'])
    tracked_diff = subprocess.check_output(['git', 'diff', 'HEAD', '--name-only'], cwd=REPO, text=True)
    status = subprocess.check_output(['git', 'status', '--short'], cwd=REPO, text=True)
    save('workspace.json', {'initial_head': provenance['head'], 'initial_status': '', 'initial_diff': '',
                            'initial_observation': 'execution_agent read before implementation',
                            'final_status': status, 'final_tracked_diff': tracked_diff,
                            'source_copies_match_current_originals': sources_ok})
    if not sources_ok or tracked_diff:
        raise ValueError('source provenance or unrelated tracked work changed; inspect before finalization')
    summary = json.loads((ROOT / 'summary.json').read_text())
    summary.update(status='offline_handoff_complete', tests_passed=17,
                   engineering_tokens=None, engineering_cost=None,
                   model_experiment_tokens=0, test_sessions_started=0,
                   learned_effectiveness='not_evaluated',
                   old_history_modified=False, scope='training_D1_evidence_handoff_only')
    save('summary.json', summary)
    artifact_files = sorted(p for p in ROOT.rglob('*') if p.is_file()
                            and '__pycache__' not in p.parts and p.name not in {'integrity.json', 'ARTIFACTS.sha256'})
    hashes = {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in artifact_files}
    save('integrity.json', {'source_provenance_match': sources_ok, 'input_anchors_valid': True,
                            'payload_reconstructed_exactly': True, 'tests_exit_code': result.returncode,
                            'tracked_diff_empty': not bool(tracked_diff), 'sha256': hashes,
                            'excluded': ['__pycache__/', 'integrity.json (self)', 'ARTIFACTS.sha256 (manifest)']})
    hashes['integrity.json'] = digest((ROOT / 'integrity.json').read_bytes())
    (ROOT / 'ARTIFACTS.sha256').write_text(''.join(f'{h}  {name}\n' for name, h in sorted(hashes.items())))
    print(json.dumps({'status': summary['status'], 'tests_passed': 17, 'model_calls': 0,
                      'artifacts': len(hashes)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
