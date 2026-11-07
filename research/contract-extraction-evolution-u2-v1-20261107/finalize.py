"""Offline failure audit only; no model, scorer, test, or retry."""
import csv,json,hashlib,subprocess,time
from pathlib import Path
from run import OUT,ROOT,read,save,sha,hashes,frozen

def citation(call,quote):
 p=OUT/'runs'/call/'contract.md';lines=p.read_text().splitlines();hits=[i for i,x in enumerate(lines,1) if quote in x];assert hits,(call,quote)
 return str(p.relative_to(ROOT))+':'+str(hits[0])
def main():
 frozen();req=read(OUT/'requests.json');meter=read(OUT/'request-meter/ledger.json');assert len(req)==2 and meter['started']==4
 rules=list(csv.DictReader((OUT/'evaluation-v1.csv').open(encoding='utf-8-sig')));rows=[]
 quotes={
 'k0-1':{'O1':'效果：继续检查准备状态，不在此时交付文件。','O3':'只有收到 ready 状态后才交付文件。','other':'未读取到候选源码或文档，因此没有可标记的当前实现事实或准确文件行号','unknown':'检查间隔、重试上限、错误处理、弹窗关闭后的处理，以及 pending 和 ready 的具体协议格式均缺少可查证来源'},
 'k0-2':{'O1':'效果：对话框继续检查该文件的准备状态。','O3':'目标文件尚未报告 ready。效果：不得提前交付文件。','other':'候选源码和文档未被读取，因此没有可引用的候选路径及行号。','unknown':'无法确认轮询间隔、超时或重试上限、错误状态处理、取消或关闭对话框后的行为、重复下载的处理，以及 pending 和 ready 状态的具体数据格式。'}}
 for rec in req:
  call=rec['call_id'];events=(OUT/'runs'/call/'events.jsonl').read_text();assert 'Code Mode is unavailable because code-mode host is disabled' in events
  assert rec['native']['started']==rec['native']['completed']==2 and rec['tools']==0
  output=(OUT/'runs'/call/'contract.md').read_text();assert json.loads((OUT/'runs'/call/'raw-answer.txt').read_text())['report']==output
  save(OUT/'runs'/call/'validity.json',{'transport_format_status':rec['status'],'experiment_validity':'FAILED_INFRASTRUCTURE','reason':'source-reading tool backend disabled by frozen execution configuration; report explicitly admits no candidate read','source_read_succeeded':False,'skills_comparison_eligible':False,'failure_is_not_semantic_model_omission':True,'receipt_preserved':True})
  for rule in rules:
   oid=rule['item_id'];direct=oid in ['O1','O3'];quote=quotes[call][oid if direct else 'other'];u=quotes[call]['unknown']
   rows.append({'call_id':call,'phase':'K0','item_id':oid,'execution_validity':'FAILED_INFRASTRUCTURE','coverage':'完整覆盖' if direct else '未覆盖','semantic_direction':'正确' if direct else '证据不足','source_accuracy':'正确（任务背景）' if direct else '证据不足（未读取源码，未冒称已读）','unsupported_additions':'无（本条未发现）','unknown_handling':'合理保留未知；未形成源码分析' if not direct else '状态编码未臆造','model_quote':quote,'model_reference':citation(call,quote),'unknown_quote':u,'unknown_reference':citation(call,u),'standard_and_source':rule['source'],'rule':rule['judgment_rule'],'assessment_reason':'只按任务背景可确认O1/O3，方向正确。' if direct else '候选未能读取；缺失归入基础设施失败，不据此判定技能固有遗漏。','comparison_eligible':False,'reviewer':'AI执行代理评价；非独立人工复核'})
 def csvsave(name,data):
  with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
 csvsave('baseline-review.csv',rows);csvsave('item-comparison.csv',rows)
 timer=[]
 for call in ['k0-1','k0-2']:
  for tid,target in [('T1','关闭时待执行retry是否存在及所属对象'),('T2','取消包装与实际调用位置'),('T3','是否可能继续检查及条件'),('T4','接口/宿主证据缺失与未知')]:
   q=quotes[call]['other'];timer.append({'call_id':call,'item_id':'O4','subitem':tid,'target':target,'coverage':'未覆盖' if tid!='T4' else '部分覆盖','quote':q,'citation':citation(call,q),'reason':'没有源码读取，只有整体不能确认声明，不能据此评价timer边界提取能力','validity':'FAILED_INFRASTRUCTURE','normative_answer':'未规定必须取消','reviewer':'AI代理评价，非人工复核'})
 csvsave('timer-boundary-review.csv',timer)
 feedback={'status':'NOT_SENT_TO_REFLECTION','basis':'baseline infrastructure failure, not evidence of extraction-skill deficiency','correct_task_only_recovery':['O1','O3'],'unavailable_source_dependent_analysis':['O2','O4','O5','O6','O7'],'semantic_reversals_observed':[],'unsupported_product_requirements_observed':[],'genuine_skill_gaps_established':[],'reason_not_reflecting':'Both frozen sessions lacked source tool backend; skill reflection would be trained on an infrastructure failure. Stop without consuming reflection or K1 slots; never rerun baseline.'}
 save(OUT/'difference-feedback.json',feedback)
 for call in ['reflect-1','k1-1','k1-2']:
  save(OUT/'runs'/call/'slot.json',{'call_id':call,'status':'NOT_RUN','actual_prompt':None,'actual_output':None,'actual_requests':0,'reason':'Stopped after two invalid baselines due source tool backend configuration; not a model failure or rejected K1 candidate'})
 save(OUT/'skill-changes.json',{'status':'NOT_GENERATED','changes':[],'K1':None,'diff':None,'reason':'No valid source-grounded baseline feedback; reflection not called; no hand-authored K1'})
 (OUT/'skill.diff').write_text('# NOT_GENERATED: reflection and K1 were not executed after infrastructure failure. No skill diff exists.\n')
 save(OUT/'K1-boundary-review.json',{'status':'NOT_APPLICABLE','candidate_exists':False,'allow_execution':False,'reason':'Stopped before reflection; no candidate to inspect or accept'})
 (OUT/'reflection-status.md').write_text('# 反思槽位未执行\n\n两次基线均未能读取候选源码，无法从中归因提取技能缺口。保留失败槽位，未发送反思prompt，未生成K1，不自动补跑。\n')
 usage={k:sum(x['usage'].get(k,0) for x in req) for k in ['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens']}
 postusage={k:sum(e['event'].get('token_usage',{}).get(k,0) for e in meter['events'] if e['event'].get('hook_event_name')=='PostModelRequest') for k in usage}
 assert usage==postusage
 costs={'top_level_sessions':len(req),'planned_session_cap':5,'native_model_requests':meter['started'],'native_model_responses':meter['completed'],'global_request_cap':49,'by_session':[{'call_id':x['call_id'],'native_requests':x['native']['started'],'seconds':x['seconds'],'usage':x['usage'],'completed_tool_items':x['tools']} for x in req],'usage':usage,'input_tokens_include_cached':True,'reasoning_tokens_subset_of_output':True,'request_hook_tool_attempts':meter['tool_attempts'],'completed_tool_items':sum(x['tools'] for x in req),'tool_backend_errors':2,'tool_backend_error_note':'two session startup errors; model-declared attempted reads failed before tool hook; exact hidden dispatch attempt count not available, do not equate zero completed tools with no attempt','total_session_seconds':sum(x['seconds'] for x in req),'usd':None,'usd_reason':'no pricing source verified; no dollar estimate fabricated','unused_slots':['reflect-1','k1-1','k1-2'],'automatic_retries':0}
 save(OUT/'costs.json',costs)
 summary={'status':'STOPPED_INFRASTRUCTURE_FAILURE','experiment_completed':False,'model':'gpt-6-sol','effort':'low','case':'U2','exposed_development_case':True,'ai_assisted_evaluation':True,'independent_human_review':False,'evaluation_version':'evaluation-v1.csv','evaluation_timer_boundary_added':True,'new_gold_standard_created':False,'baseline_valid_runs':0,'baseline_format_completed_but_invalid':2,'baseline_task_only_obligations':['O1','O3'],'genuine_model_omissions_established':False,'reflection_called':False,'K1_generated':False,'K1_executed':False,'net_improvement':None,'regressions':None,'production_acceptance':False,'costs':costs,'failure_cause':'Frozen runner DISABLE included code_mode_host; exact CLI requires that host to execute candidate read tools. Offline namespace check omitted tool-backend usability. Agent configuration error, not model quality.','stop_reason':'No valid source-grounded baseline; fixed-budget no-rerun policy. Do not convert infrastructure failure into a skill update.','no_business_changes':True,'no_maintenance_scoring':True,'no_official_gepa':True,'no_react_controller':True,'commits_created':0}
 save(OUT/'summary.json',summary)
 # All original work and prior artifacts are protected.
 ini=read(OUT/'initial-state.json');g=lambda *a:subprocess.check_output(['git',*a],cwd=ROOT)
 assert g('rev-parse','HEAD').decode().strip()==ini['head'];assert sha(g('diff','--cached','--binary'))==ini['staged_diff'];assert sha(g('diff','--binary'))==ini['unstaged_diff']
 for n,h in ini['protected_files'].items():assert sha((ROOT/n).read_bytes())==h,n
 for n,h in read(OUT/'scope-and-sources.json')['source_files'].items():assert sha(Path(n).read_bytes())==h,n
 for x in req:assert hashes(OUT/'runs'/x['call_id']/'workspace')==read(OUT/'scope-and-sources.json')['candidate_files']
 assert not list((OUT/'.runtime').rglob('auth.json'))
 save(OUT/'final-validation.json',{'status':'PASS_ARTIFACT_AND_PROTECTION_CHECKS_ONLY','experiment_validity':'FAILED_INFRASTRUCTURE','preflight_pass_did_not_test_model_tool_backend':True,'frozen_protocol_unchanged':True,'prior_files_unchanged':True,'head_and_git_diffs_unchanged':True,'read_only_workspaces_unchanged':True,'report_quotes_resolve':True,'raw_outputs_match_contract_reports':True,'native_counts_and_usage_reconcile':True,'failed_and_skipped_slots_preserved':True,'no_fake_K1_or_success_claim':True,'temporary_auth_removed':True,'model_requests':4,'no_additional_model_calls':True})
 print(json.dumps({'status':summary['status'],'usage':usage,'seconds':costs['total_session_seconds'],'rows':len(rows)},ensure_ascii=False))
if __name__=='__main__':main()
