import pathlib as P,json,csv,hashlib,importlib.util,subprocess,difflib,collections
O=P.Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('e',O/'execute.py');e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e);r=e.r;save=r.save
assert (O/'completion.json').exists() or (O/'stop.json').exists(),'Wait for frozen-plan completion or operational stop'
rows=r.read(O/'actual-schedule.json');slots=r.read(O/'schedule.json')['slots'];cases=r.cases();keys=['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens']
def cost(ds):return {'sessions':len(ds),'requests':sum(d.get('native',{}).get('started',0) for d in ds),'tools':sum(d.get('native',{}).get('tool_attempts',0) for d in ds),'shell_commands':sum(d.get('tools',0) for d in ds),'seconds':sum(d.get('seconds',0) for d in ds),'usage':{k:sum(d.get('usage',{}).get(k,0) for d in ds) for k in keys},'usage_incomplete':any(d.get('usage_incomplete') for d in ds)}
summary={'scope':'same-cluster conditional historical-failure development transfer; not independent source generalization','AI_assisted':True,'independent_human_review':False,'selected_cases':[c['case'] for c in cases],'selection_evidence':'Repeated Qwen bare-task failures, same base/model/effort, distinct historical workflows; NOT repeated automatic-Contract or target-Terra difficulty. Target bare/H each 1 prior PASS per case.','planned_top_level':14,'planned_maintenance':12,'attempted_top_level':len(rows),'attempted_maintenance':sum(d['phase']=='repair' for d in rows),'budget_requests':312,'unstarted':[s for s in slots if s['slot'] not in {d['slot'] for d in rows}],'cases':{},'total_cost':cost(rows),'extraction_cost':cost([d for d in rows if d['phase']=='extract']),'anomalies':[d['slot'] for d in rows if d.get('stop_reason') or not d.get('infrastructure_valid')],'no_retry_or_replacement':True,'currency_cost':None,'currency_reason':'No verified price; cached-input and reasoning-output are subsets. Main chat preparation/analysis token use unavailable, excluded rather than zero.'}
score_rows=[];case_rows=[];mechanism=[]
for c in cases:
 cid=c['case'];ds=[d for d in rows if d['case']==cid and d['phase']=='repair'];groups={}
 for g in ['A','B']:
  gs=[d for d in ds if d['condition']==g];valid=[d for d in gs if d['status']=='VALID'];groups[g]={'attempted':len(gs),'valid':len(valid),'scoring_valid':sum(bool(d.get('scoring_valid')) for d in gs),'pass':sum(d.get('raw_verdict')=='PASS' for d in valid),'pass_rate':sum(d.get('raw_verdict')=='PASS' for d in valid)/len(valid) if valid else None,'cost':cost(gs)}
 pairs=[]
 for rep in range(1,4):
  a=next((d for d in ds if d['condition']=='A' and d['repeat']==rep),None);b=next((d for d in ds if d['condition']=='B' and d['repeat']==rep),None)
  if not a or not b:continue
  ap=O/'runs'/a['slot'];bp=O/'runs'/b['slot'];ac=cost([a]);bc=cost([b]);asc=r.read(ap/'score.stdout.json') if (ap/'score.stdout.json').exists() else {};bsc=r.read(bp/'score.stdout.json') if (bp/'score.stdout.json').exists() else {};ae=asc.get('observed_effects',{});be=bsc.get('observed_effects',{})
  raw_added=[k for k in ae if ae[k]!=be.get(k) and be.get(k) is True];raw_lost=[k for k in ae if ae[k]!=be.get(k) and be.get(k) is False]
  pairs.append({'repeat':rep,'A':a.get('raw_verdict'),'B':b.get('raw_verdict'),'all_raw_effects_equal':ae==be,'raw_false_to_true':raw_added,'raw_true_to_false':raw_lost,'B_minus_A':{**{k:bc[k]-ac[k] for k in ['requests','tools','shell_commands','seconds']},'usage':{k:bc['usage'][k]-ac['usage'][k] for k in keys}}})
 summary['cases'][cid]={'groups':groups,'pairs':pairs}
 for d in ds:
  p=O/'runs'/d['slot'];events=[]
  for n,line in enumerate((p/'events.jsonl').read_text().splitlines(),1):
   z=json.loads(line);i=z.get('item',{})
   if z['type']=='item.completed' and i.get('type')=='command_execution':events.append({'event_line':n,'command':i.get('command'),'exit_code':i.get('exit_code'),'output':i.get('aggregated_output')})
  save(p/'command-evidence.json',events)
  if not (p/'score.stdout.json').exists():continue
  sc=r.read(p/'score.stdout.json');base=c['calibration'][0]['effects'];se=sc['observed_effects'];lost=[k for k in base if base[k] is True and se[k] is False];added=[k for k in base if base[k] is False and se[k] is True]
  score_rows.append({'slot':d['slot'],'case':cid,'condition':d['condition'],'repeat':d['repeat'],'verdict':sc['verdict'],'effects':se,'raw_true_lost_vs_start':lost,'raw_true_added_vs_start':added,'missing_required':sc['missing_required_effects'],'forbidden':sc['observed_forbidden_effects']})
  original=O/'materials'/cid/'candidate';patched=p/'workspace';changed=[];parts=[]
  for f in original.rglob('*'):
   if not f.is_file():continue
   rel=str(f.relative_to(original));g=patched/rel
   if not g.exists() or r.sha(f)!=r.sha(g):
    changed.append(rel)
    if g.exists():parts+=difflib.unified_diff(f.read_text().splitlines(True),g.read_text().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel)
  (p/'source-only.patch').write_text(''.join(parts));added_files=[str(f.relative_to(patched)) for f in patched.rglob('*') if f.is_file() and not (original/f.relative_to(patched)).exists()];save(p/'patch-scope.json',{'source_changes':changed,'added_files':added_files,'bytecode_note':'read_policy pycache generated by common guard in writable candidate; not a source repair'})
  case_rows.append({'case':cid,'slot':d['slot'],'condition':d['condition'],'repeat':d['repeat'],'status':d['status'],'failure_class':d.get('failure_class'),'infrastructure_valid':d.get('infrastructure_valid'),'scoring_valid':d.get('scoring_valid'),'verdict':sc['verdict'],'required_missing':';'.join(sc['missing_required_effects']),'forbidden':';'.join(sc['observed_forbidden_effects']),'raw_true_lost_vs_start':';'.join(lost),'source_changes':';'.join(changed),'requests':d['native']['started'],'tools':d['native']['tool_attempts'],'shell_commands':d['tools'],'seconds':d['seconds'],**d.get('usage',{})})
  mechanism.append({'slot':d['slot'],'commands':str(p/'command-evidence.json'),'source_changes':changed,'nonzero_command_events':[v['event_line'] for v in events if v['exit_code']!=0]})
summary['valid_maintenance']=sum(d['status']=='VALID' for d in rows if d['phase']=='repair');summary['all_maintenance_scoring_valid']=all(d.get('scoring_valid') for d in rows if d['phase']=='repair')
save(O/'summary.json',summary);save(O/'score-comparison.json',score_rows);save(O/'mechanism-index.json',mechanism)
if case_rows:
 with (O/'case-results.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(case_rows[0]));w.writeheader();w.writerows(case_rows)
protected=r.read(O/'protected-files.json');changed=[p for p,h in protected.items() if not P.Path(p).exists() or r.sha(P.Path(p))!=h];assert not changed;conf=r.read(O/'frozen-config.json');after=r.backend.global_snapshot();assert after==conf['global_config_before'];r.verify()
save(O/'protection-check.json',{'existing_files_checked':len(protected),'changed':changed,'global_config_unchanged':True,'global_config_after':after,'HEAD_before':r.read(O/'initial-git.json')['HEAD'],'HEAD_after':subprocess.check_output(['git','rev-parse','HEAD'],cwd=e.A.parents[1],text=True).strip(),'git_status':subprocess.check_output(['git','status','--short'],cwd=e.A.parents[1],text=True),'no_commit_created':True})
e.archive();print(json.dumps(summary,ensure_ascii=False,indent=2))
