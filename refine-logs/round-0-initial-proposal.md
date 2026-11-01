# 基于 benchmark 的工具与实验改造方案（初稿）

日期：2026-10-29。目标：ICPC 2027 Tool Demonstration。本文是待实现、待检验的设计，不能替代实际结果。

## Problem Anchor

- Bottom-line problem：利用现有 temporal-contract-bench 的任务、候选源码、行为对照与来源记录，设计一个更能帮助核查跨边界时序要求的工具，以及能检验其实际价值的实验，服务 ICPC 2027 Tool Track。
- Must-solve bottleneck：现有四问卡片主要重组启发式 finding，尚未明确连接 continuing work、对象/操作身份、不同消费者效果及保护位置；合成单例与实现测试不能回答真实审查价值。
- Non-goals：本轮不修改 benchmark 历史输入、oracle、冻结结果或独立发布版；不把既有开发案例称为未见验证；不启动付费模型或参与者研究；不在设计阶段实现全程序验证器或自动修复。
- Constraints：当前 analyzer 支持 Python、JS/TS 和 Vue 脚本；复用既有解析、归档与接口；来源相关表示不计独立样本；评估者材料与工具/Agent 可见材料分离；ICPC 2027 Tool Track 时间预算约三周。
- Success condition：从实际源码扫描与代表案例中定位可复核缺口；给出小而具体的数据结构和模块修改；实验有固定对象、信息等量对照、逐义务/消费者指标与停止规则；正、负或无效结果均能确定论文可写主张。

## 1. 现有材料对方案的约束

1. `benchmark/swe-tempoc.json` 登记 242 个表示、24 个 core、11 个来源/构造单元；`casecatalog.locations()` 当前登记 348 个历史材料。两者不能混作同一个分母。
2. 242 中存在 Java/PHP/Ruby/Go 等当前 analyzer 不支持的语言；两例 core 是原生上游 task，不能因没有本地 `base/` 就算零提示。部分派生任务的 `base/rxjs/` 内含完整上游库，需要显式分析范围。
3. 实测：listener 原始 base 解析完成，有 7 条 finding；document submit 有 3 条 finding。它们能暴露局部位置，尚未自动连成订阅、解码、发布与重入所有权的完整路径。
4. 实测：`local-config-readiness-latent-vue2` 脚本解析完成但零 finding；关键关系在子组件发布 API 与父组件使用 API 之间。不能把 parsed 当作语义覆盖，也不宜把 Vue 全框架语义支持塞入本次最小实现。
5. `studies/observational-consumers-v1`、listener、transfer 和 document 表明：同一已接受工作可能必须完成记录、持久化、审计，却应抑制退休 UI；统一取消或统一 guard 会造成错误。
6. `studies/structural-transfer-v1/RESULTS.md` 保留 24/24 全通过及集中代码未见正确率收益；`cached-feed-mechanism-v1` 中精确契约组也全部通过，未确认额外位置材料的独立收益。它们约束动机，不能充当新工具的对照实验。
7. `results/tool-report-pilot-v1/summary.json` 的 36 个槽位均 NOT_STARTED，是已有冻结计划，不能当作已完成 A–D 实验。

## 2. 技术缺口与方法主线

**方法主张候选：将审查单位从一条规则 finding 改为一个具体效果，显示这个效果关联的边界、工作身份、候选保护和未闭合连接；不同效果分别核查，不替用户决定业务政策。**

主贡献是面向效果的有界证据组织；共享快照与接口是实现支撑。新意尚需与相关工具比较，不声称图结构或局部数据流本身首创。

### 路线选择

- A：静态、可定位的效果审查单元；少量现有绑定与局部 capture/guard 关系；无法连接就显示 unresolved，由用户按源码确认。
- B：让 LLM 自动恢复全仓库契约并评分，再生成修复。它引入模型、提示、成本和新的真值风险，且会改变当前“不调用模型”的工具定位。

选择 A。LLM 仅作为后续可选材料消费者或被测 Agent，不作为契约真值和工具内部必需组件。无需训练，无 GPU 预算。

## 3. 最小实现

### 3.1 输入与输出

输入为候选源码，以及用户选定文件/函数范围。维护任务文本保留为单独可选输入；不从 benchmark 的 case ID、oracle、reference 或历史结果产生线索。

输出 `review_units`，每个 unit 至少包含：

```json
{
  "id": "unit-...",
  "effect": {"event_id": "...", "role": "call_or_write_candidate"},
  "boundary_refs": ["..."],
  "identity_refs": ["..."],
  "protection_refs": ["..."],
  "relations": [{"from": "...", "to": "...", "kind": "lexical_order", "basis": "AST", "status": "candidate"}],
  "unresolved_links": ["callback instance / consumer ownership not established"],
  "origin_findings": ["hint-..."],
  "review": {"relationship": "uncertain", "protection": "uncertain", "policy": "unknown", "support": []}
}
```

`review` 仍为独立人工 notes，不混入冻结源码报告。policy 由人工描述“该效果应继续/应停止/尚未知”，不由 `save`、`render` 等名称判定。手工建立的边带 actor、源码依据和时间，与机器提取边分别显示；对照实验中手工材料不得只提供给新工具条件。

### 3.2 提取边界

复用现有 `scope`、`references`、`value_references`、参数、`call_links`、callback_argument 与 returned_callback。第一版仅做：

1. 单函数/词法闭包中的值捕获、比较 guard、后续 effect 的引用关联，遇重赋值/遮蔽保留未知；只描述语法控制候选，不输出保护充分性。
2. 唯一相对命名导入与唯一局部函数/直接回调候选，最多扩展一层；对象成员、跨工厂实例和框架调度无法确定时不强行连边。
3. 从既有 finding 中按 effect event 分组，保留原 finding 与规则依据。找不到 effect 时保留 unassigned finding，不凭空制造效果。
4. 一次工作存在多个效果时保留多个审查单元，并列显示共享边界，但不合并其政策。可由用户确认不同消费者。

不添加全程序类型/别名求解、框架调度模拟器或自动修复。readiness 例第一版明确为“语义未建模”的负例，保留后续局部 API publication adapter 的扩展接口而不先实现。

### 3.3 界面和材料

- 默认先看 effect 与源码；显示已连接证据和 unresolved link，不用线索数表示风险。
- 一屏并列展示两个不同效果的核查状态，例如持久记录与旧 UI；初始政策均 unknown。
- 每条边显示现有依据（名称、共现、词法顺序或绑定候选），不编造正确性置信分。
- 允许选中局部范围并展示未覆盖范围；扫描总时限与分文件失败明确记录，不把超时当零提示。
- 实验先冻结机器材料再让人核查；人工审查意见使用另一个明示条件。MCP 冻结报告读取与 workbench 的人工注释交接保留区别。

### 3.4 修改位置

| 位置 | 改动 |
|---|---|
| `core.py` 与 JS/Python adapter | 仅在确认当前字段不够时补 capture/guard/局部控制关联；提取依据显式化 |
| 新 `review_units.py` | 纯函数从冻结 report 派生效果单元；支持 unresolved；不读业务 oracle |
| `boundary_cards.py` | 保留 v0 比较入口；新卡片用 effect-unit，不就地混改旧 B–G 语义 |
| `archive.py`、`report.py` | 保存新派生视图；人工关系与政策作为独立 notes；新版本新实验批次 |
| `web/app.js`、`web/style.css` | 效果并列、依据、待连关系、逐效果审查 |
| `layers.py`、`mcp_server.py` | 新实验材料名称，不覆盖旧 A–G；信息等量 flat renderer；不把 notes 隐式注入 Agent |
| 新 analyzer-side 实验适配入口 | 使用现有 bench 的候选物化与评分接口，新输出目录与版本；不替换 bench 内冻结工具 |

## 4. 三个核心实验块

### E1：工程与证据覆盖

对登记的 242 表示逐一说明完整解析、部分解析、不支持、上游待物化、超时。当前只读扫描属于探索性基线，不是缺陷检测率。选定代表实例的人工 gold 保存 effect、boundary、identity、relation 和源码锚点；case manifest/rubric 只是标注线索，不能直接当 gold。

报告逐单元有依据关系准确率、关键证据覆盖、未闭合率和审查负担。按 source_unit/来源家族聚合；242 表示不等于242独立事故。扫描解析成功和缺陷检出必须分开。

### E2：效果区分与保护审查（主实验）

从现有材料选约 12 个任务快照、涉及 8 个来源单元，覆盖完整保护、遗漏保护、错误扩大保护和信息不足。reference/mutant 由评估者在独立临时工作区物化，统一成中性文件名，不能把目录名和 oracle 标签交给工具或参与者。

四条件：S（源码＋共同通用问题）、V0（当前报告＋共同问题）、F（新提取证据的平铺材料）、U（与 F 完全相同的证据和问题，按 effect-unit 组织）。V0→F 检查提取增量，F→U 检查组织增量。S/V0/U 的总体差异不能单独归因为 UI。

优先小规模开发者 pilot：12 人×8 个任务＝96 个回答，每人同来源单元至多一个任务，四条件各2题；跨人平衡任务×条件，训练任务不重用正式任务。每题回答各效果是否继续、身份如何确定、保护充分与否及源码依据。初拟每题10分钟；独立评分者按预先规则盲于条件评分。12×8的设计是可行性预算，不是已证明统计功效。

主要指标为有源码依据的逐效果政策/保护判断，以及误抑制应继续工作和漏抑制退休 UI；时间和浏览位置为次指标。unknown 对确实缺证据的题目可正确，对已知可判定题目计未恢复；不得通过大量 abstain 提高准确率。

现有语料全部具有作者/工具暴露历史。研究可检验此任务集中的随机化辅助效果，不能宣称未见项目泛化。来源单元和代码复用谱系用于分组；补充新项目才支持外部迁移主张。

### E3：可选 Agent 维护与越界修改

只有 E1/U 比 F 提供可测价值且材料冻结后，再选择 6 个现有维护任务×4 条件×3 次＝72 次新 Agent 尝试。固定模型、等级、预算和原任务，每次启动独立工作区。全部条件同样保留通用开放审查，防止局部线索造成闭合检查清单。

沿用 bench 原 oracle 的逐义务/消费者结果，统计目标任务完成、应继续的持久化/审计是否受损、退休 UI 是否仍输出及邻近消费者是否被迁移。固定策略3重复只是探索性预算；主要按任务/来源展示，不能把72次当72事件。保留超时、故障、成本缺失与回归，不能混用历史 A。

## 5. 决策规则与可写主张

- E1 仅提高覆盖，E2无收益：只写实现/证据支持，不写理解收益。
- V0→F改善但F→U无改善：贡献归因于提取，不包装为四问/布局优势。
- F→U改善，且错误扩大保护未增加：支持效果组织在所测任务中的理解价值；外推限于参与者与任务范围。
- U减少旧UI输出但丢审计/持久工作：机制失败，不能只报总通过或局部胜利。
- E3无收益或回归：保留结果，工具论文可以转向开发者审查，不声称 Agent 增益。

## 6. 复杂度与工时

无训练组件、无需 GPU。最小静态/视图实现约4–6工作日，独立标注和pilot准备约3–5日，参与者执行约20人小时，分析写作约2日。按可用人手决定是否开展pilot，不能把招募/伦理审批当作已具备。72次Agent预算按实际后端配置另行核算，不自动启动或推算美元。

三周内优先 E1＋两个代表演示＋信息等量对照。原生上游完整运行、更多语言、全框架 readiness、全量 Agent sweep 为后续扩展，不先扩大系统。

## 7. 相关方法与新意边界

Slicito ICPC 2025 已展示交互缩小范围与更精确分析：https://www.d3s.mff.cuni.cz/publications/husak_combining_2025/ 。CodeQL 已提供局部/全局数据流：https://codeql.github.com/docs/codeql-language-guides/analyzing-data-flow-in-javascript-and-typescript/ 。这些来源约束“有图/有导航即创新”的表述。本文待检验的差异是跨边界的不同效果与政策分别核查，以及机器证据、未闭合关系和人工判断的可见区分。
