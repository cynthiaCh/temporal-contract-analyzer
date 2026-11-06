# U1技能开发集内补丁效果实验

本轮没有观察到F1修复目标行为的收益：K、F0、F1整体通过均为0/2，U1“切换后旧源新输入被额外记录”也均为0/2。F1两次保住了retry，但第二次丢失普通有序帧显示；不能用这项得失相抵后宣称有效。独立人工复核仍未完成。以下是已暴露开发案例的可信行为评分及未盲化轨迹分析，不是独立泛化、显著性或稳定性结论。

## Task 1：固定候选、来源与风险

根目录及祖先未发现AGENTS.md。本轮先检查git状态/diff并保存[initial-state.json](initial-state.json)：HEAD `d4510f5edba761fc56adfedb990c68eb3507d912`，tracked/staged diff为空。已阅读上轮PLAN、REPORT、U1候选/原始证据、review.csv及条件映射；未把代理审查写成独立人工复核通过。

选择严格遵循用户规则：由上轮private-label-mapping.json筛选unit=U1、各自条件最小sequence，不看代理评价、长度或预期。仅取raw-answer.txt的skill字段；不交付change_notes，不修订、拼接或换候选。

| 条件 | 固定候选／来源 | 父版本SHA256 | 技能SHA256／字符数 |
|---|---|---|---|
| K | K0，原U1父技能 | `6f82762517c6e604c48903324e9a62123cccf386246577f44d7488fdd0cab024` | `6f82762517c6e604c48903324e9a62123cccf386246577f44d7488fdd0cab024`／2836 |
| F0 | C8ec8c3ddfc；上轮r03、全局第3份、U1-F0首份 | 同上 | `ae66aee3aa25bfe999adf0fab11cc1ffe3787b06d8f83ade9ef6c444188c3360`／3699 |
| F1 | C4509bd4e1d；上轮r04、全局第4份、U1-F1首份 | 同上 | `5e2c82609d0f9ed905bf32c21895f6e9ed385dde5252cc2d8804c001a5a5c151`／4293 |

完整来源及原输出摘要在[candidate-sources.json](candidate-sources.json)。U2没有被使用。技能副本为[K.md](K.md)、[F0.md](F0.md)、[F1.md](F1.md)，均与来源原文相同。

[RISK_REVIEW.md](RISK_REVIEW.md)没有发现明确泄漏、案例答案/参考补丁、强制串行化/全面取消或把维护任务替换为问答的阻断项。但此前的排序风险**确实位于所选F1**，原句为“Do not infer order from decoded values or invent a frame schema.”（F1.md:11）。本案task未给出帧内排序字段，README/producer也没有这样的schema，故未确认它明显违背本任务；跨项目可能过宽，原句保持并列风险。未确认阻断不等于独立复核通过。

本轮仍是历史job `e-5b07bf1156dc48d0`对应的已暴露U1开发案例。起点使用它的**原冻结input**，没有接续它的9/10补丁。[diagnosis-origin-check.json](diagnosis-origin-check.json)确认与原failure-mechanism-diagnosis的input inventory和task SHA一致。历史9/10仅用作第三种研究比较锚点，不冒充本轮起点或配对K。

## Task 2：冻结输入、实际执行与产物

[PLAN.md](PLAN.md)、[protocol.json](protocol.json)、[schedule.json](schedule.json)在正式维护前冻结。K完整prompt与历史U1 job逐字节相同，F0/F1只替换temporal-contract-skill块；公共prefix/suffix、task及输入摘要见[input-control.json](input-control.json)。三份完整prompt为[K.prompt.md](K.prompt.md)、[F0.prompt.md](F0.prompt.md)、[F1.prompt.md](F1.prompt.md)，分别18220/19083/19677字符。

公共材料复用原官方实验归档的common、BASE、END：准确原任务、原源码RAG和固定五题字节不变，不重检索、不添加诊断B/C证据包。原执行没有交付AST，本轮也没有。执行Agent不获得历史轨迹、评分、反馈、代理审查、参考补丁或研究侧evidence-key。每次从相同原始input创建独立工作区；namespace不挂载研究目录、原仓库、同胞job或隐藏评分器。

固定gpt-6-sol/low、600秒、workspace-write/approval never；原自主Codex Workbench/IsolatedWorkbench路径，不接入ReAct控制器。CLI版本0.164.0-alpha.11.1，默认可见node v22.23.2、另提供/runtime/node16 v16.20.2，可信评分使用v16.20.2；原路径如此，本轮保持。未新增显式输出token cap。Pre/PostModelRequest只记账并拦截失败传输的自动重试，不观察工具内容、不注入行动或Stop续行。模型自己的正常工具循环不算重试。

调度种子2026110607只用于排列，不是模型采样种子：

| 顺序 | 条件／重复 | job ID |
|---|---|---|
| 1 | F1/1 | e-520c65edec8345b8 |
| 2 | K/1 | e-f0e93e01b4a44a40 |
| 3 | F0/1 | e-716dc21ef6624f21 |
| 4 | F0/2 | e-4d4d62a8fee44d56 |
| 5 | K/2 | e-fc178acbb24743fc |
| 6 | F1/2 | e-3cd151bbb1964f7b |

六次都正常结束并获得可信评分、参考校准PASS。实际维护CLI6、底层模型请求55（55个完成回执）、工具54，其中shell47/file_change7。额外反思、技能生成、GEPA、模型预跑、自动重试、补跑均为0。六次结束后才运行比较脚本。

### 单列的运行器中断及处理

第一槽结束后，原run.py的freeze错误地把会正常更新状态/用量的manifest.json也作为不可变文件，因而在第二槽启动前抛AssertionError（[execution.log](execution.log)）。这是一次调度器检查错误，不是模型失败或行为结果。

原run.py/protocol和首槽结果均保留。另存[runtime-correction.json](runtime-correction.json)、[continue_remaining.py](continue_remaining.py)及其冻结摘要，只豁免六份**操作状态清单**的整文件摘要；task、input、权限、模型、超时、case、job ID、prompt/report hash仍逐项核对，其他冻结文件保持原摘要。显式继续尚未启动的五槽，首槽不重跑，总计仍为6，顺序/技能/输入/评分不改（[continuation.log](continuation.log)）。这项实施偏差完整披露，不能称调度器全程无异常。

[preflight.json](preflight.json)保存零模型离线检查；六次使用原可信评分流程，各自后处理校准与原始stdout在trials归档。评分与Agent工作区隔离。未改评分器或评分规则。

### 新增归档

每个`trials/reports-experiments/<job>/jobs/j-001/`保存实际prompt、events.jsonl（完整工具输出）、stderr、answer、changes、patch.diff、workspace、trajectory-index和model-meter；对应evaluations保存可信原始评分/校准。入口还有candidate-sources、风险核查、公共材料/技能摘要、调度及invocations/results。

离线产物包括[behavior.csv](behavior.csv)、[costs.csv](costs.csv)、[summary.json](summary.json)、[score-excerpts.json](score-excerpts.json)、[mechanism-review.csv](mechanism-review.csv)、[nonzero-commands.json](nonzero-commands.json)、final-validation.json。analyze/evidence_extract/verify只读已归档输入、输出派生统计，无新依赖或模型调用。

## Task 3：行为结果与明确参照

全部六次实际修改源码并验证，warm初始进度项均通过，没有只回答辅助问题；但整体维护任务因保存义务失败而未通过。required计数不包含独立forbidden字段约束；后者六次均保持通过。

| 条件／重复 | 整体PASS | 目标场景／新输入历史断言 | required通过 | 失败项 |
|---|---|---|---:|---|
| K/1 | 否 | 否／否 | 8/10 | 目标、retry旧尝试显示 |
| F0/1 | 否 | 否／否 | 9/10 | 目标 |
| F1/1 | 否 | 否／否 | 9/10 | 目标 |
| K/2 | 否 | 否／否 | 8/10 | 目标、retry旧尝试显示 |
| F0/2 | 否 | 否／否 | 8/10 | 目标、retry旧尝试显示 |
| F1/2 | 否 | 否／否 | 8/10 | 目标、普通有序帧显示 |

原始评分在每行results.json.raw_score路径；score-excerpts.json的每个job对应`/schedules/start-switch-admission`保存完整事件/断言。六次都出现同一方向：step8切换B；step16旧A新emit；step17旧A额外audit；step18/19才detach/cancel。目标display/owner/最终cleanup通过，不能代替历史接纳通过。

**参照1，同一冻结未修复起点：**其原通过检查仅telemetry及“不增加byteCount”的forbidden约束。六次均未丢失这些原通过项，也未丢失起点已通过断言；所有not-emitted为空。这不是说原应保持的全部业务都没退步——该坏起点在很多必要行为上本来就失败。

**参照2，同重复K：**

- 重复1：F0和F1均新增通过retry-preserved及其same-visit-no-rollback断言，无配对K通过项丢失；目标均无改善。
- 重复2：F0与K检查/断言相同；F1新增通过retry，但丢失frame-in-order及ordered.visible断言（实际显示[1,3]，要求[1,2,3]）。两者都8/10不能掩盖这个新损失。

**参照3，历史K0的9/10结果：**F0/1、F1/1没有额外通过项损失；K/1、K/2、F0/2丢失retry；F1/2丢失frame-in-order。历史结果不是本轮配对K，不用它替代K复测。全部checks/assertions gained/lost/not-emitted完整列于summary.json，各类参照分开。

### 从技能到动作和补丁：实际证据

以下路径均指本轮对应job的`jobs/j-001`，事件编号为events.jsonl行号。common中已经交付的源码也算获得证据，未额外cat不能推断未读。没有从文字自述推断内部理解。

**共同源码依据。**原task要求保留navigation/audit；README:8–26区分visit、attempt、history/display及同步宿主回调；queue.js:11–15无条件记录、按current visit显示；progress-source.js:24–30同步start/emit；transfer.js:12–16在watch返回后才取得stop；panel.js:19–26在enqueue返回后才登记或取消handle。这支持查清“owner变化”与“取消/清理已发生”是不是同一边界，不能只按最终取消推断中间新输入有效性。精确评分顺序来自可信研究评分，不作为新增任务要求交给Agent。

**F1/1，部分区分落实，但边界用错且验证漏窗。**

- events:9实际读取transfer/progress/queue/panel/producer/telemetry/README。patch把signal传给watch；workspace/src/progress.js:6在输入时检查aborted，但:9对已接纳结果仍record；transfer.js:13–16对display再加abort检查。因此有可观察的“新输入 vs 已启动完成”分离，不能说技能完全未落实。
- 该guard只知道signal是否aborted，不能保证导航后但外层尚未返回时已失效。可信trace明确额外A输入和audit先于detach/cancel；源码中stop赋值/handle发布在同步start之后。它与观察到的漏窗一致，原trace缺调用返回标记，不能声称已直接记录全部内部调用栈。
- events:25真实测试了detach回调select、warm show回调hide，但fresh emit是在外层select/hide返回后；events:23覆盖warm/reverse/retry等，未驱动“启动中切换→外层返回前旧源新输入”。S5/S7要求的组合关系没有在可见工具轨迹中获得完整验证。
- 可信评分9/10、目标audit失败；既有late-after-hide、组合history/display通过。retry相对K改善，不能算目标修复。

**F1/2，区分迟到完成的一部分，但增加过强显示过滤。**

- events:9读取transfer/notice/README，其余producer/consumer代码已在common提供；events:25打印最终progress.js。最终:8仍无条件record，:9用active与`sequence === latest`限制receive，:22–24在stop时才改active。没有可见的启动中owner失效接纳检查。
- events:16/18实际输出显示hide后迟到结果仍进history且不显示；events:21通过hide/retry迟到完成与warm show→hide测试。说明正确处理了某些已接纳路径，不能把所有判断都写错。却仍没有驱动目标startup导航新输入窗口；Node16 events:27仅同步smoke。
- :9比较“最后到达”的序号，而非“已显示”的序号：当更晚包已到但未完成时，正常更早完成的中间帧也被抑制。可信`frame-in-order/ordered.visible`实际[1,3]而非[1,2,3]，对应明确新退步。无全局排序队列、串行解码或全面取消补丁；这是每监听器的过强latest-only过滤。
- 无证据把该退步因果归于F1那句decoded-values约束：同一技能第一次并未使用相同过滤。排序风险保留，不能事后凭结果断定唯一成因。

**F0/1，修到邻近retry关系，仍漏目标。**events:9读取相关模块；queue.js:10/15新增progressAttemptId匹配，避免同visit旧attempt的迟到display，保持record。events:16验证reversed/retry/reopen/telemetry，:19仅warm show→hide再在返回后emit。目标startup新输入未测。结果9/10，跟F1/1相同。

**K/1、K/2、F0/2，只改panel watcher startup和显示顺序。**三份补丁均为注册监听前移、每监听器arrival序号/last-shown过滤，未加同visit attempt判断或startup接纳有效性。K/1 events:29/35、K/2 :17/19、F0/2 :14/19覆盖普通、反序、hide重入等，retry即便被调用也未驱动旧attempt延迟完成的关键对照。它们都8/10，目标与retry失败。读取源码不等于理解正确，模型是否在未表述的推理中作过更准确区分未知。

所有六次late-after-hide历史保留项通过，没有观察到已接纳工作被全面取消；这只覆盖评分/可见驱动的路径，不能证明其他路径均保留。机制逐job引用与未知项见mechanism-review.csv。最接近可观察断点的是**技能要求的组合事件动作没有完整落实到验证，补丁又用取消状态替代了尚未取消时的owner有效性**；不能直接归因模型能力不足或反馈无用。

### 成本、失败与验证异常

| 条件 | CLI／底层请求 | 工具／shell | 输入token（其中cache） | 输出token | CLI秒／含评分秒 |
|---|---:|---:|---:|---:|---:|
| K | 2／17 | 21／19 | 372563（327296） | 5472 | 149.59／153.07 |
| F0 | 2／15 | 13／11 | 317908（295424） | 4014 | 127.15／130.64 |
| F1 | 2／23 | 20／17 | 524710（484608） | 7421 | 200.24／203.73 |
| 合计 | 6／55 | 54／47 | 1215181（1107328） | 16907 | 476.98／487.44 |

总输入+输出1232088；output中包含原生reasoning记录3237，不再重复加。首个会话开始到末个结束墙钟556.54秒，含显式调度修正的间隙；CLI/含评分合计与墙钟不混用。未返回结算金额，不估计货币价格。F1本轮消耗较多而未改善目标，不据此概括普遍效率。

底层Pre/Post与CLI turn用量六次逐项一致，55/55均完成，无被拦截重试。维护会话执行失败0、超时0、可信评分/校准异常0；调度器中断1（前述已修正、未补跑）。

47次shell中15次非零：[nonzero-commands.json](nonzero-commands.json)保留原命令、输出和事件行。8次是候选自写检查断言失败，集中于共享源telemetry启动预期、两个消费者覆盖deferred resolver、retry attempt预期；Agent改了检查后继续。7次是隔离工作区无Git元数据导致git status/diff返回128/129，不能把它们计作七次评分基础设施故障。Git diff检查没有成功，但实际patch由Workbench捕获并归档。事件中的hook-trust提示也不被当作模型失败。

[final-validation.json](final-validation.json)核验12777份已有文件摘要无变化、原协议/脚本保持、六个独立工作区/固定顺序/输入/评分关联和全部usage对账。Git HEAD及tracked/staged diff不变；未新装依赖、未创建提交。实验补丁仅存在本目录各隔离工作区，没有修改仓库生产代码、题库、评分器或旧档案。

## 最终回答与停止

“在这个已暴露的U1案例上，F1生成技能是否比K0和F0更能修复目标行为，同时保留已有行为？”——**本轮没有这样的证据。**目标六次均失败；F1一次仅与F0一次同为9/10，另一次引入配对K/F0均没有的有序显示损失。它保住retry的局部收益不能抵消目标未修复和新退步。不能宣称稳定有效、因果证明或独立泛化；独立人工复核仍未完成。

到此停止，不换候选、不再改技能、不追加维护或GEPA。若另行开展下一轮，优先针对“技能要求的具体顺序是否被实际驱动/检查”做一个有界验证干预，同时保留已接纳完成、ordinary/reversed两种顺序的回归检查，而不是继续泛化提醒或事后挑候选；此处只是建议，没有执行。

Git commit subject：`research: evaluate fixed U1 skills on six isolated maintenance runs`

Body：`Freeze K0 and the first F0/F1 candidates, archive paired behavior and request costs, and document persistent admission failure plus an ordered-display regression. Preserve prior studies and record the operational manifest-check correction without rerunning jobs.`
