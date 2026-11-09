8 槽均完成且有效，无中断、无重试、无缺失。

1. 实际经验：R03 修订后的五条经验，正文 SHA256 b560d2b8de712eb51fe331bc53a79bfa0c8e64a6620eda440d66051edc048674。Test-1 命中 T4；Test-2 为 T3 空库回退，A/B 提示逐字相同。
2. 整题：Test-1 A 0/2、B 1/2；Test-2 A 0/2、B 2/2；全体 A 0/4、B 3/4。Test-1 三项原问题的消费式离线离开目标，A/B 均各 2/2；两项缓存保留行为各为 A 0/2、B 1/2。Test-2 两项编辑合并目标 A/B 均各 2/2，整题差别来自完整向量中的其他行为。
3. 退步：Test-1 B 第一次相对 A 第一次多失败 offline-nonconsuming-detach；该行为在原始候选就失败，因此不能称为丢失原始成功。两项缓存保留在 A 两次和 B 第一次均丢失了原本通过的行为。其他同重复 B/A 比较没有 B 丢失项。所有组的原始成功损失及完整检查均保留；未从通过数单独推断原因。
4. 成本：A 34 请求、495,488 tokens、358.1 秒；B 34 请求、489,983 tokens、422.6 秒。B 总 tokens 少 5,505，但会话时间多 64.5 秒。全批 68 请求、985,471 tokens，未知用量请求为 0。工具尝试两组各 30。工程 tokens 与金额未知，保持 null。
5. 全部 8 槽按固定顺序执行完毕，每份有效候选仅评分一次。没有提取、反思、GEPA、评委或连接预跑，没有修改经验或生产库。

全体 B 多出的三次整题通过中，两次来自提示完全相同的回退案例，不能解释为经验收益。命中子集只含一个已暴露的同源跨语言案例、每组两次重复；不能据此声称统计显著、稳定有效或独立泛化，也不能据回退结果声称经验效果等价。

完整协议、行为向量及归档详情：

本批固定经验两案例 A/B 探索性对照已完成全部 8 槽。

经验为 R03 修订后、其余四条保持不变的五条规则，正文 SHA256：`b560d2b8de712eb51fe331bc53a79bfa0c8e64a6620eda440d66051edc048674`。源对象、AI 辅助内容核查、父版本关联和开发回验均在 experience-source/ 原样保存。开发整题 0/2 与全部退步不改变；本批仅按明确授权登记为探索性条件，不是生产接纳或已证有效。

Test-1（query Python）沿用准入分析 T4，满足五项 requires，排除 no_lazy_shared_mechanism 被源码否定，路由选中该经验。Test-2（document Python eval-v2）沿用准入分析 T3，库中没有 T3 经验，回退 AUTO，A/B 提示相同。路由只得到当前任务、候选源码/文档、原自动分析、绑定当前输入的 AI 语义核查和经验适用描述，没有获得案例 ID、历史成绩、测试标准或开发来源身份。

所有会话固定 gpt-5.6-terra / low，24 请求、600 秒，并发 1。A/B 共享同一原始候选、任务、自动 Contract 和公共要求；B 仅在命中时追加原样经验正文。独立工作区不继承补丁或会话。调用前冻结 schema/输入/路由/提示/代码/评分版本与调度。提取、反思、评委和连接预跑均为 0。

|案例/条件|计划|启动|有效|无效|未启动|整题通过/有效评分|
|---|---|---|---|---|---|---|
|T1 / A|2|2|2|0|0|0/2|
|T1 / B|2|2|2|0|0|1/2|
|T2 / A|2|2|2|0|0|0/2|
|T2 / B|2|2|2|0|0|2/2|

全体与命中/回退子集：

|集合|A 整题|B 整题|
|---|---|---|
|all|0/4|3/4|
|hit|0/2|1/2|
|fallback|0/2|2/2|

实际槽位：

|顺序|案例|条件|重复|状态|整题|满足关系|丢失原通过行为|
|---|---|---|---|---|---|---|---|
|1|T1|B|1|VALID|UNDERREACH|26/29|cached-paused-background, cached-later-consumption|
|2|T1|A|1|VALID|UNDERREACH|27/29|cached-paused-background, cached-later-consumption|
|3|T2|A|1|VALID|UNDERREACH|22/24|无|
|4|T2|B|1|VALID|PASS|24/24|无|
|5|T1|A|2|VALID|UNDERREACH|27/29|cached-paused-background, cached-later-consumption|
|6|T1|B|2|VALID|PASS|29/29|无|
|7|T2|B|2|VALID|PASS|24/24|无|
|8|T2|A|2|VALID|UNDERREACH|20/24|无|

完整行为向量 T1（按对应标准判断；禁止行为期望 false）：

|行为|B1|A1|A2|B2|
|---|---|---|---|---|
|offline-detach-false|通过|通过|通过|通过|
|offline-detach-true|通过|通过|通过|通过|
|offline-detach-always|通过|通过|通过|通过|
|offline-nonconsuming-detach|失败|通过|通过|通过|
|active-offline-resume|通过|通过|通过|通过|
|multiple-observers|通过|通过|通过|通过|
|last-observer-offline|通过|通过|通过|通过|
|unknown-unsubscribe|通过|通过|通过|通过|
|consumed-flight-cancel|通过|通过|通过|通过|
|nonconsuming-flight-cache|通过|通过|通过|通过|
|cached-paused-background|失败|失败|失败|通过|
|cached-consumed-revert|通过|通过|通过|通过|
|remount-generation|通过|通过|通过|通过|
|late-old-generation|通过|通过|通过|通过|
|always-mode|通过|通过|通过|通过|
|focus-gates-resume|通过|通过|通过|通过|
|focus-does-not-gate-first-start|通过|通过|通过|通过|
|offline-first-retry|通过|通过|通过|通过|
|nonconsuming-cancel-retry|通过|通过|通过|通过|
|reentrant-unsubscribe-at-entry|通过|通过|通过|通过|
|framework-unmount|通过|通过|通过|通过|
|cached-later-consumption|失败|失败|失败|通过|
|accepted-resume-then-offline|通过|通过|通过|通过|
|detach-after-resume-queued|通过|通过|通过|通过|
|independent-query-keys|通过|通过|通过|通过|
|dependency-config-preserved|通过|通过|通过|通过|
|cached-prior-consumed-success|通过|通过|通过|通过|
|cached-prior-consumed-cancelled|通过|通过|通过|通过|
|retained-context-query-flag|通过|通过|通过|通过|

目标行为（描述性计数）：

offline-detach-false: {"A": {"passes": 2, "valid": 2}, "B": {"passes": 2, "valid": 2}}
offline-detach-true: {"A": {"passes": 2, "valid": 2}, "B": {"passes": 2, "valid": 2}}
offline-detach-always: {"A": {"passes": 2, "valid": 2}, "B": {"passes": 2, "valid": 2}}
cached-paused-background: {"A": {"passes": 0, "valid": 2}, "B": {"passes": 1, "valid": 2}}
cached-later-consumption: {"A": {"passes": 0, "valid": 2}, "B": {"passes": 1, "valid": 2}}

同重复 A/B 完整新增通过与损失：

[{"repeat": 1, "both_valid": true, "B_new_passes_vs_A": [], "B_losses_vs_A": ["offline-nonconsuming-detach"], "interpretation": "Descriptive repeat pairing only; no sampling or causal control."}, {"repeat": 2, "both_valid": true, "B_new_passes_vs_A": ["cached-paused-background", "cached-later-consumption"], "B_losses_vs_A": [], "interpretation": "Descriptive repeat pairing only; no sampling or causal control."}]

完整行为向量 T2（按对应标准判断；禁止行为期望 false）：

|行为|A1|B1|B2|A2|
|---|---|---|---|---|
|quiet-burst|通过|通过|通过|通过|
|second-burst|通过|通过|通过|通过|
|close-before-deadline|通过|通过|通过|失败|
|switch-before-deadline|通过|通过|通过|失败|
|same-document-reopen|通过|通过|通过|失败|
|reentrant-switch-on-flush|失败|通过|通过|通过|
|reentrant-close-on-flush|失败|通过|通过|通过|
|reentrant-timer-save|通过|通过|通过|通过|
|reentrant-edit|通过|通过|通过|通过|
|preview-delay|通过|通过|通过|通过|
|preview-hide|通过|通过|通过|通过|
|preview-reuse|通过|通过|通过|通过|
|preview-valid|通过|通过|通过|通过|
|submit-before-deadline|通过|通过|通过|通过|
|submit-after-deadline|通过|通过|通过|通过|
|submit-switch-on-flush|通过|通过|通过|通过|
|submit-close-on-flush|通过|通过|通过|通过|
|submit-reopen-on-flush|通过|通过|通过|通过|
|submit-reentrant-edit|通过|通过|通过|通过|
|submit-empty|通过|通过|通过|通过|
|dispose-before-deadline|通过|通过|通过|失败|
|repeated-submit-empty-text|通过|通过|通过|通过|
|large-unicode-value|通过|通过|通过|通过|
|preview-delay-migrated|通过|通过|通过|通过|

目标行为（描述性计数）：

quiet-burst: {"A": {"passes": 2, "valid": 2}, "B": {"passes": 2, "valid": 2}}
second-burst: {"A": {"passes": 2, "valid": 2}, "B": {"passes": 2, "valid": 2}}

同重复 A/B 完整新增通过与损失：

[{"repeat": 1, "both_valid": true, "B_new_passes_vs_A": ["reentrant-switch-on-flush", "reentrant-close-on-flush"], "B_losses_vs_A": [], "interpretation": "Descriptive repeat pairing only; identical fallback prompt differences cannot be attributed to experience."}, {"repeat": 2, "both_valid": true, "B_new_passes_vs_A": ["close-before-deadline", "switch-before-deadline", "same-document-reopen", "dispose-before-deadline"], "B_losses_vs_A": [], "interpretation": "Descriptive repeat pairing only; identical fallback prompt differences cannot be attributed to experience."}]

成本（旧开发与历史评分不并入）：

|范围|会话|请求|已知 tokens 合计|未知请求用量|工具|秒|
|---|---|---|---|---|---|---|
|A|4|34|495488|0|30|358.115|
|B|4|34|489983|0|30|422.58|
|全部新增测试|8|68|985471|0|60|780.694|

每案例、每条件成本详见 summary.json 的 per_case；全部已知字段与未知数量见 costs.json。金额及工程准备 tokens 无法从接口读取，保持 null；缺失请求用量不会补零。若无有效评分，整题通过率不可计算，不写 0%。

停止记录：null

服务错误、部分输出与归档错误分别保存在各 archive 的 service-errors.json、model-outcome.json、archive-status.json 及原始事件/日志中。未完成候选不进入行为评分。每份有效候选只调用对应原评分器一次，query 保留 29 项，document 保留 23 项必需与 1 项禁止行为。复用 21 份已核对版本的历史校准，不重新评分历史候选。

结果解释边界：两个案例均已暴露，属于同源跨语言探索，不是独立泛化测试。每条件两次重复仅作描述，不声称统计显著、稳定有效或控制模型采样。Test-2 相同提示下的任何得失只反映独立运行差异，不能归因为经验，也不能证明经验效果等价。不将开发回验并入测试分母，不只报告命中或较好结果。

公共 Contract 与既有准入输出逐字复用。Test-1 保留原先“不应触发执行”的表述，而新增经验 R03 明确目标允许零入口或已中止信号入口；本批不修改该公共材料。A/B 都受同一辅助 Contract 及“依据任务源码核查、不盲从”公共要求约束，这也是解释结果时的固定条件。

推荐 Git commit subject: `research: run fixed-experience two-case routed A/B pilot`

推荐 Git commit body:

```text
Freeze the R03-revised research experience and reuse admitted Python inputs.
Record source-bound routing, exact A/B prompts and the requested eight-slot order.
Use identical isolated repair budgets with one score per valid candidate.
Report all outcomes, regressions, fallback repeats and known/unknown costs.
Preserve historical interruptions and development losses; do not learn, retry,
modify production experience or claim independent generalization.
```

未创建 Git 提交、修改历史记录、更新生产经验库或自动启动下一批。
