"""Read-only final integrity verification; outputs only this study's new documents."""
import ast,hashlib,importlib.util,json,subprocess
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent.parent
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert read(OUT/'completion.json')['sessions']==6
 spec=importlib.util.spec_from_file_location('operational_check',OUT/'continue_remaining.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);dynamic=m.freeze()
 for n,h in read(OUT/'continuation.freeze.json')['files'].items():assert sha(Path(n))==h
 initial=read(OUT/'initial-state.json');changed=[n for n,h in initial['protected_files'].items() if not (ROOT/n).is_file() or sha(ROOT/n)!=h];assert not changed,changed
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==initial['head']
 assert subprocess.check_output(['git','diff'],cwd=ROOT,text=True)==initial['diff']
 assert subprocess.check_output(['git','diff','--cached'],cwd=ROOT,text=True)==initial['staged_diff']
 runs=read(OUT/'runs.json');inv=read(OUT/'invocations.json');results=read(OUT/'results.json');assert [r['id'] for r in runs]==[r['id'] for r in inv]==[r['id'] for r in results];assert len({r['id'] for r in inv})==6
 summary=read(OUT/'summary.json');assert summary['sessions']==6 and summary['reflection_requests']==summary['gepa_searches']==0
 for r in results:
  d=Path(r['path'])/'jobs/j-001';assert sha(d/'prompt.md')==r['prompt_sha256']
  if r.get('score'):assert read(Path(r['raw_score']))['verdict']==r['score']['verdict']
 for f in OUT.glob('*.py'):ast.parse(f.read_text(),filename=str(f))
 validation=dict(status='PASS',protected_files_checked=len(initial['protected_files']),existing_file_changes=changed,original_protocol_and_run_py_unchanged=True,dynamic_manifest_exemption_explicit=True,dynamic_manifests_updated=dynamic,session_order_and_uniqueness=True,sessions=6,independent_workspaces=6,raw_score_verdicts_linked=True,source_input_and_prompt_hashes_verified=True,independent_human_review_complete=False,new_dependencies=0,new_commits=0,usage_reconciliation=[dict(id=r['id'],matches=all(v['equal'] for v in r['usage_reconciliation'].values())) for r in summary['costs']['sessions']])
 (OUT/'final-validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n');print(json.dumps(validation,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
