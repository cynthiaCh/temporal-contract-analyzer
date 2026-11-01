# ICPC 2027 Tool Demonstration — Paper Plan

日期：2026-10-29（Asia/Shanghai）。状态：draft assurance；实现描述已对照源码，独立效用研究尚未完成。

## 一句话贡献

Temporal Contracts 将源码派生的候选时序证据组织为四问边界审查卡，支持开发者定位、核查并记录异步与生命周期边界上的有效性要求。

## 范围与格式

- 工作标题：**Temporal Contracts: Reviewing Asynchronous and Lifecycle Boundaries with Source Evidence**。
- ICPC 2027 Tool Demonstration；IEEEtran `[10pt,conference]`；正文不超过 4 页，参考文献最多额外 1 页；非双盲，作者信息暂用明确占位。
- 官方来源：https://conf.researchr.org/track/icpc-2027/icpc-2027-tool-demonstration 。截稿 2026-11-19 AoE。
- 本文是 analyzer 工具稿。既有 benchmark、Paper 1 的案例数与模型结果不移入本文；不适用 Research Track 稿件的四段长 Introduction 要求。
- 不强行套用科研技能的一页 Related Work 和长篇实验章节；遵守用户指定 Tool Track 的 4+1 预算。

## Claims–Evidence Matrix

| ID | 可写主张 | 现有证据 | 状态 | 位置 |
|---|---|---|---|---|
| C1 | 从 Python、JS/TS 和 Vue 脚本提取位置、事件和有明确限定的候选关系 | core.py、python_adapter.py、parse.cjs、lifecycle.py、reentrancy.py；语法与 Vue 测试 | implemented；全局正确性未经证明 | §II |
| C2 | 每条 finding 投影为四问卡片；关系判断与保护充分性分别记录 | boundary_cards.py、archive.py、hub.py、web/app.js、test_report_hub.py | implemented；可用性收益待测 | §II–III |
| C3 | CLI、VS Code、MCP 共享报告 ID 和源码快照，支持历史核查 | archive.py、mcp_server.py、runner.js、归档与 MCP 测试 | implemented；运输记录不代表 Agent 使用 | §II |
| C4 | 受控合成示例可演示关闭后旧延续写入，以及显式失效检查 | paper/demo/；demo-traces.json、demo-analysis.json、demo-comparison.json；可复现脚本 | executed synthetic demonstration；不是独立案例评估 | §III |
| C5 | 工程回归测试通过 | paper/evidence/python-tests.log：127 Python tests；extension-tests.log：9 extension runner tests | logged rerun passed；不等于语义有效性 | §IV |
| H1 | 比源码搜索/原始提示更准确或更快地回答时序理解问题 | 尚无独立对照数据 | unadjudicated / needs experiment；不得写为结果 | 后续评估 |

## 章节预算（正文合计 4 页）

| 文件 | 目的 | 页预算 |
|---|---|---:|
| 0_abstract.tex + 标题作者 | 问题、工具机制、交互流程与演示证据范围 | 0.40 |
| 1_introduction.tex | 关闭与延续的理解问题；三项工具贡献 | 0.55 |
| 2_tool.tex | 三层架构、四问卡片、人机职责及归档 | 1.15 |
| 3_demonstration.tex | 一条受控异步调度，含保护版本和核查流程 | 0.85 |
| 4_evidence.tex | 已执行验证、独立评估计划与具体限制 | 0.55 |
| 5_related_work.tex | 问题驱动程序理解、交互分析、事件竞争检测 | 0.35 |
| 6_conclusion.tex | 工具贡献；当前公开交付状态与 AI 使用说明 | 0.15 |

References 可使用剩余正文空间或单独第 5 页；不添加附录。

## 图表计划

- Figure 1：可编辑 TikZ 架构图；源码 → 语法事件/限定关系 → 四问卡片 → 人工判断，归档支撑 CLI/IDE/MCP。说明实线是材料流，不是程序运行时 happens-before。
- Figure 2：实际运行工作台截图，来自明确标识的合成示例；不伪造英文界面或已完成审查记录。
- Listing 1：带 epoch 检查的缩减示例；未保护版删去两行身份检查。图文说明检查由人提供。
- Table I：规则族、提取内容、尚需核查内容。
- 独立结果表暂不放空数字：评估计划明确用将来时书写，未完成数据留在增强路线图中。

## 引用计划

优先使用出版者/作者页面的正文与 BibTeX；DBLP/CrossRef 获取记录。计划引用 Sillito et al. FSE 2006、Slicito ICPC 2025、EventRacer OOPSLA 2013、Whyline ICSE 2008。逐项保存来源；只在稿件保留实际引用的记录。不声称系统查新完成。

## 审查安排

按 paper-plan 与 paper-write 的 reviewer slot 分别进行 fresh-context GPT-6-Astra xhigh 评审，保留原始请求、答复及修订记录。同模型家族评审只记 `same-family / provisional`，不作为投稿通过认证。

## 下一步

1. 审查大纲，收敛贡献与技术范围。
2. 写全英文 LaTeX 正文，运行合成演示并留存测试日志。
3. 编译 PDF，核对 4+1 页、交叉引用、引用和图片。
4. 独立审稿并修订；交付中文增强路线图与尚缺证据。

## 本次执行情况

- 英文完整稿、TikZ 图、真实截图、双版本合成演示、两份归档与比较结果已生成。
- 当前 PDF 为 3 页正文（含 acknowledgment）加 1 页参考文献，满足上限；保留作者占位，未公开发布。
- 大纲 fresh-context 评审：逻辑 8/10，主张证据 8/10，证据准备 6/10，定位 7/10，篇幅可行性 6/10；已回应机制和演示问题。
- 正文 fresh-context 评审：PASS AS A WORKING DRAFT；关闭评审时无未解决 critical / major 项；minor 项的修订与保留理由见 `paper/reviews/draft-response.md`。
- 两次均为同模型家族 provisional。原始意见、响应和本地 trace 分别保留；没有将其称为独立验收或正式录用预测。
- 独立项目与理解收益数据仍待开展，增强方向见 `paper/TOOL_ENHANCEMENT_ROADMAP.md`。
