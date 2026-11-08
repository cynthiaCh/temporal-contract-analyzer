"""Offline final checks and reporting; never calls a model or scorer."""
from pathlib import Path
import json,hashlib,subprocess
A=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,d):(A/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
s=read(A/'summary.json');rows=read(A/'actual-schedule.json');vs=read(A/'behavior-vectors.json');C=read(A/'cohort.json')
assert (A/'stop.json').exists() or read(A/'stage-state.json')['stage']=='M4_COMPLETE'
checks=[]
for row in rows:
 d=A/'runs'/row['slot']/'archive';ledger=read(d/'meter/ledger.json');frozen=read(d/'input/frozen-start.json');final=read(d/'final-manifest.json');cmd=read(d/'command.json')
 assert ledger['sessions'][row['slot']]==row['native']
 assert frozen['prompt_sha256']==sha(d/'input/actual-prompt.md')
 assert final['workspace_sha256_before']==final['workspace_sha256_after']
 if row['phase']=='extract':assert final['tree_sha256']==frozen['tree_sha256']
 expected='gpt-6-sol' if row['phase']=='extract' else 'gpt-5.6-terra';effort='medium' if row['phase']=='reflect' else 'low'
 hooks=[x['event'] for x in ledger['events'] if x['event'].get('hook_event_name') in ['PreModelRequest','PostModelRequest']]
 assert hooks and all(e['model']==expected for e in hooks)
 assert cmd[cmd.index('-m')+1]==expected and 'model_reasoning_effort="'+effort+'"' in cmd
 assert '/output' not in cmd and '/meter' not in cmd and str(d) not in cmd
 profile=Path(cmd[cmd.index('/home/agent/.codex')-1]);assert not profile.exists()
 assert row['native']['started']<= (12 if row['phase'] in ['extract','reflect'] else 24)
 for line in (d/'ARTIFACTS.sha256').read_text().splitlines():
  h,rel=line.split('  ',1);assert sha(d/rel)==h
 if row['phase']=='repair':
  assert row.get('scored_candidate_unchanged')
  assert read(d/'score-before-manifest.json')==read(d/'score-after-manifest.json')==final['files']
  prompt=(A/'prompts/AUTO.md').read_text()+ ('\n\n'+(A/'NEW_EXPERIENCE.md').read_text() if row['condition']=='AUTO_EXP' else '')
  assert (d/'input/actual-prompt.md').read_text()==prompt
 if row['phase']!='reflect':assert row['source_body_proofs']
 checks.append({'slot':row['slot'],'hook_model_match':True,'cli_effort':effort,'requests':row['native']['started'],'completed_posts':row['native']['completed'],'archive':row['archive_status']['status'],'source_body_verified':bool(row['source_body_proofs']) if row['phase']!='reflect' else None,'profile_removed':True,'prompt_candidate_and_score_hashes_verified':True})
assert sha(A/'protocol.json')==(A/'protocol.sha256').read_text().strip()
for p,h in read(A/'protocol.json')['files'].items():assert sha(p)==h,p
for n in ['contract-freeze.json','feedback-freeze.json','experience-freeze.json']:
 if (A/n).exists():
  for p,h in read(A/n)['files'].items():assert sha(p)==h,p
protected=read(A/'protected-files.json')
for p,h in protected.items():assert sha(p)==h,p
assert not subprocess.check_output(['git','diff','--binary'],text=True)
assert not list(A.rglob('auth.json'))
save('integrity-validation.json',{'status':'PASS','AI_assisted':True,'sessions':checks,'frozen_files':len(read(A/'protocol.json')['files']),'protected_files':len(protected),'all_old_case_and_global_config_hashes_unchanged':True,'tracked_diff_empty':True,'no_auth_archived':True,'requests':s['total_cost']['requests_started'],'requests_cap':264,'session_count':len(rows),'session_cap':12,'only_prompt_difference_in_formal_groups':'raw frozen new experience appended exactly','server_effort_independently_attested':False})
save('completion.json',{'status':'COMPLETE_CONDITIONAL_PROTOCOL','reason':s['stop']['reason'],'sessions':len(rows),'formal_sessions':sum(x['slot'].startswith('final-') for x in rows),'experience_generated':s['experience_generated'],'experience_accepted':s.get('acceptance',{}).get('accepted') if s.get('acceptance') else None,'unstarted_slots':s['unstarted'],'no_rerun_or_second_reflection':True,'no_more_actor_calls':True})
report='''# 初始暂停查询：同题经验实验 / Terra low

## Task 1：来源、评价和工具预检

本批在用户查阅历史并回复“do”后独立执行。初始HEAD `07b7cdcdec0dd8caf016be8f8d67378c83c53156`，tracked diff为空；此前研究目录已由外部状态纳入新HEAD，本轮不创建提交或改写历史。未发现适用的额外AGENTS.md。

唯一case `query-paused-initial-fetch-10266-vanilla` 从实际cluster登记解析。旧low L/G/C原件分别为25/29、26/29、28/29，都是不同提示条件各一次，不是同条件三次重复。当前4个候选文件、12个oracle文件、任务及manifest与旧批冻结摘要对应；历史仅作选题线索，不给actor、不充当本批基线。

policy-review.md按原任务、README及src/session.js区分首次尚未进入请求的pending+paused、已开始的未消费工作、已消费工作、已有缓存刷新及query/attempt所有权；取消既要阻止无效未来调用，也要结算来源attempt并恢复先前状态。保留原有多观察者、惰性signal读取、network/focus/retry、代际结果及依赖配置。AI辅助核查不伪造人工批准，也不声称整个上游库等价。

M1零模型校准共10项：bounded/expanded两个有效参考均PASS，原始候选与7个退化变体均UNDERREACH，无runtimeError。本例无授权扩展区分，两个参考均通过不视为异常。所有原29项评分及scope-baseline保持不变。固定Python归档运行器15项离线检查、当前JS源码正文读取、只读/可写namespace、host归档隐藏、RPC账本与code_mode_host/shell工具检查通过。评分所用既有esbuild/jsdom及相关锁文件/入口摘要另外冻结，没有安装依赖。

维护所有组gpt-5.6-terra/low，提取gpt-6-sol/low，反思gpt-5.6-terra/medium；实际Node与声明一致为v16.20.2。并发1，每会话600秒，维护24请求、提取/反思12请求，总上限12会话264请求。CLI/config声明effort，hook核对型号及请求，不宣称独立认证服务端路由/effort。业务补丁只在独立工作区发生，归档由Python执行，执行环境不挂评分、历史、参考、其他槽位或host归档目录。

## Task 2：实际执行与经验接纳

'''
report+='停止/完成原因：**'+s['stop']['reason']+'**。\n\n'
for prefix,title in [('base-','AUTO开发基线'),('reval-','AUTO_EXP训练回验')]:
 v=[x for x in vs if x['slot'].startswith(prefix)];valid=[x for x in v if x['infrastructure_valid'] and x['scoring_valid']]
 report+=f'- {title}：{sum(x["overall_pass"] for x in valid)}/{len(valid)}整体通过，另有{len(v)-len(valid)}无效。\n'
report+='\n自动Contract仅提取一次，按既有栏目机械截取，完整原报告另存；不依据标准手工修正。所有维护会话均从相同原始候选开始，无会话/补丁/工具状态继承。\n\n'
if s['experience_generated']:
 report+='仅一次Reflection产生NEW_EXPERIENCE.md，原输出及摘要独立保存，不手工润色、不更新生产经验库。反馈仅含本批基线的源绑定差异、保留要求、必要实际结果；完整标准和参考补丁留评价侧。reflection-input与feedback-freeze归档。\n\n'
 if s.get('acceptance'):
  report+='经验接纳：**'+('通过' if s['acceptance']['accepted'] else '未通过')+'**。接纳依据为反思前PLAN固定的目标关系实际改善、原正确行为保留、无无据策略及实际查证/落实，不以报告长短判定。完整对应重复差异见acceptance.json与experience-evidence.json；无模型采样种子相同的主张。\n\n'
else:report+='本批未产生新经验，未启动Reflection。\n\n'
report+='各组只有是否追加冻结经验这一输入差异；模型/effort、工具、输出、时间与请求预算相同。调度种子20261108只控制交错顺序。正式开始后不再改经验/Contract/评分，结束后统一分析，正式反馈不再用于演化。开发运行不混入正式分母。\n\n'
report+='## Task 3：观察结果、成本和限制\n\n首要正式结果：\n\n|组|整体通过|有效|无效|已启动/预留|\n|---|---:|---:|---:|---:|\n'
for g,d in s['formal'].items():report+=f'|{g}|{d["pass"]}|{d["valid"]}|{d["invalid"]}|{d["started"]}/{d["reserved"]}|\n'
report+='\n逐项行为/断言向量在behavior-vectors.json，完整原始评分在runs/<slot>/archive/score/stdout.json；下表只列未通过行为，不将29个耦合检查当29个独立案例：\n\n|槽位|组|判定|未通过行为|原已过required损失|\n|---|---|---|---|---|\n'
for v in vs:report+=f'|{v["slot"]}|{v["condition"]}|{v["verdict"]}|'+', '.join(k for k,x in v['effects'].items() if not x)+'|'+', '.join(v['required_losses_vs_original'])+'|\n'
if (A/'scope-review.json').exists():report+='\n源码范围、额外文件及经验实际查证记录见scope-review.json。原始缺陷、补丁新增保留项损失与未知政策分开记录；额外文件保留，不按后缀清理。\n'
report+='\n所有阶段计量如下。input/output含缓存/推理子项，不重复相加；失败与取消请求也计入started，缺失用量为未知，不补零。\n\n|阶段|会话|请求started/completed|工具|会话秒|input tokens|output tokens|\n|---|---:|---:|---:|---:|---:|---:|\n'
for stage,c in s['stages'].items():
 if stage=='M1':report+=f'|M1离线|0模型|0/0|0模型工具|校准{c["calibration_seconds"]:.2f}秒，其他本地准备未独立计量|0模型|0模型|\n';continue
 u=c['observed_usage_subtotal'];report+=f'|{stage}|{c["sessions"]}|{c["requests_started"]}/{c["requests_completed"]}|{c["tools_pre_use"]}|{c["session_seconds"]:.2f}|{u["input_tokens"]}|{u["output_tokens"]}|\n'
c=s['total_cost'];u=c['observed_usage_subtotal'];report+=f'|合计|{c["sessions"]}|{c["requests_started"]}/{c["requests_completed"]}|{c["tools_pre_use"]}|{c["session_seconds"]:.2f}|{u["input_tokens"]}|{u["output_tokens"]}|\n\n'
report+=f'Cached input={u["cached_input_tokens"]}；reasoning output={u["reasoning_output_tokens"]}；未发送的超限dispatch={c["blocked_dispatches_not_sent"]}；未知模型用量会话={c["unknown_usage_sessions"]}。主聊天准备/分析用量不可从实验hook取得，单列未知；未核验价格，不估货币成本。阶段详情与工具流均可复核。\n\n'
if s['formal']['AUTO']['started']==3 and s['formal']['AUTO_EXP']['started']==3:
 a=s['formal']['AUTO'];b=s['formal']['AUTO_EXP'];report+=f'观察解释：本次正式AUTO为{a["pass"]}/{a["valid"]}，AUTO_EXP为{b["pass"]}/{b["valid"]}。这是同题反馈后新会话重新修复的结果；最多支持本案例、当前条件下的观察差异，不证明独立泛化、迁移、稳定性或统计显著性。不能将训练回验直接当正式收益，也不能将任何成本差异全部归因经验。\n\n'
else:report+='正式证据未完整形成，不估计正式经验收益，不将未启动槽位记作失败。\n\n'
report+='边界：训练是经验文本更新，没有模型权重更新，没有官方GEPA或搜索。案例是已暴露合成派生表示；反馈与正式题目相同，存在同题学习信息，不能宣称未见测试。后续若继续须另立协议；本批不补跑、不换case/effort、不二次反思、不恢复旧调度器。\n\n'
report+='未启动槽位：'+', '.join(x['slot'] for x in s['unstarted'])+'。\n\n完整性记录在integrity-validation.json；输入/实现/评价冻结见protocol.json，所有归档摘要见ARTIFACTS.sha256。历史、生产、原案例及全局配置摘要保持不变；没有创建提交。\n'
(A/'REPORT.md').write_text(report)
(A/'README.md').write_text('# Query paused / same case / Terra low\n\nRead [REPORT.md](REPORT.md), [summary.json](summary.json), [PLAN.md](PLAN.md), [integrity-validation.json](integrity-validation.json). All actor inputs, snapshots, traces, patch diffs, accounting and raw scores live under runs/slot/archive. Host archives are not actor-mounted. No old batches are resumed.\n')
(A/'COMMIT_MESSAGE.txt').write_text('research: archive paused-query same-case experience experiment\n\nFreeze the historical-version-matched case and Terra low maintenance pipeline.\nRecord conditional baselines, single Reflection, acceptance and any gated formal comparison.\nPreserve raw patches, behavior vectors, costs and integrity evidence without altering prior experiments.\n')
print('Closeout complete',len(rows),'sessions; integrity PASS')
