"""Read-only input/approval gate audit. Contains no model or scorer invocation."""
import hashlib,json,subprocess
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent.parent
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 provenance=read(OUT/'source-verification.json');assert len(provenance['records'])==23
 for n,entry in read(OUT/'K0.freeze.json')['files'].items():assert sha(OUT/n)==entry['sha256']
 for f in provenance['records']:
  p=Path(f['absolute_path']);assert ROOT in p.resolve().parents and p.is_file() and sha(p)==f['expected_sha256']
 for unit in provenance['inputs']:
  d=OUT/'materials'/unit['unit'];assert sha(d/'task.md')==unit['task_sha256']
  actual={str(f.relative_to(d/'candidate')):sha(f) for f in (d/'candidate').rglob('*') if f.is_file()};assert actual==unit['candidate_files']
  assert all(not any(b in name.lower() for b in ['raw-score','patch.diff','evidence-key','review.csv']) for name in actual)
  text=(d/'K0.prompt.md').read_text();assert (OUT/'analysis_skill_K0.md').read_text() in text and (OUT/'REPORT_TEMPLATE.md').read_text() in text
  assert (d/'task.md').read_text() in text and '<original-task-background>' in text
  assert 'start-switch.audit' not in text and 'downloadPending' not in text
 initial=read(OUT/'initial-state.json');changed=[n for n,h in initial['protected_files'].items() if not (ROOT/n).is_file() or sha(ROOT/n)!=h];assert not changed,changed
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==initial['head']
 assert subprocess.check_output(['git','diff'],cwd=ROOT,text=True)==initial['diff']
 assert subprocess.check_output(['git','diff','--cached'],cwd=ROOT,text=True)==initial['staged_diff']
 limits=read(OUT/'proposed-limits.json');assert limits['max_top_level_sessions']==9 and limits['maximum_native_requests_total']==8*12+1
 status=read(OUT/'confirmation-status.json');assert not status['formal_model_calls_allowed']
 result=dict(source_integrity='PASS',source_files_checked=23,source_only_candidate_inputs='PASS',K0_generic_scope='proxy checked; no case conclusions or repair requirement',approval_gate='BLOCKED: no item-level approved scope in files; conversation fact separately recorded',formal_runtime_isolation_budget_preflight='NOT_STARTED',models_invoked=0,maintenance_score_runs=0,protected_existing_files_checked=len(initial['protected_files']),existing_files_changed=changed,head_and_tracked_staged_diff_unchanged=True)
 (OUT/'offline-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
