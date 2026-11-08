import pathlib as P,json,csv,hashlib,shutil,collections
O=P.Path(__file__).resolve().parent;R=P.Path('/home/sribd/Downloads/wangshu/temporal-contract-analyzer');B=R.parent/'temporal-contract-bench-git'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
cases=json.loads((O/'cohort.json').read_text())['cases'];survey=json.loads((O/'history-survey.json').read_text());selected=[]
for c in cases:
 for h in c['history']:
  p=P.Path(h['run']).parent;calls=p/'trace/model-calls.jsonl';rows=[json.loads(l) for l in calls.read_text().splitlines()];assert rows and all(d.get('http_status')==200 for d in rows)
  h['service_requests_all_200']=True;h['service_trace_sha256']=sha(calls);h['service_calls']=len(rows)
  selected.append({'case':c['case'],'mechanism_variant':'explicit lifecycle Resource + Vue2/Vue3 presenter; eval-v2 disposal/background policy preservation','model':h['model'],'effort':h['effort'],'temperature':h['temperature'],'workflow':h['workflow'],'input_condition':h['condition'],'valid_runs':1,'behavior_failures':1,'input_tree_sha256':h['input_tree_sha256'],'source_changes':','.join(h['source_changes']) or 'no source patch despite TASK_DONE','missing_effects':';'.join(h['missing']),'forbidden_effects':';'.join(h['forbidden']),'score_basis':'same current ungranted oracle, exact raw-effect replay; task pending/ready + visible generation/cancel/close/dispose + background start override','limits':'Qwen vs target Terra; distinct historical workflows/prompts; bare task, not automatic Contract; target bare/H each 1 PASS; no target-hardness assertion','run':h['run']})
save(O/'verified-history.json',{'selected_cases':cases,'counting':'Each selected historical run individually verified; same model/effort/temperature/base within each case. Prompt/workflow differences retained, not treated as identical repeated conditions. No cross-model/effort/base pooling.','service_checks':'four historical call traces HTTP200, TASK_DONE, exit0, zero recovered tool format errors, original raw effect replay equal'})
with (O/'historical-selection.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(selected[0]));w.writeheader();w.writerows(selected)
with (O/'history-survey.csv').open('w') as f:
 keys=['case','registered','model','effort','condition','start_sha','prompt_sha256','status','termination','reported_valid_completion','verdict','run','duplicate_paths']
 w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(survey['rows'])
for n in ['PLAN.md','REPORT.md','EXPERIENCE.md','experience-approval.json','frozen-config.json','read_policy.py','request_guard.py','offline-validation.json']:
 if (R/'research/contract-repair-small-v1-20261108'/n).exists() and n in ['PLAN.md','REPORT.md']:pass
src=R/'research/u2-contract-repair-diagnostic-v1-20261108/runs/u02';d=O/'experience-source';d.mkdir(exist_ok=True)
for n in ['receipt.json','actual-prompt.md','events.jsonl','score.stdout.json','patch.diff']:
 if (src/n).exists():shutil.copyfile(src/n,d/n)
shutil.copyfile(R/'research/contract-repair-frozen-batch-v1-20261108/DIAGNOSIS.md',d/'DIAGNOSIS.md')
save(O/'source-relationship.json',{'canonical_arm':'download-polling-restoration-react18','E1_source_arm':'download-polling-restoration-low-cue-react18','E1_source_run':'research/u2-contract-repair-diagnostic-v1-20261108/runs/u02','source_failure':'Read close/reopen, implemented polling plus unmount-only active guard; successful self-test drove normal completion and unmount, not mounted close/reopen; raw close/reopen failures. Low-cue scoring-policy gap limits normative interpretation. E1 addresses event-to-verification substitution, not a universal cancellation rule.','source_event_lines':{'source_read':[9,11,13],'successful_self_test':27},'same_cluster_not_independent_sources':True,'derived_arms':[{'case':c['case'],'path':c['source_case'],'manifest_sha256':c['case_manifest_sha256'],'origin':'explicit React18 arm synthetic Vue port followed by post-hoc eval-v2 correction; shared independent_unit_id; not directly derived from E1 source run or its patch','changes':'Native Resource class separates DialogResource/WorkspaceJob from Vue presenter; explicit generation/timer/disposal ownership. Vue3 keeps foreground loading on dispose; workspace start override preserves original background start/closed state; polling still missing.','history_exposure':'Authored/research-exposed; prior target outcomes informed eval-v2 corrections; not holdout. Both target Terra/medium bare/H have one prior PASS; repeated failure evidence comes from Qwen bare task.'} for c in cases],'E1_sha256':sha(O/'EXPERIENCE.md'),'approval':'experience-approval.json + current user explicit instruction','AI_assisted_analysis':True,'independent_human_review':False})
plan='''# 同 cluster 历史失败派生任务：固定 E1 开发迁移实验

2026-11-08 Asia/Shanghai；AI辅助分析，非独立人工复核。仅本目录及仓库外私有运行目录可写，不修改生产、原经验、技能、标准、评分器或历史，不提交。

## Task 1：事前选例及证据边界

冻结案例1 `download-polling-restoration-explicit-vue2-eval-v2`；案例2 `download-polling-restoration-explicit-vue3-eval-v2`。全部选例在任何本轮模型调用前完成，不按本轮结果替换/删例。cluster canonical是react18；E1源自low-cue arm u02，称“来源案例”，不是canonical核心。两个所选变体是explicit arm的Vue合成派生及eval-v2修订，仍共享同一独立单元，不是独立来源。详见source-relationship.json和原登记。

历史筛选表historical-selection.csv逐行列四个有效行为失败，不能把每case的两行称完全相同条件的重复：它们同Qwen3-coder:30b、effort未指定、temperature=0、当前候选起点完全相同，但分别使用优化v4和quality-v5外围提示及工具流程。每行正常TASK_DONE/exit0、零工具格式恢复、全部服务调用HTTP200、非上限终止；原候选树摘要匹配，当前未改oracle重放与原effect向量完全一致。排除异常、校准、不同模型/effort/起点及归档重复。

两例仅有裸任务Qwen反复失败证据，**没有“自动Contract、无E1”反复失败证据，也没有目标Terra/medium困难性证据**。Terra/medium在每例裸任务与人工Contract各1次PASS；不同输入条件各一次不当作稳定自动组天花板，但显示明显天花板风险。本轮若两组通过仍报告天花板，不换题。Qwen两workflow结果按行报告，不把不同prompt当相同修复设置。Vue2一份TASK_DONE未交付源码补丁，单列，不把原始校准当模型失败。选择历史失败带来条件性困难任务选择偏差，不能泛化或称独立事故迁移。核心目标是同cluster且历史失败的任务上描述E1表现，目标模型相对难度未证。

explicit-react18因最近相同自动组3/3全过排除；low-cue是经验来源且关闭/精确loading政策真正未决，不用隐藏评分要求强行准入；canonical react18虽有Terra裸任务重复失败，候选close仅隐藏且无明确前台取消政策，不增造标准。其他模型、旧版本、未登记port alias及STEP_LIMIT_OR_ERROR等不并入有效计数。完整历史元数据和去重键在history-survey.json/csv，正式准入只采用四份逐件核验的历史证据，不冒称全部survey行经过独立完整审计。

## Task 2：材料、准入、提示和调度

两个case各自的原任务要求pending持续检查、ready才交付。可见Resource提供generation/timer、invalidate、cancelRetry、dispose与check回调guard；DialogResource.close调用invalidate，WorkspaceJob.close只隐藏，WorkspaceJob.start保留自身已有行为。重开即新代，包括同token。Vue3 dispose只对前台清loading；不统一前后台政策。主目标是新增轮询后排队、关闭仍挂载、旧响应/当前响应交错、重开及中间等待。保留后台继续、关闭/重启/多start、disposal快照和现有公共API。具体逐effect以原oracle为限，未规定调度取消是否绝不会触发回调、错误/非法状态/同步notify重入等不添断言。

原任务、候选、manifest、oracle文件摘要在cohort/materials。每例零模型校准8项：unchanged不通过、bounded reference PASS、六个既有mutant全部检出；另各2份历史候选原effect精确重放。校准不改任何断言。没有把旧草稿“待确认”或作者review pending机械当阻断；可见源码支持所有已使用的关闭/后台/卸载政策。评分工作在模型隔离之外。

未找到这两个case完全匹配固定K1/配置的有效自动Contract；benchmark contract-provided是人工提供规格，不冒充自动输出。每例只新增一次提取gpt-6-sol/low，只提供原任务+候选及固定K1，不含E1/人工Contract/评分/历史答案。按上一批固定四栏机械取第1栏正文交付修复，完整报告保留；不编辑/重生成，完整报告、正文、SHA及来源和两组实际提示在该例任何维护评分前冻结。若提取无效，仅停止该例并保留其未启动维护计划；不替换，可继续另一独立预选例，除非是基础设施异常。

A=原任务+候选及上一批相同公共维护指令+冻结自动Contract；B仅在A末尾逐字追加E1-v1。E1 SHA=57527138a98bfa0d34a432ca82e7b863694b33818aa5a9a3c032ad69f4aaed1e，有既有批准及本轮授权，不再提问。完整templates/extraction在prompts；实际A/B提示于提取后冻结。只给第1栏、其余栏不交付这点完全对称；不增加案例专用提示、验证脚本、角色或研究清单。

修复均gpt-5.6-terra/medium，提取gpt-6-sol/low，priority显式配置；目录支持检查、实际命令与hook型号逐槽核对，不静默换模型。原生Codex自主exec、已修复read_policy/request_guard，无ReAct外层。输出上限report=6000 Unicode字符，CLI事件stdout=16777216 bytes；没有已核验推理token原生硬上限。提取只读，修复独立可写副本；每槽相同本例冻结起点，不能接续补丁。namespace不挂研究侧标准/oracle/reference/历史/其他槽位，认证和临时运行放Git外，不归档auth/profile。执行模型只看到本例候选，不给研究观察清单。首个正式提取工具正文证据计正式预算。

最多12维护+2提取=14顶层会话；维护每槽24请求/600秒、提取每槽12请求/600秒，全局312请求/8400会话秒预留。无需提取的复用情形本轮为0，所以不超额预留。反思、技能更新、GEPA、模型筛选/预跑、补跑=0。所有正式会话含失败均计预算。种子2026110804只控制调度不是模型种子，串行并发1。按case与repeat配对：case1 X,A1,B1,A2,B2,B3,A3；case2 X,B1,A1,B2,A2,B3,A3。准确schedule.json冻结，不按结果改变。

停止：14槽计划结束即停止。正式服务/工具误拒/配置/计量/评分关联异常第一次即停止发起全部新槽，保留结果及剩余计划，不自动重试。正常模型交付/资源失败与行为失败分开；不因一次PASS或FAIL提前停。纯提取格式/未读源码无有效Contract仅跳过该例维护，不重生成。模型或服务不可用报告并停，不替换。全局原配置始末保护。

## Task 3：评价及交付

主指标为原ungranted整体verdict；逐effect、原通过项丢失、新增forbidden、实际schedule中间状态、patch范围及成本分别报告，不用检查总分抵消生命周期/后台退步。按实际轨迹检查是否调用仍挂载close、是否已排队retry、是否跨reopen交错、是否拿unmount替代close，是否作用到正确代码位置，或只是说明/工具/耗时增量。自检不能替代原评分，模型自述不算落实证据；真实命令输出/patch及原评分支持结论。未评分、未决政策单列。

全部请求、tool hook、shell命令、失败、token含缓存/推理子项、耗时保留；缓存与推理是子项不能重复加总。无核验单价不报货币，主聊天准备/分析token无法取得单列排除。小样本和变体不作显著性、稳定性、因果或独立泛化断言，两组全过报告天花板，两组失败保留未解路径，不能只留成功。

产物：历史筛选表/原始关联、来源、PLAN/配置/准入、自动Contract和E1/完整prompt/SHA、全部轨迹/patch/原评分/成本、case-results.csv、summary.json、REPORT.md、COMMIT_MESSAGE.txt。无E2、生产经验库更新、第三例或提交。
'''
(O/'PLAN.md').write_text(plan)
save(O/'admission.json',{'status':'PASS','cases':[{'case':c['case'],'historical_behavior_failures_verified':2,'target_model_difficulty_proven':False,'automatic_contract_difficulty_proven':False,'visible_policy_supported':True,'calibrations':[(z['label'],z['verdict']) for z in c['calibration']],'historical_replays':2,'oracle_files':c['oracle_files']} for c in cases],'AI_assisted_not_independent_human':True,'new_model_calls_at_admission':0,'no_new_requirement_or_scorer_edit':True})
print('PLAN and verified historical table written.')
