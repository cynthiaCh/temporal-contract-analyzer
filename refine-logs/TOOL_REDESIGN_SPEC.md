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
