"""Read archived JSON/events only. No experiment imports, model calls, or subprocess execution."""
import csv,hashlib,json,re,collections,datetime
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];SRC=ROOT/'research/gepa-official-skill-experiment-v1-20261106'
def read(p):return json.loads(Path(p).read_text())
def digest(x):return hashlib.sha256(x if isinstance(x,bytes) else x.encode()).hexdigest()
def save(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def loc(p,n=None):
 s=str(Path(p).relative_to(ROOT)) if Path(p).is_absolute() and ROOT in Path(p).parents else str(p)
 return s+(':'+str(n) if n else '')
def events(p):return [(n,json.loads(l)) for n,l in enumerate(Path(p).read_text().splitlines(),1)]
def checks(raw,case,protocol):
 cp=Path(protocol['cases'][case]['manifest']);m=read(cp);v=read(cp.parent/m['oracle']['effects'])['variants']['ungranted'];o=raw['observed_effects']
 return {**{'required:'+k:o[k] is True for k in v['required']},**{'forbidden:'+k:o[k] is False for k in v['forbidden']}}
def assertions(raw):return {s+'/'+a['id']:a['passed'] is True for s,v in raw.get('schedules',{}).items() for a in v.get('assertions',[])}
def diff(a,b):return dict(gained=[k for k,v in a.items() if not v and b.get(k) is True],lost=[k for k,v in a.items() if v and b.get(k) is False],not_emitted=[k for k,v in a.items() if v and k not in b])
def meter_cost(folder,phase):
 ev=events(folder/'events.jsonl');turns=[e['usage'] for n,e in ev if e['type']=='turn.completed'];tools=[(n,e['item']) for n,e in ev if e['type']=='item.completed' and e.get('item',{}).get('type') not in ['agent_message','reasoning','error',None]]
 row=dict(phase=phase,cli_sessions=1,task_executions=int(phase!='reflection'),**{k:sum(t.get(k,0) for t in turns) for k in ['input_tokens','cached_input_tokens','output_tokens']},tool_calls=len(tools))
 return row,ev,tools

def main():
 protocol=read(SRC/'protocol.json');rows=read(SRC/'task-results.json');led=read(SRC/'task-ledger.json');assert [r['id'] for r in rows]==[r['id'] for r in led]
 byid={};commands=[];costrows=[];rawrecords=[];skills={digest(read(f)['temporal_skill']):read(f)['temporal_skill'] for f in (SRC/'candidates').glob('*/candidate.json')}
 for r in rows:
  folder=Path(r['path']);assert SRC in folder.parents;d=folder/'jobs/j-001';raw=read(r['raw_oracle']);assert raw['case_id']==r['case'];evscore=read(r['evaluation']);assert (folder/evscore['jobs']['j-001']['result_path']).resolve()==Path(r['raw_oracle']).resolve();score=checks(raw,r['case'],protocol);aa=assertions(raw);whole=int(raw['verdict']=='PASS');assert whole==r['metric'];assert score==r['score']['checks'];assert aa==r['score']['assertions'];assert read(r['evaluation'])['calibration_verdict']=='PASS'
  cost,ev,tools=meter_cost(d,r['split']);cost.update(id=r['id'],seconds_including_scoring=r['including_score_seconds'],seconds_origin='archived monotonic receipt; raw provider costs re-summed independently')
  meter=read(d/'model-meter/ledger.json');pres=[e for e in meter['events'] if e['event']['hook_event_name']=='PreModelRequest'];posts=[e for e in meter['events'] if e['event']['hook_event_name']=='PostModelRequest'];assert meter['started']==len(pres)==r['model_requests'];assert meter['completed']==len(posts);assert meter['denied']==0
  pt={k:sum(e['event'].get('token_usage',{}).get(k,0) for e in posts) for k in ['input_tokens','cached_input_tokens','output_tokens']};assert all(pt[k]==cost[k]==r['usage'][k] for k in pt);assert cost['tool_calls']==r['tool_calls'];cost['native_requests']=len(pres);cost['completed_requests']=len(posts);jr=read(d/'result.json');cost['cli_wall_seconds_from_timestamps']=(datetime.datetime.fromisoformat(jr['completed_at'].replace('Z','+00:00'))-datetime.datetime.fromisoformat(jr['started_at'].replace('Z','+00:00'))).total_seconds();costrows.append(cost)
  manifest=read(folder/'manifest.json');assert manifest['input_files']==protocol['cases'][r['case']]['input_files'];assert digest((d/'prompt.md').read_bytes())==r['prompt_sha256'];assert digest((d/'report.md').read_bytes())==r['common_sha256'];assert r['status']=='completed';assert read(d/'result.json')['exit_code']==0
  assert all(digest((folder/'input'/k).read_bytes())==v for k,v in protocol['cases'][r['case']]['input_files'].items());expected_prompt=(SRC/'materials'/r['case']/'common.md').read_text()+'\n<base-execution>\n'+(SRC/'BASE.md').read_text()+'\n</base-execution>\n\n<temporal-contract-skill>\n'+skills[r['skill_sha256']]+'\n</temporal-contract-skill>\n\n<fixed-ending>\n'+(SRC/'END.md').read_text()+'\n</fixed-ending>\n';assert (d/'prompt.md').read_text()==expected_prompt
  changes=read(d/'changes.json');entry=dict(sequence=r['sequence'],id=r['id'],case=r['case'],phase=r['phase'],split=r['split'],whole_pass=whole,checks=score,assertions=aa,raw_score=loc(r['raw_oracle']),events=loc(d/'events.jsonl'),prompt=loc(d/'prompt.md'),patch=loc(d/'patch.diff'),changed_paths=[f['path'] for f in changes['files']],skill_sha256=r['skill_sha256'],source_row=r)
  byid[r['id']]=entry;rawrecords.append({k:v for k,v in entry.items() if k!='source_row'})
  for n,e in ev:
   item=e.get('item',{})
   if e['type']!='item.completed' or item.get('type')!='command_execution':continue
   cmd=item['command'];output=item.get('aggregated_output','');code=item['exit_code'];category=None
   if code not in [0,None]:
    if 'Not a git repository' in output or 'not a git repository' in output:category='environment_git_absent'
    elif 'ERR_ASSERTION' in output:category='candidate_assertion_failed'
    elif 'ERR_UNKNOWN_FILE_EXTENSION' in output:category='other_jsx_check_invocation'
    elif 'Cannot find module' in output or ('ls ' in cmd and 'node_modules/react' in cmd):category='environment_dependency_missing'
    elif code==1 and 'rg --files' in cmd:category='normal_search_no_match'
    elif code==2 and 'rg -n' in cmd:category='other_search_missing_path_or_glob'
    else:category='unclassified';raise AssertionError((r['id'],n,code))
   commands.append(dict(job_id=r['id'],sequence=r['sequence'],case=r['case'],event_line=n,source=loc(d/'events.jsonl',n),exit_code=code,category=category,command=cmd,output=output))
 bycost={}
 for i,ref in enumerate(read(SRC/'reflection-calls.json'),1):
  assert ref['exit_code']==0 and ref['status']=='completed';folder=Path(ref['path']);cost,ev,tools=meter_cost(folder,'reflection');cost.update(id=f'reflection-{i}',seconds_including_scoring=ref['seconds']);cost['native_requests']=ref['native_requests_after']-ref['native_requests_before'];costrows.append(cost);assert cost['native_requests']==1 and not tools
  assert all(cost[k]==ref['usage'][k] for k in ['input_tokens','cached_input_tokens','output_tokens'])
 assert sum(c['native_requests'] for c in costrows if c['phase']=='reflection')==read(SRC/'reflection-meter/ledger.json')['started']
 for phase in ['train','val','reflection','test','total']:
  rr=[r for r in costrows if r['phase']==phase or phase=='total'];bycost[phase]={k:sum(r.get(k,0) for r in rr) for k in ['cli_sessions','task_executions','native_requests','input_tokens','cached_input_tokens','output_tokens','seconds_including_scoring','cli_wall_seconds_from_timestamps','tool_calls']}
 ev=events(SRC/'official-events.jsonl');batches=read(SRC/'adapter-evaluations.json');datasets=read(SRC/'reflection-datasets.json');selection=[];feedback_audit=[]
 for iteration in range(1,6):
  ee=[(n,e) for n,e in ev if e['data'].get('iteration')==iteration];select=next((n,e) for n,e in ee if e['event']=='on_candidate_selected');proposal=next((n,e) for n,e in ee if e['event']=='on_proposal_end');reject=next((n,e) for n,e in ee if e['event']=='on_candidate_rejected');evals=[(n,e) for n,e in ee if e['event']=='on_evaluation_end'];pe,ce=evals;parentids=[o['task_execution_id'] for o in pe[1]['data']['outputs']];childids=[o['task_execution_id'] for o in ce[1]['data']['outputs']]
  assert parentids==datasets[iteration-1]['task_ids'];par=select[1]['data']['candidate']['temporal_skill'];skill=proposal[1]['data']['new_instructions']['temporal_skill'];key=digest(json.dumps({'temporal_skill':skill},sort_keys=True));candidate=SRC/'candidates'/key;assert read(candidate/'candidate.json')['temporal_skill']==skill;assert read(candidate/'review.json')['allow_execution'];assert read(candidate/'validation.json')['valid'];assert digest(skill)==read(candidate/'review.json')['skill_sha256']
  prompt=(SRC/f'reflections/call-{iteration:02}/prompt.md').read_text();rawanswer=(SRC/f'reflections/call-{iteration:02}/raw-answer.txt').read_text();assert prompt==proposal[1]['data']['prompts']['temporal_skill'];assert rawanswer==proposal[1]['data']['raw_lm_outputs']['temporal_skill'];assert par in prompt;assert skill in rawanswer
  batch=batches[iteration*2-1];childbatch=batches[iteration*2];assert batch['task_ids']==parentids and childbatch['task_ids']==childids;ds=read(datasets[iteration-1]['path']);assert digest(Path(datasets[iteration-1]['path']).read_bytes())==datasets[iteration-1]['sha256']
  comparisons=[];audit_items=[]
  for pos,ident in enumerate(parentids):
   a=byid[ident];child=next(byid[k] for k in childids if byid[k]['case']==a['case']);assert a['split']==child['split']=='train';assert a['skill_sha256']==digest(par) and child['skill_sha256']==digest(skill);assert skill in Path(ROOT/child['prompt']).read_text()
   comparisons.append(dict(case=a['case'],parent_job=ident,child_job=child['id'],parent_whole=a['whole_pass'],child_whole=child['whole_pass'],parent_required_passed=sum(v for k,v in a['checks'].items() if k.startswith('required:')),child_required_passed=sum(v for k,v in child['checks'].items() if k.startswith('required:')),check_delta=diff(a['checks'],child['checks']),assertion_delta=diff(a['assertions'],child['assertions']),parent_score=a['raw_score'],child_score=child['raw_score'],child_events=child['events'],child_patch=child['patch']))
   data=ds['temporal_skill'][pos];g=data['Generated_Outputs'];feedback=data['Feedback'];assert data['Inputs']['original_maintenance_task']==(SRC/'materials'/a['case']/'task.md').read_text();assert data['Inputs']['visible_context']==(SRC/'materials'/a['case']/'source.md').read_text();assert data['Inputs']['original_maintenance_task'] in prompt and data['Inputs']['visible_context'] in prompt
   actual={c['event_line']:c for c in commands if c['job_id']==ident};trunc=[]
   for c in g['tool_observations']:
    act=actual[c['event_line']];assert c['command']==act['command'][:8000] and c['actual_output']==act['output'][:5000] and c['exit_code']==act['exit_code'];assert c['command_truncated']==(len(act['command'])>8000);assert c['output_truncated']==(len(act['output'])>5000)
    if c['output_truncated'] or c['command_truncated']:trunc.append(dict(event_line=c['event_line'],category=act['category'],full_output_characters=len(act['output']),included_output_characters=len(c['actual_output']),command_truncated=c['command_truncated']))
   actual_changes=read(Path(a['source_row']['path'])/'jobs/j-001/changes.json')['files'];assert len(actual_changes)==len(g['modified_locations'])
   for c,ac in zip(g['modified_locations'],actual_changes):assert c['path']==ac['path'] and c['diff']==ac['diff'][:18000]
   assert feedback['whole_behavior_score']==a['whole_pass'];assert feedback['original_passed_check_loss_count']==len(a['source_row']['score']['original_check_losses'])
   audit_items.append(dict(parent_job=ident,case=a['case'],exact_task_and_context_match=True,exact_tool_observation_match=True,exact_patch_match=True,feedback=feedback,tool_output_truncations=trunc,patch_truncations=sum(c['truncated'] for c in g['modified_locations']),command_truncations=sum(c['command_truncated'] for c in g['tool_observations']),forwarded_sections=list(data),passed_effect_vector_forwarded=False,scored_schedule_trace_forwarded=False,agent_messages_forwarded=False,visible_validation_lines=[c['event_line'] for c in g['visible_validation']]))
  before=sum(byid[k]['whole_pass'] for k in parentids);after=sum(byid[k]['whole_pass'] for k in childids);assert before==reject[1]['data']['old_score'] and after==reject[1]['data']['new_score'] and not after>before
  selection.append(dict(candidate_id=f'P{iteration}',archive_key=key,skill_sha256=digest(skill),skill_path=loc(candidate/'skill.md'),parent_pool_index=select[1]['data']['candidate_idx'],parent_skill_sha256=digest(par),reflection_input=loc(SRC/f'reflections/call-{iteration:02}/prompt.md'),reflection_output=loc(SRC/f'reflections/call-{iteration:02}/raw-answer.txt'),reflection_dataset=loc(datasets[iteration-1]['path']),parent_jobs=parentids,child_jobs=childids,comparisons=comparisons,acceptance=dict(stage='train_strict_improvement_before_val',before_sum=before,after_sum=after,accepted=False,reason=reject[1]['data']['reason'],event=loc(SRC/'official-events.jsonl',reject[0]),official_code=loc(SRC/'official-src/src/gepa/strategies/acceptance.py',50)),entered_val=False,entered_official_pool=False,archived=True,event_refs=dict(selected=loc(SRC/'official-events.jsonl',select[0]),parent_evaluated=loc(SRC/'official-events.jsonl',pe[0]),proposed=loc(SRC/'official-events.jsonl',proposal[0]),child_evaluated=loc(SRC/'official-events.jsonl',ce[0]))))
  feedback_audit.append(dict(candidate=f'P{iteration}',actual_rendered_prompt_characters=len(prompt),official_prompt_exact_match=True,official_raw_output_exact_match=True,items=audit_items))
 result=read(SRC/'official-result.json');assert result['total_metric_calls']==len([r for r in rows if r['phase']=='opt'])==22;assert len(result['candidates'])==1 and result['best_idx']==0;assert all(b['valid_component'] for b in batches);assert len(batches)==11
 allval=[(n,e) for n,e in ev if e['event']=='on_valset_evaluated'];assert len(allval)==1 and allval[0][1]['data']['candidate_idx']==0
 nz=[c for c in commands if c['category']];assert len(nz)==45;categories=dict(collections.Counter(c['category'] for c in nz))
 cm={r['id']:r for r in costrows};candidate_costs=[]
 for x in selection:
  groups={}
  for role,ids in [('parent_train',x['parent_jobs']),('child_train',x['child_jobs']),('generation',['reflection-'+x['candidate_id'][1:]]),('val',[])]:groups[role]={k:sum(cm[i].get(k,0) for i in ids) for k in ['cli_sessions','task_executions','native_requests','input_tokens','cached_input_tokens','output_tokens','seconds_including_scoring','tool_calls']}
  candidate_costs.append(dict(candidate=x['candidate_id'],costs=groups))
 save('candidate-costs.json',candidate_costs)
 save('selection-trace.json',dict(official_commit=read(SRC/'environment/official.json')['commit'],candidates=selection,only_val_event=loc(SRC/'official-events.jsonl',allval[0][0]),official_final=dict(pool_size=len(result['candidates']),best_idx=result['best_idx'],parents=result['parents'],val_scores=result['val_aggregate_scores'],Kstar_equals_K0=(SRC/'Kstar.md').read_bytes()==(SRC/'K0.md').read_bytes()),stop=read(SRC/'budget-checks.json')[-1],reported_iteration_count_caveat=next(e['data'] for n,e in ev if e['event']=='on_optimization_end')))
 save('feedback-audit.json',feedback_audit);save('raw-recalculation.json',dict(tasks=rawrecords,costs=bycost,cost_receipts=costrows,nonzero_shell_counts=categories,model_calls_in_this_audit=0,validation_rule='archived raw scores only; no scorer or candidate code re-execution',actual_metric_calls=22,formal_cli_sessions=33,total_native_requests=sum(c['native_requests'] for c in costrows)))
 save('command-classification.json',nz)
 with (OUT/'command-classification.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=['job_id','sequence','case','event_line','source','exit_code','category','command']);w.writeheader();w.writerows({k:c[k] for k in w.fieldnames} for c in nz)
 up=read(SRC/'environment/official.json');installed=Path(up['installed']);source_package=SRC/'official-src/src/gepa';package_files=list(installed.rglob('*.py'));assert all((source_package/f.relative_to(installed)).read_bytes()==f.read_bytes() for f in package_files);save('official-package-verification.json',dict(commit=up['commit'],metadata_version=up['version'],installed_source_identical_python_files=len(package_files),provider_or_optimizer_executed=False))
 save('offline-validation.json',dict(status='PASS',model_calls=0,checks=['28 launch/result joins','raw oracle verdict/effect/assertion recomputation','five parent-child pairs and score sums','five dataset/job and event-line matches','five actual official reflection prompt/output exact matches','all candidate skills actually delivered','provider token receipts equal CLI turn totals','all 45 shell failures classified','budget and final pool reconciliation'],input_files_preservation='checked separately against initial-state.json'))
 print(json.dumps(dict(status='PASS',categories=categories,costs=bycost,feedback_truncations=sum(len(j['tool_output_truncations']) for x in feedback_audit for j in x['items'])),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
