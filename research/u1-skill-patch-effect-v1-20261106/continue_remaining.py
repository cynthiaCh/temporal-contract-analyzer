"""Explicit operational repair: skip dynamic manifest hashes, never rerun a slot."""
import importlib.util,json,shutil,time
from pathlib import Path
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('frozen_u1_study',OUT/'run.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
read=s.read;save=s.save;sha=s.sha

def freeze():
 p=read(OUT/'protocol.json');assert sha((OUT/'protocol.json').read_bytes())==(OUT/'protocol.sha256').read_text().strip()
 runs=read(OUT/'runs.json');dynamic={str(Path(r['path'])/'manifest.json'):r for r in runs};changed=[]
 for n,h in p['frozen_files'].items():
  if n not in dynamic:assert sha(Path(n).read_bytes())==h,n
  elif sha(Path(n).read_bytes())!=h:changed.append(n)
 common=(OUT/'materials'/s.CASE/'common.md').read_text();old=read(Path(read(OUT/'historical-comparators.json')['historical_parent_execution']['path'])/'manifest.json')
 for n,r in dynamic.items():
  m=read(Path(n));assert m['id']==r['id'] and m['input_files']==r['input_files'] and m['task']==old['task']
  assert m['mode']=='workspace-write' and m['model']=='gpt-6-sol' and m['model_override']=='gpt-6-sol' and m['effort']=='low' and m['timeout']==600 and m['conditions']==['none'] and m['local_codex'] is True
  assert m['file_modes']==old['file_modes'] and m['case']==old['case'] and len(m['jobs'])==1
  j=m['jobs'][0];assert j['id']=='j-001' and j['prompt_sha256']==r['prompt_sha256'] and j['report_sha256']==sha(common)
  assert sha((Path(r['path'])/'jobs/j-001/prompt.md').read_bytes())==r['prompt_sha256']
  assert all(sha((Path(r['path'])/'input'/f).read_bytes())==h for f,h in r['input_files'].items())
 return changed

def execute():
 assert read(OUT/'preflight.json')['status']=='PASS';assert not (OUT/'continuation.freeze.json').exists(),'Only one explicit continuation; no auto retry'
 changed=freeze();ledger=read(OUT/'invocations.json');rows=read(OUT/'results.json');assert len(ledger)==len(rows)==1 and ledger[0]['id']==read(OUT/'runs.json')[0]['id']
 save(OUT/'runtime-correction.json',dict(reason='Original freeze incorrectly included operational manifests; first completed job changes status/usage/timestamps as designed',original_protocol_preserved=True,original_run_script_preserved=True,changed_dynamic_manifests=changed,immutable_inputs_unchanged=True,completed_slots_not_rerun=[x['id'] for x in ledger],remaining_slots=5,session_cap_unchanged=6,autonomous_executor_and_scoring_unchanged=True))
 save(OUT/'continuation.freeze.json',dict(at=s.rt.archive.now(),files={str(f):sha(f.read_bytes()) for f in [Path(__file__),OUT/'runtime-correction.json']},scope='Operational validation only; original inputs, skills, prompts, schedule and scoring unchanged'))
 w=s.rt.wb();completed_ids={x['id'] for x in ledger}
 for r in read(OUT/'runs.json'):
  if r['id'] in completed_ids:continue
  freeze()
  for n,h in read(OUT/'continuation.freeze.json')['files'].items():assert sha(Path(n).read_bytes())==h
  assert len(ledger)<6;ledger.append(dict(id=r['id'],sequence=r['sequence'],at=s.rt.archive.now()));save(OUT/'invocations.json',ledger);row=dict(r);start=time.monotonic()
  try:
   w.start(r['id']);w.thread.join();m=w.read(r['id']);j=m['jobs'][0];d=Path(r['path'])/'jobs/j-001';ep=w.latest_evaluation(r['id']);ev=read(ep) if ep else {};entry=ev.get('jobs',{}).get('j-001',{})
   category='execution-failure' if j['status']!='completed' else 'behavior' if ev.get('calibration_verdict')=='PASS' and entry.get('status') in ['passed','failed'] else 'validation-unverified'
   tr=s.rt.usage((d/'events.jsonl').read_text());changes=read(d/'changes.json') if (d/'changes.json').exists() else {'files':[]};meter=read(d/'model-meter/ledger.json') if (d/'model-meter/ledger.json').exists() else None
   if 'failed to spawn code-mode host' in (d/'events.jsonl').read_text():category='execution-tool-unavailable'
   row.update(category=category,status=j['status'],evaluation=str(ep) if ep else None,started_at=j.get('started_at'),completed_at=j.get('completed_at'),score=None,usage=tr['totals'],tool_calls=len(tr['tools']),model_requests=meter['started'] if meter else None,model_completed=meter['completed'] if meter else None,denied_retries=meter['denied'] if meter else None,changed_paths=[f['path'] for f in changes['files']])
   if category=='behavior':
    rawpath=Path(r['path'])/entry['result_path'];row.update(raw_score=str(rawpath),score=s.rt.normalize(s.CASE,read(rawpath)))
   save(d/'trajectory-index.json',tr);(d/'patch.diff').write_text('\n'.join(f.get('diff','') for f in changes['files']))
  except Exception as e:row.update(category='execution-error',error=repr(e),score=None)
  finally:shutil.rmtree(OUT/'.runtime'/r['id'],ignore_errors=True)
  row['including_score_seconds']=time.monotonic()-start;rows.append(row);save(OUT/'results.json',rows)
  print(json.dumps(dict(event='session_finished',sequence=r['sequence'],id=r['id'],status=row['category'])),flush=True)
 save(OUT/'completion.json',dict(status='COMPLETE',sessions=len(ledger),at=s.rt.archive.now(),no_retries=True,operational_continuation=True));print('SIX_SESSIONS_FINISHED',flush=True)
if __name__=='__main__':execute()
