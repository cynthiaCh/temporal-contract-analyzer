本次 D1 证据交接修复后的最小开发验证已按停止规则结束。

本轮固定使用原 D1，不增加 AUTO 基线、提取、分类、评委或测试会话。比较基线按实际开始时间选择，见 baseline-selection.json。

反思使用 gpt-5.6-terra / medium，维护使用 gpt-5.6-terra / low；分别最多 12/24 请求、600 秒，并发 1。源代码、任务、自动 Contract、工具、公共提示及原 29 项评分器均已离线核验并冻结。维护唯一有意新增的材料是未经润色的候选经验正文。

本轮逐条核查为执行 Agent 的 AI 辅助核查，不是独立人工批准。已保存原始 CLI 事件、完整/部分模型消息、请求/工具事件、错误、工作区、补丁、原评分与计量。原始服务 wire body 若 CLI 未暴露则明确记为不可用，未伪造。

|条件|有效评分|整题|满足关系|缓存后台保留|延后读取保留|相对原始版本损失|
|---|---|---|---|---|---|---|
|AUTO 1|True|UNDERREACH|27/29|False|False|cached-paused-background, cached-later-consumption|
|AUTO 2|True|UNDERREACH|27/29|False|False|cached-paused-background, cached-later-consumption|
|经验回验 1|未启动|—|—|—|—|—|
|经验回验 2|未启动|—|—|—|—|—|

全部 29 项行为向量：

|关系|AUTO 1|AUTO 2|
|---|---|---|
|offline-detach-false|通过|通过|
|offline-detach-true|通过|通过|
|offline-detach-always|通过|通过|
|offline-nonconsuming-detach|通过|通过|
|active-offline-resume|通过|通过|
|multiple-observers|通过|通过|
|last-observer-offline|通过|通过|
|unknown-unsubscribe|通过|通过|
|consumed-flight-cancel|通过|通过|
|nonconsuming-flight-cache|通过|通过|
|cached-paused-background|失败|失败|
|cached-consumed-revert|通过|通过|
|remount-generation|通过|通过|
|late-old-generation|通过|通过|
|always-mode|通过|通过|
|focus-gates-resume|通过|通过|
|focus-does-not-gate-first-start|通过|通过|
|offline-first-retry|通过|通过|
|nonconsuming-cancel-retry|通过|通过|
|reentrant-unsubscribe-at-entry|通过|通过|
|framework-unmount|通过|通过|
|cached-later-consumption|失败|失败|
|accepted-resume-then-offline|通过|通过|
|detach-after-resume-queued|通过|通过|
|independent-query-keys|通过|通过|
|dependency-config-preserved|通过|通过|
|cached-prior-consumed-success|通过|通过|
|cached-prior-consumed-cancelled|通过|通过|
|retained-context-query-flag|通过|通过|

结果与停止：

{"planned": 3, "started": 1, "valid_sessions": 1, "invalid_sessions": 0, "not_started": 2, "valid_new_behavior_scores": 0, "whole_task_passes_new": null, "content_rejected_reflections": 1}

停止记录：{"reason": "Candidate support protocol invalid: ValueError('rule quotation is not verbatim candidate text')", "classification": "candidate_rejected", "time": 1794153645.9683425, "no_retry": true, "no_more_model_calls": true}

候选内容核查：见 semantic-review.json、structural-review.json / candidate-rejection.json；候选原文和逐规则证据分别保存。

后续冻结资格：No qualifying content-supported development improvement established.

成本（旧基线与本次新增分开）：

```json
{
  "existing_AUTO_only": {
    "sessions_started": 2,
    "requests_started": 11,
    "tool_attempts": 9,
    "known_usage_subtotal": {
      "input_tokens": 144091,
      "cached_input_tokens": 105216,
      "cache_write_input_tokens": 0,
      "output_tokens": 8051,
      "reasoning_output_tokens": 3721,
      "total_tokens": 152142
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 144091,
      "cached_input_tokens": 105216,
      "cache_write_input_tokens": 0,
      "output_tokens": 8051,
      "reasoning_output_tokens": 3721,
      "total_tokens": 152142
    },
    "seconds": 213.30908036231995,
    "money": null
  },
  "new_reflection": {
    "sessions_started": 1,
    "requests_started": 1,
    "tool_attempts": 0,
    "known_usage_subtotal": {
      "input_tokens": 69946,
      "cached_input_tokens": 0,
      "cache_write_input_tokens": 0,
      "output_tokens": 2758,
      "reasoning_output_tokens": 1232,
      "total_tokens": 72704
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 69946,
      "cached_input_tokens": 0,
      "cache_write_input_tokens": 0,
      "output_tokens": 2758,
      "reasoning_output_tokens": 1232,
      "total_tokens": 72704
    },
    "seconds": 43.19871187210083,
    "money": null
  },
  "new_maintenance": {
    "sessions_started": 0,
    "requests_started": 0,
    "tool_attempts": 0,
    "known_usage_subtotal": {
      "input_tokens": 0,
      "cached_input_tokens": 0,
      "cache_write_input_tokens": 0,
      "output_tokens": 0,
      "reasoning_output_tokens": 0,
      "total_tokens": 0
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 0,
      "cached_input_tokens": 0,
      "cache_write_input_tokens": 0,
      "output_tokens": 0,
      "reasoning_output_tokens": 0,
      "total_tokens": 0
    },
    "seconds": 0,
    "money": null
  },
  "new_total": {
    "sessions_started": 1,
    "requests_started": 1,
    "tool_attempts": 0,
    "known_usage_subtotal": {
      "input_tokens": 69946,
      "cached_input_tokens": 0,
      "cache_write_input_tokens": 0,
      "output_tokens": 2758,
      "reasoning_output_tokens": 1232,
      "total_tokens": 72704
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 69946,
      "cached_input_tokens": 0,
      "cache_write_input_tokens": 0,
      "output_tokens": 2758,
      "reasoning_output_tokens": 1232,
      "total_tokens": 72704
    },
    "seconds": 43.19871187210083,
    "money": null
  },
  "engineering": {
    "elapsed_batch_wall_seconds": 421.4100298881531,
    "offline_setup_seconds": 0.36209607124328613,
    "tokens": null,
    "money": null,
    "note": "Execution-agent engineering usage not exposed; not zero."
  }
}
```

未知用量保持 null；未启动槽位不计行为失败。训练原有成功、改善和全部退步未因目标项改善而省略。

本轮四项结论：

1. 候选是否仍含无据政策或错误事实：AI 辅助核查未确认新正文重犯旧的“一律结算未开始工作”与“必须迁移消费记录”两项错误，正文也没有宣称旧补丁已整题修好。但候选仍无效：三条 rules.quote 全部不在候选正文中，而是引用任务或文档；conditions 和部分 preserve 是文字说明而不是协议要求的证据/约束 ID。requires 中 boundary_persistence、discard_boundary_policy、entry_snapshot 未获得其定义要求的 D1 依据。完整逐条结论见 semantic-review.json 和 candidate-audit.json。

2. 两项目标是否改善：新回验有效评分为 0。没有新有效评分时，改善未知，不能把旧基线结果当作新经验收益。

3. 是否引入其他损失：未执行维护时无法判断新修复的行为损失；旧两次 AUTO 已知损失分别完整列出。

4. 是否值得进入后续冻结经验测试：当前不具备进入冻结经验测试的依据。

工程与解释边界：输出协议的 JSON 类型和长度检查通过，完整原始响应为 8,131 bytes，正文为 2,992 字符，未截断也未补全。失败发生在逐条证据交接核查，服务本身正常。当前 schema 对证据 ID 仅约束为字符串，动态绑定依赖本地核查；反思输入未包含所有适用前提名称的完整定义。后者可能影响解释，但不能据此断言模型产生错误的原因。没有在观察输出后修改 prompt、schema 或候选来放行。

模型把“多处修改没有隔离因果”标为 policy，把“尚未有完整已验证修复”标为 applicability。这些标签本身不证明核心业务冲突；执行 Agent 将其解释为因果验证与开发范围限制。此次拒绝以真实的文本/证据绑定错误为依据，不以这些标签机械判错。

本轮只有同题开发观察；即使结果改善，也不能单凭该轮证明交接修复有稳定因果收益、独立测试收益或同源跨语言迁移。没有测试案例被运行；后续测试不自动启动。

推荐 commit subject: research: archive rejected D1 evidence-handoff reflection

推荐 commit body:

```text
Verify and reuse the latest two condition-matched D1 AUTO baselines.
Run one bounded reflection with grounded feedback and rejected-clause critique.
Preserve raw output and record AI-assisted rule-by-rule evidence review.
Stop after invalid text/evidence bindings; leave both repair slots unstarted.
Archive baseline behavior vectors, raw candidate, rejection evidence and
separate old/new costs without retries, test runs or production updates.
```

未创建 Git 提交，未更新生产经验库，未修改历史实验或全局配置。
