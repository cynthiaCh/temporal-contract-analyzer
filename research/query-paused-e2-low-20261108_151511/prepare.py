"""Offline evidence projection and immutable source reuse; no model/scorer calls."""
import sys,json,hashlib,shutil,subprocess,time,random
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;S=A.parent/'query-paused-frozen-experience-followup-20261108_144036';O=A.parent/'query-paused-same-case-low-20261108_140200'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def verify(d):
 for p,h in d.items():assert sha(p)==h,p
assert not (A/'diagnosis.json').exists()
save(A/'initial-state.json',{'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'status':subprocess.check_output(['git','status','--short'],text=True),'tracked_diff':subprocess.check_output(['git','diff','HEAD'],text=True),'time':time.time(),'instructions':'No applicable ancestor/root/research AGENTS.md; nested unrelated official-src AGENTS.md does not apply.'})
for src in [S,O]:
 verify(read(src/'protocol.json')['files']);assert sha(src/'protocol.json')==(src/'protocol.sha256').read_text().strip()
 for line in (src/'ARTIFACTS.sha256').read_text().splitlines():
  h,f=line.split('  ',1);assert sha(src/f)==h,(src,f)
verify(read(S/'protected-files.json'))
c=read(S/'cohort.json');assert c['case']==read(S/'materials/manifest.json')['id'];B=Path(c['source_case'])
modules=['runner.py','archive.py','native_backend.py','guard_server.py','guard_client.py','request_guard.py','read_policy.py','prompts.py','research-config.toml','models-cache.snapshot.json','extraction.schema.json','reflection.schema.json']
provenance={}
for n in modules+['cohort.json','automatic-contract.md','automatic-contract-full.md','scorer-dependencies.json','training-targets.json']:
 shutil.copyfile(S/n,A/n);provenance[n]={'source':str(S/n),'sha256':sha(A/n)}
shutil.copytree(S/'materials',A/'materials');shutil.copyfile(S/'NEW_EXPERIENCE.md',A/'E1.md')
(A/'prompts').mkdir();shutil.copyfile(S/'prompts/AUTO.md',A/'prompts/AUTO.md')
protected=read(S/'protected-files.json')
for p in S.rglob('*'):
 if p.is_file() and not p.is_symlink():protected[str(p.resolve())]=sha(p)
save(A/'protected-files.json',protected)
fc=read(S/'frozen-config.json');old_ref=read(O/'runs/reflection/archive/input/config.json')
assert (old_ref['model'],old_ref['effort'],old_ref['requests_per_session'],old_ref['seconds_per_session'])==('gpt-5.6-terra','medium',12,600)
for row in read(S/'actual-schedule.json'):
 cfg=read(S/'runs'/row['slot']/'archive/input/config.json');assert (cfg['model'],cfg['effort'],cfg['requests_per_session'],cfg['seconds_per_session'])==('gpt-5.6-terra','low',24,600)
fc.update(roles={'repair':['gpt-5.6-terra','low',24,'maintenance'],'reflect':['gpt-5.6-terra','medium',12,'reflection']},max_sessions=7,max_underlying_requests=156,maintenance_sessions=6,maintenance_requests=144,maintenance_cumulative_seconds=3600,reflection_sessions=1,reflection_requests=12,reflection_cumulative_seconds=600,cumulative_session_seconds=4200,source_batch=str(S),experience_candidates=1,no_reflection_extraction_gepa=False,no_extraction_or_gepa=True)
save(A/'frozen-config.json',fc)
# Immutable source snapshots for readable evidence; no reference/correct patch is delivered to reflection.
for f in ['base/src/session.js','base/README.md','oracle/worker.cjs','oracle/recovery-rubric.json','oracle/assertion-obligation-map.json','oracle/effects.json']:
 p=A/'evidence/standard'/f;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(B/f,p)
targets=read(A/'training-targets.json')['targets'];failures=['cached-prior-consumed-success','retained-context-query-flag'];runfacts=[]
for slot in ['block-1-B','block-2-B','block-3-B']:
 d=S/'runs'/slot/'archive';z=A/'evidence'/slot;z.mkdir(parents=True)
 for f in ['patch.diff','events.jsonl','raw-answer.txt','receipt.json','usage.json']:
  shutil.copyfile(d/f,z/f)
 shutil.copytree(d/'final-candidate',z/'final-candidate');shutil.copytree(d/'score',z/'score')
 score=read(z/'score/stdout.json');assert all(score['observed_effects'][k] for k in targets) and all(not score['observed_effects'][k] for k in failures)
 messages=[];commands=[]
 for n,l in enumerate((z/'events.jsonl').read_text().splitlines(),1):
  e=json.loads(l);item=e.get('item',{})
  if e.get('type')=='item.completed' and item.get('type')=='agent_message':messages.append({'event_line':n,'text':item['text']})
  if e.get('type')=='item.completed' and item.get('type')=='command_execution':commands.append({'event_line':n,'command':item.get('command'),'exit_code':item.get('exit_code'),'output':item.get('aggregated_output')})
 save(z/'visible-messages.json',messages);save(z/'commands.json',commands)
 checks={k:score['schedules'][k] for k in targets+failures}
 getter='attempt only' if slot!='block-2-B' else 'writes attempt and query; cancellation reads attempt only'
 fact={'slot':slot,'effects':score['observed_effects'],'verdict':score['verdict'],'positive_targets':targets,'failures':failures,'relevant_raw_schedules':checks,'consumption_change':getter,'explicit_model_plan':messages[1] if slot!='block-1-B' else messages[-1],'actual_patch':(z/'patch.diff').read_text(),'actual_final_report':(z/'raw-answer.txt').read_text(),'visible_messages':messages,'source':str(d)}
 runfacts.append(fact)
# Historical same-E1 success is only a causal-limit witness, not a replacement formal result or golden patch feedback.
old_success=read(O/'runs/reval-2/archive/score/stdout.json');old_code=(O/'runs/reval-2/archive/final-candidate/src/session.js').read_text();assert old_success['verdict']=='PASS' and 'if(q.consumed)' in old_code
mapping=read(B/'oracle/assertion-obligation-map.json');obligation=next(x for x in read(B/'oracle/recovery-rubric.json')['obligations'] if x['id']=='lazy-signal-consumption')
feedback={'projection':'AI-assisted offline source/trace/score evidence; not another model judgment','source_batch':str(S),'E1_instruction_assessment':{'explicit_attempt_consumption_migration_required':False,'actual_emphasis':['按尝试身份区分','是否曾进入执行与是否读取取消能力分别何时记录','依据是否已启动、缓存刷新及原有生命周期约定判断'],'omitted_boundary':'No explicit reset/ownership rule separating shared consumption state from attempt/controller validity.','causality_limit':'Potential overextension is a hypothesis. Visible plans and patches establish chosen implementation, not hidden reasoning or single-sentence causation.'},'source_behavior':{'actual_entry':'invoke resets query-level consumption; lazy getter marks its owning query and returns originating attempt controller','paused_creation':'subscribe constructs new attempt without resetting existing query consumption','last_observer':'unsubscribe consults query-level consumption before canceling originating current attempt','ownership_boundary':'Shared query state and individual attempt/controller identity have different lifetimes; their existing contracts must be established separately.'},'standard':{'obligation':obligation,'assertion_witnesses':[x for x in mapping['assertions'] if x['schedule'] in targets+failures],'original_source_sha256':sha(A/'materials/candidate/src/session.js'),'standard_worker_sha256':sha(A/'evidence/standard/oracle/worker.cjs')},'runs':runfacts,'preserve_success':'All three target relations passed in all three B runs; do not discard initial retirement/idle settlement/queued invalidation, legal cached refresh or started nonconsuming completion.','correct_failure':'Both failing schedules invoked twice rather than the required once; retain expected existing behavior, not relax evaluator.','feedback_exposure':'This training feedback may contain score/standard details. Future maintenance sees only unchanged A plus raw frozen E2, not this feedback, patches or score explanations.','unknowns':['No counterfactual patch was executed or scored in this offline diagnosis.','No causal certainty about experience wording; no universal law for every shared-cache system.','No reference or manually repaired patch supplied.']}
save(A/'training-feedback.json',feedback)
save(A/'diagnosis.json',{'status':'OFFLINE_COMPLETE','E1_sha256':sha(A/'E1.md'),'case':c['case'],'explicit_instruction_requires_attempt_consumption':False,'model_selected_attempt_consumption_in_all_three':True,'shared_query_consumption_standard_explicit':True,'missing_self_checks':'Visible self-validation lacks the two cross-attempt consumption/retained-context sequences; ordinary same-attempt cancel and unconsumed refresh checks passed.','mechanism':'Loss of query-scoped consumption across a paused replacement or old retained context prevents cancellation of its current paused attempt; reconnect invokes again.','causal_limit':'Observed implementation convergence, not proof E1 uniquely forced it; wording is ambiguous/incomplete, not an explicit demand to migrate consumption.','historical_counterevidence':{'source':str(O/'runs/reval-2/archive/score/stdout.json'),'sha256':sha(O/'runs/reval-2/archive/score/stdout.json'),'verdict':'PASS','same_E1':True,'query_consumption_retained':True,'not_pooled_in_followup':True,'no_success_patch_delivered_to_reflector':True},'model_calls':0,'maintenance_executions':0,'score_reruns':0,'no_business_source_edits':True})
prefix=(O/'reflection-input.md').read_text().split('\n\n原任务：',1)[0]
# Preserve original output protocol and generality restrictions; revise task from first experience to one E2 update.
prefix=prefix.replace('根据本批同题开发的源绑定差异与真实维护结果，只做一次Reflection，输出一份通用时序修复经验。','根据已冻结经验E1及后续同题对照的源绑定成功与失败证据，只做一次Reflection，修订为唯一候选E2。')
source='\n\n'.join('SOURCE '+str(p.relative_to(A/'materials/candidate'))+'\n'+p.read_text() for p in (A/'materials/candidate').rglob('*') if p.is_file() and p.suffix in ['.js','.md'])
prompt=prefix+'\n\n本轮修订关注：在保留三项目标改善的同时，区分单次尝试有效性/取消控制器与共享查询状态的生命周期。依据源码与标准解释应查证什么、验证什么；不要直接给出补丁，不把本例字段名或评分项写入通用经验。\n\nE1原文：\n'+(A/'E1.md').read_text()+'\n\n原任务：\n'+(A/'materials/task.md').read_text()+'\n\n候选可见文档与源码：\n'+source+'\n\n本轮成功与失败的真实反馈及标准依据：\n'+json.dumps(feedback,ensure_ascii=False,indent=2)
(A/'reflection-input.md').write_text(prompt)
rng=random.Random(20261108);slots=[]
for rep in [1,2,3]:
 arms=['A','B'];rng.shuffle(arms)
 for arm in arms:slots.append({'slot':f'block-{rep}-{arm}','case':c['case'],'phase':'repair','condition':'AUTO' if arm=='A' else 'AUTO_EXP','repeat':rep,'arm':arm})
save(A/'schedule.json',{'seed':20261108,'seed_scope':'schedule only, not model sampling','slots':slots})
save(A/'sources.json',{'source_development':str(O),'source_followup':str(S),'case_from_manifest':c['case'],'reused_files':provenance,'E1_sha256':sha(A/'E1.md'),'A_prompt_sha256':sha(A/'prompts/AUTO.md'),'original_manifest_sha256':c['manifest_sha256'],'no_reextraction_or_case_change':True,'reflection_model_budget_matches_development':True,'maintenance_model_budget_matches_followup':True,'protected_files':len(protected)})
print('Offline evidence complete; no model/scorer calls; source',c['case'],'protected',len(protected))
