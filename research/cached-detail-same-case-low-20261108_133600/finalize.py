"""Offline closeout; never launches an actor, scores or retries."""
from pathlib import Path
import json,hashlib,subprocess,ast
A=Path(__file__).resolve().parent;R=A.parents[1]
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,d):(A/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
s=read(A/'summary.json');rows=read(A/'actual-schedule.json');vectors=read(A/'behavior-vectors.json');assert (A/'stop.json').exists() and len(rows)==3
checks=[];scope=[];policy=(A/'prompts.py').read_text()
for row in rows:
 d=A/'runs'/row['slot']/'archive';ledger=read(d/'meter/ledger.json');usage=read(d/'usage.json');frozen=read(d/'input/frozen-start.json');final=read(d/'final-manifest.json');events=[json.loads(x) for x in (d/'events.jsonl').read_text().splitlines()]
 assert ledger['sessions'][row['slot']]==row['native']
 assert frozen['prompt_sha256']==sha(d/'input/actual-prompt.md')
 assert frozen['tree_sha256']==final['workspace_sha256_before'] if row['phase']=='extract' else True
 assert final['workspace_sha256_before']==final['workspace_sha256_after']
 expected='gpt-6-sol' if row['phase']=='extract' else 'gpt-5.6-terra'
 modelhooks=[x['event'] for x in ledger['events'] if x['event'].get('hook_event_name') in ['PreModelRequest','PostModelRequest']];assert modelhooks and all(e['model']==expected for e in modelhooks)
 assert len([e for e in modelhooks if e['hook_event_name']=='PostModelRequest'])==row['native']['started']==row['native']['completed']
 cap=12 if row['phase']=='extract' else 24;assert row['native']['started']<=cap
 cmd=read(d/'command.json');assert cmd[cmd.index('-m')+1]==expected and 'model_reasoning_effort="low"' in cmd
 assert '/output' not in cmd and '/meter' not in cmd and str(d) not in cmd
 profile=Path(cmd[cmd.index('/home/agent/.codex')-1]);assert not profile.exists()
 assert row['archive_status']['status']=='OK' and row['output_format_valid'] and row['infrastructure_valid']
 assert not usage['usage_incomplete'] and row['source_body_proofs']
 for line in (d/'ARTIFACTS.sha256').read_text().splitlines():
  h,rel=line.split('  ',1);assert sha(d/rel)==h
 if row['phase']=='repair':
  assert row['scoring_status']=='COLLECTED' and row['scored_candidate_unchanged']
  assert read(d/'score-before-manifest.json')==read(d/'score-after-manifest.json')==final['files']
  assert (d/'input/actual-prompt.md').read_text()==(A/'prompts/AUTO.md').read_text()
  changes=read(d/'file-changes.json');assert changes['changed']==['src/detail-panel.js'] and not changes['added'] and not changes['deleted']
  scope.append({'slot':row['slot'],'business_changed':['src/detail-panel.js'],'added_files':[],'model_created_archive_artifacts_observed':False,'unsupported_scope_changes_found':False,'policy_review':'Current activation installed/selected before cache callback; closure checks activation identity, late handle released if retired; network path and adjacent consumers retained. No added cache policy, scheduling, keys-only ownership or public API expansion.','self_verification_evidence':[{'event_line':n,'exit_code':e['item'].get('exit_code'),'command':e['item'].get('command')} for n,e in enumerate(events,1) if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='command_execution' and ('--check' in e['item'].get('command','') or 'assert' in e['item'].get('command',''))]})
 checks.append({'slot':row['slot'],'input_and_archive_hashes_verified':True,'hook_model_match':True,'effort_cli_low':True,'ledger_requests':row['native']['started'],'accounting_complete':True,'archive_outside_namespace':True,'auth_profile_removed':True})
save('scope-review.json',{'AI_assisted':True,'independent_human_review':False,'runs':scope,'formal_experience_effect_estimated':False})
assert sha(A/'protocol.json')==(A/'protocol.sha256').read_text().strip()
for p,h in read(A/'protocol.json')['files'].items():assert sha(p)==h,p
protected=read(A/'protected-files.json')
for p,h in protected.items():assert sha(p)==h,p
assert not subprocess.check_output(['git','diff','--binary'],text=True)
assert not list(A.rglob('auth.json'))
save('integrity-validation.json',{'status':'PASS','AI_assisted':True,'session_checks':checks,'frozen_files_checked':len(read(A/'protocol.json')['files']),'protected_files_checked':len(protected),'all_historical_production_case_and_global_config_hashes_unchanged':True,'tracked_diff_empty':True,'no_auth_archived':True,'max_sessions':12,'actual_sessions':len(rows),'max_requests':264,'actual_requests':s['total_cost']['requests_started'],'no_hidden_model_calls_or_retries':True,'formal_sessions':0,'unstarted_slots':len(s['unstarted']),'source_reader_actual_body_verified':True})
save('stage-state.json',{'stage':'STOPPED_M2_BASELINE_CEILING','reason':s['stop']['reason'],'experience_generated':False,'formal_started':False,'no_more_model_calls':True})
save('completion.json',{'status':'COMPLETE_AT_PREDEFINED_STOP','stage':'M2','reason':s['stop']['reason'],'model_sessions':len(rows),'maintenance_sessions':2,'reflection_sessions':0,'formal_sessions':0,'unstarted_slots':s['unstarted'],'unchanged_inputs_after_freeze':True,'no_case_replacement_effort_change_or_rerun':True})
report='''# cached-detail 同题经验实验：Terra low 开发筛查

## Task 1：来源、评价和工具预检

用户在同题开发/冻结后验证方案后授权“do”。本批独立目录，HEAD `40919fb9f33f2336a581c7d013d4d5d888505387`，起始tracked diff为空，保留已有两个未跟踪研究目录。无适用的额外AGENTS.md。

唯一case `cached-detail-activation-vanilla`，从服务器reentrant-lifecycle-handoff/cluster.json的arm.path解析。原任务/候选/manifest/oracle完整复制并SHA冻结。候选可见任务、README及repository注释支持缓存必须在open内显示、当前activation继续network、每次同key打开是新activation、最新导航优先、迟到handle归原activation并在退役时释放，以及compliance/preview不同策略。policy-review.md是AI辅助核查，不伪造人工批准，也不用参考通过反推政策。

原始、bounded、expanded与6个mutants，共9项离线校准符合预期：仅bounded整体PASS，其余正确触发原ungranted规则。校准不计模型修复结果。15项固定Python归档运行器离线测试通过；当前案例5份JS源码正文逐行读取、readonly、host archive/output/meter隐藏、guard RPC、code_mode_host和shell工具可用性检查通过。首次预检的文件数硬编码断言已在首个模型调用前修正为实际清单核对，失败证据保留。

维护配置固定gpt-5.6-terra/low，提取gpt-6-sol/low，一次反思预留gpt-5.6-terra/medium。CLI/config给出effort声明，真实hook核对型号与每次请求；不宣称独立认证服务器effort或路由。声明Node v16.20.2，实际全批统一v18.17.0，两者分开记录。并发1，维护24请求、提取/反思12请求，每会话600秒；最高12会话264底层请求。没有安装依赖、修改全局配置或生产代码，没有创建提交。

## Task 2：实际执行与停止

**执行至M2，停止：AUTO开发基线2/2整体通过，本次未观察到同题经验提升空间。**

一次K1自动Contract有效提取，原报告与栏目1机械交付分别保存，未根据标准答案人工修改。两次AUTO从同一原始候选独立创建工作区，使用相同任务/Contract、low参数、工具和资源上限，没有继承会话或补丁。

|开发槽位|有效性|官方评分|归档|业务改动|额外文件|
|---|---|---|---|---|---|
|base-1|有效|PASS|OK|src/detail-panel.js|无|
|base-2|有效|PASS|OK|src/detail-panel.js|无|

两次都建立/选中activation再调用可能同步回调的prefer-cache订阅，使用对象身份守卫当前发布，并释放归属已退役activation的迟到handle；合规与预览源码未改动。两轮都执行内联断言和语法检查，实际命令与输出见runs各archive。源码审查未发现无据策略扩展；这只是AI辅助核查与当前评分覆盖内结论。

Python独立保存原始/最终快照、实际prompt、事件/工具输出/stderr、raw answer、账本、patch.diff和评分。两轮未创建模型归档副本或patch目录，宿主归档不挂给模型；不据不同case/effort/输入的历史运行推断节省了多少请求。

停止后没有反思、没有新经验、没有训练回验，也没有正式AUTO/AUTO_EXP对照。未启动9个预留槽位：反思1、回验2、正式6。没有补跑、替换案例或改effort继续找结果。

## Task 3：观察结果、成本和限制

首要正式结果：两组均未启动，不能把开发2/2混入正式分母。

|正式组|通过|有效|无效|未启动|
|---|---:|---:|---:|---:|
|AUTO|0|0|0|3|
|AUTO_EXP|0|0|0|3|

本批无可估计的经验增益，也不是经验组失败。它提供的是：该案例在当前固定自动Contract+Terra low条件下，观察到两次完整修复，缺少本轮经验开发所需的失败反馈。小样本不能证明永远没有提升空间，不能推广到其他case或medium设置。

逐项行为向量见behavior-vectors.json，完整断言/轨迹见每轮archive/score/stdout.json。两轮14个required effects全部true，禁止的preview-cache-migrated为false。共同存在的原已过断言没有true→false；部分旧断言只在原始无cache路径的条件分支出现，新正确cache路径不再生成，单列为absent而不伪称行为丢失。这里没有进行经验接纳判断。

|阶段|模型会话|底层请求|工具调用|模型会话秒|input tokens|output tokens|
|---|---:|---:|---:|---:|---:|---:|
'''
for name,c in s['stages'].items():
 if name=='M1':report+=f'|M1离线预检|0|0|0模型工具|非模型校准{c["calibration_seconds"]:.2f}秒，其余准备时间未独立计量|0模型|0模型|\n';continue
 u=c['observed_usage_subtotal'];report+=f'|{name}|{c["sessions"]}|{c["requests_started"]}|{c["tools_pre_use"]}|{c["session_seconds"]:.2f}|{u["input_tokens"]}|{u["output_tokens"]}|\n'
c=s['total_cost'];u=c['observed_usage_subtotal'];report+=f'|模型阶段合计|{c["sessions"]}|{c["requests_started"]}|{c["tools_pre_use"]}|{c["session_seconds"]:.2f}|{u["input_tokens"]}|{u["output_tokens"]}|\n\n'
report+=f'全部{c["requests_started"]}次底层请求均有完成hook与用量，无失败/取消/超限调度；permission events=0，完成shell命令{c["shell_commands_completed"]}次。Cached input={u["cached_input_tokens"]}、reasoning output={u["reasoning_output_tokens"]}，是各自input/output子项，不重复相加；cache-write=0。未知模型用量会话为空。主聊天准备/分析用量及未测的本地编排时间未知，不补零；未核验单价，不报货币成本。完整分阶段计量见summary.json与各archive/usage.json。\n\n'
report+='限制与下一步：同题、作者构造且已暴露，未来即便有经验增益也只能称同题开发收益。本次不产生新经验，也不检验跨case或跨语言迁移。若继续研究，需要另立协议选择有集中失败证据的候选，或明确研究其他设置；本批不自动换case、降低effort或追加调用。\n\n完整性验证见integrity-validation.json，冻结协议见protocol.json与protocol.sha256，全部文件摘要见ARTIFACTS.sha256。历史/生产/案例/全局配置的保护摘要均不变。\n'
(A/'REPORT.md').write_text(report)
(A/'README.md').write_text('# cached-detail / same-case / low\n\nStart with [REPORT.md](REPORT.md), [summary.json](summary.json), [PLAN.md](PLAN.md). Stopped at M2: AUTO development 2/2 PASS, no experience generated and no formal comparison launched.\n\nThe only actual actor sessions are extract, base-1, base-2. Each runs/slot/archive contains runner-owned snapshots, prompt, events, tool output, usage, patch and trusted external score. No model-created archive files. No old scheduler resumed or historical files changed.\n')
(A/'COMMIT_MESSAGE.txt').write_text('research: archive cached-detail same-case low baseline screen\n\nFreeze the source, automatic Contract and runner-owned archival protocol.\nRecord two valid AUTO passes and stop before reflection or formal validation.\nPreserve raw traces, behavior vectors, costs and integrity evidence.\n')
print('Closeout PASS; report and integrity records saved; no further model calls')
