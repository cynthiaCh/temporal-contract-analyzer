# v4运行工程记录

修复前系统审计见 [审计报告](D:/projects/temporal-contract-analyzer/experiments/experience-growth/deepseek-integration-audit-20261118/AUDIT_REPORT.md)。当前独立run为 `growth-v12-ds-adapter-v4-20261118-01`。

1. 启动前监督器将策略文件写进尚未初始化的run根，触发部分初始化保护。确认无manifest、无账本、无模型请求后，保存原策略与日志到startup-incident-01，将监督策略移到run外。求解源码和冻结配置未修改。
2. M0开头连续行为FAIL触发定向检查。前7个完成case都有实际代码补丁，Gold读取候选逐文件等于Action归档，旧namespace错误0；7个Gold均有效，其中1PASS、6UNDERREACH。证据见run下engineering-observations/early-m0-failures.json。继续原队列，没有改提示、评分、预算或择优重试。
3. M0-T30唯一最终Gold的三个重入调度返回worker exit 2。候选新增onSaved(event)却未传导航参数；对应回调需要navigation.open/close，独立JS参数复现抛TypeError，另外12个调度正常返回。原probe未保留失败worker的详细stdout，因此具体原始堆栈未知。维持冻结classifier的runtime-error→invalid口径，明确闭审为final_gold_candidate_runtime_error，不改为行为FAIL、不再求解或Gold。原始收据和候选不修改；独立闭审工具核对所有冻结哈希、用量结算和唯一Gold。证据为engineering-observations/M0-T30-evaluator-audit.json。只读审计器原来假设所有invalid都在Gold前发生，现允许有明确gold_attempted标记的无效结果恰有一次Gold；这不修改评分。M0收尾7PASS、22行为FAIL、1执行无效，主准确率留空。恢复后进入D01。
4. 宿主Python原缺matplotlib，已在独立report-deps目录补齐并记录版本，PNG/PDF及CSV/JSON已导出。绘图缓存改用工作区目录；求解源码、镜像和模型环境未改变，训练未因此停顿。
5. D01三次Action均有效UNDERREACH，专家总结实际执行3请求；生成的JSON在第4条规则的一处引用中额外加入file_note字段，违反原有additionalProperties约束，严格校验拒绝。不是漏执行、写错库或namespace故障（D01此类读取错误0）。原生response-validation保留明确错误，但外层error字段为null，排查时不能只看外层error。原始输出未修补，监督器按已授权规则闭审为经验阶段执行无效、无新增经验，保留训练真实评分，不补重试。证据见engineering-observations/D01-expert-schema-invalid.json。仍需监测是否连续发生同类无效，而不预设无经验就是写库错误。
6. D02第二次Action通过，成功反思候选经AI内容审核accept，正式批准库从0增至1；D03实际协议绑定包含该经验的快照c83446aa34b2cf745c408c5501fcc4df3916e8e0acd3de5d29aaecbb659794f6。成功提炼/审核/激活/传递有真实证据。
7. D03专家输出的经验规则多写body_note。发现原生structured.py.validate不检查anyOf，而外层schema_validator.py检查并正确拒绝；原监督器只识别native valid=false，漏识别外层已有的schema拒绝，导致退出。监督器v5补齐“原始native结果有效、但冻结外层schema拒绝”的无新增经验闭审，并保存validation_failure和raw_native_valid；原始答案、冻结模型源码、schema约束、已批准经验均不改变。原v4监督策略保留，v5策略单独绑定。模型请求与Gold均未追加。
8. 为核查anyOf影响范围，在D04未prepare/未派发时短暂工程停止。84个原生标记有效的输出重放既有严格schema，发现D03及D02初次diagnosis-2两处差异；D02原validation记录已拒绝初稿，并在原stage预算内完成允许的一次correction，修正输出有效。没有发现绕过严格外层校验入库的输出，D02经验仍有效。检查无新增模型调用、无case中断，随后恢复D04。证据见engineering-observations/native-anyof-scope-audit.json。冻结原生解析器缺口保留为诊断标签限制，最终约束仍由既有严格外层校验执行。
9. D04三次有效训练失败后，专家候选通过独立AI内容审核，批准库增至2；失败总结路线也已在正式运行中有效入库。D05首个Action则在24请求内反复编译、执行和调试模型自写Java检查，预算耗尽前未给最终JSON；记录执行无效、不额外Gold或重试。javac/java正常执行，无namespace问题；其中一次探索性jshell因试图写受保护home的preferences失败，作为工具环境限制单列，没有误说全部非零返回都是模型能力。原候选与原检查不改写。证据见engineering-observations/D05-action-budget.json。
10. D06闭审后批准库增至3。针对训练端有效失败较多，核对D01–D06已有的14次有效训练验收：每次Oracle目录逐文件均等于对应Action候选，未发现旧补丁误传或写入丢失。14次有效Gold中1次PASS；同一冻结grader已有100例原始/参考/负例准入，不额外重复评分。当前受控反馈常只有验收结论、公开语法检查与unknown，不能据此编造失败原因或把隐藏测试细节回流；本轮保持已批准工作流并如实报告这一信息限制。证据见engineering-observations/training-candidate-delivery-through-D06.json。
11. D08再次出现经验规则额外字段rules，被既有严格schema拒绝；监督器v5已自动正确闭审，无新调用。D10读取public RxJS源码时使用多区间sed脚本，超出冻结的单区间闭合语法，守卫拒绝并记录执行无效；没有关闭守卫、扩展工具语法或补跑。首批10例：1训练通过、7有效失败、2求解执行无效；4批准经验、3经验阶段无效、1合法无新增（另2求解无效闭审无新增）。
12. M10前四例均实际收到含4条经验的冻结快照，任务/源码/model与M0一致，但检索选择数均为0，其中存在逐条引用校验拒绝。代表性M10-T04：模型把源码中的单引号'progress'改写成双引号，因此BO-02/BO-10的引用不再是原文，关联覆盖评估被拒；输入payload与original源码逐字一致，非传输转义或错库。维持严格证据要求，不把语义近似当原文，不强制纳入经验、不因测试结果更改提示。实际经验使用率必须与批准库大小分开报告。证据见engineering-observations/M10-citation-screening-audit.json。

13. M10-T26候选把PHP桥接操作close改为aclose，四个调度的原始回执均为unknown host call aclose。冻结worker提供close并映射到底层records.aclose，原公开PHP源码也使用close；容器ExitCode=0、OOM=false。公开host-api却仅描述next/aclose，没有明确桥接命名映射，存在文档歧义，不能全部归咎于模型能力。本轮不热改输入、候选或评分，不重跑Gold；保留执行无效、passed=null。独立闭审工具补充识别既有逐调度runtimeError存储形态（此前仅识别顶层runtime_errors），仅影响收据归档。证据见engineering-observations/M10-T26-evaluator-audit.json。关联M10-T27/T28仅恢复有证据证明未派发的阶段，保留已完成结果与剩余预算。

14. 用户提出提速后，M10全部30例完成的边界做调度修订，停止时没有D11状态/请求、在途0、未知0；没有因主动停止制造无效案例。原102个求解/输入绑定、原manifest、单例预算保持不变，新增run_growth_parallel.py继承原Run，仅把M20起独立测试并发改为4；训练仍串行。原账本存入engineering-observations/scheduler-2-to-4/balance-before.json，当前账本仅改变max_inflight_stages及对应封印，全部历史用量逐字段保留；明确修订见scheduler-amendment.json，监督器另立v6。离线验证M0/M10并发2、M20/M70并发4、每节点30个唯一任务及相同快照、账本允许4拒绝第5个并正确结算，模型/Gold调用0。当前容器低负载（两个solver约25/29MiB、各约2.5% CPU），主机16逻辑核、Docker约7.6GiB；仍监测提高并发后的超时/资源竞争。并发是可比性中的运维差异，报告单列，不声称所有节点调度完全相同。

15. D12首次Action的公开检查与训练Oracle均PASS，但成功反思输出operation=revise且failure_attribution=implementation_gap，触发原有experience_reflection.plan语义拒绝。原始JSON和schema有效，离线调用冻结校验函数复现完全相同错误；没有生成candidate-pool/success.json，也未进入AI内容审核或激活。原引擎将整个state标为execution_invalid，不能因此抹掉已有效的训练PASS。独立close_reflection_invalid.py严格核对这个特定拒绝、原始结果哈希、完整用量和未变化的经验快照，闭审为经验阶段执行无效/无新增，保留训练PASS和原始state不动；不改答案、不追加请求。D12共11请求，库仍5条。报告器区分有有效训练评分的经验阶段失败与求解执行无效。证据见engineering-observations/D12-reflection-semantic-invalid.json。

16. D14首次训练验收PASS，候选已产生，但AI内容审核的R02/R03/R05/R08原文引用无法通过冻结来源校验，未写入批准决定。JSON/schema本身有效；独立close_citation_invalid.py调用同一冻结来源校验逐条复现拒绝，扩展的只是单独无新增闭审工具，不修改正式求解或监督器绑定。候选与审核原文保留、不激活，不把审核输出accept等同于合法批准；D14真实训练PASS和16次请求保留，经验库仍5条。完整被拒规则及引用保存在D14/review/closure.json的validation_failure中，无额外模型/Gold调用。

追加过程事件见EVENTS.jsonl；每次恢复保留不可变完成收据及计量核对。一般行为FAIL不是自动调参理由。
