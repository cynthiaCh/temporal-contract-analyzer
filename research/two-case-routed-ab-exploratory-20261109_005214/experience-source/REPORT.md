本轮 R03 局部经验演化与 D1 开发回验已完成。

固定父候选：research/d1-rule-object-validation-20261109_001011/。仅允许替换 R03 规则对象，原 R01/R02/R04/R05 的正文和元数据、机制适用字段、未决说明均保持不变。未重新生成完整经验、改写其他条款或引入旧 E2。

反思输出为一个沿用现有字段与合法 ID 枚举的 verification 规则对象。Python 复制父对象并仅替换第三项，确定性编号与渲染；完整新候选和正文都是程序派生产物，原始模型输出仅为 r03-raw.txt 中的 R03。lineage.json、candidate-differences.json、experience.diff、derivation.json 保存父版本、精确差异和摘要。

离线核查复用现有运行器、隔离、计量及 schema；检查父评审与结构核查接口兼容、支持依据不静默放宽、修改范围受限、部分输出拒绝，以及固定基线的输入/权限/评分版本一致。结果见 offline-checks.log、freeze.json 和 condition-audit.json。

内容核查为执行 Agent 的 AI 辅助核查，不是独立人工批准。其他四条及机制前提的评审复用父批已有 AI 核查；对 R03 的新正文与引用逐项核对。R04 的已消费取消仍按已进入工作上下文解释，网络模式例外保持父批边界。未把复用评审包装为独立复核。

1. R03 是否纠正过度收紧与字段放置：通过 AI 辅助核查，具体原文与依据见 semantic-review.json。

2. 其余规则是否保持不变：程序已确认四条完整规则对象、机制适用字段及未决说明完全不变。

3. 两项目标与整题结果：有效新评分 2 份；完整结果如下。没有评分的槽位保持未知，不计为行为失败。

4. 新行为损失：所有相对原始版本和两份 AUTO 的损失均列于 summary.json、behavior-vectors.json 与下表，不能因目标改善而省略。未启动维护时损失未知。

|条件|评分|满足关系|整题|缓存后台保留|延后消费保留|相对原始版本损失|
|---|---|---|---|---|---|---|
|AUTO 1|有效|27/29|UNDERREACH|False|False|cached-paused-background, cached-later-consumption|
|AUTO 2|有效|27/29|UNDERREACH|False|False|cached-paused-background, cached-later-consumption|
|回验 1|有效|27/29|UNDERREACH|True|True|cached-prior-consumed-success, retained-context-query-flag|
|回验 2|有效|26/29|UNDERREACH|False|False|cached-paused-background, cached-later-consumption, accepted-resume-then-offline|

全部 29 项：

|关系|AUTO 1|AUTO 2|回验 1|回验 2|
|---|---|---|---|---|
|offline-detach-false|通过|通过|通过|通过|
|offline-detach-true|通过|通过|通过|通过|
|offline-detach-always|通过|通过|通过|通过|
|offline-nonconsuming-detach|通过|通过|通过|通过|
|active-offline-resume|通过|通过|通过|通过|
|multiple-observers|通过|通过|通过|通过|
|last-observer-offline|通过|通过|通过|通过|
|unknown-unsubscribe|通过|通过|通过|通过|
|consumed-flight-cancel|通过|通过|通过|通过|
|nonconsuming-flight-cache|通过|通过|通过|通过|
|cached-paused-background|失败|失败|通过|失败|
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
|cached-later-consumption|失败|失败|通过|失败|
|accepted-resume-then-offline|通过|通过|通过|失败|
|detach-after-resume-queued|通过|通过|通过|通过|
|independent-query-keys|通过|通过|通过|通过|
|dependency-config-preserved|通过|通过|通过|通过|
|cached-prior-consumed-success|通过|通过|失败|通过|
|cached-prior-consumed-cancelled|通过|通过|通过|通过|
|retained-context-query-flag|通过|通过|失败|通过|

相对每份 AUTO 的完整得失：

回验 1: [{"baseline": 1, "improvements": ["cached-paused-background", "cached-later-consumption"], "regressions": ["cached-prior-consumed-success", "retained-context-query-flag"], "retained_success_count": 25}, {"baseline": 2, "improvements": ["cached-paused-background", "cached-later-consumption"], "regressions": ["cached-prior-consumed-success", "retained-context-query-flag"], "retained_success_count": 25}]
回验 2: [{"baseline": 1, "improvements": [], "regressions": ["accepted-resume-then-offline"], "retained_success_count": 26}, {"baseline": 2, "improvements": [], "regressions": ["accepted-resume-then-offline"], "retained_success_count": 26}]

成本（旧基线与新增分开）：

|范围|会话|请求|已知 tokens|未知用量请求|工具|秒|
|---|---|---|---|---|---|---|
|旧 AUTO|2|11|152142|0|9|213.309|
|新反思|1|1|73795|0|0|24.882|
|新维护|2|15|223925|0|13|228.323|
|本次新增合计|3|16|297720|0|13|253.205|

工程准备 tokens 和金额无法从接口读取，保持 null；工程时间与完整分项见 costs.json。未知请求用量不补零。父批反思成本未混入本次新增成本或基线成本。

模型固定为反思 gpt-5.6-terra / medium、维护 gpt-5.6-terra / low；分别 12/24 请求，每会话 600 秒，并发 1，总请求上限 60。每次维护从相同原始候选独立开始，只追加冻结派生正文，不交付训练评分、账本、标准答案或参考补丁；仅有效完整候选按原 29 项规则评分一次。

实际槽位与停止：{"counts": {"planned": 3, "started": 3, "not_started": 0, "complete_model_sessions": 3, "incomplete_model_sessions": 0, "valid_new_behavior_scores": 2, "whole_task_passes_new": 0}, "stop": null}

候选后续冻结资格：Content supported and observed target/overall development improvement. 当前未更新任何生产经验库，也未开展测试集运行。

本轮只作同题开发诊断：不能凭两次开发回验宣称稳定效果、独立测试收益、同源迁移或泛化。未进行下一轮反思、额外评委、分类、提取、连接预跑、重试或补跑。完成后停止。

推荐 Git commit subject:

`research: evaluate a bounded R03-only experience revision on D1`

推荐 Git commit body:

```text
Revise only R03 with one bounded reflection using frozen D1 evidence.
Keep the parent protocol and all other rules and mechanism fields intact.
Archive raw revision, deterministic synthesis, exact scope checks and
AI-assisted evidence review before up to two isolated repair sessions.
Record every behavior, regression, known cost and unknown/unstarted slot
without test runs, retries, baseline reruns or production registry updates.
```

未创建提交，未修改父批或其他历史记录，未修改全局配置。

补充开发解读（两次完成后生成，未回流模型）：

两项目标各在 1/2 新回验通过；整题仍 0/2。总满足关系为 53/58，旧基线 54/58，未观察到整体收益。局部改善符合预定最低记录条件，但存在完整记录的新损失，不能解释为经验效果已验证。没有父经验维护对照，无法单独归因于 R03 修订。源码事实、逐检查差异和未知原因分别见 DEVELOPMENT_AUDIT.md 与 revalidation-audit.json。
