# Contract—标准—输入输出离线映射

**AI 辅助核查，不是独立人工复核。**选 U2 一个完整案例，拆为7条义务：[MAPPING.csv](MAPPING.csv)；逐字引用、版本摘要及关联：[SOURCES.json](SOURCES.json)。未调用模型、重跑评分、修改技能或创建提交。

## Task 1：来源、发现与验证

历史归档位于相邻 `temporal-contract-bench-git/results/core-24-completion-20261005/recovered-06-node18/`。j0001未提供Contract，j0002提供；均为gpt-5.6-terra／medium、600秒、CLI 0.159.2、ungranted、空overlay，起始树同为 `e381e156…b4b223e0`。两组实际prompt的非空文本仅差Contract后缀。原始score为UNDERREACH（4/8必需效果）与PASS（8/8），均未观测到禁止效果。

核对了plan、实际prompt、run、事件记录、原始score及最终candidate，重算起始树、最终树、manifest和prompt摘要均匹配。SOURCES保存由核验后的base／candidate离线推导的差异，未冒称历史patch.diff。实际input/output token为147608/4668与179643/6329，上限相同而消耗不同。

**限制：**每组一次、顺序执行，不能分辨每条Contract的因果作用。失败组仅识别字符串pending/ready，worker提供false/true；成功组兼容布尔值，因此改善也包含状态协议处理差异。另一批gpt-6.1-sol／medium两组均PASS，不能宣称稳定收益。当前oracle已读并留摘要，但历史receipt没有逐文件oracle摘要；执行字节不能独立认证。两组缺独立分析报告，完成摘要不作为内部理解证据。

## Task 2：标准、映射与差距

[已确认U2标准](../code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md)的S1–S6为源码事实，R1–R4为义务／政策边界，§6为原因假设与未知，A1–A6为分析评价。确认保留未知，不批准唯一实现。标准讨论的是另一次历史补丁 `e-0f86af18a30343df`，不是本次选取的两份修复；原始候选逐字一致。U1版本边界已阅读；C1–C3仍待确认，没有跨案例配对。

- **O1持续轮询、O3未ready不完成：**R1已完整包含；分析评价及行为评分明确检查（A）。
- **O2等待期间loading保持：**R2已有等待义务，但明确保留“loading是否唯一表达”的未知。历史Contract更具体（F），不能称完整等价，也不能说标准漏了等待。
- **O4关闭使timer失效：**R3/R4已有关闭与后续工作的关系，覆盖较宽；评分驱动请求中关闭，未独立驱动“retry已排队后关闭”（B，且具体政策输入不足为F）。
- **O5关闭使所有在途响应失效、O6重开隔离旧代：**R3已有防止旧回调错误影响，具体政策仍有未知；评分只覆盖单个在途请求和异token重开，多请求、同token重开未验证（F／部分评价覆盖）。
- **O7后台关闭后继续，授权迁移除外：**S6有当前行为事实，R4/A5要求分开考察；workspace所有权定义和授权例外不在候选可见规格中（F）。本配对未授权，不能外推授权分支。

实际分析a01、a07、a09的prompt、工作区及原始JSON报告已核对：都准确表达O1/O3，其余政策保留未知有依据；a03执行失败、报告缺失。未证实D（输入充分但报告未恢复）。这些报告没有生成历史补丁，未证实E（报告已表达但对应补丁未落实）。通过整体评分不等于每条义务独立验证；缺单独检查不等于实现违反。

## Task 3：唯一下一步、限制与保护

**优先改评价设计：**在已有U2-R3/R4下单列“retry已排队→close→尝试触发旧timer”的覆盖项，并注明前台政策必须有输入依据。本轮不实施。证据是已有关闭关系未被所选评分独立驱动，不能用close测试通过代表timer边界已覆盖。

没有确认需新增的关键标准义务（C），不支持优先改提取或补丁落实。loading唯一表达、前台完整生命周期政策、状态协议、全称响应隔离、授权分支仍不能确定。分析使用gpt-6-sol／low、K0/K1分析协议且无Contract；历史修复使用另一模型和任务协议，**不能串成同一因果链**。

离线检查通过：两仓库HEAD、暂存／未暂存diff、原tracked／staged文件及引用来源保持。只新增本目录，不改变既有批准状态；机械核验不等于人工批准。

建议Git commit（仅文本，未创建）：

Subject: `research: map archived U2 contract to standards and evaluation`

Body: `Trace seven obligations to paired prompts, versioned inputs, raw scores, analysis reports and final candidates. Preserve policy unknowns and existing work; identify the queued-retry evaluation gap without model calls, rescoring or skill changes.`
