# 官方GEPA五候选只读机制审计

本轮模型调用0、评分器重跑0、维护任务重跑0。只读归档，不生成新技能、不改执行器/适配器/评分器/历史。审计不是独立外部模型评审。

## 主要结论

**五个候选均在train小批次严格改进门槛被拒，根本未进入val；val满分不是这五次实际拒绝的原因。** 四个候选同分，一个退步。未获接纳不等于没有写补丁：十个子任务都实际修改了代码，download四次整体通过，transfer五次都局部修复但没有相对K0的完整行为增量。

**唯一优先项：A，反思反馈适配。** 已观察到的最早信息损失是：可信评分中的有方向事件差异，没有进入反思材料，而被压成“不保持历史/界面/重试组合”。这是反馈投影的设计不足，不是评分传错或官方算法失常。D（补丁与可见验证）也有直接下游缺口；A是否足以解决它尚未证实，不强行把不同候选归为单一内部机制。

## 1. 范围、来源和保护

根目录及祖先未发现适用AGENTS.md；读取了官方源码子树AGENTS.md（仅作源码审查，不在其中执行Python或优化任务）。初始tracked diff为空、原有六个未跟踪研究目录保留；本轮新增在gepa-mechanism-audit-v1-20261106。initial-state.json保存原文件摘要，最终preservation-check.json复核。

实读PLAN、实际配置/代码、官方固定实现及安装文件、五个candidate.json/skill/review、五份实际反思prompt/原始输出、十份父train和十份子train轨迹与patch、28份原始可信评分，以及请求计量/CLI用量。报告仅作为导航，不用其归因作事实。相邻ReAct报告只帮助识别公开验证限制；本结论由本次GEPA原始证据独立支持。

固定版本：commit `8e9ae9ed063f6a0259c93db595b96953fdab0e6d`、metadata0.1.4；逐文件比对安装包与源码，见official-package-verification.json。没有网络查询、安装依赖、启动GEPA或调用反思端。所有统计脚本仅用标准库解析文本/JSON。

## 2. 官方拒绝路径，不把val天花板当作实际挡板

官方[StrictImprovementAcceptance](../gepa-official-skill-experiment-v1-20261106/official-src/src/gepa/strategies/acceptance.py#L50)比较`sum(child.scores)>sum(parent.scores)`；AllImprovements（strategies/proposal_selection.py:34–43）只保留通过此门的提案。适配器[73行](../gepa-official-skill-experiment-v1-20261106/gepa_adapter.py#L73)返回每任务整体PASS=1，否则0；不是required检查项总数，不是成本。官方[engine.py:656](../gepa-official-skill-experiment-v1-20261106/official-src/src/gepa/core/engine.py#L656)在无选中proposal时直接return，之后[662行](../gepa-official-skill-experiment-v1-20261106/official-src/src/gepa/core/engine.py#L662)才全val评估。

以下P1–P5是审计别名，完整archive key、文件路径、父子job及日志行见selection-trace.json；每个父版本都是K0/pool0，不是上一个被拒子版本。

| 候选/archive前缀 | 父K0：download/transfer | 子：download/transfer | 检查gained/lost | 拒绝事件（official-events.jsonl行） | val/pool |
|---|---|---|---|---|---|
| P1 / 611d52731327 | 1/0 | 1/0 | 0/0 | 16：sum 1→1 | 均未进入 |
| P2 / ae63846ca3f8 | 1/0 | 0/0 | 0/2 | 31：sum 1→0 | 均未进入 |
| P3 / 43fa4e58ac2a | 1/0 | 1/0 | 0/0 | 46：sum 1→1 | 均未进入 |
| P4 / 8d254922f594 | 1/0 | 1/0 | 0/1 | 61：sum 1→1 | 均未进入 |
| P5 / c0cec3d4e909 | 1/0 | 1/0 | 0/0 | 76：sum 1→1 | 均未进入 |

P1/P3/P5的逐案例整体结果、检查与明确断言均无得失；没有出现“通过任务换成另一任务但仍1/2”。P2在transfer丢失重试检查（9/10→8/10），download丢失等待检查（8/8→7/8），整体1/2→0/2。P4整体仍1/2，但transfer9/10→8/10，丢失同一个重试检查。三个检查损失项次各对应一个明确断言损失，不算六个独立事故；没有检查gained，不用总分抵消。

只有seed做过val，见[official-events.jsonl:2](../gepa-official-skill-experiment-v1-20261106/official-events.jsonl#L2)，两例均1。所有child评估只在train；最终[official-result.json](../gepa-official-skill-experiment-v1-20261106/official-result.json)仅含K0，best_idx=0。五个被拒proposal仍保存在candidates及on_proposal_end日志，不在官方pool不等于被删档。merge关闭。

val满分仅是**反事实的最终选择限制**：即使某提案先通过train门、再追平val，官方最高均值/最早索引规则仍可能保留seed。但这里没有任何提案到达该阶段，不能说它阻止了本次五候选。严格0/1指标确实忽略P4局部损失，却没有把一个整体改善候选误拒；不应为保留失败候选放宽评分。

### 缓存、波动、预算及适配

- cache_evaluation=False；11次evaluate批次均实际启动对应新job，无评分缓存命中。供应商缓存输入token是上下文缓存，不是复用任务分数。
- K0五次transfer分别8/10、9/10、8/10、9/10、8/10，整体均0；download五次均1。P2/P4的配对损失真实存在，但没有模型采样种子或更多重复，不能认定由技能导致；也不能用这种波动抹掉损失。
- 22个优化metric call=22次真实优化任务；五个候选都完整完成父/子评估，未因预算截断。剩余2不足最坏六次预留，才停止下一轮。5个反思请求无重试、无工具；未触发硬上限。预算限制了搜索机会，不是五次拒绝的判定依据。
- 所有技能通过边界审查并逐字节送到对应执行prompt；无效技能0分分支未发生，未形成适配门偏差。原始评分路径、case_id、job关联、实际prompt、用量均校验一致，无跨job/过期结果证据。
- 原生结束callback写`total_iterations=4`，但有五组proposals。这是[engine.py:1153](../gepa-official-skill-experiment-v1-20261106/official-src/src/gepa/core/engine.py#L1153)直接返回从-1开始的state.i，而各轮日志用state.i+1（state.py:325、engine.py:992/1000）。按事件重建是5轮，不能把该字段误当4次反思；不影响metric22或拒绝。

分类：严格改善、train前置、stateless父反思、保守预算与无merge均是**官方正常行为/冻结研究控制**；反馈不定向、正向保留关系未结构化是**适配表达不足**；模型内部理解和技能造成波动属于**证据不足**。未发现分数传输或官方API实现错误。

## 3. 五条变化链：文本不等于理解，也不等于动作完全没有发生

完整逐候选链保存在[candidate-mechanisms.csv](candidate-mechanisms.csv)：反思归因、实际证据、步骤增删、动作、判断、补丁、验证、行为与精确来源。反思模板要求只返回完整技能（REFLECTION_TEMPLATE.md:19），五份输出没有独立失败原因说明；CSV明确将其写作“文本关注点”，不把推测当成模型确认的原因。

| 候选 | 有依据的文本变化 | 实际动作与首个可定位下游缺口 |
|---|---|---|
| P1 | 每effect五问；启动、retry和cleanup重入；回调前后追踪 | transfer子job e-3df2db08080046ff events24/28确有retry与同步hide→detach→导航。retry仅检查队列/notice，没有旧pending跨retry；导航未观察旧源随后新输入的history。只改progress。 |
| P2 | 新S4列listener→start→handle→ownership→cleanup；polling同步调度 | e-51563b1aff074e6e events9读全模块、18/20测反序/hide，但未公开whole-handoff判断。download e-0f86af18a30343df events18仅语法，21承认未做React行为检查；patch在pending前清loading，丢失等待状态。 |
| P3 | 修改前写effect contract；whole call stack；release前接纳工作 | e-b12b0d2631224d8c events16在recordProgress回调内hide、验证晚完成history/display，确有新动作；但仍未检查启动导航后旧源接纳或跨attempt完成，patch仅progress。 |
| P4 | 强调producer/cleanup内部transition和不任意削弱失败断言 | e-7bafa6c497b04619 events14失败、16修订后成功、19同步hide成功后尾随git失败。telemetry断言修订与源实现一致，不能直接判为逃避验证。仍缺关键两种组合关系，丢失父retry检查。 |
| P5 | 显式事件表、事实/要求/假设/未知、外部调用返回后重新核对 | e-591a6553e0bc4b52 events18确有hide→detach导航且测试新源继续输入；没有对旧源新输入的history断言。16的retry只查末帧/queue shape。公开记录未见事件表，不能证明内部没有想过。 |

五个transfer子补丁都只改progress.js，形态均为监听提前和单watcher内的到达序号；未修改其他跨attempt/启动交接路径。它们修复了局部同步初始帧/乱序显示，却没有相对K0的行为增量。download四个子job通过，P2失败，不能把所有候选写成“完全不修复”或“只回答问题”。十个子job都有实际diff。

### 不能过度归因的判断

公开说明和补丁支持它们理解了“先订阅再start”及“到达顺序不等于decode完成顺序”；不支持它们已经形成正确完整的访问/尝试/输入接纳/完成有效性契约。源码被读取不等于理解正确；这里也缺少足够公开记录来确定“正确判断但纯编码失误”。

可见源码本身支持进一步查证：[README:8](../gepa-official-skill-experiment-v1-20261106/materials/transfer-progress-composition-v4-vanilla/input/README.md#L8)区分visit和attempt，[queue:11](../gepa-official-skill-experiment-v1-20261106/materials/transfer-progress-composition-v4-vanilla/input/src/queue.js#L11)区分记录和显示，[transfer:10](../gepa-official-skill-experiment-v1-20261106/materials/transfer-progress-composition-v4-vanilla/input/src/transfer.js#L10)有调用后继续执行，[progress-source:8](../gepa-official-skill-experiment-v1-20261106/materials/transfer-progress-composition-v4-vanilla/input/src/progress-source.js#L8)说明同步detach回调。它们已获得这些文件/片段，不能仅归因源码不可见。

原始可信评分的失败关系更具体：启动内导航后，旧源的新输入继续进入历史；同visit重试后，早先attempt的延迟帧进入当前显示。这里是研究侧对原始评分事件的概括，不把隐藏expected数组或修复方案写进执行技能。逐job原始JSON位置见selection-trace.json的parent_score/child_score。

模型称“retry/reentry检查通过”通常有对应工具输出；问题是测试只覆盖其驱动的变体，不是输出虚构。P4末个复合shell退出129，但前面的Node输出已确认成功；反过来仅node --check成功也不能算pending状态行为通过。没有证据把全部自测失败视为真实产品错误：多次telemetry空数组预期与“先订阅后另一个consumer启动源”的实际事件冲突，修订预期有源码依据。

技能并非只增加“更仔细”：P2/P3加入whole-handoff，P5要求事件表，均可执行；部分又是K0已有动作的细化。P2/P3删除了K0对rollback/permission withdrawal等不适用例的显式例举，未证明影响了这些任务，也不能假定长文本始终更好。

## 4. 反馈适配器：实际发送了什么，损失了什么

核对的是[实际反思prompt](../gepa-official-skill-experiment-v1-20261106/reflections/call-01/prompt.md)，不是目录中“可读取”的材料。五份均与on_proposal_end.prompts逐字节匹配，原始输出也完全匹配。每份反思绑定本轮父train的两个新job；没有使用被拒子job、val或test轨迹。

### 存在且正确关联

原任务、当前K0技能、冻结源码RAG上下文、工具命令/退出码/真实输出、实际diff、是否交付、整体评分、失败区域的自然语言描述和未知项都在消息中。不是仅给“0分请改进”。五份实际prompt依次70,717、56,559、53,990、66,246、67,336字符；任务/源码/diff均与相应父job一致。技能送达、边界审查和接口解析没有失效证据。

### 没有传入或表达不足

关键投影在[gepa_adapter.py:12](../gepa-official-skill-experiment-v1-20261106/gepa_adapter.py#L12)、[19行](../gepa-official-skill-experiment-v1-20261106/gepa_adapter.py#L19)、[45–50行](../gepa-official-skill-experiment-v1-20261106/gepa_adapter.py#L45)：它把失败检查翻译成“未保持required combination”或“未保持retry record/notice/current-display combination”，却不说明哪个副作用多/少、是在新输入接纳还是既接纳结果完成、发生于哪个顺序边界。原始评分包含这些事件事实，但`feedback()`没有读取/投递schedules trace。故实际是失败区域定位，而非完整行为差异。

没有结构化的已通过effect/场景保留表；所有原通过项损失count均0，但这些count相对于“未修改源码”校准，不是相对当前父技能（runtime.py:70–74）。父K0在P2/P4已正确保留retry的事实没有作为明确正向评分证据传入，只能从完整父diff/工具自测间接理解；缺表不等于相关代码完全缺失。反思也没有收到后续被拒子候选的退步，这是本配置stateless+只反思所选父的正常行为，不能把“不自动记住子失败”说成适配器传错job。

Agent的公开行动说明/最终自述没有被转发（非内部思维链）；因此反思端不能直接比较公开契约声明与补丁落实。visible_validation也只是正则标签：git diff --check会被归入，复合命令可能有成功Node片段和失败git尾部。退出码/原输出仍在，未伪造pass，但需读者自行区分格式、语法与行为验证。

实际截断共9处，全部是缺少.git导致的冗长git输出；没有命令文本截断、没有diff截断，未发现必要源读取因该5000字符投影而丢失。不能把失败主因写成“源码被截断”。工具输出和visible_validation正文还被重复转发，较长文本并未补足评分关系的方向性。原材料的来源RAG本来不完整，但有路径/行号与继续阅读提示。

未知项字段正确警告读取不等于理解、评分不能唯一隔离原因，没有把某个未证实根因写死。上述反馈信息不足是可定位设计缺口；是否因此导致候选遗漏关系仍需控制实验，不能靠本次审计宣称因果。

## 5. 原始评分、用量及45次非零命令复算

逐案例检查和断言gained/lost见selection-trace.json；raw-recalculation.json由原始oracle输出重建，不调用评分器。request meter的PostModelRequest.token_usage逐请求相加，与CLI turn.completed及归档usage逐项一致。正式28次维护、5次反思=33个CLI会话；底层请求187（182执行+5反思），不等于优化metric22。最终test6次不计入GEPA metric；14次历史无模型评分校准不算维护Agent或模型调用。

| 阶段 | 任务/CLI会话 | 底层请求 | 输入token（含缓存） | 缓存输入 | 输出token | 含评分秒 | 工具调用 |
|---|---:|---:|---:|---:|---:|---:|---:|
| train父子执行 | 20/20 | 134 | 2,823,966 | 2,507,648 | 37,634 | 1311.8 | 143 |
| seed val选择 | 2/2 | 13 | 264,927 | 255,872 | 3,784 | 122.2 | 11 |
| 候选生成 | 0/5 | 5 | 139,192 | 58,880 | 4,527 | 145.6 | 0 |
| 最终基线test | 6/6 | 35 | 680,092 | 611,840 | 7,377 | 314.6 | 30 |
| 总计 | 28/33 | 187 | 3,908,177 | 3,434,240 | 53,322 | 1894.1 | 184 |

token与请求可逐原始receipt复算；“含评分秒”只能重新累加原monotonic用量收据，不能从存档重建计时器本身。脚本另从job result started/completed UTC时间重算CLI墙钟，口径不含后续评分。没有美元账单，不推算价格。逐提案的生成/父train/子train/val成本另见candidate-costs.json。总计约1894.1秒是阶段时间和，不是冻结到完成的墙钟35.7分钟。

| 非零命令分类 | 次数 | 判定与范围 |
|---|---:|---|
| 正常搜索无匹配 | 4 | rg --files没有测试/AGENTS匹配；不表示工具故障 |
| 候选自写断言失败 | 5 | Node实际执行并抛ERR_ASSERTION；分别保留后续修订与输出，不等同可信任务失败 |
| 固定环境：无.git | 28 | git diff/status不可用；若在复合命令尾部，不抹掉之前检查的真实成功 |
| 固定环境：依赖可用性失败 | 3 | 两次明确缺模块，一次ls探测退出2且stderr被抑制，不能确认具体缺哪一包；可见挂载验证受限，可信评分正常 |
| 其他：JSX检查方式不适配 | 2 | node --check不能直接识别.jsx；不是业务断言失败 |
| 其他：检索路径/通配符问题 | 3 | rg同时输出有效匹配但指定不存在test*/其他路径，返回2；不能按零源码读取处理 |

合计45。逐条原命令、退出码、完整输出、job及事件行见command-classification.json/csv。没有把它们统一记作容量或基础设施异常；正式CLI均退出0、trusted calibration均PASS、评分无runtimeError。最终仅K0基线6/6，新B未执行，不能将其当第二组通过或演化收益。

## 6. 唯一优先项、替代解释和证伪

**选择A：先让反思收到当前父任务的有方向关系证据和已通过保留事实，而不是先增加通用提醒。** 在数据流上，这是最早能由当前归档直接证实的表达损失：原始评分事件→反馈摘要。五个反思都得到相同笼统失败区域而产生更具体的通用步骤，后续执行仍只验证邻近变体。该链支持先做低侵入、可证伪的反馈实验，不证明A是所有失败的唯一根因。

- 暂不选B：五个技能都实际送达且增加了可执行步骤，多个子job真的驱动了同步重入；不是单纯技能未加载。覆盖不全确可能含动作落实问题，但“未见事件表”不能证明内部没检查。
- 暂不选C：局部判断正确，完整关系判断缺少公开证据；没有足够材料把“解释错误”与“正确理解但未落实”分开。仅凭读过源码不能下结论。
- 暂不选D：自测覆盖确实不足，是直接下游失败证据；但目前反思没有收到“哪种输入/副作用/先后关系出错”的具体差异。在补新验证前先检验这个更早投影，且无需改执行器或给出案件专用修复。若A完整送达仍不改变验证/补丁，下一步应转D/B，而不是反复加反馈文本。
- 暂不选E：当前官方拒绝与冻结0/1目标一致；val天花板未实际介入。改成检查项总分或允许同分晋级会改变问题，不能解释为什么补丁没满足完整行为。新保留数据必须有区分力，但它是下一轮共同准入条件，不作为本轮候选失败的唯一原因。

下一轮最小改动见[NEXT_EXPERIMENT.md](NEXT_EXPERIMENT.md)：只比较原feedback与当前父评分事件的源绑定定向投影，保留官方算法/模板/技能边界和执行系统。不发布新技能，不把隐藏ID、原始expected数组、参考修复或补丁步骤传入技能。

能削弱A解释的结果：定向反馈确实送达，候选也明确要求对应关系，执行仍选同一窄变体；或能确认完整契约正确而补丁实现错。那应转向B/D。若仅多写文字、没有正确动作和整体行为收益，也不算A有效。若val预检全满分或新保留来源不满足则停止，不能声称检验了有效性。

## 7. 未知、未证实关系和下一轮状态

本审计不能恢复模型内部思维；无法确认每个候选是否曾形成正确完整契约。只有一个child采样/每提案两例，父局部行为又波动，不能把P2/P4损失严格归因于技能。没有重新执行任一补丁或测试，无法追加新输入行为证据；我们核查的是当时实际工具输出与可信评分。

现有暴露登记不能证明至少五个新的独立项目可供val/test；已审查94条bench元数据中“注册时无结果”并非今天无暴露。NEXT_EXPERIMENT因此有明确离线来源准入门，尚不能启动。不能通过挑选本次赢家任务、预跑test或发现满分后换题来制造收益。

因果缺口不是靠再读REPORT能补齐。最少需要未来在相同执行系统下的定向反馈对照，观察新增关系是否真的进入检查、断言和补丁；若需进一步区分C/D，还需有公开、简短的契约结论与源码/实际检查引用，不能把模型自述当最终证据。

## 新增产物及复核

必要交付：AUDIT.md、candidate-mechanisms.csv、selection-trace.json、NEXT_EXPERIMENT.md。辅助：audit_stats.py（只读统计）、write_audit_doc.py（文档渲染）、raw-recalculation.json、feedback-audit.json、command-classification.json/csv、candidate-costs.json、official-package-verification.json、offline-validation.json、recalculation.log、initial-state.json、preservation-check.json。全部在本目录。

离线最小验证包含28个launch/result/score关联、五次父子分数/检查/断言复算、五份实际反思prompt/输出一致、所有tool/diff与父job事件对齐、技能逐字节交付、provider与CLI用量相等、45命令完整分类、官方预算与pool核对、原输入保护。没有为审计启动模型、评分器或官方优化器。

建议Git commit subject：`research: audit GEPA rejection paths and feedback projection`

Body：`Reconstruct five proposal mechanisms from raw prompts, jobs, patches and scores. Classify shell failures, reconcile costs, and document a feedback-only follow-up without changing prior experiments.`
