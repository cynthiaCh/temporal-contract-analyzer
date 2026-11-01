# Round 1：面向 ICPC Tool Demonstration 的方法设计评审

日期：2026-10-29。评审对象：`round-0-initial-proposal.md`，以及已完成的 `BASELINE_DIAGNOSIS.md` 和原始扫描盘点。

评审性质：fresh-context、same-family / provisional。以下评分只评价设计的清晰度与可检验性，不是实现通过、工具有效、创新性获证或会议录用认证。没有运行模型实验或参与者研究，没有修改提案、产品代码或 benchmark。

<details>
<summary>完整原始评审</summary>

## 结论与评分

**VERDICT: REVISE。OVERALL SCORE: 7.30 / 10。CALIBRATION: none。**

方向符合锚点，也适合以可追溯静态证据支持程序理解的工具定位。当前最重要的缺口不是缺少模型，而是“效果单元”仍没有获得独立于旧 finding 的发现规则，以及足够具体的身份、闭包捕获和保护关系接口。若只按现有 finding 重新分组，它会继承最关键的效果遗漏；若把同名引用与词法顺序都画成连线，图只是更有结构的线索清单。两者都不能单凭界面变化支撑现有方法主张。

| 维度 | 权重 | 分数 | 依据 |
|---|---:|---:|---|
| Problem Fidelity | 15% | 9 | 保留跨边界、工作归属、不同效果政策和保护位置；诚实保留 readiness 未建模与作者暴露。|
| Method Specificity | 25% | 6 | 有输出草图和修改位置，但效果候选集合、身份节点、捕获/guard 连接条件和停止规则仍欠定义。|
| Contribution Quality | 25% | 7 | 逐效果区分政策是集中的候选贡献；目前还未证明其表示增量超过重新包装旧线索。|
| Appropriate Frontier Leverage | 15% | 9 | 静态设计与可定位、可冻结、可审计的目标一致，避免让生成模型成为业务真值是正确选择。|
| Feasibility | 10% | 7 | 复用解析与归档使局部实现可行；三周内跨语言捕获解析、标注和四条件研究仍需明确降级路径。|
| Validation Focus | 5% | 6 | F/U 的因果分解和负结果规则好，但信息等量、回答分母、政策真值来源和试验停止条件尚未落实。|
| Venue Readiness | 5% | 7 | 有工具演示的明确使用场景，但还缺完整的具体 walkthrough 与冻结的小型验证协议。|

加权计算：`0.15×9 + 0.25×6 + 0.25×7 + 0.15×9 + 0.10×7 + 0.05×6 + 0.05×7 = 7.30`。

**GAP:** 未提供事先由人类挑选并标记的三个正面、三个反面校准范例，因此不能声称分数已锚定，也不自行挑选范例。相对本次明确的 READY 门槛，主要差距在 Method Specificity 和 Validation Focus：一个实现者仍需自行决定哪些 effect 可成为单元、哪些同名引用属于同一声明、哪些 guard 真正指向该 effect，以及 F 是否包含 U 显示的全部关系。解决这些接口问题、提供两个从源码到单元的完整演示、冻结单一主比较即可明显接近门槛，无须增加模型或大规模 benchmark。

## 锚点检查

以下原始锚点保持不变：

- Bottom-line problem：利用现有 temporal-contract-bench 的任务、候选源码、行为对照与来源记录，设计一个更能帮助核查跨边界时序要求的工具，以及能检验其实际价值的实验，服务 ICPC 2027 Tool Track。
- Must-solve bottleneck：现有四问卡片主要重组启发式 finding，尚未明确连接 continuing work、对象/操作身份、不同消费者效果及保护位置；合成单例与实现测试不能回答真实审查价值。
- Non-goals：本轮不修改 benchmark 历史输入、oracle、冻结结果或独立发布版；不把既有开发案例称为未见验证；不启动付费模型或参与者研究；不在设计阶段实现全程序验证器或自动修复。
- Constraints：当前 analyzer 支持 Python、JS/TS 和 Vue 脚本；复用既有解析、归档与接口；来源相关表示不计独立样本；评估者材料与工具/Agent 可见材料分离；ICPC 2027 Tool Track 时间预算约三周。
- Success condition：从实际源码扫描与代表案例中定位可复核缺口；给出小而具体的数据结构和模块修改；实验有固定对象、信息等量对照、逐义务/消费者指标与停止规则；正、负或无效结果均能确定论文可写主张。

**Drift Warning: NONE。** 目前方向没有实质漂移。继续排除全框架建模、自动业务政策推断和自动修复。建议的有限符号绑定与效果候选枚举只是使既有方法主线可实现，不要求改成全程序验证器。

## 已核查的实现与材料证据

1. 已完整阅读问题锚点、初稿和 `BASELINE_DIAGNOSIS.md`；盘点 JSON 的 242 个唯一 case ID 与 roster 相符，roster SHA 与当前文件相符，234 个成功生成的报告对应 parsed/partial/empty，另有 6 个超时与 2 个待上游物化。状态为 139 parsed、72 partial、23 empty、6 timeout、2 materialization；23 个 empty 都是 PHP 标签，69 个 partial 的 parsed_files 为零。这是收集/解析范围证据，不能当作效果召回率。`casecatalog.locations()` 返回 348，另一个分母没有混入本轮 242。
2. `core.py:95–150` 的 `enrich()` 给出词法/命名导入候选目标，参数调用标作 `parameter_callback` 或 `parameter_member`。它没有实际参数到形式参数的值映射，没有运行时实例标识，也不解决跨工厂对象身份。JS/Python adapter 的 references 是表达式名称，不是已经消歧的符号 ID；函数作用域和参数可帮助新增有界消歧，但不能直接当成完成的 capture 图。
3. `boundary_cards.py:28–60` 逐 finding 取 evidence，effect 资格只有 write 或精确 effect 名称标签。`layers.py:157` 也从 finding evidence 选择位置。因此“纯函数派生新卡片”若仍只输入旧选择集，会漏掉已解析但从未进入 finding 的效果。
4. transfer 的 `src/progress.js:4` 明确有 `record(frame); receive(frame);`。原始报告中它们是 `e3/e4`，均为 `parameter_callback`，均不在任何 finding 内；该案例四张卡均没有 effect 引用。这是最小而直接的机制反例：候选效果必须在 finding 之外发现。
5. document 的 `src/workspace.js:14–15` 有 `archive.capture(...)` 与 `renderSubmission(receipt)`。二者都在 snapshot finding 内，但调用分别是 `parameter_member` / `parameter_callback`，不属于当前精确 effect 标签；所谓 effect 槽可以只剩 origin/receipt 局部变量赋值。局部暂存写入不能替代归档与 UI 两个效果。
6. listener 的报告能连接 `subscribeChannel` 的命名导入目标，但不能仅凭该边证明 `publish → receive → decoded.then(receive)` 是哪一次 panel/订阅的消费者。`receive(decoded)` 事件也不在 finding 内。它适合作为明确展示部分连接与剩余未知的演示，不宜声称已恢复完整跨实例链。
7. readiness 源码的关键关联确实横跨 `SchemaForm.vue` 的延迟 `$emit("input", API)` 与父组件模板 `v-model`/`this.formApi.setValue`。目前只有脚本语法与两个 config-service 导入候选目标，零 finding 不能解释为无风险。把它保留为未建模示例是合理限界。
8. 已阅读 observational-consumers、structural-transfer、cached-feed 的主结果/说明。前者支持需要分别核查消费效果的设计动机；后两者明确保留全通过、未观察到额外位置收益，以及作者构造/人工审核限制。它们不能证明新工具的有效性。历史 tool-report-pilot 的确只有 36 个 NOT_STARTED 槽位。

## CRITICAL：把“效果单元”定义为真正的新提取单位

最低修正不是再加一层图展示，而是写清 `review_units(report, selected_scope)` 的确定性输入域和候选资格。

- 候选应直接枚举已选范围中的 AST events，至少覆盖参数回调调用、参数成员调用、成员写入和已有 effect 名称线索；局部临时变量赋值默认作为 capture/identity 证据，不自动成为主要效果。每个被纳入的 event 带 eligibility reason。名称规则只决定候选资格，不决定业务政策。
- 词法/命名导入的一层展开允许暴露更多候选，但必须说明“一层”的起点、终点及递归停止条件。未覆盖的动态调用、计算属性和对象工厂显示为范围缺口，不通过堆更多 API 名称掩盖。
- `origin_findings` 作为后挂的解释来源，不能控制是否创建 unit；没有 finding 的 effect 仍可建立单元。手工添加 effect 也要记录依据、操作者与耗时；实验 F/U 同样获得这种添加能力或同一冻结添加材料。
- 输出静态效果位置，不声称它等于一个动态消费者实例。同一函数中的两个调用能被分开审查，这是第一版可诚实实现的增量。

一个应写进提案的具体 walkthrough 是 transfer：`record(frame)` 和 `receive(frame)` 各产生一个候选单元，共享 `frame` 参数声明及 `deliver` 回调候选；前者和后者的继续/停止政策由审查者按同一任务证据分别填写。若工具不能把这两个旧 finding 未包含的调用独立显示，当前设计尚未解决锚点最直接的反例。

## CRITICAL：让身份、连接与保护字段有可执行含义

`identity_refs` 只有 ID 数组不足以表达工作身份。将“源码里引用同一个词”和“同一个运行时工作/实例”严格分开，至少定义以下内容，无须做别名求解：

- **符号候选：** 使用 `file + declaring_scope + parameter/declaration anchor` 作为声明级标识；每个 use 附其绑定依据。遇遮蔽、赋值来源不唯一或成员对象稳定性未知，记录具体断点。不能只把 `visit`、`frame` 等字符串相同当作身份相同。
- **有限关系：** 指定 capture-use、直接实参到形参候选、callback-argument-to-scope、guard-to-effect 候选的生成条件。每条边保留端点、语法依据、适用范围和未知项；词法先后与同一 owner 命名空间只作为弱背景关系，不升级为数据流或生命周期关系。
- **保护候选：** 至少区分效果位于 guard 分支内、前置退出后的局部位置、以及仅在同一词法单元共现。当前条件字符串不够处理所有早返回或跨调用保护；第一版可以只支持第一类并把后两类留给人工，不必实现完整 CFG。提案必须声明实际支持的这一种规则，不能用“局部控制关联”代替规格。
- **场景/截止点：** 一个静态 effect 的政策必须相对于指定 boundary/scenario。cached-feed 中退休后“拒绝新的接收”与“完成退休前已接受的解码记录”同时成立；一个无场景的 continue/stop 值会丢失核心区别。给单元或 review 条目加 `boundary_ref / scenario_ref` 与“接受工作”的源码候选锚点即可；真值依旧来自共同任务材料和人工判断。

最低验收材料只需两个正向演示与一个拒绝连接演示：transfer 的局部双效果；document 的捕获、归档、显示及中间回调窗口；一个遮蔽/重赋值或跨工厂实例而必须 unresolved 的例子。展示确切输入片段、预期节点/边及尚未连接之处。这是方法设计核对，不是新增有效性实验菜单。

## IMPORTANT：F/U 必须真的包含相同关系信息

“完全相同的证据”需要可核验定义。F 如果只有源码片段和 event facts，U 却有 effect→identity→guard 的边、共享边界或未闭合提示，就增加了信息，不能将差异归因于组织。

让 F 与 U 从同一个规范化 payload 渲染：候选节点、声明级身份候选、带端点的 typed relations、依据、未闭合项、分析范围、共同问题与人工初始材料全部一致。F 可按源码顺序显示节点表和关系表，U 按效果组织同一内容；并列展示的“共享边界”也要在 F 中可读。用 canonical payload/hash 检查内容一致，而不是比较字数。互动条件允许的导航、加注、计时和源码访问保持一致；若 U 的交互本身是干预，就在主张中写清。

V0→F 反映提取和新增材料的联合变化，作为诊断即可；主比较固定为 F→U。S/V0 的差异不应额外变成另两条论文主贡献。

## IMPORTANT：只保留一个明确的主张及一个可选支撑主张

**主张候选：** 在固定的、作者已接触的任务快照中，按 effect 和具体边界组织同一组静态候选关系，能帮助审查者作出更多有源码依据的消费者政策/保护判断，同时不增加对本应继续工作的误抑制。

这是待检验的设计假设。必须由 F/U 的内部随机化比较决定是否可写；仅有演示、关系精度或成功解析不够。

**可选支撑主张：** 在明示的局部分析范围内，这个有界提取器能补出旧 finding 未直接呈现的消费效果和连接，并把无法连接的身份/保护关系显式保留为未知。E1 用范围内 gold 的覆盖、错误候选和人工负担支持它，不把 242 的数量当独立缺陷样本。

共享归档、MCP 和多入口属于实现支撑；不需要独立贡献编号。图结构本身也不宜作为首创论点。Slicito 已展示交互缩小范围与分析组合，CodeQL 明确提供局部/全局数据流和带保护条件的分析。这里可能有价值的是按不同效果和截止点组织不完整证据的审查工作流；该差异仍需完整相关工作检查，当前评审不认证新颖性。[Slicito 作者页](https://www.d3s.mff.cuni.cz/publications/husak_combining_2025/)、[CodeQL 官方数据流文档](https://codeql.github.com/docs/codeql-language-guides/analyzing-data-flow-in-javascript-and-typescript/)。

## IMPORTANT：收紧 E1/E2，保留阴性与未知结果

**固定对象与暴露。** 初稿的“约 12 个任务、8 个来源”仍是预算描述，不是冻结对象。协调者补充拟改为 8 个来源各 1 个正式 task snapshot、另 12 个 E1 控制；这有助于明确单位，但尚不属于已实现或已执行证据。请在修订版列出具体快照/哈希、来源谱系、角色、变体生成方式与预先选择依据。不要从“工具已经能连出的例子”中事后挑正式任务。此语料均为作者已接触材料；内部随机化比较仍然有意义，但不能称为未见项目、独立来源泛化或暴露无关的检测能力。

**政策真值。** 每个任务共同提供必要任务说明和 boundary/scenario，不要让“任务文本可选”造成受试者判断不同的问题。评估者 gold 区分：从参与者可见源码/公开说明可恢复的政策；需要不可见业务假设才能确定的政策；仅保护实现未知。oracle/reference 只是候选标注线索。可见材料不足时 unknown 应是合法答案，而不是要求人猜隐藏 oracle。独立复核应针对这些源码支持与歧义，不能只核对 JSON 格式。

**分母与遗漏。** 用预先标注的 effect×scenario 义务作为回答评分分母，并将其聚合到一次 participant×task 回答；不能用工具实际生成的单元作为分母，否则漏 effect 会消失。若题目直接列出所有 gold effect，则测的是已给定效果的关系/政策审查，不能宣称帮助自发发现效果。若需要测发现，就允许开放回答，并按隐藏 gold 对齐、记录遗漏和无依据新增，不要同时改变主张。

**一个主要结果。** 预先规定“源码依据有效且政策/保护判断正确”的计分规则及任务内聚合方式，误抑制应继续工作单独作为有方向的失败结果。对可判定义务的 unknown 计未恢复；对资料确实不足的义务，带出缺失依据的 unknown 可正确。不要只报告回答项中的条件准确率，也不要把多个 effect 当独立受试者。

**功效与成本。** 12 人×8 题仍是 12 个参与者和 8 个 task/source 单元，不是 96 个独立事故。四条件平衡后每 task×condition 只有 3 个回答；因此先定位为可行性 pilot，不能将“不显著”写成无效或等效。主比较只预定 F/U，按参与者和 task/source 的重复结构报告效应、区间及逐任务结果；不要拟合超过样本能承受的模型或追加多重探索比较。若预算不变且主要目的是估计组织增量，可以把正式人类条件压到 F/U，S/V0 留作工程比较；也可以保留四条件，但诚实限定结论精度。

10 分钟每题意味着 96 题的纯作答上限为 16 小时，另计训练、休息、招募、独立标注与判分。记录超时、未完成、材料生成失败、提示阅读和人工补关系时间；包括失败尝试的成本。时间到顶时要保留部分回答并按预定缺失/超时规则统计，不悄悄替换。依赖人工完成大量连接的方案，必须报告这部分预处理/审查劳动，否则“节省理解成本”没有完整分母。

**停止规则。** 先冻结资格/关系规则和 F/U payload 一致性；若代表双效果案例仍不能生成独立单元，先修方法，不招募。若共同材料不能产生可复核 gold，标为信息不足或移到方法限界，不能偷偷补给 U。规定材料冻结日与招募最低可执行规模；三周内未达到就交付 E1＋两个透明演示，主张限定为可用的证据支持工作流。E2 不得按中途观察到的组间差异补人或换任务。E3 默认移出这轮必做项；即使后续执行，也只作为探索性 Agent 结果。

## 小于 7 分的最低修正要求

| 维度 | 具体弱点 | 最低修正 | 优先级 |
|---|---|---|---|
| Method Specificity = 6 | 单元仍依赖 finding；identity_refs 没有声明级语义；guard 共现可能伪装为保护联系 | 明文定义独立 effect eligibility、声明级符号候选和最多四种关系的前置条件/拒绝条件；给出 transfer、document 的预期输出及一个 unresolved 例 | CRITICAL |
| Validation Focus = 6 | F/U 信息等量、可见材料决定的 gold、评分分母与主比较未冻结 | 单一规范 payload 双渲染；固定 task×source 清单与 effect×scenario gold；只预定 F/U 为主要比较，明确 unknown/遗漏/超时/人工成本和 pilot 停止规则 | IMPORTANT |

## Simplification Opportunities

1. 新逻辑收敛在一个纯函数提取/组织层及必要的 adapter 字段补充；复用现有归档、源码范围和 notes。不要新增独立身份推断服务或全程序图引擎。
2. 把旧 findings 当附加解释，把临时写入当证据节点，删除“每条 hint 都必须变成卡片”的继承关系。
3. 三周必做只保留 E1 和一项围绕 F/U 的人类 pilot 准备/执行路径；Agent 维护实验移到有必要时再做。减少条件或界面入口扩展，比增加样本菜单更能保护主线。

## Modernization Opportunities

**NONE。** 本次适当的现代化是冻结可复现材料、让 Agent 作为可选下游消费者、把机器候选与人工判断分开，而非引入 LLM 生成契约。现有静态路线能对准问题；没有证据表明一个模型模块会更小、更可验证或更适合三周期限。

**最终判定：REVISE。** 保留锚点与静态路线，先使“遗漏效果也能成为单元”和“关系类型真的多提供了什么”变得可执行，再固定信息等量的主比较。这轮无需 RETHINK，也尚未达到 READY。

</details>
