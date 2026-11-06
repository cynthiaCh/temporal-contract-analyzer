"""Offline archive replay and safety checks; never run a scorer or model."""
import ast,copy,csv,hashlib,importlib.util,json,sys
from pathlib import Path
from projections import OUT,TRAIN,Context,F0Projector,F1Projector,ProjectionError,read,sha
from guards import BudgetLedger,BudgetExceeded,AdmissionBlocked,admission,skill_boundary,deduplicated_test_schedule
OLD=OUT.parent/'gepa-official-skill-experiment-v1-20261106'
def save(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def main():
 import gepa
 from gepa.strategies.instruction_proposal import InstructionProposalSignature
 context=Context(OUT,OLD/'trials/reports-experiments','OFFLINE_ARCHIVE');f0=F0Projector(context);f1=F1Projector(context);rows=[r for r in read(OLD/'task-results.json') if r['split']=='train'];byid={r['id']:r for r in rows};datasets=read(OLD/'reflection-datasets.json');trace=read(OUT.parent/'gepa-mechanism-audit-v1-20261106/selection-trace.json')['candidates'];parentmap={c['child_job']:c['parent_job'] for x in trace for c in x['comparisons']}
 context.paired_parents=parentmap
 oldsrc=(OLD/'gepa_adapter.py').read_text();oldtree=ast.parse(oldsrc);parts=[]
 for x in oldtree.body:
  if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DESCRIPTIONS' for t in x.targets) or isinstance(x,ast.FunctionDef) and x.name=='feedback':parts.append(ast.get_source_segment(oldsrc,x))
 assert (OUT/'feedback_f0_legacy.py').read_text()=='\n\n'.join(parts)+'\n';lengths=[];packets={};relations=[]
 skills_by_sha={sha(read(f)['temporal_skill']):read(f)['temporal_skill'] for f in (OLD/'candidates').glob('*/candidate.json')}
 def render(data,skill=None):
  prompt=InstructionProposalSignature.prompt_renderer(dict(current_instruction_doc=(OUT/'K0.md').read_text() if skill is None else skill,dataset_with_feedback=data,prompt_template=(OUT/'REFLECTION_TEMPLATE.md').read_text()))
  if len(prompt)>72000:raise ProjectionError('Shared full-reflection prompt cap exceeded; no silent truncation')
  return prompt
 for r in rows:
  p0=f0.project(r);p1=f1.project(r);packets[r['id']]=(p0,p1)
  assert p0.data['Inputs']==p1.data['Inputs'];g0=p0.data['Generated_Outputs'];g1=p1.data['Generated_Outputs']
  assert all(g0[k]==g1[k] for k in g0 if k!='visible_validation')
  assert [x['event_line'] for x in g0['visible_validation']]==[x['event_line'] for x in g1['visible_validation']]
  raw=read(r['raw_oracle']);facts=p1.data['Feedback']['directional_observations'];positive=p1.data['Feedback']['preserved_current_behaviors'];assert len(positive)==sum(r['score']['checks'].values());assert p1.data['Feedback']['comparison_objects']['against_parent_execution']['available'] is False
  assert all(f['unknowns'] and f['evidence'] for f in facts)
  assert p1.metadata['unresolved_directions']==0,'All existing failed archive relations must have resolved directional observations'
  for key,entry in p1.private_evidence_index.items():
   assert entry['job_id']==r['id'] and entry['raw_score_sha256']==sha(Path(r['raw_oracle']).read_bytes());node=raw
   for token in entry['json_pointer'].split('/')[1:]:node=node[int(token)] if isinstance(node,list) else node[token]
  if r['case'].startswith('transfer'):
   need=sum(not v for k,v in r['score']['checks'].items() if k.startswith('required:'));assert len(facts)==need
   for fact in facts:
    pointers=[p1.private_evidence_index[k]['json_pointer'] for k in fact['evidence']];rawassert=[p for p in pointers if '/assertions/' in p][0];_,_,sk,_,ai=rawassert.split('/');a=raw['schedules'][sk]['assertions'][int(ai)];assert len(a['actual'])>len(a['expected']);seq=[p for p in pointers if '/trace/' in p];ev=[raw['schedules'][sk]['trace'][int(p.rsplit('/',1)[1])] for p in seq];assert [x['step'] for x in ev]==sorted(x['step'] for x in ev)
    if fact['direction']==['extra']:
     assert ev[-1]['type']=='progress.audit' and ev[-2]['type']=='feed.emit' and ev[-2]['deferred'] is False;assert ev[-1]['fileId']==ev[-2]['fileId']!=ev[-3]['fileId'];assert ev[-3]['type']=='host.select'
    else:
     assert fact['direction']==['ownership_mismatch','order_error'];assert ev[0]['type']=='feed.emit' and ev[0]['deferred'] is True;assert ev[1]['type']==ev[2]['type']=='progress.visible';assert ev[1]['attemptId']!=ev[2]['attemptId'];assert ev[0]['seq']==ev[2]['seq'] and ev[0]['fileId']==ev[2]['fileId']
  elif facts:
   assert len(facts)==1 and facts[0]['direction']==['missing'];s=next(v for v in raw['schedules'].values() if isinstance(v.get('afterFirstPending'),dict));assert s['afterFirstPending']['loading'] is False and s['afterFirstPending']['retryScheduled'] is True and not s['afterFirstPending']['completed'];assert s['final']['completed']
  for version,packet in [('F0',p0),('F1',p1)]:
   d=OUT/'examples'/r['id'];save(d/(version+'.feedback.json'),packet.data);skill=skills_by_sha[r['skill_sha256']];assert skill in (Path(r['path'])/'jobs/j-001/prompt.md').read_text();prompt=render([packet.data],skill);(d/(version+'.prompt.md')).write_text(prompt)
   assert not any(v in prompt for v in read(OUT/'private-score-identifiers.json'))
   lengths.append(dict(scope='single archived train job',record=r['id'],current_skill_sha256=r['skill_sha256'],arm=version,prompt_characters=len(prompt),prompt_bytes=len(prompt.encode()),length_cap=72000,exact_model_tokens=None,token_note='No gpt-6-sol tokenizer available; no inference used to count. Actual new provider usage is zero.',additional_truncation=False,fields=list(packet.data)))
  save(OUT/'research-evidence'/r['id']/ 'source-index.json',p1.private_evidence_index)
  if r['id'] in parentmap:
   paired=f1.project(r,parent=byid[parentmap[r['id']]]);comp=paired.data['Feedback']['comparison_objects']['against_parent_execution'];a=byid[parentmap[r['id']]]['score']['checks'];b=r['score']['checks'];assert len(comp['lost'])==sum(v and not b.get(k) for k,v in a.items());assert len(comp['gained'])==sum(not v and b.get(k) for k,v in a.items());save(OUT/'research-evidence'/r['id']/'explicit-paired-comparison.json',comp)
  relations.append(dict(job_id=r['id'],directions=[f['direction'] for f in facts],preserved_count=len(positive),unresolved_directions=p1.metadata['unresolved_directions']))
 for i,ds in enumerate(datasets,1):
  original=read(ds['path'])['temporal_skill'];data0=[packets[k][0].data for k in ds['task_ids']];data1=[packets[k][1].data for k in ds['task_ids']];assert data0==original
  prompt0=render(data0);prompt1=render(data1);assert prompt0==(OLD/f'reflections/call-{i:02}/prompt.md').read_text()
  d=OUT/'paired-reflection-inputs'/f'batch-{i:02}';d.mkdir(parents=True,exist_ok=True)
  for arm,prompt in [('F0',prompt0),('F1',prompt1)]:
   (d/(arm+'.prompt.md')).write_text(prompt);lengths.append(dict(scope='original two-record reflection batch replay, not a model request',record=f'batch-{i:02}',arm=arm,prompt_characters=len(prompt),prompt_bytes=len(prompt.encode()),length_cap=72000,exact_model_tokens=None,additional_truncation=False))
 # Fail-closed scope/mismatch checks, with no altered historical files.
 rejected=[]
 def must_reject(name,call,kind):
  try:call()
  except kind:rejected.append(name);return
  raise AssertionError(name+' unexpectedly accepted')
 sample=rows[0]
 for name,changes in [('val_row',dict(split='val')),('test_row',dict(split='test')),('wrong_case',dict(case=TRAIN[0] if sample['case']==TRAIN[1] else TRAIN[1])),('metric_swapped',dict(metric=1-sample['metric'])),('unverified',dict(category='validation-unverified'))]:must_reject(name,lambda changes=changes:f1.project(dict(sample,**changes)),ProjectionError)
 must_reject('cross_arm',lambda:F1Projector(Context(OUT,OLD/'trials/reports-experiments','F1')).project(dict(sample,arm='F0')),ProjectionError)
 other=next(r for r in rows if r['case']!=sample['case']);must_reject('cross_case_parent',lambda:f1.project(sample,parent=other),ProjectionError)
 child=next(r for r in rows if r['id'] in parentmap);stale=next(r for r in rows if r['case']==child['case'] and r['id']!=parentmap[child['id']]);must_reject('same_case_stale_parent',lambda:f1.project(child,parent=stale),ProjectionError)
 must_reject('overlength_prompt',lambda:render([dict(Inputs=dict(offline_length_test='x'*72001))]),ProjectionError)
 # Capacity simulation is explicitly not formal usage.
 sims={}
 for arm in ['F0','F1']:
  ledger=BudgetLedger();ledger.reserve_task_batch(12);ledger.account_metrics(12);must_reject(arm+'_task13',lambda:ledger.reserve_task_batch(1),BudgetExceeded)
  for _ in range(3):ledger.reserve_reflection_cli();ledger.account_reflection_pre_request()
  must_reject(arm+'_reflection4',ledger.account_reflection_pre_request,BudgetExceeded);must_reject(arm+'_reflection_cli4',ledger.reserve_reflection_cli,BudgetExceeded);assert not ledger.may_start_iteration();sims[arm]=ledger.snapshot()
 assert sum(x['task_executions'] for x in sims.values())==24;assert sum(x['reflection_native_requests'] for x in sims.values())==6
 meter_spec=importlib.util.spec_from_file_location('new_offline_request_meter',OUT/'request_meter.py');meter=importlib.util.module_from_spec(meter_spec);meter_spec.loader.exec_module(meter)
 md=OUT/'offline-meter';save(md/'config.json',dict(max_requests=3))
 if (md/'ledger.json').exists():md=OUT/'offline-meter-rechecks'/('check-'+str(len(list((OUT/'offline-meter-rechecks').glob('check-*')))+1));save(md/'config.json',dict(max_requests=3))
 for _ in range(4):meter.account(dict(hook_event_name='PreModelRequest',simulation=True),md,kill=False)
 assert read(md/'ledger.json')['started']==3 and read(md/'ledger.json')['denied']==1
 k=(OUT/'K0.md').read_text();assert skill_boundary({'temporal_skill':k})['allow_execution'];assert not skill_boundary({'temporal_skill':'Use src/queue.js and retry-preserved.'})['allow_execution']
 renamed={'temporal_skill':'Let the first lifetime be amber and the replacement violet. Always prescribe the concrete transition sequence from the diagnostic example.'};assert not skill_boundary(renamed)['allow_execution'];bad_review=dict(skill_sha256=sha(renamed['temporal_skill']),allow_execution=False,no_hidden_scoring_or_reference_repair=True,no_case_specific_answer_including_renamed_answers=False,source_qualified_not_new_business_rules=False,fixed_maintenance_objective_preserved=True);assert not skill_boundary(renamed,bad_review)['allow_execution']
 from official_adapter import ProjectionAdapter
 model_attempts=[];runner=lambda *x:model_attempts.append(x)
 ad=ProjectionAdapter('F0',context,BudgetLedger(),runner);must_reject('source_gate_before_runner',lambda:ad.evaluate([dict(case=TRAIN[0],split='train')],{'temporal_skill':k},True),AdmissionBlocked);assert not model_attempts
 from types import SimpleNamespace
 wrong=next(r for r in rows if r['skill_sha256']!=sha(k));must_reject('cross_candidate_reflection',lambda:ad.make_reflective_dataset({'temporal_skill':k},SimpleNamespace(trajectories=[dict(wrong,arm='F0')]),['temporal_skill']),AdmissionBlocked)
 for count in [1,2,3]:
  skills={f'v{i}':f'synthetic unique text {i}' for i in range(count)};schedule=deduplicated_test_schedule(['synthetic-a','synthetic-b','synthetic-c'],skills);assert len(schedule)==count*6
 assert len(deduplicated_test_schedule(['synthetic-a','synthetic-b','synthetic-c'],{'K0':k,'F0':k,'F1':k}))==6
 must_reject('novel_source_gate',admission,AdmissionBlocked)
 from importlib import metadata
 installed=Path(gepa.__file__).parent;up=read(OLD/'environment/official.json');source=OLD/'official-src/src/gepa';assert metadata.version('gepa')==up['version'];files=list(installed.rglob('*.py'));assert all((source/f.relative_to(installed)).read_bytes()==f.read_bytes() for f in files)
 save(OUT/'environment-lock.json',dict(version=up['version'],commit=up['commit'],reused_existing_isolated_environment=str(Path(sys.executable)),installed_package=str(installed),official_python_files_verified=len(files),new_dependencies_installed=False,official_optimize_called=False))
 save(OUT/'lengths.json',lengths);save(OUT/'relation-validation.json',relations);save(OUT/'offline-validation.json',dict(status='PASS',formal_admission='BLOCKED_SOURCE_ADMISSION',real_model_calls=0,real_task_executions=0,scorer_reruns=0,official_optimization_calls=0,archived_train_jobs_verified=len(rows),old_feedback_records_exactly_reproduced=10,old_full_reflection_prompts_exactly_reproduced=5,all_facts_directions_verified=True,current_vs_parent_comparators_distinguished=True,negative_checks=rejected,synthetic_budget_capacity=sims,underlying_pre_request_counter_simulated=dict(allowed=3,denied=1),test_dedup_capacity=dict(maximum=18,identical_skills=6),semantic_leakage_review='mechanical checks and mandatory hash-bound semantic review; renamed answers not automatically authorized',input_token_measurement='unavailable offline; no guessed exact model token counts',length_max_by_arm={a:max(x['prompt_characters'] for x in lengths if x['arm']==a) for a in ['F0','F1']}))
 print(json.dumps(read(OUT/'offline-validation.json'),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
