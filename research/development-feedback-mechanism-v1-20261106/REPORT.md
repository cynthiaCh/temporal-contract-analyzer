# 开发集内反馈机制实验

本轮的未盲化代理审查支持一个有限判断：恢复方向性证据后，模型在两种关系的两次重复中都明确识别了实际方向；针对动作的新增主要见于U1。U2的F0也已提出可执行的中间状态检查，不能把它算成F1独有能力。没有运行维护任务、GEPA搜索、评分器或新LLM judge；没有关于正确补丁、修复收益和泛化的结果。独立人工复核尚未完成。

## Task 1：单元与证据

开始时读取既有审计、变化链、选择路径、反馈投影实现/报告/离线校验及原实验模板/配置/父技能/原始记录。工作目录及祖先未发现AGENTS.md；官方克隆内的局部AGENTS已查阅，本轮未在其中改动。初始HEAD、git状态和diff、已有文件摘要保存在[initial-state.json](initial-state.json)。旧的来源不足停止记录完全保留，没有把其旧来源改名为独立test。

原审计[selection-trace.json](../gepa-mechanism-audit-v1-20261106/selection-trace.json)记录P1–P5均在train严格改善门槛失败，未进入val；val满分不是这些提案被拒的步骤。本轮不重做候选选择，不把旧候选当本轮输出。

在生成前以可还原性和机制差异选择以下两个已暴露开发单元，见[units.freeze.json](units.freeze.json)、[evidence-key.json](evidence-key.json)。后者含精确原始评分路径、traceIndex、轨迹/补丁路径与摘要，仅研究侧持有，没有作为额外证据交给模型。

| 单元 | 冻结执行job与父技能 | 原始观察与保留项 | 未知与限制 |
|---|---|---|---|
| U1 | `e-5b07bf1156dc48d0`；K0，SHA `6f82762517c6e604c48903324e9a62123cccf386246577f44d7488fdd0cab024` | required 9/10；启动中发生导航后，旧源**新输入**仍多记历史。须区分此前已接纳工作的迟到完成；后者、retry、queue/notice、telemetry等已通过，不能一刀切禁止所有迟到记录。 | 原始trace没有调用返回标记；不从事件先后断定唯一调用栈或补丁。 |
| U2 | `e-0f86af18a30343df`；该执行实际使用的原提案P2，SHA `fd3bbd5dd40deaf3a31bd73ce3197939870b4cf4ab60041a63afeee00acfd9ad` | required 7/8；pending后已有下一次retry，随后完成，但中间等待指示缺失。须区分单次请求settle与整个preparation仍未完成，保留既有delivery、close/reopen及background政策。 | 短任务未完整定义flag schema；background代码只是对照，不自动成为foreground规范。 |

U2的P2是本轮冻结反思的父技能，不能误称原GEPA池中的父版本。两单元分别涉及输入接纳边界和操作阶段指示，不是同一事件的轻微变体。研究者人工定向选择，且案例、评分、投影均已暴露；没有独立测试分布。

原始证据在[evidence/U1](evidence/U1)和[evidence/U2](evidence/U2)。U1实际工具事件28/32中的检查覆盖warm、反序decode、hide/reselect、retry等，但没有针对“启动导航后旧源新输入”的可见检查。U2只有语法验证，未证明渲染期pending显示；其共同RAG实际上包含preparation API源码，不能仅因没有额外cat就声称Agent没读过它。

## Task 2：输入、调用与匿名审查

[PLAN.md](PLAN.md)、[protocol.json](protocol.json)及46份输入/脚本摘要在生成前冻结；[offline-validation.json](offline-validation.json)通过后才开始正式请求。

A只用既存F0.Feedback，B只用既存F1.Feedback；父技能、原任务、源码RAG、Generated_Outputs（实际轨迹、补丁和完整可见验证）、反思模板公共部分及schema一致。之前F1样例在Feedback以外对visible_validation的去重，本轮明确排除，两组都使用F0同一完整正文及其既有重复。各单元common-record.json、common-prefix/suffix、完整A/B prompt、input.diff与control-check.json保存实际差异。

| 单元 | F0/F1反馈块字符数 | 完整F0/F1 prompt字符数 |
|---|---:|---:|
| U1 | 755 / 8,859 | 32,905 / 41,009 |
| U2 | 727 / 7,030 | 25,650 / 31,953 |

完整prompt共同上限72,000字符，无静默裁剪或填充。U2的UTF-8字节数比字符数多4，见control-check。F1增加事件顺序、差异方向、保留行为、来源与未知信息，远不止措辞替换；本轮不能把结果唯一归于某一个方向词。

沿用原官方反思模板（[历史版本](HISTORICAL_REFLECTION_TEMPLATE.md)及[本轮版本](REFLECTION_TEMPLATE.md)）。原模板只允许fenced skill，而本轮要求skill和简短说明，因此**仅共同替换最后输出条款**为JSON skill/change_notes；未额外强化方向性提示。skill≤6000字符，notes字段值合计≤1200。其余历史文字不变，包括模板中关于官方GEPA的历史措辞；本轮没有据此启动优化器，只用其反思生成模板。此共同格式适配意味着不是历史协议逐字重放，但A/B该项完全相同。

端点沿用原CLI的`gpt-6-sol / low`，600秒/槽，无额外温度或模型采样种子。固定调度种子2026110606（不是模型采样种子）：

`U2-B1 → U2-A1 → U1-A1 → U1-B1 → U2-A2 → U2-B2 → U1-B2 → U1-A2`。

八个槽位分别新建ephemeral会话，无共享输出。只读空工作区、研究目录不可见；shell/apps/plugins/code-mode等关闭，工具尝试由同步hook拒绝并终止。PreModelRequest全局8/每槽1硬上限由同步hook在返回前终止超限CLI，不能靠hook的JSON输出阻断模型请求；同namespace的假provider/假工具离线校验通过，未做模型预跑。接口依据为[官方hooks说明](https://learn.chatgpt.com/docs/hooks)，实际控制代码为[request_guard.py](request_guard.py)、[run.py](run.py)，原始Pre/Post事件见[request-meter/events.jsonl](request-meter/events.jsonl)。

实际8次CLI、8对Pre/Post、8次底层模型请求，均完成；工具尝试0、重试0、超时0、格式失败0。无维护/评分/GEPA/LLM judge请求。每次actual-prompt、原始事件、stderr、raw-answer、receipt见[runs](runs)。

**监测异常单列：**冻结run.py把CLI `item.error`警告误当工具，导致八份原始receipt均标`generation_failure`。实际各槽exit0、turn.completed1、底层请求完成1、真实工具0；警告为两条hook-trust通知及预期的code-mode禁用通知。[receipt-reconciliation.json](receipt-reconciliation.json)统一按事件类型和计数纠正为有效完成。原始状态、脚本和输出均未改，没有重生成。该异常不被计作八次端点失败，也不被隐去。

全部输出保存后用OS随机ID生成[匿名包](anonymous-review/README.md)，标签映射独立保存在private-label-mapping.json。候选+父diff+notes、必要原始证据及research evidence-key均在包中；common-observations.json是生成时同一共同材料的副本，用以防止把未额外cat等同未获得源码。匿名化只能隐藏标签，内容、原始证据仍可能暴露来源/条件。

当前执行Agent参与过准备，故64项语义记录均标**未盲化代理审查**，不是独立人工盲评，也没有另调模型充当judge。统一空表留给独立人工。先冻结[review.csv](review.csv)、[review-narrative.md](review-narrative.md)和77个审查文件摘要（[review.freeze.json](review.freeze.json)），然后验证冻结摘要再读取映射；解盲汇总在[unblinded-results.csv](unblinded-results.csv)。离线脚本只做格式、diff、字段、标识和用量核验，不自动判断语义质量。

## Task 3：逐单元、逐重复结果

维度分别报告，不加总。D1=实际关系方向；D2=不把邻近变体当目标；D3=针对关系的可执行新增步骤；D4=保留通过行为；D5=假设与事实；D6=原维护目标；D7=可复用、无案例答案泄漏/无扩张；D8=长度/重复。下表“满/部”分别为满足/部分满足；依据、原文行号及各维解释完整保存在review.csv，允许的等价表述在生成前PLAN/evidence-key冻结。

| 单元/重复 | 条件 | 匿名ID | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | skill/notes字符 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| U1/1 | F0 | C8ec8c3ddfc | 部 | 部 | 部 | 满 | 满 | 满 | 满 | 满 | 3699/712 |
| U1/1 | F1 | C4509bd4e1d | 满 | 满 | 满 | 满 | 满 | 满 | 部 | 满 | 4293/855 |
| U1/2 | F0 | Ce9171f6270 | 部 | 部 | 部 | 满 | 满 | 满 | 满 | 满 | 3523/900 |
| U1/2 | F1 | Cef4fc8724a | 满 | 满 | 满 | 满 | 满 | 满 | 满 | 满 | 3876/708 |
| U2/1 | F0 | C88dc697f47 | 部 | 满 | 满 | 满 | 部 | 满 | 满 | 满 | 4510/710 |
| U2/1 | F1 | C278cbcff31 | 满 | 满 | 满 | 满 | 满 | 满 | 满 | 满 | 4223/777 |
| U2/2 | F0 | C4aacd8de3d | 部 | 满 | 满 | 满 | 满 | 满 | 满 | 满 | 4360/727 |
| U2/2 | F1 | Cfeff72a075 | 满 | 满 | 满 | 满 | 满 | 满 | 满 | 满 | 4489/819 |

### U1：有动作设计增量，仍有范围风险

F0两次并非只有“更加仔细”：C8ec8c3ddfc skill第11/17行要求启动重入/旧调用恢复及调用后效应检查；Ce9171f6270第11/15行要求旧调用不能覆盖新owner，并测试startup/reentry。这是有效邻近机制查证。但notes仅指历史/current组合不符，没有明确“切换后的新输入多记历史”，技能也未要求将它与**已接纳完成**分开驱动。因此D1–D3只部分满足。

F1的[C4509bd4e1d/skill.md](anonymous-review/candidates/C4509bd4e1d/skill.md)第9行拆分admission/accepted work/settle，第13行要求交接后fresh old-source input并分别观察history/display，第17行要求组合启动回调检查。其notes第4行引用新增旧源fresh input，第9行保留缺调用返回标记的未知。[Cef4fc8724a/skill.md](anonymous-review/candidates/Cef4fc8724a/skill.md)第9/13/17行要求比较transition-before-input与input-before-transition并保留已接纳工作的完成。两次都把信息用于要求执行不同的检查动作，而不只是描述更具体。

风险没有抵消：C4509bd4e1d第11行“Do not infer order from decoded values”较为绝对。邻近的source-backed排序要求可能限制其范围，但若泛用于其他项目，值本身可能合法编码顺序；因此D7部分满足，不能称F1无新增约束风险。本轮未执行它，不推定实际冲突或行为退步。

### U2：方向解释改善，动作优势有限

F0两次已区分waiting副作用，并要求pending/retry/ready/close中间快照（[C88dc697f47](anonymous-review/candidates/C88dc697f47/skill.md)第9/13/17行；[C4aacd8de3d](anonymous-review/candidates/C4aacd8de3d/skill.md)第11/19行）。这比只验证最终delivery更有针对性。其notes主要称waiting mismatch，没有说明实际是**缺失等待指示但仍retry且最终成功**，故D1部分满足，不能把两份F0都写成没有行动。

F1的[C278cbcff31](anonymous-review/candidates/C278cbcff31/skill.md)第11/15/19行和[Cfeff72a075](anonymous-review/candidates/Cfeff72a075/skill.md)第9/13/17行把单次request结束与operation仍在准备分开，要求请求返回后、下次retry前的观察；对应notes第4行明确缺失方向及最终完成事实，同时保留flag定义未知。其解释更准确，但相较F0的动作增量没有U1那么明确。

F0 C88dc697f47 notes第4行声称没有读preparation API。共同RAG已含该源码（anonymous-review/evidence/Ebb0124/common-observations.json的Inputs）。没有额外读取工具证据只能证明“未额外cat”，不能证明未获得/未读，故D5部分满足；不把模型自述当事实。其他候选未见同样断言。

### 保留、泄漏、重复及未知

八份技能都保留原维护交付及验证要求，没有改成辅助问答，也没有代码补丁。未见案例名、隐藏标识、fixture答案或参考修复进入技能；机械扫描零命中只是支持证据，语义仍需人工复核。notes作为研究侧说明可以引用反馈依据，不能直接交付执行Agent。未见被明确删除的关键保留行为；这只评价技能文本，不能宣称实际运行无退步。

所有长度合规，机械扫描无完全重复句；没有按字数给F1加分。F1技能并不总更长：U2第一重复F1短于对应F0，第二重复则更长。八份候选只涉及两个诊断单元，每条件两次重复，不是八个独立任务，不做显著性推断或稳定性承诺。

### 成本与验证

| 条件 | 底层请求/CLI | 输入token（其中cache） | 输出token | CLI耗时合计 |
|---|---:|---:|---:|---:|
| F0 | 4/4 | 66,122（16,896） | 3,762 | 115.24秒 |
| F1 | 4/4 | 73,570（27,904） | 3,868 | 109.22秒 |
| 合计 | 8/8 | 139,692（44,800） | 7,630 | 224.46秒 |

调度墙钟224.60秒；output中原生记录reasoning token合计9，不重复加到总token。总输入+输出147,322。端点未提供结算金额，不套用不确定价格。成本包括全部8次反思，没有维护、评分、搜索或judge成本；不能把短墙钟差异当成本效率优势，缓存命中和上下文长度不同。

[finalize.py](finalize.py)离线校验冻结输入/审查记录、映射/原始输出摘要、8对Pre/Post与CLI usage一致，以及12,539份已有文件摘要；[final-validation.json](final-validation.json)通过。原HEAD不变，tracked/staged diff为空，未安装依赖、未创建提交。初始未跟踪的旧研究目录属于既有工作，未重置或纳入本轮修改。

## 回答与下一步边界

“恢复方向性事件信息之后，模型有没有真正利用这些信息，生成更针对实际失败关系的技能修改？”——**从本轮输出文本及未盲化代理审查，支持有利用，最清楚在U1的输入接纳与已接纳完成区分及其测试动作；U2主要改善方向说明，F0已具有不少相同动作。**无法从文本证明内部思维，也尚未经过独立人工复核。该反馈同时增加来源、保留事实、未知项及长度，不能把现象唯一归因于方向性词句。

停在本轮机制分析。[NEXT_EXPERIMENT.md](NEXT_EXPERIMENT.md)只提出复核及后续最小验证，不执行；不启动维护、GEPA或评分。修复收益、执行落实、稳定性和泛化仍未回答。

Git commit subject：`research: compare F0 and F1 reflection mechanisms on exposed development traces`

Body：`Freeze two diagnostic units and run eight one-request reflections with shared inputs. Archive anonymous candidates, proxy review and native usage; record directional gains, scope risks and the absence of repair evaluation without changing prior experiments.`
