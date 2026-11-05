# 时序契约问题库 v1

2026-11-05 的离线证据提炼，共 5 条独立可检索问题。本目录是研究数据产物；未接入现有 RAG，未修改分析器、评分器、历史记录，未调用模型或重跑行为实验。仓库初始 Git 状态干净，HEAD 与来源摘要见 provenance.json。仓库及祖先目录没有可读取的 AGENTS.md；已阅读 README、docs/RAG_ONLY.md、docs/FAILURE_LEARNING.md、rag.py、learning.py。

## 实验范围

按实际 job 时间而非文件修改时间或目录日期排序。时间均为 Asia/Shanghai（UTC+8）。选取 11 月 4—5 日六个包含原任务修复、反馈续修、源码检索和审查问题对照的批次；按导出表的成员选择，不递归混入后来追加在同一 reports-experiments 目录的任务。

| 批次（results/ 下） | 实际时间 | 模型/推理 | 条件 | 调用数；行为通过/失败/执行失败 |
|---|---|---|---|---|
| ad-model-effort-20261104 | 11-04 01:07—01:46 | gpt-5.6-terra、gpt-5.6-sol、gpt-6-sol；low/medium | none、review、learned_review | 66；22/44/0 |
| hypothesis-repair-v2-20261104 | 11-04 10:12—10:57 | 同上各模型；继承父任务强度 | review、hypothesis_review | 22；6/16/0 |
| rag-only-v1-20261104 | 11-04 13:50—14:07 | 同上各模型；继承父任务强度 | rag_only | 11；3/8/0 |
| assistance-applicability-v1-20261105 | 11-05 09:06—09:16 | gpt-6-sol/low | A/R/S/D；仅可交付槽位调用 | 48；40/8/0 |
| information-gap-controls-v1-20261105 | 11-05 10:00—10:07（有时间戳的 28 次小项目槽位） | gpt-6-sol/low | 小项目 A/P/R/B/C/S*/D*；全仓 A 筛选 | 40；25/13/2 |
| checklist-vs-dstar-v1-20261105 | 11-05 19:08—19:31 | gpt-6-sol/low | A/G/CG/D* | 64；52/12/0 |

合计 251 次：148 次行为通过，101 次行为失败，2 次执行失败。这里只列归档结果，不能跨批汇总成方法效果。信息缺口批次另 12 次全仓 A 调用无单 job 起止时间字段；目录归档归属 11 月 5 日，具体钟点未知，不能把上表时间当全批起止时间。provenance.json 保留这一缺口。所有实际模型/强度组合和材料路径按 job 可查。

A 是原任务；R 是该研究冻结的源码检索；P 是普通源码打包；B/C 是位置/事实；S 是静态事实；D 是 review。星号表示后续研究限定来源与预算的材料变体，并非生产 D；G 是通用重入清单，CG 是同源码前缀加 G。不同批次 R 的定义/导入扩展并不相同，以各批 protocol、prompt 和导出为准。learned_review、hypothesis_review 暴露历史反馈，是开发条件。RAG 批次只计 11 次新调用，未重复计入复用的 22 个历史对照。

来源入口均在 provenance.json 的 scope 中：每批 membership 是原导出路径与 SHA256，runs 给出案例、条件、experiment/job、manifest。11 个精读 job 在 jobs 中另含原任务、输入源码、已评分候选、changes.json、提示、校准和原始行为输出路径。已有人工/研究核查关联 CASE_NOTES、MECHANISM_NOTES、DIAGNOSTIC_NOTES；不把它们当作独立盲审。所有路径相对仓库根，摘要绑定当前归档字节；部分实验归档由本地忽略规则排除，普通 Git clone 未必带有证据文件，需另行迁移原归档并复核摘要。

未将更早 external-tests、规则测试、门控回放及 d-text/d-evidence 等重叠诊断批次穷尽纳入。以上是可复核的最近六批范围，不是仓库全部失败的普查，也不是跨项目随机事故样本。

## 提炼方法与主要发现

先读任务与可见文档，再追踪实际事件派发、异步延续、状态写入和副作用调用方；对照 changes.json 与 evaluations 下实际被评分的 candidate，避免把可变 workspace 当评分输入。使用参考校准 PASS 的原始行为结果，检查失败断言实际值及 trace，再对照成功补丁与已有核查。归档 probe 对结构化语义失败使用 exit_code=1；不能把这一退出码单独当作基础设施异常，需结合校准、可信输出与进程记录。来源中的摘要只用于导航，模型回答和静态命中均不构成缺陷证明。

- TCQ-001：同步首次事件与监听生效顺序。输入派发实现本身给出丢失窗口；已修复首次接收但整体失败的候选，不能被误说成仍有首次事件缺陷。
- TCQ-002：已开始异步工作不会因移除监听自动消失；资源相同也不等于访问相同。
- TCQ-003：同步回调可重入；外层恢复后的写权限与晚返回清理句柄需要核查。最后开始者优先只来自相应项目要求。
- TCQ-004：统一 active 守卫曾使续修丢失父补丁已通过的两项历史记录行为；另有持久归档保留、旧界面通知错误的对照。接纳后完成与失效后继续接纳新事件需要分开。
- TCQ-005：即时写入改为延迟合并后，离开与提交的同步持久化义务仍可能存在；临时预览的取消语义不同。

TCQ-003 核查可重入调用栈及状态写权限，TCQ-004 核查不同副作用的义务，TCQ-005 核查延迟工作结算边界；虽然共用草稿证据，审查对象不同，不按文件或函数机械拆题。成功样本只作反向对照，不证明单个补丁、提示句或 RAG 的因果贡献。问题中的常见错误修复同时包括已观察退步和有明确前提的源码推演风险；provenance.questions.limits 标明未被实际失败样本验证的风险。

## 数据格式与检索

只允许把 **questions.jsonl** 加入 Agent 索引；每行是一个完整条目，以 id 为独立检索单元。不要递归索引本目录、README、provenance.json 或 pending-review.md。

字段：id（稳定，不重用）、title、contract_category、core_question、preconditions、observable_clues、event_orders（sequence/check）、source_evidence_to_seek、verification_methods、non_applicability_and_preserved_behavior、common_wrong_repairs（repair/possible_regression）、retrieval（zh_keywords/en_keywords/description）、evidence_status、applicability_scope。修改内容不改机制 ID；拆分或退役保留历史映射，不把旧 ID 赋给新机制。

检索时可拼接 title/core_question/observable_clues/retrieval 做词法搜索；取回整条条目，让 Agent 根据当前任务判断适用前提，再回当前源码验证事件顺序与必须保留的行为。关键词只是入口，题目不是缺陷判决或无条件修复模板。当前未增加索引器、检索评测或对现有 rag.py 的调用；现有 task-only RAG 语义保持原样。

provenance.json 是研究侧关联产物：questions 以题目 ID 关联机制证据、精确源码行和 job key；jobs 保存证据文件索引与失败片段；scope 保存六批成员和执行分类；split_policy 保存开发来源排除规则。隐藏断言、评分标识、载荷和原始行为详情只允许在研究侧。没有复制标准补丁到检索文件，校准仅引用研究侧结果路径。

## 数据泄漏与适用限制

所有选入批次的案例保守标为 development-source，包括只用于核查或尚未入正式题库的案例。它们的同源变体、改名、low-cue 版本、同一上游 issue/commit、衍生任务或共享 authored template，后续均不得作为独立泛化测试。不能只按 case ID 去重。未能判定谱系的来源先隔离待核查，不能自动划为独立来源。

provenance.split_policy.affected_cases 给出明确案例集合，family_exclusion 给出重点家族。未来运行器须在研究侧加载此排除元数据，Agent 侧仍只索引 questions.jsonl。去掉答案、隐藏评分内容和案例名不会消除开发来源暴露。当前标记不自动约束其他运行器，也不证明模型已有知识或本地读取完全隔离。

题库只有少量作者暴露、相关联案例的有界机制证据。没有验证其召回、迁移或修复收益；未来需使用排除同源来源的独立对照实验。执行/验证异常、业务语义冲突、泛化推断见 pending-review.md。

## 最小检查与工作量

从仓库根执行，不调用模型、分析器或评分器，不安装依赖：

```sh
python3 -B research/temporal-contract-question-bank-v1/check.py
```

检查 JSON/JSONL 解析、ID 与必填字段、双向关联、来源存在与 SHA256、源码锚点、候选与评分清单绑定、251 个归档槽位的执行/校准/原始结果分类，以及检索文本中的路径、案例/评分标识和隐藏断言标识。该扫描只能排除指定形式，不能证明无语义泄漏，仍需人工阅读与来源隔离。

本次工作为六批清点、11 个 job 的源码/补丁/行为精读、5 条问题编写与来源绑定；没有穷尽精读 251 份补丁，也没有新增模型或行为实验。验证输出见 validation.json；脚本可重复执行只读检查并将结果打印到 stdout。
