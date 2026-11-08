"""Post-run deterministic accounting and full behavior-vector analysis; no model calls."""
import sys,json,csv,subprocess,time
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A))
from archive import save,sha,inventory,digest
import runner as r

def read(p):return json.loads(Path(p).read_text())
def main():
 assert (A/'completion.json').exists() or (A/'stop.json').exists(),'No interim quality analysis'
 rows=read(A/'actual-schedule.json') if (A/'actual-schedule.json').exists() else []
 c=read(A/'cohort.json');rules=read(A/'materials/evaluation/effects.json')['variants']['ungranted'];items=list(c['calibration'][0]['effects']);orig=c['calibration'][0]['effects'];targets=read(A/'training-targets.json')['targets']
 assert sha(A/'protocol.json')==(A/'protocol.sha256').read_text().strip()
 r.verify(read(A/'protocol.json')['files']);r.verify(read(A/'protected-files.json'))
 assert [x['slot'] for x in rows]==[x['slot'] for x in read(A/'schedule.json')['slots']][:len(rows)]
 groups={};vectors={};audits=[];per=[]
 for row in rows:
  p=A/'runs'/row['slot']/'archive'
  if not (p/'receipt.json').exists():per.append({'slot':row['slot'],'valid':False,'exception':row.get('exception')});continue
  cfg=read(p/'input/config.json');assert (cfg['model'],cfg['effort'],cfg['requests_per_session'],cfg['seconds_per_session'])==('gpt-5.6-terra','low',24,600)
  assert (p/'input/actual-prompt.md').read_bytes()==(A/'prompts'/f"{row['condition']}.md").read_bytes()
  assert cfg['slot']=={k:row[k] for k in cfg['slot']}
  assert read(p/'input/frozen-start.json')['prompt_sha256']==sha(p/'input/actual-prompt.md')
  assert r.backend.hashes(p/'input/original')==c['candidate_files']
  assert row['started_at']>=read(A/'protocol.json')['frozen_at']
  for line in (p/'ARTIFACTS.sha256').read_text().splitlines():
   h,f=line.split('  ',1);assert sha(p/f)==h,(row['slot'],f)
  final=read(p/'final-manifest.json');assert digest(inventory(p/'final-candidate'))==final['tree_sha256']
  assert inventory(p/'final-candidate')==inventory(p.parent/'workspace')
  assert final['workspace_sha256_before']==final['workspace_sha256_after']==final['tree_sha256']
  cmd=read(p/'command.json');assert cmd[cmd.index('-m')+1]=='gpt-5.6-terra' and 'model_reasoning_effort="low"' in cmd
  assert str(p) not in cmd and '/meter' not in cmd and '/output' not in cmd
  ledger=read(p/'meter/ledger.json');events=ledger.get('events',[]);posts=[x['event'] for x in events if x['event'].get('hook_event_name')=='PostModelRequest']
  assert ledger['started']==row['native']['started']<=24 and ledger['completed']==row['native']['completed']==len(posts)
  assert all(e['model']=='gpt-5.6-terra' for e in posts)
  valid=bool(row.get('infrastructure_valid') and row['archive_status']['status']=='OK' and row.get('scoring_status')=='COLLECTED' and row.get('scored_candidate_unchanged') and row.get('score_result',{}).get('score_valid'))
  effects=row.get('score_result',{}).get('effects',{});usage=read(p/'usage.json');changes=read(p/'file-changes.json')
  if valid:
   assert set(effects)==set(items)
   assert read(p/'score-before-manifest.json')==read(p/'score-after-manifest.json')==inventory(p/'final-candidate')
   assert row['scored_candidate_sha256']==final['tree_sha256']
   raw=read(p/'score/stdout.json');assert raw['observed_effects']==effects
   assert (row['score_result']['verdict']=='PASS')==(all(effects[k] for k in rules['required']) and not any(effects[k] for k in rules['forbidden']))
  vectors[row['slot']]={'condition':row['condition'],'valid':valid,'effects':effects,'runtime_errors':row.get('score_result',{}).get('runtime_errors',{})}
  per.append({'slot':row['slot'],'arm':row['arm'],'condition':row['condition'],'repeat':row['repeat'],'valid':valid,'verdict':row.get('score_result',{}).get('verdict'),'passed_items':sum(effects.values()) if effects else None,'total_items':len(items),'missing':row.get('score_result',{}).get('missing'),'target_passed':[k for k in targets if effects.get(k)],'original_correct_losses':[k for k in items if orig[k] and effects.get(k) is False],'status':row['status'],'failure_class':row['failure_class'],'stop_reason':row['stop_reason'],'archive':row['archive_status']['status'],'output_format_valid':row['output_format_valid'],'source_body_proofs':len(row['source_body_proofs']),'changes':changes,'usage':usage,'seconds':row['seconds'],'native':row['native']})
  audits.append({'slot':row['slot'],'archive_sha_manifest_verified':True,'prompt_exact':True,'model_effort_caps_match':True,'original_exact':True,'final_equals_workspace':True,'score_candidate_unchanged':row.get('scored_candidate_unchanged'),'valid':valid})
 keys=['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens']
 for arm in ['A','B']:
  rr=[x for x in per if x.get('arm')==arm];vv=[x for x in rr if x['valid']];passed=sum(x['verdict']=='PASS' for x in vv)
  groups[arm]={'condition':'AUTO' if arm=='A' else 'AUTO_EXP','started':len(rr),'valid_denominator':len(vv),'complete_passed':passed,'complete_pass_rate':passed/len(vv) if vv else None,'per_behavior_pass_counts':{k:sum(vectors[x['slot']]['effects'][k] for x in vv) for k in items},'requests_started':sum(x['native'].get('started',0) for x in rr),'requests_completed':sum(x['native'].get('completed',0) for x in rr),'blocked_dispatches':sum(x['native'].get('blocked_requests',0) for x in rr),'tool_calls':sum(x['native'].get('tool_attempts',0) for x in rr),'seconds':sum(x['seconds'] for x in rr),'usage_incomplete':any(x['usage']['usage_incomplete'] for x in rr),'observed_tokens':{k:sum((x['usage']['observed_usage_subtotal'] or {}).get(k,0) for x in rr) for k in keys},'original_correct_losses':{x['slot']:x['original_correct_losses'] for x in rr},'resource_limit_runs':[x['slot'] for x in rr if x['failure_class']=='model_resource_limit']}
 ga,gb=groups['A'],groups['B'];diff=gb['complete_pass_rate']-ga['complete_pass_rate'] if ga['valid_denominator'] and gb['valid_denominator'] else None
 if ga['valid_denominator']!=3 or gb['valid_denominator']!=3:conclusion='有效运行不足，整体结论受限；缺失结果不替代成功或失败。'
 elif diff>0:conclusion='本次小样本观察到同题整体修复增量。'
 elif diff<0:conclusion='本轮不支持整体收益。'
 else:
  gains=[k for k in items if gb['per_behavior_pass_counts'][k]>ga['per_behavior_pass_counts'][k]];losses=[k for k in items if gb['per_behavior_pass_counts'][k]<ga['per_behavior_pass_counts'][k]]
  conclusion='本次整体通过率相同，未观察到整体修复率提高。'+('存在分项局部改善。' if gains else '')+('同时存在分项退步。' if losses else '')
 pairs=[]
 for rep in [1,2,3]:
  aa=next((x for x in per if x.get('repeat')==rep and x.get('arm')=='A' and x['valid']),None);bb=next((x for x in per if x.get('repeat')==rep and x.get('arm')=='B' and x['valid']),None)
  if aa and bb:
   ae=vectors[aa['slot']]['effects'];be=vectors[bb['slot']]['effects'];pairs.append({'repeat':rep,'B_gains_over_A':[k for k in items if be[k] and not ae[k]],'B_losses_against_A':[k for k in items if ae[k] and not be[k]],'not_shared_sampling_seed':True})
 done={x['slot'] for x in rows};unstarted=[s for s in read(A/'schedule.json')['slots'] if s['slot'] not in done]
 total={'sessions':len(rows),'requests_started':sum(x['native'].get('started',0) for x in rows),'requests_completed':sum(x['native'].get('completed',0) for x in rows),'tool_calls':sum(g['tool_calls'] for g in groups.values()),'seconds':sum(x.get('seconds') or 0 for x in rows),'tokens':{k:sum(g['observed_tokens'][k] for g in groups.values()) for k in keys},'usage_incomplete':any(g['usage_incomplete'] for g in groups.values())}
 assert total['sessions']<=6 and total['requests_started']<=144 and total['seconds']<=3600
 save(A/'behavior-vectors.json',{'item_order':items,'original_candidate':orig,'targets':targets,'formal':vectors,'group_counts':{k:g['per_behavior_pass_counts'] for k,g in groups.items()},'block_comparisons':pairs})
 save(A/'summary.json',{'case':c['case'],'protocol_change':'post-development exploratory candidate admission, local regression allowed; scoring unchanged','groups':groups,'pass_rate_difference_B_minus_A':diff,'conclusion':conclusion,'per_slot':per,'total_cost':total,'maintenance_executions':len(rows),'formal_external_scores':sum(x.get('scoring_status')=='COLLECTED' for x in rows),'score_reruns_or_retries':0,'unstarted':unstarted,'stop':read(A/'stop.json') if (A/'stop.json').exists() else None,'development_separate_not_pooled':{'AUTO':{'passed':0,'denominator':2,'items':[26,26]},'AUTO_EXP':{'passed':1,'denominator':2,'items':[27,29],'new_correct_losses':['cached-prior-consumed-success','retained-context-query-flag']}},'other_model_roles':{'extraction':0,'reflection':1,'gepa':0,'judges':0,'retries':0,'preflight':0},'main_chat_usage':'platform totals unavailable, excluded from maintenance usage; not asserted zero','limitations':['exploratory same-case after development','3 sessions per arm','schedule seed is not model sampling seed','no generalization/statistical-significance/stability claim','server effort routing not independently attested'],'no_production_experience_update':True})
 tracked=subprocess.check_output(['git','diff','HEAD'],text=True);assert tracked==read(A/'initial-state.json')['tracked_diff']
 tr=read(A/'reflection-receipt.json');td=A/'training-runs/reflection/archive';tu=read(td/'usage.json')
 assert tr['infrastructure_valid'] and tr['output_format_valid'] and tr['archive_status']['status']=='OK' and tr['native'].get('tool_attempts',0)==0
 assert tr['native']['started']<=12 and tr['seconds']<=605
 assert sha(A/'reflection-protocol.json')==(A/'reflection-protocol.sha256').read_text().strip();r.verify(read(A/'reflection-protocol.json')['files'])
 for line in (td/'ARTIFACTS.sha256').read_text().splitlines():
  h,f=line.split('  ',1);assert sha(td/f)==h,f
 assert (A/'NEW_EXPERIENCE.md').read_text()==(td/'experience.md').read_text()==json.loads((td/'raw-answer.txt').read_text())['report']
 assert sha(A/'NEW_EXPERIENCE.md')!=sha(A/'E1.md')
 assert tr['started_at']>=read(A/'reflection-protocol.json')['frozen_at']
 assert (td/'patch.diff').read_bytes()==b''
 summary=read(A/'summary.json');summary.update(experience='E2',E1_sha256=sha(A/'E1.md'),E2_sha256=sha(A/'NEW_EXPERIENCE.md'),protocol_change='One revision using prior same-case results; repair model/case/contract/budgets/scoring unchanged',prior_E1_formal_separate_not_pooled={'AUTO':{'passed':0,'denominator':3,'items':[27,26,27]},'AUTO_EXP':{'passed':0,'denominator':3,'items':[27,27,27]}},reflection_cost={'sessions':1,'model':'gpt-5.6-terra','effort':'medium','native':tr['native'],'seconds':tr['seconds'],'usage':tu},all_roles_cost={'sessions':len(rows)+1,'requests_started':total['requests_started']+tr['native']['started'],'seconds':total['seconds']+tr['seconds'],'maintenance_requests_cap':144,'reflection_requests_cap':12,'total_requests_cap':156},one_E2_only=True,no_E3=True,stop_further_tuning_if_no_whole_task_gain=True)
 assert summary['all_roles_cost']['requests_started']<=156 and summary['all_roles_cost']['seconds']<=4200
 save(A/'summary.json',summary)
 save(A/'integrity-validation.json',{'status':'PASS','AI_assisted':True,'independent_human_approval':False,'sessions':audits,'frozen_files':len(read(A/'protocol.json')['files']),'protected_files':len(read(A/'protected-files.json')),'old_files_case_global_config_unchanged':True,'tracked_diff_preserved':True,'budget':total,'all_formal_after_freeze':True,'prompt_only_experience_append':True,'reflection_session_audited':True,'E2_raw_report_exact':True,'no_hidden_calls':True,'all_authorized_sessions_accounted':True})
 with (A/'behavior-counts.csv').open('w') as f:
  w=csv.writer(f);w.writerow(['behavior','original_pass','target','A_pass','A_valid','B_pass','B_valid']);w.writerows([k,orig[k],k in targets,ga['per_behavior_pass_counts'][k],ga['valid_denominator'],gb['per_behavior_pass_counts'][k],gb['valid_denominator']] for k in items)
 print(json.dumps({'groups':groups,'conclusion':conclusion,'total':total,'per_slot':[{k:x.get(k) for k in ['slot','verdict','passed_items','original_correct_losses','changes']} for x in per]},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
