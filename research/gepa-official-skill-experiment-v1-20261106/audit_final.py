"""Deterministic evidence audit; no extra model review or task execution."""
from runtime import *

def main():
 p=frozen();rows=read(OUT/'task-results.json');ledger=read(OUT/'task-ledger.json');sel=read(OUT/'selection.freeze.json');complete=read(OUT/'completion.json');checks=[]
 assert [r['id'] for r in ledger]==[r['id'] for r in rows];assert len({r['id'] for r in rows})==len(rows);checks.append('unique launch/result association')
 assert sum(r['phase']=='opt' for r in rows)<=24 and sum(r['phase']=='test' for r in rows)<=12;assert read(OUT/'official-result.json')['total_metric_calls']==sum(r['phase']=='opt' for r in rows);assert requests_used()<=6;checks.append('all three budgets and official metric counter')
 skills={sha(read(f)['temporal_skill']):read(f)['temporal_skill'] for f in (OUT/'candidates').glob('*/candidate.json')}
 for r in rows:
  d=Path(r['path'])/'jobs/j-001';m=read(Path(r['path'])/'manifest.json');assert m['input_files']==p['cases'][r['case']]['input_files'];assert sha((d/'prompt.md').read_bytes())==r['prompt_sha256']==sha(full_prompt(r['case'],skills[r['skill_sha256']]))
  assert sha((d/'report.md').read_bytes())==r['common_sha256']==p['cases'][r['case']]['common_sha256'];assert r['category']=='behavior'
  meter=read(d/'model-meter/ledger.json');assert meter['denied']==0;assert meter['started']==r['model_requests'];assert all(e['event'].get('model')=='gpt-6-sol' for e in meter['events'] if e['event'].get('hook_event_name')=='PreModelRequest')
  assert read(r['evaluation'])['calibration_verdict']=='PASS';assert Path(r['raw_oracle']).is_file();assert (d/'patch.diff').is_file()
 checks.append('all actual prompts, common bytes, starts, scoring links, model and native counters')
 tests=[r for r in rows if r['phase']=='test'];assert all(datetime.fromisoformat(r['at'].replace('Z','+00:00')).timestamp()>=sel['at'] for r in tests)
 assert [(r['case'],r['arm'],r['replicate']) for r in tests]==[(r['case'],r['arm'],r['replicate']) for r in read(OUT/'test.schedule.json')]
 if sel['Kstar_equals_K0']:assert len(tests)==6 and all(r['arm']=='A' for r in tests)
 checks.append('selection before test, fixed paired schedule, duplicate condition cancelled')
 for r in read(OUT/'reflection-calls.json'):
  txt=(Path(r['path'])/'prompt.md').read_text();assert not any(k in txt for k in read(OUT/'private-score-identifiers.json'));assert not any(c in txt for c in VAL+TEST);assert r['tool_calls']==0
 checks.append('reflection train-only content, no private score IDs, no tools')
 assert not list((OUT/'.runtime').rglob('auth.json'));initial=read(OUT/'initial-git.json');assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==initial['head'];assert subprocess.check_output(['git','diff'],text=True)==initial['diff'];checks.append('protected inputs and existing git state; temporary auth profiles removed')
 save(OUT/'integrity-audit.json',dict(status='PASS',type='deterministic self-audit, not independent external review',checks=checks,real_tasks=len(rows),real_model_review_calls=0))
 print('AUDIT_PASS')
if __name__=='__main__':main()
