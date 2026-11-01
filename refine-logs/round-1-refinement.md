# Round 1 Refinement: Effect, boundary and work context

## Anchor Check
The original bottleneck remains source-backed review of different effects across temporal boundaries. No automatic repair or LLM inference component is added.

## Simplicity Check
One dominant contribution: bounded source evidence organized by effect x boundary x work context. Shared archive is reused. Whole-program ownership, full Vue scheduling and automatic policy inference remain out of scope.

## Changes Made
1. Seeds are independent of existing findings, including supplied callbacks and object calls with explicit candidate status.
2. Declaration-qualified symbol references replace bare identity labels. Runtime instance and accepted-work semantics remain unknown until source-backed review.
3. Judgments are per effect x boundary x context, preserving new-admission versus accepted-completion distinctions.
4. F and U share every node, typed edge, context membership, unresolved link and question.
5. The developer pilot has 6 primary tasks from distinct declared reuse families, 12 slots, 72 answers. It measures directed review with shared requirements, not spontaneous hidden-contract discovery.
6. Exposed source lineage, incomplete scope, normative support, unknown scoring and participant/task dependence are explicit.
7. Optional Agent integration needs a new adapter; existing frozen A-G runners are not silently replaced.



# Problem Anchor

- Bottom-line problem：利用现有 temporal-contract-bench 的任务、候选源码、行为对照与来源记录，设计一个更能帮助核查跨边界时序要求的工具，以及能检验其实际价值的实验，服务 ICPC 2027 Tool Track。
- Must-solve bottleneck：现有四问卡片主要重组启发式 finding，尚未明确连接 continuing work、对象/操作身份、不同消费者效果及保护位置；合成单例与实现测试不能回答真实审查价值。
- Non-goals：本轮不修改 benchmark 历史输入、oracle、冻结结果或独立发布版；不把既有开发案例称为未见验证；不启动付费模型或参与者研究；不在设计阶段实现全程序验证器或自动修复。
- Constraints：当前 analyzer 支持 Python、JS/TS 和 Vue 脚本；复用既有解析、归档与接口；来源相关表示不计独立样本；评估者材料与工具/Agent 可见材料分离；ICPC 2027 Tool Track 时间预算约三周。
- Success condition：从实际源码扫描与代表案例中定位可复核缺口；给出小而具体的数据结构和模块修改；实验有固定对象、信息等量对照、逐义务/消费者指标与停止规则；正、负或无效结果均能确定论文可写主张。

# 工具改造规格：以具体效果为单位核查边界

日期：2026-10-29。**状态：设计，尚未修改产品分析器。** 基线实测见 `BASELINE_DIAGNOSIS.md`。

## 1. 先改什么

当前 22 个本地 core 有 74 条 finding，只有15张卡的 effect 槽有引用，其中还包含局部临时写入。10个有提示的 core 没有任何 effect 槽引用。最先要解决的是“审查具体影响哪个效果”，而不是再加一批边界关键词。

最小路线：**独立提名效果候选 → 关联有依据的边界、值与保护 → 按效果×边界×工作上下文分别核查 → 未连通处明确保留未知。** 既有 finding 成为证据入口，不再限定所有新单元的种子。

同一个 `record(frame)` 在退休后新事件接收的上下文中应被阻止，在退休前已经接收、退休后解码完成的上下文中却可能必须继续。effect只是源码位置，不能独自决定政策。acceptance/admission/completion 是人工确认的语义阶段；机器最多标注 listener callback/Promise continuation 等源码上下文候选。

## 2. 三个必须看得见的前后变化

| 案例与实际位置 | 当前报告 | 改造后应展示的候选结构 | 人仍需判断 |
|---|---|---|---|
| `transfer-progress-maintenance-v2-vanilla/base/src/progress.js` 的 `record(frame); receive(frame)` | 4条 finding，但所有卡均无 effect 引用；两个调用不在 finding evidence 中 | 从两个参数回调独立建立两个候选效果，显示它们共享 decoded/deliver 回调上下文，语义政策各自 unknown | 哪个消费者承载已接受历史、哪个是当前 UI；关闭后各应继续还是停止 |
| `document-submit-snapshot-vanilla/base/src/workspace.js` 的 `archive.capture` 与 `renderSubmission` | 已有 snapshot-output-lifetime-split，但 effect 槽主要拾取 origin/receipt 局部写入 | archive 调用和外部渲染回调各一个单元；显示 origin 捕获、receipt 使用、flush 若已存在则列为边界候选 | 提交归属、旧访问通知和同步导航优先级；不自动认为两者共用一个 guard |
| `listener-registration-order-vanilla` 的 subscribe/receive 与 metrics | 有注册/清理线索，但没有完成实例与消费者策略恢复 | 注册→回调体是源码连接；decode→receive 的局部引用候选；presence/metrics 分开列出，跨工厂实例保持 unresolved | bootstrap 应先登记还是后登记；当前 visit 与 channel 是否同一身份 |

对 readiness 负例：显示“脚本已解析、跨组件 API 发布/绑定未建模”，保留零 finding；不能补一个泛化 Vue 规则后声称已经解决。局部 `formApi.setValue` 可成为交互候选，但子组件 `input` 到父组件 `v-model` 的连接仍需专门语义支持。

## 3. 可实现的输入、输出和边界

### 3.1 用户输入

- 必需：候选源码根或编辑器文本；显式扫描文件/目录范围。
- 可选：用户指定的审查文件/函数/效果位置，对所有实验条件相同。
- 不读取：case ID 对应的答案、`oracle/`、`reference/`、`mutants/` 标签、历史结果来决定候选。
- 研究者测试 reference/mutant 时，先在新的中性候选目录物化该版本，工具只见这一棵源码树；oracle 在评分侧隔离。

### 3.2 候选种子，不依赖 finding 是否命中

在声明的源码范围中保留以下类别，分类名明确为 interaction/effect **candidate**：

| eligibility | 机械依据 | 例子 | 限制 |
|---|---|---|---|
| supplied_callback_call | 唯一参数声明绑定的直接调用，包括合法闭包捕获 | `receive(frame)`、`renderSubmission(receipt)` | 回调可能纯计算，不据此断言可观察输出 |
| supplied_object_call | 参数对象成员调用，receiver 根能绑定到参数 | `archive.capture(...)`、`state.showQueued(...)` | 包括 read 等纯查询；必须计审查负担，不能把名字当类型 |
| member_write | 成员/索引写入事件 | `state.current = ...` | 属于候选状态效果，不自动证明外部可观察性 |
| mutator_name_clue | 复用现有 reentrancy mutator 词表 | `records.set(...)` | 仅名称依据，不能等同实际 Map/持久化 |
| existing_effect_name_clue | 复用现有 effect tags | `publish(...)`、`commit(...)` | 保留原弱依据 |

局部 `const origin = ...` 不独立成为效果单元，但可作为 capture 证据。重复命中同一 event 合并 eligibility，不重复计单元。没有绑定信息时保留弱候选或 unresolved，禁止凭名称补出参数身份。所有种子都可追溯，不用 Top-K 静默隐藏不利候选；材料超预算需明确失败或按预注册同一范围规则处理。

### 3.3 最少新增的符号信息

当前 `scope` 与字符串 references 不能消除所有遮蔽和重赋值。需要在 JS/Python adapter 中补**声明限定的 symbol 引用**，并保留现有字段供旧版本读取：

```text
symbol_id = path + declaration_start + binding_kind
binding_kind = parameter | local | import | unknown
reference = {symbol_id?, access_path, source_range, resolution_status}
```

JS 分清函数/块作用域和参数解构；Python 遵守函数局部、闭包、global/nonlocal 的实际边界，不确定保持 unknown。对多次赋值，第一版不做 reaching-definitions：关系标为 reassigned/ambiguous，不构造确定 capture flow。access path 相同不代表对象实例相同。

### 3.4 最小关系集合

| kind | 建立条件 | 不能推出 |
|---|---|---|
| lexical_before | 同一语法块的明确位置先后 | 两点都可达或必然按此运行 |
| callback_body | inline callback_argument/returned_callback；或实参唯一绑定到未重赋值的本地命名函数/闭包，并映射到其function scope | 传入函数就等于执行、一定同步通知；命名目标不唯一时保留unresolved |
| value_reference | 同一声明限定符号在 capture/argument 中出现 | 对象不可变、没有别名写入 |
| predicate_reference | guard 表达式引用该符号 | guard 足以保护效果 |
| guarded_region | 效果在相应 if 分支的语法区域内 | 条件蕴含业务有效性、跨异常路径完整 |
| candidate_call | 唯一命名导入/局部函数的一层候选目标 | 动态派发、跨工厂实例或完整调用链 |
| lifecycle_cooccurrence | 复用原生命周期词法共现线索 | 同一请求、同一资源或同一消费者 |

早退形式 `if (obsolete) return; publish()` 可先显示 predicate 与源码先后；如果没有结构化的退出边证明，就不能标为 guarded_region。v1 不做完整 CFG 或支配分析。

命名回调的“未重赋值”允许声明自己的 initializer。例如实际 `const deliver = frame => ...` 同时生成function binding和初始化write；不能直接复用 `not writes` 而拒绝它。必须区分declaration initialization与后续assignment；额外write、目标遮蔽或目标不唯一时显示unresolved。验收必须包含真实 `.then(deliver)`、`addEventListener(..., listener)`，以及后续重赋值的负例。边只证明该函数值被传入调用，不证明通知实际发生或同步发生。

### 3.5 review unit（示意 schema）

```json
{
  "id": "u-...",
  "effect_event": "src/progress.js::e...",
  "eligibility": ["supplied_callback_call"],
  "contexts": [{"id": "ctx-...", "callback_scope": ".../deliver", "source_entry_ref": "...", "boundary_ref": "...", "scenario_id": "shared-task-scenario-or-unknown", "source_context": "continuation_candidate", "accepted_work": "unknown", "runtime_instance": "unknown"}],
  "capture_refs": [{"symbol_id": "...", "event_id": "..."}],
  "predicate_refs": ["..."],
  "relations": [{"kind": "value_reference", "from": "...", "to": "...", "basis": "declared_symbol", "status": "candidate"}],
  "unresolved_links": [{"kind": "consumer_ownership", "reason": "no unique instance binding"}],
  "origin_findings": ["hint-..."],
  "scope_status": "bounded_source_review"
}
```

独立 notes 以 `(effect_event, context_id)` 为键，存 `relationship`、`protection`、`effect_policy`（应继续/应停止/未知）、acceptance依据、缺失证据与 actor。context_id 必须区分边界与源码入口/给定scenario，不仅是callback scope；同一个deliver在新接收与已接受完成的问题中允许分别审查。scenario来自共同任务或用户提供的情境，不能由隐藏oracle自动注入。不得按effect一个标签覆盖所有边界情境。用户确认的 consumer/ownership 链与机器关系分别存，不写入 source-only 冻结材料。共享传输对象不能自动充当 visit identity。上下文不明确就保持unknown，不能拼成完整因果链。

## 4. 函数接口与模块改动

```python
collect_effect_candidates(report, scope=None) -> list[EffectCandidate]
derive_review_units(report, scope=None, max_direct_call_hops=1) -> ReviewUnitReport
render_units_flat(units) -> str
render_units_grouped(units) -> str
```

`derive_review_units` 是纯函数；不扫描其他目录、不调用模型、不读人工答案。F/U renderer 使用同一个 canonical payload：节点、symbol、typed edges、端点、依据、未闭合项、范围限制和问题正文全部相同；只有排序、分组与交互定位不同。将这些关系藏在 U 的图中、却从 F 文本省略，会破坏信息等量对照。

| 模块 | 必改内容 | 最小验收 |
|---|---|---|
| `tools/.../parse.cjs`、`python_adapter.py` | 声明限定引用及局部 guarded_region；保留旧字段 | 遮蔽、重赋值、跨闭包三种实际用例不误连 |
| 新 `review_units.py` | 独立种子、关系、unresolved、effect 分组 | record/receive 两个单元；没有业务政策自动标签 |
| `boundary_cards.py` | 新旧视图明确区分 | V0 原 payload 可复现，不覆盖旧实验 |
| `core.py`、CLI/归档入口 | 范围/预算/部分失败描述；PHP 等未收集源码显式说明 | unsupported/timeout 不显示为零风险；可指定局部库范围 |
| `archive.py`、`report.py` | 派生视图与独立 notes | 扫描、人工注释、行为结果三者可分别追溯 |
| `web/app.js` | 效果并列、依据与未知连接；逐效果保护判断 | 应保留记录与应抑制 UI 能分别标注 |
| `layers.py`、`experiment.py`、MCP | 新材料名、flat/grouped；冻结材料接口与 notes 边界 | 不替换旧 B–G，也不隐式注入作者判断 |
| 新实验适配入口 | 绑定新版工具材料与原 bench 物化/评分 | 新计划新目录，历史 scorer 和输入不变 |

## 5. 与 benchmark 对齐的验收矩阵

| 族 | 正确/错误对照 | 应验证的工具行为 |
|---|---|---|
| listener | bounded vs order-only/channel-identity/late-owner | 保留注册顺序、pending decode、visit/transport 区别与重入待核查项；metrics 单独列出 |
| document submit | bounded vs retarget-after-flush/drop-accepted-submit/document-key-notice | archive 与通知两个候选效果分开；捕获与 flush 的前后证据保留；不判统一取消 |
| transfer progress | bounded vs drop-accepted-progress/register-only | record/receive 均独立提名；接收前 admission 与完成后的 UI 有不同检查位置 |
| download | bounded vs shared-dialog-policy/retry-without-invalidation | foreground/background 不自动合成一个关闭政策；重开与 token 复用保留未知 |
| async generator | bounded vs detach-aclose/close-only-on-match | 列出 return、资源和 close/await 源码位置；清理完成不由 close 名称推断 |
| workspace projection | bounded vs local-editor-only/only-workspace-guard | editor 与 caller projection/history 的效果分开；不因局部guard存在关闭整条审查 |
| readiness | bounded vs promise-microtask-retention | 作为明确未建模关系的负例；不得显示“没有提示因此通过” |

以上用于开发回归。元数据、reference、mutant 名称和已有行为结果只留在研究者侧，不成为提取器规则。

## 6. 推进顺序与删除规则

1. **先做种子与完整性**：修复真实 record/receive/renderSubmission 漏槽；记录 unsupported/scope/timeout。先看每个单元是否有可点击真实源码。
2. **再做有界符号连接**：只做局部 capture/predicate/一层调用；无足够依据就显示未知。
3. **最后做并列审查与 F/U 材料**：图形不是必要条件，先用清楚的效果表与源码链。若 flat 同样有效，就保留简单视图，不把 UI 当作贡献。
4. Vue API publication、原生上游完整运行、多语言、自动修复均后置。只有代表案例显示同一缺口反复阻碍审查，才增加相应模型。

预计核心实现4–6个专注工作日；符号作用域若明显超预算，先交付明确 scope 的交互候选版并收窄论文，不把弱关联改名为确定身份。性能时限以串行实测再设；本次20秒仅盘点保护，不是产品 SLA。

# 工具改造实验计划

日期：2026-10-29。状态：设计；除 E0 基线盘点外，以下实验均未执行。主线为 ICPC Tool Track 的定向时序审查，最多两个论文主张。

## 1. 主张与关键反解释

| ID | 待验证主张 | 最小证据 | 反解释 |
|---|---|---|---|
| C1 | 新版能把指定源码范围内的候选效果及其边界/上下文证据显式呈现，同时保留未知连接 | E1 的完整候选负担、锚点核查和逐问题证据覆盖；不把 parsed 当覆盖 | 只是扩大关键词命中、局部变量写入冒充业务效果 |
| C2 | 在给定相同源码、要求和证据的任务中，按“效果×边界×工作上下文”组织材料帮助完成有依据的审查 | E2 中 F→U 的信息等量随机化比较；保留错误和未完成 | U 额外得到作者政策、关系边、更多问题或 oracle 答案 |

不预设修复成功率提高、不声称自动推断契约、不以图结构本身主张新意。Agent 维护仅为可选后续，不承担核心论文第二条研究主线。

## 2. E0：已执行的探索性盘点

242表示、24core、11来源单元；历史catalog348材料。结果：139 parsed、72 partial、23 empty、2需上游物化、6超时。22个本地core均解析完成，2个零提示；其74条finding只有15张卡的effect槽有引用。详见 `BASELINE_DIAGNOSIS.md`。

这不是完整准确率实验，也不是正式性能测量。20秒时限、并发和本轮缓存不能用于宣称快慢；PHP empty、原生未物化、超时和无 finding 不合并。

## 3. E1：改动是否补到了真实缺口（MUST）

### 对象和范围

- 全242保留一个纳入/解析状态清单，用来界定工具适用范围。
- 22个本地core作为源码回归集合，V0与V1使用同样的候选和扫描范围。
- 从下表8个来源单元建立12个开发/核查快照，覆盖 bounded、局部遗漏、错误扩大保护和语义未建模；正式选择须在V1输出人工评分之前登记。
- 这些数据已被作者和工具开发接触，只能称既有语料的开发与内部验证。单独的新项目数据才支持未见项目迁移。

| 任务源 case | source_unit | 关键对照或检查 |
|---|---|---|
| listener-registration-order-vanilla | listener-registration-order | presence bootstrap vs metrics；pending decode与新接收 |
| document-submit-snapshot-vanilla | debounced-submit-flush | 历史receipt保留 vs旧UI抑制；同文档重开不等于同visit |
| download-polling-restoration-low-cue-react18 | download-polling-restoration | 前台关闭 vs后台继续；新token/重开 |
| async-generator-close-python | async-generator-close-python | 提前返回与所有权、异步关闭完成 |
| transfer-progress-maintenance-v2-vanilla | transfer-retry-abort-handoff | admission前退休拒绝新工作；已接受record继续；UI单独保护 |
| draft-async-save-handoff-vanilla | draft-autosave-handoff-v2 | 已接受save、revision、状态提示的不同期限 |
| workspace-draft-projection-latent-vanilla | reentrant-lifecycle-handoff | caller projection/history与editor-local保护 |
| local-config-readiness-latent-vue2 | local-config-readiness | 保留未建模的API publication/use关系，记录负例 |

### 评估者材料与工具输入

评估者可查原rubric、reference、mutant、schedules和行为校准记录；这些只帮助建立可复核问题。机器可见材料只有中性物化候选源码和声明扫描范围。两位复核者独立确认要求的来源和最小证据集，保留分歧；不将 acceptable_evidence_paths 的文件列表自动当完整真值。

候选快照必须标记是原程序、参考控制还是作者错误控制；标签留研究者侧。`reference`/`mutant`原目录名、case标题中答案、oracle测试不能混入工具或参与者的文件名。

### Gold 最小字段

```text
question_id / snapshot_id / source_unit / reuse_family
effect_anchor / boundary_anchor / work_context
requirement_support: task | source | unknown
normative_policy: continue | suppress | unknown
protection_for_stated_scope: sufficient | insufficient | unknown
minimal_evidence_sets: alternatives allowed
missing_link / witness_status / review_disagreement
```

**同一个效果遇不同工作上下文可有不同政策。** 如已退休listener收到新事件应拒绝；退休前已接收decode的历史record应完成。不能用一个effect级continue/stop覆盖两种问题。工作“已接受”由任务/源码支持并由人工确认，不能由函数名自动推断。

### 指标和结果解释

1. 源码锚点有效性：引用确实指向对应冻结版本；工程目标是全部有效，失配必须修复后才开展 E2。
2. 逐候选审查相关性：有多少候选对任务有用；分开报告 parameter callback、parameter member、member write、name clue。不删除 read 等纯查询误候选。
3. 问题证据覆盖：预先声明的最小充分证据集至少有一组被提供的比例；未闭合连接单列。单有endpoint不算恢复了relation。
4. 负担：单元数、重复引用、材料长度；按case/source_unit聚合。无ground truth的关系报告unknown，不进入“正确”分子。
5. 缺口：readiness、跨工厂实例、动态派发及框架调度分别列，不能把它们从主覆盖表静默删掉。

如果候选增加但证据覆盖与相关性均未改善，停止做UI美化，先删减无用种子/关系。若总是只给出两个已知位置而没有有依据连接，论文收窄为线索组织。

## 4. E2：信息等量的定向审查比较（核心，MUST）

### 问题定义

研究**给定要求的审查**：所有条件提供相同候选、同一任务/要求、同一组上下文问题。要求若在原任务中缺失，可使用明确公开给全部条件的简短要求说明；此操纵不再称“从隐含契约独立发现”。只用隐藏oracle建立正确答案、却不给参与者任何可恢复规范，会使判断无效。

每道题对固定 effect×boundary×work_context 判断：该效果在此情境应继续/停止/未知；当前保护是否满足题目规定的有限审查范围；引用源码或指出缺少什么。对潜在任意执行的全局安全性不设置伪真值。

### 条件

| 条件 | 可见材料 | 用途 |
|---|---|---|
| S | 全部源码＋共同任务/要求/通用审查问题 | 常规源码审查基线 |
| V0 | S＋当前0.6.0报告/卡片，无历史人工notes | 现有工具基线 |
| F | S＋V1 canonical证据payload的平铺视图 | 新提取器及信息完整对照 |
| U | S＋与F相同payload，按效果×边界×上下文组织 | 新组织方法 |

F必须包含相同nodes、symbol ID、typed edges及其端点、context membership、依据、unknown、coverage和问题正文。U不得额外获得人工确认、保护充分性结论或oracle。按unit分组的关联若是新信息，必须也序列化到F。所有条件使用同一个作答表单与unknown选项。

V0→F是提取/信息组合的差异；F→U才检验组织差异；S→U不能单独证明布局或认知机制。任务可导航全文源码，不能通过屏蔽原代码人为削弱基线。

### 规模和分配

- 预算方案：12名具备相关语言经验的开发者×6个固定任务快照＝72份回答。主任务为 listener、document submit、download、async generator、transfer progress、local-config readiness；draft async save和workspace projection只用于E1回归。
- 原因：实际完整候选复用检查发现document与workspace的draft-store/trailing-task/search-preview文件完全相同，且三种draft任务具有共同工程谱系。source_unit不同不自动等于独立家族。正式研究前必须对完整物化候选复查字节与来源；发现新的跨任务复用则调整任务集并重新冻结，不能只检查名称。
- 每人四条件各1或2题，余数跨参与者平衡；每个task×condition恰有3份回答。用四条件Williams/Latin分配与预定任务顺序块生成具体表，并检查每人不重复已知reuse family。设计文件是匿名槽位，不代表已招募参与者。
- 六道正式题每题最多10分钟，加训练/休息约80–90分钟/人；总参与者工时约16–18小时。训练使用另外的合成例，不重复正式题。
- 这是小规模pilot预算，未进行功效证明。不能因有72份回答就把样本当72独立开发者或72独立事故。招募、适用伦理流程和同意必须在实际执行前落实；本次不开展招募。
- 若只能6人或更少，明确作为可用性/可行性pilot，仅描述任务结果，不承诺显著性。不能将模型回答替代开发者回答而不更换主张。

已生成的设计材料：`evidence/review-design/allocation.csv` 和 `allocation-checks.json`。12个P编号仅为匿名分配槽位，实际参与者数0、采集回答0。`tasks-analyst-only.json` 记录8个中性base+overlay物化快照及完整文件摘要；6个为主任务，2个为相关谱系控制。`reuse-audit.json` 检查完整候选中的源码重复，发现3对复用，主6题没有字节完全相同的源码文件。没有精确重复不证明语义或历史独立。原scorer验证、gold独立复核和答案显著性检查尚未完成；不能把已准备快照当作正式冻结研究。

### 主要终点

**有充分证据支持的正确判断比例**：每个预注册question评分为0（错误）、1（决定正确但证据不充分）、2（决定及证据均充分）。主要终点为2分question数/该任务全部固定question数，先按任务聚合，再比较条件。所有未答/超时题保留在分母。

- unknown仅在gold确实unknown且回答说明对应缺口时可得2分；对可判定问题unknown计未恢复，不能靠一律弃权提高准确率。
- 同时完整报告原始0/1/2计数，避免平均数隐藏错误。
- 两名评分者使用同一预先定义的alternative evidence sets，尽可能盲于条件。若文字本身透露来源，记录盲法破坏；报告一致性及分歧处理，禁止LLM单独当真值裁判。

**重点错误**单列：误要求停止应保留的accepted record/save/audit；允许退休后的新接收；允许旧UI发布；把同文档/传输当同visit；假称guard已证明充分。这些是分层诊断指标，不追加多个未经控制的主要显著性检验。

时间、浏览文件/位置数和负担为次要指标。超时记为censored/budget exhausted，不能只统计成功者耗时。若正确率相近但时间降低，只能报告相应准确性与不确定性支持的效率结果，不能把不显著说成等效。

### 分析与成功条件

预指定主要对比F→U，V0→F和S→U为次要描述；按参与者和task/source family处理交叉重复测量。该pilot优先展示参与者内和任务内差异、原始分母与分层不确定性。若使用混合模型或bootstrap，需在采样前确定实现并验证；6个任务家族不足以支持稳定总体外推或随意选模型。

只有在主要指标方向、实际差异与不确定性共同支持时，才写“在这些定向审查任务中有帮助”。CI跨零或任务间矛盾时保留无明确收益结论。不得在看结果后更换主要终点、增加样本到显著或删除readiness失败题。开发中若必须改工具，重新冻结研究，不续混同一实验。

## 5. E3：可选 Agent 维护（NICE-TO-HAVE）

目的：检验同一材料是否减少逐义务遗漏及错误扩大保护，不测模型内部理解。

- 6任务×S/V0/F/U×3次＝72个新尝试，模型/等级/预算先由作者确定；3重复为探索性预算。模型与随机性可控时记录seed，无法控制不伪称采样seed。
- 所有条件使用相同基础任务和通用开放审查文本；F/U证据同一payload。全部包含不足与未覆盖说明，不能把U列成完整检查清单。
- 固定 `ungranted` 授权范围；允许授权迁移的任务另分层，不把扩大范围当误修复。
- 原case oracle检验新增任务、保留义务、相邻消费者与可观察效果；缺失consumer_outcomes的历史字段不补PASS。
- 保留已开始、有效评分、timeout、invalid、评分故障、逐义务结果、完整补丁/轨迹和成本缺失数。每个任务/sourceunit单列，不将72次重复视为72独立事件，不以check条数作为样本量。
- 历史A–G和cached-feed/structural-transfer结果只作背景，不混入新分母。

**集成限制**：现有 `diagnosticbench.py` 固定导入 bench 的 `temporal_evidence` 并校验旧实现摘要；`agentbench.py run-development` 没有任意新材料的CLI参数。因此不能把新renderer放到路径上后宣称运行器已支持。需要 analyzer-side 新适配器，复用候选物化、Agent进程与原评分接口，显式绑定新工具版本和新材料。该适配器未实现、命令尚不可执行；不修改旧冻结实验去绕过校验。

预算可先做24次dry/sanity槽位计划再决定是否72次，但不得查看试跑效果后按失败率选任务或改变主要分析；模型调用与美元成本本次均为0。

## 6. 时间和决策门

| 阶段 | 产出 | 继续条件 | 资源 |
|---|---|---|---|
| M0 已执行 | E0全量登记与当前扫描 | unsupported/empty/timeout不丢失 | 本机CPU；无模型 |
| M1 1–2日 | candidate seed、源码锚点、unresolved | record/receive和renderSubmission均可被提名；纯查询负担可见 | 工程开发 |
| M2 2–4日 | 有界symbol/context/edge＋flat/grouped | 同名不误连；F/U payload一致；旧结果不被重写 | 工程开发 |
| M3 2–3日 | 独立gold、题目、分配表、试装 | 原要求可恢复；可判/不可判题区分；适用研究准备完成 | 标注与研究准备 |
| M4 研究周 | E2 pilot | 所有数据按冻结设计保存，失败保留 | 约16–18参与者小时 |
| M5 1–2日 | 分析、两个演示、论文改写 | 主张与结果一致；没有效果就收窄 | 分析/写作 |
| 可选M6 | E3 72新尝试 | 时间/预算允许，材料与runner已实现验证 | 付费后端另定 |

## 7. 结果到论文的映射

| 结果 | 可写 | 不可写 |
|---|---|---|
| 只有候选覆盖改善 | 工具呈现更多可核查效果证据 | 开发者理解提高、Agent修复提高 |
| V0→F改善，F→U未见改善 | 提取/信息支持有用 | 效果组织本身带来收益 |
| F→U改善且证据支持 | 在所测定向审查任务中的组织价值 | 普遍隐含契约发现、跨项目泛化 |
| 旧UI保护改善但record受损 | 具体回归与机制限制 | 只报局部成功，称整体修复有效 |
| E2不确定/无效 | 可用性、失败案例和实现范围 | 通过小样本不显著证明等效或有效 |
| E3无收益/回归 | 保留Agent材料实验结论 | 从开发者pilot推断Agent理解提升 |

独立新项目case study、原生上游完整scope验证、更多语言与框架语义属于后续加强项；不为凑benchmark数量提前扩张。
