# F0/F1官方GEPA反馈投影对照：离线实施与准入停止报告

结论：**离线投影实现与验证完成；新保留来源不足，依照预定门停止，未启动两条正式GEPA搜索。** 不能据此判断假设有效或无效。

## Task 1：来源及开跑条件

读取审计、五候选CSV、选择轨迹、下一轮草案、原计划/实际配置/适配器及原始归档。重新检查official-events：五个旧候选均在train严格改善门被拒（四次sum1→1、一次1→0），没有child进入val，只有seed被评估。val满分不是这些实际拒绝的原因。证据见historical-rejection-check.json及原日志行16/31/46/61/76。

核验当前94条bench登记、2条本地登记，合并同源unit为47；共享结果索引2015条，封印hash验证通过。47/47个unit均有positive token usage或agent_started收据证据。另一个本地swe-tempoc目录只有24个已包含的case，没有新来源。不能把不同版本、不同模型或“创建时无运行”标签当作当前未暴露。

特别是此前待确认的handoff-redirect已有2次运行；metrics/audit/trace/error四个新观测任务分别有3/1/1/1次记录。source-verification.json逐unit保存收据ID、模型、用量、来源JSON pointer及manifest/验证文件摘要。部分原始原件不在本机，因此明确采用封印共享收据作为保守暴露证据，不冒充重新读取全部原日志。

两例已暴露train保持原冻结起点和材料。符合新来源要求的val/test数均0，无法形成至少2/2/3的完整划分；没有用已暴露任务替代，没有新编业务要求或评分。现成验证文件作了清单与摘要核验，没有重跑评分。**来源门不满足，正式准入为BLOCKED**。

## Task 2：信息变化、离线验证及实际执行量

F0旧函数正文原样保留。恢复排序JSON丢失的原运行时检查顺序后，10条真实反思记录及5份完整prompt完全复现；详见F0_REPLAY.md。F1只改变反思反馈投影，外围模板、K0、公共任务/源码RAG/AST/题库及评分都未改。

F1恢复了三类具体关系：

- 源启动并产生进度、导航到另一个资源、旧源随后发出新输入，该新输入仍进入旧操作历史：方向为额外记录；区别于导航前已接纳工作晚完成。
- 旧操作已有pending decode，替换操作先显示，旧结果随后更新当前显示：方向为归属不符/顺序错误，记录与显示分开。
- pending后的快照有retry、尚未交付却没有被评分的等待指示，后续仍能完成：方向为缺失；不把简短任务未定义的flag语义编成确定业务规范。

这些是从研究侧评分事件和候选可见材料绑定得到的事实/比较，不是参考补丁或确定根因。原始trace没有call-return标记时保留调用栈未知；原因假设明确附证据且未被确诊。源路径/行号/摘要和不透明证据key可追溯，隐藏断言名称、oracle标识、fixture expected数组及修复步骤不进入反思消息。执行端最终只应接收审查后的技能，本轮没有新技能。

20个归档train job离线核验得到19条有方向观察和181项“当前这次执行已通过”的保留事实。这不是19次新模型成功或181个独立任务。相对未修改源码与相对父执行的比较对象被明确区分；未提供父记录时返回未知，不冒充零丢失。使用审计中的精确父子配对另行核对三项次损失；过期同case父记录也会被拒绝。

两组完整反思输入均以72,000 Unicode字符为上限：

| 原反思批次重放 | F0字符 | F1字符 |
|---|---:|---:|
| 1 | 70,717 | 71,966 |
| 2 | 56,559 | 62,052 |
| 3 | 53,990 | 60,042 |
| 4 | 66,246 | 65,574 |
| 5 | 67,336 | 67,561 |

没有新增截断或填充。原F0的工具前缀限制保持相同且显式标记：实际五份历史反思批次有9处git冗长输出截断；全部20个job的单记录离线例子共有21处（18处git相关、3处拼接源码读取，后3处只在child例子）。没有命令/diff截断。研究侧原全文保留；截断前缀不代表完整阅读。新方向性事件本身不截断，超总上限直接阻塞模型请求。精确模型token离线未知，未调用模型或伪造token计数；实际provider token新增0。

负例核验包括val/test、跨case、跨arm、跨candidate、错误分数、未验证结果和同case过期父job拒绝。技能机械筛查及强制哈希绑定语义审查可执行；仅改名的答案不会自动获得执行许可，但机械筛查不保证所有语义泄漏都能自动识别。两臂12任务/3反思、底层PreModelRequest守卫及最多18次test摘要去重均做无模型容量模拟。模拟计数不计为正式用量。

复用官方0.1.4/commit8e9ae9e的原隔离环境，111个安装Python文件与固定源码一致。只使用官方纯prompt renderer；**gepa.optimize调用0次**。official_adapter.py实现两投影的协议桥接与准入前置拒绝，执行端由原路径注入；没有启用模型端点或完成live工作区/交错调度联调。start.py明确拒绝本次未准入尝试，不能自动解锁。

最新用户预算已记录：每臂12次维护/3次反思，共24/6；最终3例×至多3种不同技能×2重复≤18。旧草案2次反思/9次test没有被沿用。计划两例val的官方初始化仅需2任务/臂，在12内；但本轮没有合格val，所以实际初始化0，不缩减划分来勉强开跑。

## Task 3：是否转化成技能与修复收益

| 本轮正式项目 | 实际值 |
|---|---:|
| 优化维护任务、metric call | 0 / 0 |
| 最终test任务 | 0 |
| 执行/反思CLI会话 | 0 / 0 |
| 执行/反思底层模型请求 | 0 / 0 |
| 新候选生成/接纳 | 0 / 0（搜索未启动） |
| 新输入/输出token | 0 / 0 |
| 评分器重跑 | 0 |

F0/F1尚无K*，不是已选择K0；没有因此启动六次基线测试。arms/中的NOT_STARTED档案为空状态说明，不是模拟正式轨迹；examples/与paired-reflection-inputs/明确是历史记录的离线样例。train/val/test行为成绩为未评估，不记录为0分失败。没有因F1包含更多信息就宣称有效，也没有把旧候选改算本轮F0结果。

“有方向、源绑定的反馈是否帮助GEPA生成针对实际失败关系的技能候选？”——**尚未检验**。本轮只验证信息确实恢复且可追溯；没有新反思输出或候选可供判断。

“这种变化是否转化成修复收益？”——**尚未检验，没有新增修复收益证据**。来源不足造成准入停止，不是该反馈假设被否定。

下一步先补足可审计、无跨组同源暴露、已有可信行为验证的新保留来源；当前旧案例只能开发诊断。另开实验目录冻结具体case、材料、两臂交错顺序和完整执行协议后，才可测试该假设。不能预跑test挑选失败任务、放宽官方接纳规则或扩大本轮预算。

## 交付与保护

PLAN、gepa-config、F0/F1实现、官方适配协议桥、guards/request_meter、原K0/BASE/END/反思模板、source-verification/split、offline-validation、原始记录的F0/F1对照、private研究索引、lengths/information-delta、historical-rejection-check、environment-lock、formal-ledger、summary及本报告均在本目录。

所有历史档案/生产文件、原技能和评分器保持不变；未新装依赖，未创建提交。保护结果另见preservation-check.json。离线接口检查不能代替尚未执行的端点、完整调度或效果验证。

Git commit subject：`research: add source-gated GEPA feedback projection control`

Body：`Preserve F0, implement directional F1, and verify archive replay, provenance, leakage boundaries and budgets offline. Record the failed holdout-source admission and zero formal model calls without altering prior studies.`
