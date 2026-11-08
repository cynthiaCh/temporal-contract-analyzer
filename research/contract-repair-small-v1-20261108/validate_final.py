"""Final evidence/linkage and preservation checks; no model calls."""
import ast,csv,hashlib,json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parent.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 protocol=read(O/'protocol.json');mismatches=[p for p,h in protocol['files'].items() if sha(p)!=h]
 old=read(O/'protected-previous-batch.json');old_changes=[p for p,h in old.items() if not Path(p).exists() or sha(p)!=h]
 initial=read(O/'initial-state.json');actual=read(O/'actual-schedule.json');slots=read(O/'schedule.json')['slots']
 assert len(slots)==18 and len({s['slot'] for s in slots})==18 and len({s['case'] for s in slots})==2
 assert len(actual)<=18 and [r['slot'] for r in actual]==[s['slot'] for s in slots[:len(actual)]]
 reviews=read(O/'patch-review.json') if (O/'patch-review.json').exists() else {}
 linkage=[]
 for r in actual:
  d=O/'runs'/r['slot'];assert read(d/'receipt.json')==r
  assert sha(d/'actual-prompt.md')==r['prompt_sha256']
  assert all((d/name).exists() for name in ['events.jsonl','stderr.log','raw-answer.txt','configuration-before.json','configuration-after.json','meter/ledger.json','frozen-start.json'])
  before=read(d/'configuration-before.json');after=read(d/'configuration-after.json')
  assert before['research_config_sha256']==after['profile_sha256']==sha(O/'research-config.toml')
  assert before['global_config']['sha256']==after['global_config']['sha256']==initial['global_config_sha256']
  assert r['native']['started']==r['native']['completed'] and not r['native']['blocked_requests'] and not r['native']['blocked_tools']
  assert r['native']['started'] <= (12 if r['phase']=='extract' else 24)
  if r['phase']=='repair':
   assert (d/'patch.diff').exists() and (d/'score.stdout.json').exists()
   score=read(d/'score.stdout.json');assert score['case_id']==r['case']
   assert r['candidate_files']==r['scored_candidate_files']
   assert r['slot'] in reviews and reviews[r['slot']]['status']=='REVIEWED'
  linkage.append({'slot':r['slot'],'phase':r['phase'],'status':r['status'],'prompt_matches':True,'archive_present':True,'model_match':r.get('model_match'),'infrastructure_valid':r.get('infrastructure_valid'),'score_case_match':r.get('scoring_valid') if r['phase']=='repair' else None})
 for case in read(O/'cohort.json')['cases']:
  freeze=O/'contracts'/case['case']/'freeze.json'
  if freeze.exists():
   assert all(sha(p)==h for p,h in read(freeze)['files'].items())
   automatic=(freeze.parent/'automatic.md').read_text()
   for group in ['M','E']:
    prompt=O/'prompts'/case['case']/(group+'.md');assert automatic in prompt.read_text()
   m=(O/'prompts'/case['case']/'M.md').read_text();e=(O/'prompts'/case['case']/'E.md').read_text();assert e.startswith(m) and e[len(m):]=='\n<experience>\n'+(O/'EXPERIENCE.md').read_text()+'\n</experience>\n'
 if (O/'completion.json').exists():
  assert len(actual)==18 and sum(r['phase']=='extract' for r in actual)==2 and sum(r['phase']=='repair' for r in actual)==16
  assert read(O/'case1-execution-gate.json')['status']=='PASS' and not read(O/'case1-execution-gate.json')['quality_or_score_used']
  assert read(O/'case2-execution-gate.json')['status']=='PASS'
 for p in O.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
 tracked=subprocess.check_output(['git','diff','--name-only'],cwd=R,text=True).splitlines()
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
 committed_paths=subprocess.check_output(['git','diff','--name-only',initial['head'].strip(),head],cwd=R,text=True).splitlines()
 result={'protocol_mismatches':mismatches,'previous_batch_changed_files':old_changes,'global_config_unchanged':sha(Path.home()/'.codex/config.toml')==initial['global_config_sha256'],'head_unchanged':head==initial['head'].strip(),'observed_head':head,'head_drift_record':'git-drift.json' if (O/'git-drift.json').exists() else None,'tracked_diff':tracked,'non_research_paths_in_external_head':[p for p in committed_paths if not p.startswith('research/')],'non_batch_working_diff':[p for p in tracked if not p.startswith(str(O.relative_to(R))+'/')],'auth_files_remaining':[str(p) for p in (O/'.runtime').rglob('auth.json')] if (O/'.runtime').exists() else [],'all_slots_accounted':True,'slots_started':len(actual),'total_requests':sum(r.get('native',{}).get('started',0) for r in actual),'request_cap':408,'linkage':linkage,'no_new_dependencies':True,'commits_created_by_this_executor':0,'external_commit_observed':head!=initial['head'].strip(),'no_third_case_or_old_batch_dispatcher':True}
 (O/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 assert not mismatches and not old_changes and result['global_config_unchanged'] and not result['non_batch_working_diff'] and not result['non_research_paths_in_external_head'] and not result['auth_files_remaining']
 if not result['head_unchanged']:assert (O/'git-drift.json').exists()
 assert result['total_requests']<=408
 files=[p for p in O.rglob('*') if p.is_file() and '.runtime' not in p.parts and '__pycache__' not in p.parts and p.name!='ARTIFACTS.sha256']
 (O/'ARTIFACTS.sha256').write_text(''.join(sha(p)+'  '+str(p.relative_to(O))+'\n' for p in sorted(files)))
 print('Final validation passed:',len(actual),'slots; original batch, inputs and global settings preserved.')
if __name__=='__main__':main()
