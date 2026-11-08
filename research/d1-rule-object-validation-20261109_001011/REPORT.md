本轮已完成反思协议修复和零模型核查，执行一次反思后按候选拒绝规则停止。没有启动两次维护回验。

此次工作仅限 D1 同题开发诊断，不开展测试集运行、不额外提取 Contract 或重跑 AUTO。保留旧 E2 不作为种子，未把任何测试反馈加入训练材料。

1. 机械绑定问题是否解决：

已移除重复全文与逐字引用，唯一正文为 rules[].body；Python 稳定编号并渲染。schema 按冻结账本生成合法 ID 枚举，并提供 predicate 完整定义。23 项离线检查通过；本次实际模型对象也通过 JSON schema，全部 ID 合法，没有旧的重复引用错误。该结论限于离线检查和这一次输出，不证明未来输出永不出错。

2. 候选还有哪些问题：

R03 的 support 只列实际评分观察，规范依据列在 conditions；按调用前冻结的规则，support 本身缺少规范依据，候选被拒绝。必须区分“字段准入失败”与“完全没有任务文档引用”：后者不成立，本轮没有移动 ID 或修改规则来放行。

AI 辅助核查还发现 R03 将“不能携带 live signal 进入”扩大为“重连时不得进入执行”的唯一验证要求。原任务、训练 rubric 和冻结评分器允许没有入口，或入口的 signal 已中止；并未把零入口作为唯一正确方案。不能从旧 AUTO 采用零入口的结果推导出更强业务政策。具体原文、依据、限制与逐规则核查见 semantic-review.json 和 training-policy-check.json。

新候选没有重犯必须迁移共享消费记录或所有无观察者工作一律取消的旧错误。所选机制适用前提有当前文档/源码支持；多处修改的独立因果贡献仍未知。R04 的已消费取消描述按已进入工作上下文核查，不将其扩展成新建未进入工作永不允许中止的规则。

3. 两项目标和整题结果是否改善：

新增有效维护评分为 0，两项目标与整题收益均未知。已有两次 AUTO 都是 27/29，失败项为 cached-paused-background 与 cached-later-consumption。两次新回验均未启动，不能填作失败。

4. 是否损失已有正确行为：

新维护未执行，新增损失未知。旧 AUTO 各自原有成功 21、保留 19、改善 8、退步 2；完整 29 项向量和实际/预期检查保留在 feedback.json、behavior-vectors.json 与基线归档。

|条件|评分状态|满足关系|整题|缓存后台保留|延后消费保留|
|---|---|---|---|---|---|
|AUTO 1|有效|27/29|UNDERREACH|False|False|
|AUTO 2|有效|27/29|UNDERREACH|False|False|
|经验回验 1|未启动|—|—|—|—|
|经验回验 2|未启动|—|—|—|—|

|关系|AUTO 1|AUTO 2|回验 1|回验 2|
|---|---|---|---|---|
|offline-detach-false|通过|通过|未评分|未评分|
|offline-detach-true|通过|通过|未评分|未评分|
|offline-detach-always|通过|通过|未评分|未评分|
|offline-nonconsuming-detach|通过|通过|未评分|未评分|
|active-offline-resume|通过|通过|未评分|未评分|
|multiple-observers|通过|通过|未评分|未评分|
|last-observer-offline|通过|通过|未评分|未评分|
|unknown-unsubscribe|通过|通过|未评分|未评分|
|consumed-flight-cancel|通过|通过|未评分|未评分|
|nonconsuming-flight-cache|通过|通过|未评分|未评分|
|cached-paused-background|失败|失败|未评分|未评分|
|cached-consumed-revert|通过|通过|未评分|未评分|
|remount-generation|通过|通过|未评分|未评分|
|late-old-generation|通过|通过|未评分|未评分|
|always-mode|通过|通过|未评分|未评分|
|focus-gates-resume|通过|通过|未评分|未评分|
|focus-does-not-gate-first-start|通过|通过|未评分|未评分|
|offline-first-retry|通过|通过|未评分|未评分|
|nonconsuming-cancel-retry|通过|通过|未评分|未评分|
|reentrant-unsubscribe-at-entry|通过|通过|未评分|未评分|
|framework-unmount|通过|通过|未评分|未评分|
|cached-later-consumption|失败|失败|未评分|未评分|
|accepted-resume-then-offline|通过|通过|未评分|未评分|
|detach-after-resume-queued|通过|通过|未评分|未评分|
|independent-query-keys|通过|通过|未评分|未评分|
|dependency-config-preserved|通过|通过|未评分|未评分|
|cached-prior-consumed-success|通过|通过|未评分|未评分|
|cached-prior-consumed-cancelled|通过|通过|未评分|未评分|
|retained-context-query-flag|通过|通过|未评分|未评分|

成本与实际槽位：

|范围|会话|请求|已知总 tokens|用量未知请求|工具调用|秒|
|---|---|---|---|---|---|---|
|旧 AUTO 基线|2|11|152142|0|9|213.309|
|本次反思|1|1|73570|0|0|55.766|
|本次维护|0|0|0|0|0|0|
|本次新增合计|1|1|73570|0|0|55.766|

金额与执行 Agent 工程准备 tokens 无法从接口读取，保持 null。已知 token 合计与未知请求数分别记录；原始用量不补零。工程墙钟时间见 costs.json，包含人工代码准备、核查与等待，不等于模型计费时间。

新 schema、输入、公共提示和运行配置在调用前冻结，冻结记录为 freeze.json。维护条件与原 AUTO 相同：gpt-5.6-terra / low、24 请求、600 秒；反思 gpt-5.6-terra / medium、12 请求、600 秒、无工具；本轮最多 60 请求，并发 1。

此次反思服务正常、完整输出，无断流、无隐性重试。原始对象、原始 CLI 事件、校验、派生正文、逐规则依据、拒绝、计量均已归档。派生正文仅供审计，明确不是新模型原始全文，未交给维护 Agent。

执行 Agent 的核查标为 AI 辅助，不伪造独立人工批准。没有更改旧失败对象或拒绝决定；用于转换检查的夹具明确为 synthetic_derived_test_fixture，不作为候选或效果证据。

当前候选不具备进入冻结经验测试的依据。此次观察说明机械重复可以消除，但结构合法不保证规则有据。未测得新经验效果，不宣称测试收益、稳定收益或泛化。完成后停止，没有自动进入下一轮。

推荐 Git commit subject:

`research: render ledger-bound reflection rules from a single source`

推荐 Git commit body:

```text
Replace duplicated experience text and quotations with a single rule list.
Generate evidence-ID schemas from the ledger, provide predicate definitions,
and render deterministic rule numbering and exact model bodies in Python.
Preserve semantic review and replay old invalid outputs in offline checks.
Archive one bounded D1 reflection and its rejection; leave both repair slots
unstarted, retain full baseline vectors, and separate old/new costs.
```

未创建提交、更新生产经验库或修改全局配置。已有暂存区及历史文件保持原状。
