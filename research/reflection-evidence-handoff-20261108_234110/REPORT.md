本次已完成两项零模型工作：建立训练证据约束账本，以及修复反思材料的证据交接。未开展新反思、开发回验或 A/B 测试；未生成或入库新经验。

工作目录独立于所有旧批次。开始时 HEAD 为 `1fe2b8ec52cd7d802c676869787de017581e6178`，Git status 与 diff 均为空。所有新增文件位于本目录，未修改原实验、评分器、案例、生产经验库、依赖或全局配置，未创建 Git 提交。

证据与处理：

|问题|本次可确认的内容|判断边界|
|---|---|---|
|取消资源与消费记录混同|原源码 getter 写共享查询记录，返回尝试自己的 controller；离开逻辑读取共享记录。旧反思却要求消费记录必须属于尝试。|这是没有得到保留要求支持的政策扩展。允许重构实现，但不能仅凭 controller 所属关系推导另一记录的语义归属。|
|未开始工作一律结算|任务目标限定为离线创建并离开的 fresh query；原始缓存后台两项通过，两次新 AUTO 均退步。旧反思仍提出未开始工作应结算的未限定规则。|真实退步已确认。多个补丁同时变化，尚未逐项隔离其因果贡献；不能把所有退步都断言为单一代码修改导致。|
|反馈丢失原有成功|候选某关系结果未知时，旧反馈函数跳过了原始版本成功项。|新函数独立记录原始成功与候选成功；未知结果保留未知，不计为失败或退步。当前两份完整评分数值不受此边界修复影响。|

两份实际训练 AUTO 均为 UNDERREACH，分别保留 27/29 个目标关系。每份：原有成功 21、保留成功 19、改善 8、退步 2；包含全部 75 条实际/预期检查及 7 条失败检查。两条退步为 cached-paused-background 与 cached-later-consumption。完整关系向量、已通过项、失败的 actual/expected、补丁和模型公开交付均保存在 `feedback.json` 与 `inputs/`。公开交付是待核对的模型声称，未升级为行为事实。

接口改变：

- `handoff.py`：校验输入 SHA256、逐字源码行、JSON pointer 观察值及训练材料角色；反思载荷只从显式训练清单读取，反馈必须与冻结的训练评分重新计算结果一致。
- `evidence-ledger.json`：区分文档要求、源码事实、实际观察、执行 Agent 的保留解释、原因假设与未知；标注作者和出处。针对本训练案例的解释由执行 Agent 明确编写，未伪装成通用自动诊断。
- `reflection.schema.json` / `reflection-prompt.md`：为每条候选规则增加原文引用、支持依据、适用条件、保留义务、反例处理及因果状态。规则元数据与经验正文分离，后续维护端只应收到通过入库的正文。经验正文仍禁止案例标识、断言名、专用字段、路径与补丁。
- 结构检查通过不意味着语义正确。还要求绑定候选与账本摘要的执行 Agent 核查，确认没有遗漏正文中的规范规则、保留行为或反例。不存在独立干预证据时不能声称 verified cause。普通范围限制与核心政策未知分开处理。
- 此模块仅实现反思交接及候选前置核查，不实现或绕过开发回验入库流程。即使核查通过，`admitted` 仍为 false；后续仍须原定预算内开发观察和入库依据。

复用与隔离：

原任务、正确的自动 Contract、原源码/文档、训练标准、原始与两份训练评分、完整补丁及交付均逐字复制并记录摘要。旧错误候选和旧反思输入仅放入 `audit/old/` 用于离线审计，不进入新反思载荷，不作为种子，也没有人工改写候选。评分解释和标准仅在训练侧使用。测试评分、参考补丁、测试身份与预期类别均不进入新载荷。

本次没有改变案例选择。原 cohort 的 D1/T1、D2/T2 分别是同源跨语言配对；两对并非同一种机制。本次仅处理 D1 已观察到的反思交接问题，没有额外搜索 T3 经验，也没有验证新的分类能力。旧结果不能证明经验有效或无效，本次离线检查也不能证明迁移收益。

验证：标准库 unittest 共 17 项通过，原始拒绝候选按原文回放仍不入库。检查包括 checks/assertions 两种格式、完整得失、未知结果、源码与 JSON 证据篡改、来源角色、反馈注入、遗漏反例、绑定错误、普通范围限制和政策未知的不同处理。合成候选仅是单元测试内的结构夹具，没有保存为实际模型输出。实际日志见 `verification.json` / `verification.log`，来源对照与完整性见 `integrity.json`。

成本：新增实验模型会话 0、请求 0、实验 tokens 0；新增行为评分 0。执行 Agent 的工程准备 tokens 和金额无法从当前接口读取，保持 null。旧实验的未知用量不改写，不纳入本次零调用的计量。

后续需要新的、明确预算内的反思与开发验证，才能检查新接口是否帮助模型产生有据经验。本目录没有调度器或自动启动入口。服务断流可靠性与新模型输出质量未在此次零模型工作中得到验证，不能据此直接宣称可以稳定重跑 A/B。

推荐 Git commit subject：`research: add evidence-grounded reflection handoff and offline replay`

推荐 Git commit body：

```text
Preserve training requirements, complete behavior deltas, patches and public
deliveries in a hash-pinned, training-only reflection payload.

Separate source facts, observations, preservation judgments and causal
hypotheses. Require rule evidence, conditions, preservation obligations,
counterexample handling and a separate hash-bound semantic review.

Keep original successes when candidate observations are unknown. Replay the
rejected raw candidate without rewriting or admitting it. Add 17 offline
checks; run no model sessions and modify no historical or production data.
```
