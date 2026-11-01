# ICPC 2027 Tool Track：现有工具改进与候选 idea

日期：2026-10-31，Asia/Shanghai。对象：`temporal-contract-analyzer` 当前工作区。性质：代码检查、初步文献比较、探索性小实验和选题建议；尚未实现新工具、开展独立效果实验或提交论文。

## 先给判断

当前 analyzer 已有 CLI、VS Code、MCP、报告归档与边界审查卡，工程形态足以支撑一个工具稿。最先需要补的是效果证据缺口和真实维护案例，而不是继续增加入口。Oct29 已有的“效果×边界×情境”方案应继续利用，不重新包装成新发现。

本轮新增候选主线是 **TemporalDelta：面向异步代码审查的时序关系差分**。开发者输入前后两个源码版本，工具直接展示有效性检查、等待点和候选效果之间的关系发生了什么变化，以及证据不足的位置。它应先作为现有 analyzer 的一个受限模式验证。最终 fresh-context 评审结论是 PROCEED_PILOT：总体交付优先级 L1 最高，新增方向 L3 最高；先做 1–2 天证伪，不立刻整体改写当前稿件。失败后完善现有稿件，不再启动另一套工具。

假设：用户主要希望在本届截止前完善可交付工具；单作者、CPU 可运行、不增加依赖、不购买 GPU 或启动付费模型实验。下面工期均为聚焦工程估计，不是承诺或已完成工作。

## Task 1：当前工具哪里值得改

### 1. 效果事件已有，卡片仍可能没有效果入口

本轮只读复测 transfer 开发案例：7 个文件完整解析、127 个事件、4 条提示；4 张卡均无 effect 槽引用。与此同时，`record(frame)` 和 `receive(frame)` 已存在于事件表并标记 `parameter_callback`。

源码原因在 `boundary_cards.cards()`：只从每条 finding 已有的 evidence 找槽位，effects 只接受 write 或 effect tag。源码中已存在、但未被 finding 选中的参数回调不会独立进入审查。`write` 又可能只是局部变量赋值，不能等同外部效果。

建议沿已有计划实现：从全体 events 独立提名参数回调、参数对象调用和成员写入等 interaction/effect candidates，再与 finding、边界、保护关联。纯查询也可能被提名，必须显示提名依据并统计无关阅读负担。仅把 parameter_callback 加入 effects 条件不能解决 finding 外的漏入口。

拟改：`core.py`、新 `review_units.py`、`boundary_cards.py` 及展示层。旧冻结 B–G、归档和 Paper 1 的分析器/结果保留原版本。此项属于 Oct29 方案执行，窄实现约 4–6 人日。

### 2. 当前比较单元是提示签名，无法直接回答关系变化

`core.compare()` 对 finding 的 rule/path/scope/证据事件签名比较新增和删除，并报告 changed_files；它没有独立比较任意 guard/await/effect 的前后关系。

本轮作者构造了两段极小程序：

```js
// before
if (!active()) return;
const result = await read();
render(result);

// after
const result = await read();
if (!active()) return;
render(result);
```

结果：两版均 parsed，各有一条 effect-after-await；文件变化可见，但新增提示 0、删除提示 0。给定“read 等待时 active 从 true 变为 false”的受控调度，before 输出 payload，after 无输出。

这说明该关系变化没有直接成为现有 delta 的输出对象。现有 compare 已清楚限定用途，因此这是拟扩展的能力边界，不应把它说成违反既有规格的 bug。

该例也不能证明 after 是完整正确修复。根据评审建议，本轮已补跑三个受控情境，同时记录 read 调用和 render：

| 情境 | before：read 次数 / render | after：read 次数 / render |
|---|---|---|
| 等待期间失效 | 1 / payload | 1 / 无 |
| 入口已 inactive | 0 / 无 | 1 / 无 |
| 始终 active | 1 / payload | 1 / payload |

所以 after 在入口已失效时仍会调用 read，其副作用、异常或资源消耗可能不同。三个情境是有限观察，没有验证完整行为等价。

### 3. parsed 和无提示必须与关系覆盖区分

Vue readiness 开发案例本轮复测：4 文件、120 事件、2 个候选调用链接，完整解析，零 finding。当前 SFC adapter 明确不建模模板、响应式调度和组件实例派发，不能把零提示解释为 API 已就绪。

建议保留源码范围说明，并让零 finding 页面也显示“分析了什么、哪些关系未建模”。不要为提高命中数临时补一个泛化 Vue 规则。跨组件 API 发布/使用可以另做窄工具，但不是本届最便宜的改进。

### 4. 把交付和证据优先级排清楚

| 优先级 | 工作 | 验收 | 估计 |
|---|---|---|---|
| P0 | 修复效果候选入口，复用已有 parser 事实 | record/receive 等能独立定位；纯查询、unknown 和未连接候选保留 | 4–6 人日 |
| P0 | 冻结版本后核查外部维护实例 | 固定选择规则；记录真实范围、无关提示、未覆盖项、来源和失败 | 3–5 人日，受案例可运行性影响 |
| P0 | 一个可安装的公开交付路径与英文 quickstart | 干净环境试装；源码或二进制公开链接；必要许可证决定由作者作出 | 1–2 人日 |
| P1 | 如 pilot 支持，新增关系差分模式 | 前后源码、关系依据、匹配歧义均可见；不宣称自动修复判决 | 7–11 人日，不能与以上工期简单相加 |
| P1 | 同证据平铺 vs 组织视图的理解 pilot | 各条件拥有相同事实、问题与需求；保留错误、未完成与负担 | 准备约 2–4 人日，招募执行另计 |

当前稿件的合成演示和历史 127 项 Python/9 项插件检查是已有记录；本轮只运行了指定分析器测试文件，18 项通过，没有重新认证全部测试或跨平台可用性。

## Task 2：还可以做哪些工具

两组生成共 16 提案，按相同问题与机制合并为八个家族；完整原始答复和 coverage receipt 在同目录。没有因“看起来不够新”先行删除可行家族。

| 家族 | 用户真正要回答的问题 | 最小产品 | 主要风险 |
|---|---|---|---|
| L1 效果覆盖 | 哪些候选交互还没有审查入口？ | 独立候选清单、未连接证据和源码定位 | 已有方案，主要是补当前覆盖 |
| L2 取消策略 | 关闭后，哪些已接受效果继续，哪些停止？ | 按工作情境并排审查不同效果 | 业务要求输入可能已包含答案 |
| L3 TemporalDelta | 补丁跨过等待点移动了什么检查？ | 关系前后比较和可点击依据 | 普通语法移动太浅，完整语义恢复过重 |
| L4 ReadyPath | 子组件 API 首次使用前真的发布了吗？ | 单一 Vue 发布/绑定协议的证据链 | 模板与实例身份模型尚缺，约 9–14 人日 |
| L5 调度见证解释 | 测试通过时危险顺序是否发生过？ | 短轨迹映射到情境和断言 | 容易成为普通日志/时间线，约 7–12 人日 |
| L6 重审队列 | 哪条旧人工结论因依据变化需要重查？ | 显式依赖的失效解释 | 隐含依赖不完整，约 5–8 人日 |
| L7 清理完成 | 调用了 close/cancel，还是已经等到清理完成？ | 局部 Python 资源退出链 | 容易退化为 missing-await，约 6–10 人日 |
| L8 API 入门 | 哪些使用顺序必须遵守，先读哪里？ | 有来源的协议到消费者导航 | 人工维护文档与 typestate 工作重叠，约 5–9 人日 |

L1/L2 适合完善现有稿件。L4 是另一个具体、有前端经验可用的题目，但需要新框架语义。L6 可以复用 L3 的对齐基础，不能与 L3 同时声称为两套独立算法。

### 直接相关工作

以下为本轮读到的原始摘要、引言或工具说明，不是系统综述。项目没有 `papers/`、`literature/` 或配置的外部本地库；本轮主要用公开作者论文、arXiv、官方文档和 GitHub。未使用 Zotero/Obsidian，也没有用标题推断未读论文的结果。

| 工作 | 发表状态 | 已有方法 | 对我们的约束 |
|---|---|---|---|
| [Slicito — Husák et al.](https://arxiv.org/abs/2503.15675) | ICPC 2025 Tool Demonstration | 交互缩小范围，再组合数据流和符号执行 | 通用交互分析/源码图不是新点 |
| [AsyncG — Sun et al.](https://atlarge-research.com/pdfs/2019-nodejs-async-graphs-hsun.pdf) | CGO 2019，已由 PDF 页脚核对 | Node.js 运行时 Async Graph | 异步关系可视化已有直接前例 |
| [PromiseKeeper — Alimadadi et al.](https://www.franktip.org/pubs/oopsla2018promisekeeper.pdf) | OOPSLA 2018 | 动态 promise graph 和反模式 | 不能泛称首个 promise 关系工具 |
| [Sahand — Alimadadi et al.](https://people.ece.ubc.ca/saba/dl/sahand.pdf) | ICSE 2016 | 全栈异步交互模型与可视化 | 已有理解研究，收益不能转用于本工具 |
| [NodeRacer — Endo & Møller](https://cs.au.dk/~amoeller/papers/noderacer/) | ICST 2020，作者仓库有说明 | happens-before 引导的延迟与重执行 | 调度见证搜索本身已有工作 |
| [DrAsync — Turcotte et al.](https://reallytg.github.io/files/papers/drasync.pdf) | ICSE 2022 | 静态反模式、运行 promise 生命周期与源码导航 | “静态+动态+可视化”不能作为区别 |
| [Caprese — Tavakoli & Alimadadi](https://arxiv.org/abs/2606.21187) | 2026 arXiv v2，同行评审状态未核实 | 历史共同修改与动态依赖的 JS 影响推荐 | 未修改消费者推荐不能笼统声称首次 |
| [Collector-Sahab — Etemadi et al.](https://arxiv.org/abs/2212.11077) | IEEE TSE 2023，arXiv journal ref | 在 diff 中显示观测到的运行状态差异 | 运行时增强 diff 不是空白 |
| [ChangeGuard — Gröninger et al.](https://arxiv.org/abs/2410.16092) | FSE 2025，arXiv v2 Comments 已核对 | Python 成对学习引导执行，检查行为变化 | 不能把静态关系变化叫行为等价证明 |
| [PromiseAwait — Magesty & Montandon](https://aserg.labsoft.dcc.ufmg.br/assets/papers/2026-forge-promiseawait.pdf) | FORGE 2026 | 真实 Promise→async/await 迁移数据 | 可作为候选来源；迁移标签不是 bug/等价标签 |
| [SemaDiff — Ayub et al.](https://arxiv.org/abs/2607.13111) | 2026 arXiv 预印本，发表状态未核实 | 提取未修改依赖调用者，生成调用代码与测试，对比提交前后行为 | “未修改消费者+跨版本比较”也已被研究，不能作为独立新点 |
| [SemanticDiff 官方说明](https://semanticdiff.com/docs/what-is-semanticdiff/) | 现有产品文档，非研究效果证据 | 语言感知 diff、移动/重命名和语法不变量 | “看见代码移动”本身不够 |

冻结的十篇论文提取槽 LIT01 覆盖 10/10；评审后根执行器另外联网读到 SemaDiff 摘要，并单独补入上表。原十篇的覆盖范围不变，依据根执行器先冻结的原文摘录和摘要；抽取槽未再次联网核验。后续原始 arXiv 页面补充确认 ChangeGuard 为 FSE 2025；冻结文件原有未决状态保留，不暗改历史证据。AsyncG 曾被初始生成 prompt 误写为 ICPC 2019，两个生成槽及根执行器根据 PDF 修正为 CGO 2019，报告只使用修正后的信息。

## Task 3：推荐先验证的 idea——TemporalDelta

工作标题：**TemporalDelta: Reviewing Changes Across Asynchronous Boundaries**。

目标用户是审查异步补丁的开发者。一个最短任务是：“两个版本都有等待后的效果提示；这次改动到底在哪个等待点之后重新检查了有效性？”

### 实际构建步骤

1. 输入两个明确版本的 JS/TS 源码范围，保留报告和原始源码快照。
2. 对齐同一函数内的声明、等待、检查和用户选定/工具提名的效果位置；目标不唯一时输出 unresolved，不偷偷选一个相似名称。现有 eN 遍历编号、含 offset 的 block 以及重名函数 # 序号均不是跨版本稳定身份，不能直接沿用作匹配键。
3. 比较有限关系，显示“检查从这个 await 前移到后”“候选效果仍在此处”等具体变化与双边源码锚点。词法先后标为词法先后；只有实现了对应局部退出/分支模型才显示该区域的控制关系。
4. 在现有 compare 页面展示变化和待核查问题。通过唯一命名导入可解释的一跳调用者可以后加；没有关系证据就不展示确定影响集合。

一个可理解的输出是：

```text
refresh() / render(result)
before: active 检查 → await read() → render
after : await read() → active 检查 → render
改变 : 检查跨过等待点
依据 : 两版对应源码位置
待核查 : active 是否描述这次工作？等待期间它能否变化？
```

这个输出不直接写“修复成功”“保护充分”。控制流、异常、循环、别名、重赋值或工作身份超出支持范围时，缺口必须可见。当前 parser 的 conditions 记录 if 分支，却不将 early return 的否定条件传播到后续效果；因此不能仅凭现有 conditions 声称已经恢复 guard→effect 保护。第一版先准确输出检查与等待的关系，局部控制覆盖需另有明确定义和检查。

### 有限新意与最大风险

候选贡献是：**把跨异步边界的关系变化作为审查对象，并用源码依据解释它为何值得重新核查**。它有可能让审查者少追踪一些散落语句，但这仍是待检验假设。

与原项目相比，新输出单元是关系 delta，不是 finding 数量。与 SemanticDiff 相比，需要把语句移动连成明确的等待点—检查—候选效果审查材料。与 Collector-Sahab/ChangeGuard 相比，第一版不依赖运行并不作行为等价判定。与 Caprese/SemaDiff 相比，若将来推荐消费者，必须展示它与具体关系变化之间的有限依据；单纯把未修改调用者接到跨版本比较上已经不构成区别。

这些是基于已读工作提出的区分假设，不能证明相关工具完全没有相同能力。正式稿写差异前仍需对直接比较对象做功能级查新。

最大风险：如果工具只是把“移动了 if”换成一句话，普通 diff 已足够；如果必须恢复所有对象、路径和调度语义，三周范围又不成立。核心原型应在这两者之间，用有限但可核查的关系说明审查问题。

### MVP 范围

- 第一版只做 JS/TS，同一文件的唯一具名函数、一个显式 await、可对齐的检查和局部效果。重复/匿名/重命名目标先显示未支持。
- 局部控制关系仅支持明确定义的直接 if-return 模式；复杂分支、循环、异常路径保持未知。现有文本压缩规范化不能充当 AST 等价判断，也不能抹掉字面量差异。
- 第一轮只比较同一类关系：有效性检查相对 await 的存在与位置，包含明确的新增/移除和跨等待点移动。捕获时点、注册/清理顺序后置，不同时加入。
- 不同时实现 Vue 实例模型、跨语言、全程序 points-to、自动修复、通用调度器、LLM 推断业务策略。
- 不依赖旧 finding 命中作为唯一入口；允许用户指定要审查的效果位置。
- 未修改消费者是后续条件能力，不是第一天必做项。若未实现/未验证，题目、演示和主张均不包含它。

### 先做 1–2 天的证伪检查

先固定纳入和排除规则，再冻结 12 对版本，不能看到工具输出后只留成功例：

- 4 对目标关系变化：至少 2 对来自实际维护来源，另外 2 对受控片段。真实来源争取来自两个仓库；同一提交的多个方法不计多个独立来源。
- 4 对负例：2 对纯格式变化，2 对在声明范围内经人工先确认的等价改写。提交信息中的“refactor”不能直接当等价真值。
- 4 对歧义/未支持例：重复事件、遮蔽或重赋值、嵌套回调、复杂控制流，期望明确弃权。

先在纸面 canonical payload 或一次性脚本上核对，不先重做 UI。按“有依据关系、错误关系、未知、原始匹配歧义”逐例记账，源码 diff 和旧 compare 作基础对照。

评审建议的继续条件：目标关系 4/4 有可追溯依据；负例无伪关系变化；歧义例无强制错误匹配；真实例能够提出普通移动标记之外的具体审查问题。此阈值是工程决策规则，不是统计显著性、准确率承诺或会议标准。

停止条件：48 小时内找不到匹配的真实来源；必须引入全程序分析；仍发生错误稳定匹配；或输出仅复述语句移动。失败后执行既有 L1/L2 改造与真实实例核查，不能转做同样依赖对齐的 L6 来挽救工期。通过后再估计剩余窄实现约 5–7 人日；pilot 加实现总体约 7–11 人日，公开交付和论文工作另计。

后续理解收益至少比较：源码 diff；当前提示差分；新关系差分。若要将收益归因于组织方式，还需同事实平铺 vs 关系组织，保证源码、问题、依据、unknown 和业务要求等量。没有实际参与者或受控对照结果时，论文只写工程与案例证据。

### 一个已找到的真实案例来源

本轮通过 GitHub 读取了 [VS Code 固定提交 b7fc990](https://github.com/microsoft/vscode/commit/b7fc99026406e926fb4710809f75788672f24205)。补丁在加载完成后的多个入口补充 disposal 检查，并增加以 DeferredPromise 控制“等待期间 dispose”的测试。该提交涉及新增 guard 和扩充谓词，并非已有 guard 从 await 前移到后。它证明这类维护问题有真实来源，可供后续“检查新增”的候选评估；不能当作真实“移动检查”样本。本轮未运行上游测试，也未将其纳入独立效果评估。

此外找到 task-system readiness 修复和关闭前等待数据库写入的提交元数据，见 `external-case-scout.json`；尚未逐一复现。三个提交同属 VS Code，不能宣称三个独立项目。PromiseAwait 可扩充候选来源，但必须重新核查目标关系和语义要求。

## 最终排序与评审响应

完整评审在 [ranking-review.md](ranking-review.md)。综合交付价值排序为 L1 → L3 → L2 → L6 → L7 → L5 → L8 → L4。L1 排第一是因为可复核的当前覆盖缺口；L3 是唯一新增 pilot 候选，不能将两个排序混成“两个工具都完整实施”。L6 同样依赖跨版本对齐，不是 L3 失败后的低成本替代。

已吸收的评审修正：补入 SemaDiff；明确事件 ID 与 early-return 模型缺口；区分真实提交的新增检查与合成例的移位；追加初始 inactive/read 调用实测；将 pilot 分为目标/负例/弃权三组。以上均是方案或诊断材料修订，产品能力未因此变化。

## 投稿安排与交付边界

本轮直接获取并核对 [ICPC 2027 Tool Demonstration 官网](https://conf.researchr.org/track/icpc-2027/icpc-2027-tool-demonstration)：截止为 **2026-11-19 AoE**；IEEE `10pt,conference`，正文 4 页、参考文献可额外 1 页；非双盲；工具源码或二进制必须公开；3–5 分钟视频为建议项。官网强调工作原型、程序理解相关性、技术基础、成熟度与预期使用/影响。独立用户研究是竞争力增强手段，不应写成官网强制条件。

建议在 11/2 前决定是否做 L3；11/3–11/9 只推进选定机制和真实实例；11/10–11/14 冻结实现、整理证据和英文演示；11/15–11/18 完成外部试装、论文主张/页数核对。若实际实现或证据落后，沿已有稿件收窄主张，不同时开三条工具线。

## 本轮做了什么、没有得到什么结果

- 完成当前 diff/源码与 Oct29 方案的检查；未改 analyzer 产品代码或现有论文。
- 两个固定生成槽各八项视角，机械合并为八家族；文献抽取十篇，根执行器另核对 SemaDiff；fresh-context 排序评审另附原始答复与 trace。模型同家族评审仅为 provisional。
- 实际执行一个作者构造源码对及三个受控情境；两个已暴露开发案例只读扫描。它们均不是独立效用实验。
- `python3 -B -m unittest discover -s tests -p test_temporal_contract_analyzer.py`：18 项通过。该测试范围不能替代完整套件、IDE 宿主或跨平台检查。
- 复现：从 analyzer 根运行 `python3 -B idea-stage/probe_current_tool.py`。它只执行脚本内作者自写的 JavaScript；benchmark 候选只读取，不执行，不改历史输入/oracle/结果。
- 新增研究输出位于 `idea-stage/` 和 `.aris/`；仅追加 MANIFEST 记录。开始时已有的 10 个跟踪文件修改保留原样。
- 没有证实新工具效果、完整新颖性、缺陷检出率或录用可能性。没有 GPU 作业、付费效果实验、参与者研究、公开发布或 Git commit。

## 建议 Git 提交文字

```text
docs: assess temporal analyzer and propose bounded temporal diffs

- Record current-tool probes, external case sources, and literature comparisons
- Preserve the existing effect-review plan and rank eight tool directions
- Specify a bounded temporal-diff MVP, pilot criteria, and submission priorities
- Validation: 18 focused analyzer tests passed; ideation probes reproduced
```

仅准备提交文字；实际提交时只选取本轮研究输出，不能把工作区原有产品改动一起纳入。
