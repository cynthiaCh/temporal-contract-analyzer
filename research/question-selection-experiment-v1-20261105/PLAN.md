# 小规模选题对照实验（冻结前计划）

目标：判断自动选择问题是否值得继续投入，不预设题库有收益。Task 1 核对历史、来源与校准；Task 2 独立检索与冻结；Task 3 24 次模型调用、评分与证据分析。

## 实际历史与边界

仓库、工作区子目录及所有祖先均未找到 AGENTS.md。已读根 README、题库 README、docs/RAG_ONLY.md，以及上轮 run.py/source_retrieval.py/protocol.json 和实际归档 prompt。历史实际核对见 prior-audit.json。

本轮复用上轮源码 BM25 文件的原始字节（top8，48行/stride40，12000字符），以及未修改的 Workbench/可信评分器。它是上一轮研究用源码 RAG，不等同于生产 rag.py 的 AST 扩展配置。S/F/R 的每个案例共享同一段原始源码检索字符串；查询题库只使用原任务及该 packet.snippets 的 code 字节，不加路径、案例名、分数或隐藏材料。检索器只打开 questions.jsonl。

## 假设与预设分析

H1：R 相对 F 少交付无关题目，降低 token/模型时间；分别报告数量、实际含缓存 token 和耗时，不将其等同费用。
H2：R 相对 S 的整体通过增加或原通过项丢失减少；允许零增量或负面结果。主要以案例为单位展示两次重复，聚合调用保留分母，不作显著性和独立泛化推断。
H3：不适用案例 R 应拒绝返回；若 F/R 引发额外改动，结合实际补丁与现有行为检查判断。无禁用效果不等于没有无谓改动。

S=原任务+源码RAG；F=S+全部五题；R=S+自动0—2题。F/R 相同 allowlist JSON 展示，包含核心问题、适用条件、事件顺序、源码核查方法与应保留行为；不交付来源、证据状态或错误修复模板。两组附加完全相同的中文条件声明。

检索权重与阈值见 retriever.CONFIG / offline-validation.json：title2、两种keywords3、description2、core_question2、preconditions1、verification_methods1；weighted TF BM25 k1=1.5 b=.75。score>=5 且至少3个非停用英文词命中，按分数/ID选top2；稳定ID去重，重复core_question只留一题。全分数/贡献/拒绝原因可复核。门槛为先验保守下限，仅用三份旧开发任务片段与合成负查询检查，不看本轮模型得分。英文支持门槛对纯中文查询不友好，是本轮局限，不改题库弥补。正式前冻结，之后不调参。

## 案例与来源

1. listener-registration-order-vanilla：直接题库开发来源，首次监听/异步归属/重入。
2. document-submit-snapshot-vanilla：直接开发来源，延迟结算/重入/持久归档与显示。
3. handoff-redirect-reentrancy-vanilla：manifest明示从autosave stress拆分，与已提炼草稿作者扩展存在谱系关联，保守开发来源，不独立。
4. feature-flag-readiness-vue3：readiness负案例，五题的适用前提均不满足；manifest为clean-room重建、独立语义复核pending；与已暴露readiness样例共享短小temporal-flow模板结构，不能作为已认证独立样本。

候选 export-completion-ownership 明示同一 debounced-submit-flush 单元，不能当新事故；debounced-submit-flush也是草稿来源家族；async-role/cache-hydration等重建同样待语义复核/共享模板。本轮无法获得四个充分认证独立且当前运行环境可信的案例，因此按用户允许采用探索来源，不声称独立泛化。manifest来源与验证缺口保存在 protocol.cases；研究侧可以读谱系/校准，但不进入检索或Agent材料。

正式前使用原评分标准校准 unchanged/reference；要求reference PASS、unchanged UNDERREACH。现有oracle仅提供有界可信行为，不替代独立语义审核。冻结完整输入/题库/源码包/prompt/检索脚本和评分器摘要；不修改生产/原题库/历史记录。

## 执行与评价

固定 gpt-6-sol / low，600秒；同上轮 use_local_config=True、workspace-write、approval never、相同工具/运行器、无新增显式输出token限制（上轮未设置）。运行器本地配置继承是既有行为，记录实际命令，不将其称为密闭文件系统。模型API不提供本轮可控随机seed；仅调度seed=2026110502。每个重复随机案例顺序和条件顺序，每block三条件独立并行；block完成含评分屏障。8 blocks共24次，不重试、不扩大。

每次全新独立工作区，自相同候选快照开始，不接续其他补丁。执行前最小离线检索/格式检查、运行器mock测试、真实不调用模型的校准/命令验证。selection-review.json在调用前由主研究Agent审查visible task/code：非独立人工评审，可标不确定；审查不改变选题。

主要：整体行为通过、相对起点原已通过项的丢失/退步、负案例无必要行为变化。辅助：每案例必需检查通过数/分母、禁止效果、token、模型与检索秒、交付题数、执行失败和验证异常。额外给出对S的配对变化与S两次稳定通过项丢失；这些是独立新补丁间比较，不称续修退步率。不得将检查项当独立样本。

轨迹证据基于events.jsonl命令及源码内容、changes.json和可信评分，不以回答自述断因。关键差异引用实际prompt、代码读取、补丁和评分路径；没有轨迹证明核查时标不确定。错误路径审计只匹配显式命令，不证明绝对无泄漏。
