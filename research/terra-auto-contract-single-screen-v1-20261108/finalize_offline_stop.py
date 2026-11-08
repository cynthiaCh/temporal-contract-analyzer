import pathlib as P,json,hashlib,shutil,importlib.util,subprocess,re
O=P.Path(__file__).resolve().parent;sp=importlib.util.spec_from_file_location('screen_execute',O/'execute.py');e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e);r=e.r;save=r.save;A=e.A
assert not (O/'actual-schedule.json').exists() and not (O/'runs').exists(),'Stop must precede every formal session'
r.verify();c=r.cases()[0];src=P.Path(c['source_case']);source=O/'materials'/c['case']/'candidate';task=(O/'materials'/c['case']/'task.md').read_text();code=(source/'src/workflow.py').read_text();readme=(source/'README.md').read_text();worker=(src/'oracle/worker.cjs').read_text()
assert "self.state['loading']=False;self.publish()" in code
assert "{loading:true,retryScheduled:true,completed:[]}" in worker
save(O/'policy-gap.json',{'status':'UNRESOLVED','case':c['case'],'task':{'path':str(O/'materials'/c['case']/'task.md'),'sha256':r.sha(O/'materials'/c['case']/'task.md'),'scope':'keep checking pending and deliver only after ready; no exact loading-field semantics'},'candidate_facts':[{'path':'src/workflow.py','line':42,'quote':"self.state['loading']=False;self.publish()",'meaning':'DialogResource.pending currently clears loading; adding queued retry alone need not restore this field unless an additional state policy is justified'},{'path':'README.md','line':1,'meaning':'documents false/true, repeated pending, external retry scheduling, foreground/workspace ownership and disposal; no rule requiring loading alone to encode the waiting interval'}],'scoring_requirement':{'path':str(src/'oracle/worker.cjs'),'line':30,'assertion':'poll-pending-keeps-loading-N','expected':{'loading':True,'retryScheduled':True,'completed':[]},'also_aggregated_as':'download-waits-after-pending'},'supported_policies':'foreground close/reopen invalidation, generation guards, cancellation/disposal and background visibility-only close are candidate-visible and not disputed','unresolved_policy':'Whether loading must stay true throughout request-free queued waiting, versus waiting represented by retryScheduled or another documented combination','why_calibration_insufficient':'Reference PASS and mutant detection establish implementation/scorer consistency, not normative support for a particular field policy absent from task/docs. No scorer filtering or new policy was invented.','action':'Stop before extraction or repair; no second candidate, no model call, no request for a new requirement inside this batch.','not_a_model_behavior_failure':True})
save(O/'final-admission.json',{'status':'STOP_POLICY_BASIS_INSUFFICIENT','supersedes':'admission.json preliminary lifecycle/calibration PASS; not a final authorization to launch','new_policy_gap':'policy-gap.json','model_calls':0,'candidate_replacements':0,'all_planned_slots_unstarted':r.read(O/'schedule.json')['slots'],'no_E1':True,'no_contract_generated':True})
save(O/'stop.json',{'phase':'offline_before_formal_calls','reason':'unresolved exact loading-field policy in required score','no_retry_or_replacement':True,'all_unstarted':r.read(O/'schedule.json')['slots']})
(O/'contracts').mkdir(exist_ok=True);save(O/'contracts/STATUS.json',{'status':'NOT_GENERATED','reason':'Final policy admission failed before any model call','extraction_sessions':0,'existing_contract_reused':False,'repair_prompt_materialization':False})
summary={'case':c['case'],'batch_type':'single-case Terra/medium automatic-Contract baseline screening, no E1','status':'OFFLINE_STOP_POLICY_GAP','selection_frozen_before_model_calls':True,'final_admission':'STOP_POLICY_BASIS_INSUFFICIENT','screening_classification':'证据不足','recommendation':'证据不足','planned':{'extraction_sessions':1,'maintenance_sessions':2,'requests_cap':60,'repair_model':'gpt-5.6-terra','repair_effort':'medium','extraction_model':'gpt-6-sol','extraction_effort':'low'},'actual':{'extraction_sessions':0,'maintenance_attempted':0,'maintenance_valid':0,'model_requests':0,'model_tokens':0,'formal_model_seconds':0,'pass_rate':None,'model_behavior_failures':0,'infrastructure_failure_slots':0,'case_replacements':0},'unstarted_slots':r.read(O/'schedule.json')['slots'],'offline_calibration':{'invocations':len(c['calibration']),'seconds':sum(x['seconds'] for x in c['calibration']),'source_unchanged_verdict':c['calibration'][0]['verdict'],'reference_verdict':c['calibration'][1]['verdict'],'not_model_difficulty_evidence':True},'policy_gap':'Exact pending waiting loading=true unsupported by visible task/README while base pending clears it; lifecycle ownership supported. See policy-gap.json.','prior_Terra_medium':'one bare-task PASS and one human-contract PASS; neither is fixed-K1 automatic Contract','other_model_failures_counted':False,'future_E1_comparison':'Must be a separate independently run batch; no merging this offline audit or any future screen failures with enhanced results','AI_assisted_analysis':True,'independent_human_review':False,'main_chat_preparation_cost':'Unavailable and excluded, not assumed zero','currency_cost':None}
save(O/'summary.json',summary)
(O/'maintenance-results.csv').write_text('slot,status,valid,verdict,reason\nr1,NOT_STARTED,false,,policy_admission_failed\nr2,NOT_STARTED,false,,policy_admission_failed\n')
report='''# 单案例 Terra/medium 自动Contract筛选：离线停止

最终推荐：**证据不足**。尚未产生Terra/medium自动Contract维护结果，不能认定难例、稳定易例或E1适用对象。全批正式模型调用0，无提取、维护、E1、替换案例或补跑。

## Task 1：只选此case及最终准入缺口

事前唯一选定`download-polling-restoration-python3-eval-v2`。cluster canonical是react18，E1历史来源是low-cue arm u02；本例登记为canonical家族的非explicit Python/asyncio派生，eval-v2已暴露开发修订，不是独立来源，也未参加近期explicit/Vue2/Vue3或transfer的同条件比较。它没有已找到的版本匹配固定K1自动Contract/Terra-medium维护记录，因此可用于筛选该条件的空白，而不是预先称难例。

历史Terra/medium对当前case分别有一次裸任务PASS、一次人工Contract PASS；实际run、prompt及原始评分已保存于history/。Qwen/其他模型结果仅列historical-context.json，不作为Terra难度证据。原始未修改代码UNDERREACH只是校准；服务/工具/上限异常也没有被合并成有效模型失败。原任务、3份候选文件、manifest、source-record及评分器版本均关联冻结于materials/cohort/source。

候选可见的生命周期政策充分：DialogResource.close→invalidate（generation增加、取消timer/retry、清loading），reopen新代，response/retry检查disposed/generation；WorkspaceJob.close只隐藏、工作继续，start和dispose按自身原行为保留。没有把low-cue旧关闭政策争议移植过来，也没有因作者确认栏空白机械阻断。

**最终缺口在另一项独立评分要求。** 原任务只明确pending持续检查、ready后交付。README说明异步false/true、外部调度及ownership，没有定义loading字段必须独自表达整个等待区间。候选DialogResource.pending却明确执行`self.state['loading']=False;self.publish()`。现有worker.cjs:30的`poll-pending-keeps-loading-N`断言要求每个pending间隙同时`loading=true,retryScheduled=true,completed=[]`，并进入整体PASS。仅从“loading”命名、相邻后台状态或参考补丁不能补出该字段规范；等待由retryScheduled/其他组合表达的可能性尚未被可见资料排除。

因此，初步admission.json中的生命周期/校准PASS，不能作为完整评分政策准入。最终final-admission.json明确覆盖为STOP_POLICY_BASIS_INSUFFICIENT，policy-gap.json保存具体来源、原断言及未知。没有删掉该评分项、过滤分数、补隐藏要求、改任务、增加人工Contract或选择第二例。

## Task 2：实际调用、校准及成本

已完成8次零模型原评分校准：unchanged=UNDERREACH；bounded reference=PASS；retry-without-invalidation、timer-not-cancelled、same-token-generation、premature-ready均UNDERREACH；duplicate-delivery和shared-dialog-policy均UNDERREACH_AND_OVERREACH。原始stdout/receipt完整保留。这证明评分可复现并能区分参考与错误变体，**不能证明全部断言都有当前任务可见依据**。

已使用修复后的读取后端零模型重放本例全部源码/文档正文，提取副本只读、研究路径隐藏，模型目录支持检查通过。为Python源码正文证据将记录后缀从.js换为.py；没有修改模型权限或旧读取门。认证及运行目录在Git之外，离线profile已删除。

准备配置为维护gpt-5.6-terra/medium、提取gpt-6-sol/low，priority显式；report上限6000 Unicode字符、事件输出16MiB。计划仅x01提取→r1→r2，最多60请求，提取12/600秒，维护24/600秒。PLAN及材料已冻结；尚未发起任何模型请求就因规范缺口停止。配置“可用目录支持”不冒称已实际调用/认证服务可用。

实际提取0/1，维护启动0/2、有效0/2；r1/r2均NOT_STARTED，成功率为null而非0%。正式模型请求/token/会话耗时均0；没有基础设施失败槽位，也没有模型行为失败。原始校准、正文读取和文件操作是本地准备成本，校准秒数见summary.json；主聊天准备/分析token不可取得，明确排除而非计0。无核验单价，不估货币。

准备脚本曾假设source-record.md，而本例实际为source-record.json；仅修正来源文件复制并校验原记录SHA，保留说明，没有重复校准、调用模型或覆盖历史。此元数据准备错误与正式工具/服务失败不同。

## Task 3：后续适用性及证据限制

本批的有效维护分母为0，无法应用“两次失败/一过一败/两次通过”的行为筛选规则。按预先规则归入证据不足。不能凭原代码校准失败、Qwen失败、历史人工Contract通过或可见生命周期结构就称为Terra自动Contract困难候选。

暂不推荐将它直接投入固定E1效果对照：完整评分仍含未充分说明的字段政策，可能把“未获规范”误当“未落实经验”。本批到此结束，不追加E1、不生成经验/技能、不运行GEPA、不换题、不扩大规模；没有Future enhanced组可拼接。后续若另有合法匹配任务与已明确规范，需独立立批、重新运行基线，不能把本轮离线校准或审查当对照结果。

分析为AI辅助，不冒称独立人工复核。旧历史、经验、评分器、生产和全局配置摘要始末核验不变；HEAD及Git差异记录见protection-check.json。未创建提交，归档无auth.json/凭证，零模型准备的临时认证目录已清理。Contract未生成状态在contracts/STATUS.json；实际prompt不存在，prompts仅是未执行模板/提取计划，不冒称模型收到过。所有3个未启动槽位及预算保留。

建议Git commit subject/body见COMMIT_MESSAGE.txt；不创建提交。
'''
(O/'REPORT.md').write_text(report)
(O/'COMMIT_MESSAGE.txt').write_text('research: stop single Terra contract screen at policy admission\n\nSelect the registered non-explicit Python derivative before model calls.\nVerify historical target-model conditions, visible lifecycle ownership,\nsource isolation and unchanged scorer calibration.\nRecord the unresolved exact loading-field requirement and stop before\nextraction or either repair; retain all three unstarted planned slots.\nPreserve prior research, production, experience, scorers and global config.\nNo E1, new skill, GEPA, model request, replacement case or commit execution.\n')
protected=r.read(O/'protected-files.json');changed=[p for p,h in protected.items() if not P.Path(p).exists() or r.sha(P.Path(p))!=h];assert not changed
conf=r.read(O/'frozen-config.json');after=r.backend.global_snapshot();assert after==conf['global_config_before'];git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=A.parents[1],text=True).strip();assert git_head==r.read(O/'initial-git.json')['HEAD']
save(O/'protection-check.json',{'existing_files_checked':len(protected),'changed':changed,'global_config_unchanged':True,'global_config_after':after,'HEAD_unchanged':True,'HEAD':git_head,'git_status':subprocess.check_output(['git','status','--short'],cwd=A.parents[1],text=True),'no_commit_created':True})
e.archive();assert not list(A.rglob('auth.json'));assert not (O/'.runtime').exists() or not any((O/'.runtime').iterdir())
patterns=[rb'sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{30,}',rb'"(?:access_token|refresh_token|id_token)"\s*:\s*"[^"\s]{20,}"'];hits=[str(p.relative_to(A)) for p in A.rglob('*') if p.is_file() and any(re.search(pat,p.read_bytes()) for pat in patterns)];assert not hits,hits
save(A/'archive-audit.json',{'status':'PASS','auth_filenames':0,'credential_pattern_hits':0,'temporary_profiles_removed':True,'formal_model_sessions':0,'unstarted_sessions':3,'frozen_prelaunch_protocol_intact':True,'policy_stop_separately_recorded_after_initial_freeze':True,'no_runtime_process_left_running':True})
files={str(p.relative_to(A)):r.sha(p) for p in A.rglob('*') if p.is_file() and p.name!='ARTIFACTS.sha256'};(A/'ARTIFACTS.sha256').write_text(''.join(h+'  '+p+'\n' for p,h in sorted(files.items())))
print('OFFLINE STOP: 0 model calls, 0 valid repairs; recommendation 证据不足; archived',len(files),'files; protected',len(protected))
