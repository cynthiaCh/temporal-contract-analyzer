from pathlib import Path
import json,hashlib,subprocess,datetime
O=Path(__file__).resolve().parent;R=O.parent.parent;B=R.parent/'temporal-contract-bench-git'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
rows=read(O/'requests.json');assert all(r['status']!='launched' for r in rows),'execution still running'
meter=read(O/'request-meter/ledger.json');native_usage={}
for r in rows:
 posts=[(e['event'].get('token_usage') or {}) for e in meter.get('events',[]) if e['call_id']==r['call_id'] and e['event'].get('hook_event_name')=='PostModelRequest']
 native_usage[r['call_id']]={k:sum(p.get(k,0) or 0 for p in posts) for k in ['input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens']}
save('native-usage.json',{'by_slot':native_usage,'source':'PostModelRequest token_usage sum; retains accounted usage even if final turn is absent','completed_request_usage_only':True,'unknown_usage_requests':[{'slot':e['call_id'],'status':e['event'].get('status'),'error':e['event'].get('error')} for e in meter.get('events',[]) if e['event'].get('hook_event_name')=='PostModelRequest' and e['event'].get('token_usage') is None],'reported_final_turn_usage':{r['call_id']:r['usage'] for r in rows}})
admission=read(O/'admission.json');base=read(O/'calibration/unchanged/stdout.json')['observed_effects'];req=[k for k in base if k not in ['background-continuation-policy-violated','background-close-cancels-work']];forb=['background-continuation-policy-violated']
def good(raw):return {**{k:raw[k] for k in req},**{k:not raw[k] for k in forb}}
bgood=good(base);out=[];raws={}
for r in rows:
 folder=O/'runs'/r['call_id'];p=folder/'score.stdout.json'
 try:raws[r['call_id']]=read(p)
 except (ValueError,FileNotFoundError):raws[r['call_id']]=None
Ns={r['repeat']:raws[r['call_id']] for r in rows if r['condition']=='N' and r['status']=='completed' and raws[r['call_id']]}
start_hash=read(O/'frozen-config.json')['public_materials'];source_hash={k.removeprefix('candidate/'):v for k,v in start_hash.items() if k.startswith('candidate/')} if hasattr(str,'removeprefix') else {k[len('candidate/'):]:v for k,v in start_hash.items() if k.startswith('candidate/')}
for r in rows:
 folder=O/'runs'/r['call_id'];raw=raws[r['call_id']];valid=r['status']=='completed' and raw is not None and r.get('score_exit_code') in [0,1];g=good(raw['observed_effects']) if raw else None;n=Ns.get(r['repeat']);ng=good(n['observed_effects']) if n else None
 hashes={str(p.relative_to(folder/'workspace')):sha(p) for p in (folder/'workspace').rglob('*') if p.is_file()};changed=[k for k in source_hash.keys()|hashes.keys() if source_hash.get(k)!=hashes.get(k)]
 out.append({'slot':r['call_id'],'condition':r['condition'],'repeat':r['repeat'],'execution':r['status'],'valid_behavioral_result':valid,'verdict':raw['verdict'] if valid else None,'observational_score_if_execution_invalid':None if valid else raw,'target_existing_effect':raw['observed_effects']['download-retries-until-ready-once'] if valid else None,'requirements':g if valid else None,'gained_vs_start':[k for k,v in g.items() if v and not bgood[k]] if valid else None,'lost_vs_start':[k for k,v in bgood.items() if v and not g[k]] if valid else None,'gained_vs_paired_N':[k for k,v in g.items() if v and not ng[k]] if valid and ng else None,'lost_vs_paired_N':[k for k,v in ng.items() if v and not g[k]] if valid and ng else None,'actual_patch_delivered':bool(changed),'changed_files':sorted(changed),'usage':native_usage[r['call_id']],'seconds':r['seconds'],'requests':r['native'].get('started',0),'tools':r['tools'],'receipt':str(folder/'receipt.json'),'raw_score':str(folder/'score.stdout.json')})
save('outcomes.json',out)
agg={}
for group in ['N','H','M']:
 rr=[r for r in out if r['condition']==group];valid=[r for r in rr if r['valid_behavioral_result']];agg[group]={'sessions':len(rr),'valid_behavioral_sessions':len(valid),'overall_pass':sum(r['verdict']=='PASS' for r in valid),'target_pass':sum(r['target_existing_effect'] for r in valid),'patches':sum(r['actual_patch_delivered'] for r in rr),'regression_sessions_vs_start':sum(bool(r['lost_vs_start']) for r in valid),'regression_sessions_vs_N':sum(bool(r['lost_vs_paired_N']) for r in valid),'seconds':sum(r['seconds'] for r in rr),'requests':sum(r['requests'] for r in rr),'tools':sum(r['tools'] for r in rr),'tokens':{k:sum(r['usage'].get(k,0) for r in rr) for k in ['input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens']}}
cost={'by_condition':agg,'formal_sessions':len(rows),'native_requests':sum(r['requests'] for r in out),'seconds':sum(r['seconds'] for r in out),'tools':sum(r['tools'] for r in out),'request_cap':49,'usage_source':'sum native PostModelRequest token_usage; failed requests without token_usage unknown, totals are accounted lower bounds','oracle_calibration_runs':3,'formal_scoring_runs':sum(raw is not None for raw in raws.values()),'currency_estimate':None,'reason':'no verified frozen monetary tariff','extra_model_pre_runs':0,'reflections':0,'retries':0,'extraction_runs':0,'GEPA':0};save('costs.json',cost)
# Preserve exact observations without applying policies outside the historical rubric.
patches=[]
for r in rows:
 f=O/'runs'/r['call_id'];p=f/'raw-answer.txt';report=p.read_text() if p.exists() else ''
 patches.append({'slot':r['call_id'],'condition':r['condition'],'repeat':r['repeat'],'delivery':report,'patch':str(f/'patch.diff'),'usePreparation':(f/'workspace/src/usePreparation.js').read_text(),'self_check_evidence':str(f/'events.jsonl'),'scope_limit':'Self-check claims retained as delivery evidence, not new trusted oracle or universal policy coverage.'})
save('patch-review.json',patches)
policy_notes=[]
for r in rows:
 p=O/'runs'/r['call_id']/'workspace/src/BackgroundExportPanel.jsx';text=p.read_text()
 if 'endsWith(":dialog")' in text:
  policy_notes.append({'slot':r['call_id'],'condition':r['condition'],'file':str(p),'line_quotes':[{'line':i,'text':line} for i,line in enumerate(text.splitlines(),1) if any(q in line for q in ['isDialogOwned',':dialog','this.active = false'])],'classification':'unsupported new token encoding / potential untested regression, not a scored outcome','reason':'Exact historical H mentions authorization suffix as an exception, but supplies no :dialog token encoding; benchmark granted authorization is a separate prompt instruction. No authorization update was present this round.','coverage':'existing ungranted worker uses workspace-export token only; no dynamic result claimed for :dialog token.'})
save('unscored-policy-review.json',{'findings':policy_notes,'no_new_scoring_assertions':True})

initial=read(O/'initial-state.json');validation={}
for name,p in [('analyzer',R),('bench',B)]:
 for key,args in [('head',['rev-parse','HEAD']),('diff',['diff']),('staged_diff',['diff','--cached'])]:
  actual=subprocess.check_output(['git','-C',str(p),*args],text=True);validation[name+'_'+key+'_unchanged']=actual.strip()==initial[name][key].strip()
validation['protected_files_unchanged']=all(Path(p).exists() and sha(Path(p))==h for p,h in read(O/'protected-files.json').items())
validation['protocol_hash_unchanged']=sha(O/'protocol.json')==(O/'protocol.sha256').read_text().strip();validation['frozen_files_unchanged']=all(sha(Path(p))==h for p,h in read(O/'protocol.json')['files'].items());validation['global_config_unchanged']=sha(Path.home()/'.codex/config.toml')==initial['global_config_sha256']
validation['independent_same_starts']=all(read(O/'runs'/r['call_id']/'frozen-start.json')['candidate_files']==source_hash for r in rows)
validation['actual_prompts_match']=all(sha(O/'runs'/r['call_id']/'actual-prompt.md')==sha(Path(r['prompt'])) for r in rows)
validation['actual_order_matches_prefix']=[r['call_id'] for r in rows]==[r['call_id'] for r in read(O/'schedule.json')['order'][:len(rows)]]
validation['actual_native_model_matches']=all(e['event'].get('model')=='gpt-5.6-terra' for e in meter.get('events',[]) if e['event'].get('hook_event_name') in ['PreModelRequest','PostModelRequest'])
validation['medium_effort_command_matches']=all('model_reasoning_effort=\"medium\"' in r['command'] for r in rows)
validation['per_session_configs_unchanged']=all(read(O/'runs'/r['call_id']/'configuration-before.json')['research_config_sha256']==read(O/'runs'/r['call_id']/'configuration-after.json')['profile_config_sha256']==sha(O/'research-config.toml') for r in rows)
validation['no_auth_profile_left']=not list((O/'.runtime').glob('*/auth.json'))
critical=[k for k in validation if k not in ['analyzer_head_unchanged','analyzer_diff_unchanged']];assert all(validation[k] for k in critical),validation
validation['status']='PASS_FROZEN_INPUTS_WITH_OBSERVED_GIT_DRIFT' if not all(validation[k] for k in ['analyzer_head_unchanged','analyzer_diff_unchanged']) else 'PASS';validation['git_drift_details']='git-drift.json';save('validation.json',validation)
save('actual-schedule.json',{'seed':2026110812,'order':[{k:r[k] for k in ['call_id','condition','repeat','started_at','completed_at','status']} for r in rows]})
execution_errors=[];tool_nonzero=[]
for r in rows:
 events=[json.loads(line) for line in (O/'runs'/r['call_id']/'events.jsonl').read_text().splitlines()]
 for i,event in enumerate(events,1):
  if event.get('type') in ['error','turn.failed']:execution_errors.append({'slot':r['call_id'],'line':i,'event':event})
  item=event.get('item',{})
  if event.get('type')=='item.completed' and item.get('type')=='command_execution' and item.get('exit_code') not in [None,0]:tool_nonzero.append({'slot':r['call_id'],'line':i,'command':item.get('command'),'exit_code':item.get('exit_code'),'output':item.get('aggregated_output')})
save('execution-anomalies.json',{'terminal_errors':execution_errors,'nonzero_tool_commands':tool_nonzero,'note':'Nonzero commands are observations including probe/self-check failures, not automatically terminal infrastructure faults or model behavioral failures. Service termination and native request cap are separately recorded.'})
planned=read(O/'schedule.json')['order'];executed={r['call_id']:r for r in rows};unused=[p['call_id'] for p in planned if p['call_id'] not in executed];save('slot-status.json',{'slots':[{'slot':p['call_id'],'condition':p['condition'],'repeat':p['repeat'],'status':executed[p['call_id']]['status'] if p['call_id'] in executed else 'NOT_EXECUTED_PREDECLARED_STOP'} for p in planned],'unexecuted':unused,'budget_started':meter.get('started'),'budget_blocked':meter.get('blocked_requests'),'first_gate':read(O/'first-formal-gate.json')['status']})
failures=[{'slot':r['call_id'],'status':r['status'],'exit_code':r.get('exit_code'),'native':r.get('native'),'format_errors':r.get('format_errors')} for r in rows if r['status']!='completed'];anomalies=[r['call_id'] for r in rows if not raws[r['call_id']] or r.get('score_exit_code') not in [0,1]]
if len(rows)<6:conclusion=('Stopped at the frozen 49-request global budget; incomplete comparison.' if meter.get('started',0)>=49 else 'Stopped by the first-formal execution validity gate; incomplete comparison.')
elif failures or anomalies:conclusion='Infrastructure/execution anomalies prevent a complete six-slot behavioral comparison; no replacements.'
elif agg['N']['overall_pass']==agg['H']['overall_pass']==2:conclusion='N/H both 2/2: no incremental H benefit observable this round; ceiling. M outcome reported separately.'
elif agg['H']['overall_pass']>agg['N']['overall_pass']:
 conclusion='H better than N in observed repeats. '+('M matches H observed success count; preliminary positive signal only.' if agg['M']['overall_pass']==agg['H']['overall_pass'] else 'M differs from H; compare exact Contract/patch requirements without inferring clause causation.')
else:conclusion='Historical H advantage not reproduced on overall pass count; inspect per-effect outcomes, variation and execution differences.'
paired=[]
for repeat in [1,2]:
 nn=next((r for r in out if r['condition']=='N' and r['repeat']==repeat and r['valid_behavioral_result']),None);hh=next((r for r in out if r['condition']=='H' and r['repeat']==repeat and r['valid_behavioral_result']),None)
 if nn and hh:paired.append({'repeat':repeat,'N':nn['verdict'],'H':hh['verdict'],'H_gained':hh['gained_vs_paired_N'],'H_lost':hh['lost_vs_paired_N']})
if paired and all(p['N']==p['H']=='PASS' for p in paired):human_answer=f'在{len(paired)}个有效N/H配对中均为PASS/PASS，未再次观察到历史整体通过增益；不外推未覆盖政策。'
else:human_answer='有效N/H配对结果：'+str(paired)+'；按实际向量报告，不由单次同现推断因果。'
mvalid=[r for r in out if r['condition']=='M' and r['valid_behavioral_result']]
model_answer=f'M有效结果{len(mvalid)}次，整体通过{sum(r["verdict"]=="PASS" for r in mvalid)}次；'+('不足两重复，无法完成预定的重复比较。' if len(mvalid)<2 else '完整保留两次结果与波动。')+'目标effect与各生命周期项分开报告，不能声称等价或必然保留H作用。'
summary={'status':('STOPPED_AT_FROZEN_GLOBAL_BUDGET' if meter.get('started',0)>=49 and (len(rows)<6 or failures) else 'COMPLETED_DEVELOPMENT_DIAGNOSTIC' if len(rows)==6 else 'STOPPED_BY_PREDECLARED_GATE'),'AI_assisted':True,'independent_human_review':False,'case':'U2 historical exposed development case','historical_pair':'recovered-06-node18 j0001 N UNDERREACH / j0002 H PASS','historical_model_effort_matched':'gpt-5.6-terra/medium','strict_historical_reproduction':False,'M_selected':'U2 v2 k1-1 exact section 1','formal_sessions':len(rows),'planned_unexecuted_slots':unused,'by_condition':agg,'execution_anomalies':failures,'terminal_error_events':execution_errors,'nonzero_tool_commands':len(tool_nonzero),'unsupported_unscored_policy_findings':policy_notes,'scoring_anomalies':anomalies,'conclusion':conclusion,'historical_H_effect_observed_again':human_answer,'M_vs_H':model_answer,'valid_N_H_pairs':paired,'uncovered':['queued retry before close','same-token reopen','multiple concurrent responses','authorization migration','full file delivery'],'causal_claim':False,'independent_generalization_claim':False,'new_Contract_or_skill':False,'GEPA':False,'executor_created_commits':0,'observed_git_drift':read(O/'git-drift.json')};save('summary.json',summary)
report='''# U2 N/H/M 修复开发诊断（2026-11-08）

AI辅助分析，已暴露开发案例，非独立人工复核或泛化测试。

## Task 1：历史作用与本轮可比程度

准确配对来自 mapping-v1 已核验的 recovered-06-node18：j0001 未给Contract，UNDERREACH；j0002 给Contract，PASS。逐字核对实际prompt、run、最终candidate和原始score，并用bench的tree_sha256重算起点/最终树；两组起点e381e156…b4b223e0、原任务、gpt-5.6-terra/medium、600秒、CLI0.159.2、ungranted、空overlay相同。非空prompt只差准确Contract后缀，没有发现其他实验条件同时改变。耗时、token与补丁实现不同，是输出差异。历史单次顺序执行，不能判定稳定因果。

历史N只接受字符串pending/ready，而worker提供false/true；H补丁兼容布尔值及其他形态。这使历史成功差异还包含状态协议处理，不能把改善全部归于等待或生命周期条款。对应历史输入、原始评分和离线推导diff见 [historical-pair-verification.json](historical-pair-verification.json) 与 history/；diff是本轮从已核验历史candidate推导，不冒称历史已有patch.diff。

H逐字采用成功组实际收到的文本：[contracts/H.txt](contracts/H.txt)。pending持续检查、ready后交付可从原任务恢复；精确loading等待、前台timer与全部在途响应失效、reopen代际、后台workspace所有权及授权例外，包含不同程度的人工额外明确规格。逐条来源、争议及评价范围沿用映射而不扩写，见 [H-source-applicability.json](H-source-applicability.json)。保留这些历史规格不意味着提取模型应凭不足输入猜中。

M固定为U2 v2首份有效K1 k1-1，实际开始时间、运行/原始输出/技能摘要及截取规则见 [M-selection.json](M-selection.json)。只取第1栏目正文，未改字、未补其他栏；内容仅为pending继续、ready交付及编码未知说明。其完整报告的等待/旧回调关系仍在其他栏目，本次没有交付给修复模型；因此包装和可用规格差异也是解释限制。未生成新Contract，未追加K0/K1提取技能或标准。

本轮三组外围维护指令相同，只有额外Contract文本改变；保留精确历史任务和自检Node路径，共同追加workspace、依赖路径与JSON交付说明。模型及medium推理保持历史配置，Node18.17.0与历史二进制摘要相同。旧CLI缺失，改用当前0.164.0-alpha.11.1；显式priority而历史tier未知；请求/输出硬上限历史未归档，本轮沿用已核验的研究上限。bwrap隔离和源码工具显式配置、只读React依赖等差异见 [configuration-differences.json](configuration-differences.json)，不能称严格历史复刻，也未静默换模型或后端。服务端tier路由未独立认证。

## Task 2：准入、实际执行与异常

当前case manifest、base及六个oracle文件逐项匹配历史plan input_sha256。没有独立逐次oracle字节认证记录，本轮不补造。无模型校准3次：起点UNDERREACH，历史N/H完整effect向量精确复现UNDERREACH/PASS，证明当前原评分与归档结果相容；见 [admission.json](admission.json)。评分沿用历史ungranted明确规格，不改断言、不造综合分，不将未覆盖政策加入评分。

[PLAN.md](PLAN.md)、[protocol.json](protocol.json)和[prompts/](prompts/)在调用前冻结。gpt-5.6-terra/medium、priority，原生Codex自主exec，无ReAct；600秒/槽、12底层请求/槽、全局49请求、最终report6000字符，最多六槽。原生hook计量且禁自动重试。各独立工作区启动前保存准确起点摘要，模型仅挂载本次候选、运行时、独立profile和输出，不挂载评分器、参考补丁、标准、历史或其他运行。源码后端code_mode_host/shell_tool离线可用。

'''
actual=' → '.join(r['call_id']+' '+r['condition']+'-r'+str(r['repeat']) for r in rows);report+='种子2026110812，实际顺序：**'+actual+'**。首个正式槽位真实源码读取门：'+read(O/'first-formal-gate.json')['status']+'，证据为成功工具输出匹配原始源码正文，非文件列表或模型自述；不按质量/得分决定继续。每槽退出后研究侧评分，后续执行模型不可见。实际轨迹、输入、交付、patch.diff、score.stdout.json和配置始末位于runs/各槽。\n\n'
report+=f"实际发起正式会话 {len(rows)}/6；完整有效 {sum(r['valid_behavioral_result'] for r in out)}；执行异常 {len(failures)}，评分异常 {len(anomalies)}。异常详情见 [summary.json](summary.json) 与 [execution-anomalies.json](execution-anomalies.json)，不作为模型行为失败，不替换槽位。无模型预跑、反思、自动重试、补跑或扩容。\n\n"
report+='u05 N-r2因服务断流（error decoding response body）未完成，无重试；u06 M-r2在全局49次请求全部发起后被硬门阻止下一请求，未补跑。两份中间工作区虽有原始评分，均不计为正式行为失败。非零工具命令共7次：5次git diff遇到独立工作区无Git仓库、1次缺react-test-renderer、1次node --check遇到.jsx不支持；完整输出保留，后续有效会话的替代自检不冒充原评分。\n\n'
report+='## Task 3：结果、行为得失与成本\n\n|条件|有效结果|整体通过|目标effect通过|实际补丁|相对起点/配对N退步会话|输入token（含缓存）|输出token|秒|请求|工具|\n|---|---|---|---|---|---|---|---|---|---|---|\n'
for group,a in agg.items():
 t=a['tokens'];report+=f"|{group}|{a['valid_behavioral_sessions']}/{a['sessions']}|{a['overall_pass']}/{a['valid_behavioral_sessions']}|{a['target_pass']}/{a['valid_behavioral_sessions']}|{a['patches']}|{a['regression_sessions_vs_start']}/{a['regression_sessions_vs_N']}|{t['input_tokens']}（{t['cached_input_tokens']}）|{t['output_tokens']}|{a['seconds']:.2f}|{a['requests']}|{a['tools']}|\n"
report+='\n目标effect为原评分download-retries-until-ready-once，覆盖两次pending后继续检查及ready的completed一次；不是新综合分。等待状态及全部其他规格逐项列下，不用总分掩盖关键退步。缓存包含在输入中、推理包含在输出中，不能重复相加。工具数来自完成tool item，底层请求来自原生hook；token取逐请求token_usage，失败请求没有用量记录时保持未知，因此异常槽及全批token合计只表示已记账下界，见native-usage.json；耗时为会话累计墙钟时间。无核验价格表，未估货币成本。\n\n'
report+='|既有评分要求|起点|'+'|'.join(r['slot']+' '+r['condition'] for r in out)+'|\n|---|---|'+'|'.join('---' for r in out)+'|\n'
for effect,passed in bgood.items():report+='|'+('禁止项未发生：'+effect if effect in forb else effect)+'|'+('通过' if passed else '未过')+'|'+'|'.join(('通过' if r['requirements'][effect] else '未过') if r['requirements'] else '异常/不计行为' for r in out)+'|\n'
report+='\n禁止项列的通过表示该禁止行为未发生；原始observed_effects仍保留false，未重写评分。\n\n逐槽新增/丢失行为、配对N及改变文件见 [outcomes.json](outcomes.json)。实际补丁、提交交付及自检原文见 [patch-review.json](patch-review.json)；自检只作为交付证据，未替代原可信评分。\n\n'
for r in out:
 report+=f"- {r['slot']} {r['condition']}-r{r['repeat']}：{r['verdict'] or '无有效行为评分'}；改动 {', '.join(r['changed_files']) or '无'}；相对起点新增 {r['gained_vs_start']}，丢失 {r['lost_vs_start']}；相对配对N新增 {r['gained_vs_paired_N']}，丢失 {r['lost_vs_paired_N']}。\n"
if policy_notes:
 report+='\n**未被PASS消除的新增风险：**'+', '.join(n['slot']+' '+n['condition'] for n in policy_notes)+' 在 BackgroundExportPanel.jsx 新增 token.endsWith(":dialog") 所有权迁移规则。历史H没有给出这个编码；本轮没有授权迁移指令。该token下close会把active置false并取消后台工作。原ungranted测试只使用workspace-export，故整体PASS不能证明此分支符合要求；这是静态核对出的无输入依据新增约定/潜在未测退步，不伪装成原评分已检出的失败。源码行号及范围见 [unscored-policy-review.json](unscored-policy-review.json)。\n'
report+='\n重点范围：pending后继续、ready后completed交付、中间等待、请求中关闭、异token reopen旧响应及原后台路径由原评分有限覆盖。**retry已排队后关闭未独立驱动，同tokenreopen、多个旧响应、授权迁移、真实文件交付接口未覆盖**；不得用close测试或整体PASS代替这些结论。completed数组只是候选交付效果代理。\n\n'
report+='**本轮解释：**'+conclusion+'\n\n人工Contract历史作用是否再次出现：'+human_answer+'\n\n模型Contract是否获得相近结果：'+model_answer+'\n\n'
report+='''必须把整体、具体effect和波动一起看；没有对某一条Contract进行单独消融，不从条款与修复同时出现推断因果。若M落后H，差异可能涉及额外人工规格、仅第1栏目包装、状态协议处理或执行随机性；不能直接判提取技能失败。若H失败，先核对CLI、共同指令、限制及补丁差异；若N/H都通过则停止于天花板，不换题追赢家。每组两重复仅作描述性开发诊断，不作显著性、等价或独立泛化结论。

源码、技能、标准、评分器与历史结果保护核验见 [validation.json](validation.json)，冻结输入与受保护文件摘要均未变，原全局配置未变，临时认证已移除。本执行仅写本目录、未调用提交命令、无GEPA、无下一轮。但会话期间HEAD从70b27e3变为9d02bd7，来源未确认的提交把前轮目录和本轮部分归档纳入版本控制；不能声称Git HEAD/diff保持不变。新增提交路径均在这两个研究目录，没有业务路径变化；当前prepare.py差异仅为本轮准备脚本main保护。详见 [git-drift.json](git-drift.json)。未回退、重置或覆盖该提交。

建议Git commit subject：`research: diagnose U2 repair with frozen N H M contracts`

Body：

```text
Verify the exact archived U2 N/H inputs, patches and raw effects.
Reuse the historical H verbatim and mechanically select U2 v2 k1-1 M.
Calibrate the unchanged oracle, freeze comparable native repair sessions,
and archive all outcomes, usage and limits without skill or GEPA changes.
```
'''
(O/'REPORT.md').write_text(report)
(O/'COMMIT_MESSAGE.txt').write_text('research: diagnose U2 repair with frozen N H M contracts\n\nVerify the exact archived U2 N/H inputs, patches and raw effects.\nReuse the historical H verbatim and mechanically select U2 v2 k1-1 M.\nCalibrate the unchanged oracle, freeze comparable native repair sessions,\nand archive all outcomes, usage and limits without skill or GEPA changes.\n')
print(json.dumps({'conclusion':conclusion,'by_condition':agg},ensure_ascii=False,indent=2))
