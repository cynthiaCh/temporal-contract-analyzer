状态：completed。固定测试例 query-paused-initial-fetch-10266-python3；维护启动 4/4，有效评分 4。

完整沿用本 Python 案例的 29 项原关系评分；未删减、统一分数或放宽行为规则。

本批只重做一次受影响测试提取；限定条件修复使用通用逻辑指导与当前原任务的词法上下文，不给出旧错误/经验/评分作为提取输入。原始模型 Contract 未人工改写，词法覆盖提醒不能替代逐条语义核查。45项离线检查通过，旧失败输出及拒绝决定保持原样。

经验为上一 query 困难案例开发批次的冻结规则正文，原文未改，登记类别来自原训练预分析。测试预分析没有收到该类别、开发轨迹、经验、历史成绩或评分材料。
实际测试分类：T4；路由：{"condition": "ROUTED", "primary_class": "T4", "reason": "source_bound_premises", "selected": {"version": "query-headroom-fresh-rules-1", "sha256": "dfb1d630862fc4413ac89708504a8006eacdabce92676be60d3302bc9e0c16f4", "text_sha256": "a7a57383f9e2c29651345ffc98f17bcffebcc2a163f7b00cab4315fef0b1fc95"}, "checks": [{"sha256": "dfb1d630862fc4413ac89708504a8006eacdabce92676be60d3302bc9e0c16f4", "premises": [{"predicate": "shared_lifetime", "state": "known", "evidence": [{"file": "README.md", "line": 16, "quote": "The component owns observer scope; the cache remains outside individual views."}], "satisfied": true}, {"predicate": "observer_lifetime", "state": "known", "evidence": [{"file": "README.md", "line": 12, "quote": "Multiple observers share one fetch. Unconsumed active work can finish into cache"}], "satisfied": true}, {"predicate": "attempt_resource", "state": "known", "evidence": [{"file": "README.md", "line": 7, "quote": "accessor. Each actual access records consumption; each fetch owns its controller"}], "satisfied": true}, {"predicate": "lazy_consumption", "state": "known", "evidence": [{"file": "README.md", "line": 23, "quote": "invokes the native consumption closure synchronously; Promise settlement later"}], "satisfied": true}, {"predicate": "async_resume", "state": "known", "evidence": [{"file": "README.md", "line": 9, "quote": "paused continuation resumes on a Promise turn. First start uses network mode;"}], "satisfied": true}], "exclusions": [], "eligible": true}]}。

类别、源码证据和每项前提判断见 derived/T/analysis.json、semantic-review.json 与 testing/route.json；核查为执行 Agent 的 AI 辅助核查，不是独立人工批准。
A/B提示相同：False。若回退，重复运行差异不能归因为经验，亦不证明经验效果等价。

|条件|计划|启动|有效|无效|未启动|整题通过/有效|
|---|---|---|---|---|---|---|
|A|2|2|2|0|0|0/2|
|B|2|2|2|0|0|1/2|

|槽位|满足关系|整题|相对原始候选新增通过|丢失原通过|
|---|---|---|---|---|
|B1|29/29|True|['offline-detach-false', 'offline-detach-true', 'offline-detach-always', 'offline-nonconsuming-detach', 'last-observer-offline', 'framework-unmount', 'detach-after-resume-queued', 'independent-query-keys']|[]|
|A1|27/29|False|['offline-detach-false', 'offline-detach-true', 'offline-detach-always', 'offline-nonconsuming-detach', 'last-observer-offline', 'framework-unmount', 'detach-after-resume-queued', 'independent-query-keys']|['cached-paused-background', 'cached-later-consumption']|
|A2|26/29|False|['offline-detach-false', 'offline-detach-true', 'offline-detach-always', 'last-observer-offline', 'framework-unmount', 'detach-after-resume-queued', 'independent-query-keys']|['cached-paused-background', 'cached-later-consumption']|
|B2|27/29|False|['offline-detach-false', 'offline-detach-true', 'offline-detach-always', 'offline-nonconsuming-detach', 'last-observer-offline', 'framework-unmount', 'detach-after-resume-queued', 'independent-query-keys']|['cached-paused-background', 'cached-later-consumption']|

|完整行为向量（按原期望判断）|B1|A1|A2|B2|
|---|---|---|---|---|
|offline-detach-false|通过|通过|通过|通过|
|offline-detach-true|通过|通过|通过|通过|
|offline-detach-always|通过|通过|通过|通过|
|offline-nonconsuming-detach|通过|通过|失败|通过|
|active-offline-resume|通过|通过|通过|通过|
|multiple-observers|通过|通过|通过|通过|
|last-observer-offline|通过|通过|通过|通过|
|unknown-unsubscribe|通过|通过|通过|通过|
|consumed-flight-cancel|通过|通过|通过|通过|
|nonconsuming-flight-cache|通过|通过|通过|通过|
|cached-paused-background|通过|失败|失败|失败|
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
|cached-later-consumption|通过|失败|失败|失败|
|accepted-resume-then-offline|通过|通过|通过|通过|
|detach-after-resume-queued|通过|通过|通过|通过|
|independent-query-keys|通过|通过|通过|通过|
|dependency-config-preserved|通过|通过|通过|通过|
|cached-prior-consumed-success|通过|通过|通过|通过|
|cached-prior-consumed-cancelled|通过|通过|通过|通过|
|retained-context-query-flag|通过|通过|通过|通过|

全部有效B与A的逐项描述性比较：
```json
[
  {
    "B": "B1",
    "A": "A1",
    "improvements": [
      "cached-paused-background",
      "cached-later-consumption"
    ],
    "regressions": [],
    "retained_successes": [
      "offline-detach-false",
      "offline-detach-true",
      "offline-detach-always",
      "offline-nonconsuming-detach",
      "active-offline-resume",
      "multiple-observers",
      "last-observer-offline",
      "unknown-unsubscribe",
      "consumed-flight-cancel",
      "nonconsuming-flight-cache",
      "cached-consumed-revert",
      "remount-generation",
      "late-old-generation",
      "always-mode",
      "focus-gates-resume",
      "focus-does-not-gate-first-start",
      "offline-first-retry",
      "nonconsuming-cancel-retry",
      "reentrant-unsubscribe-at-entry",
      "framework-unmount",
      "accepted-resume-then-offline",
      "detach-after-resume-queued",
      "independent-query-keys",
      "dependency-config-preserved",
      "cached-prior-consumed-success",
      "cached-prior-consumed-cancelled",
      "retained-context-query-flag"
    ],
    "unknown": []
  },
  {
    "B": "B1",
    "A": "A2",
    "improvements": [
      "offline-nonconsuming-detach",
      "cached-paused-background",
      "cached-later-consumption"
    ],
    "regressions": [],
    "retained_successes": [
      "offline-detach-false",
      "offline-detach-true",
      "offline-detach-always",
      "active-offline-resume",
      "multiple-observers",
      "last-observer-offline",
      "unknown-unsubscribe",
      "consumed-flight-cancel",
      "nonconsuming-flight-cache",
      "cached-consumed-revert",
      "remount-generation",
      "late-old-generation",
      "always-mode",
      "focus-gates-resume",
      "focus-does-not-gate-first-start",
      "offline-first-retry",
      "nonconsuming-cancel-retry",
      "reentrant-unsubscribe-at-entry",
      "framework-unmount",
      "accepted-resume-then-offline",
      "detach-after-resume-queued",
      "independent-query-keys",
      "dependency-config-preserved",
      "cached-prior-consumed-success",
      "cached-prior-consumed-cancelled",
      "retained-context-query-flag"
    ],
    "unknown": []
  },
  {
    "B": "B2",
    "A": "A1",
    "improvements": [],
    "regressions": [],
    "retained_successes": [
      "offline-detach-false",
      "offline-detach-true",
      "offline-detach-always",
      "offline-nonconsuming-detach",
      "active-offline-resume",
      "multiple-observers",
      "last-observer-offline",
      "unknown-unsubscribe",
      "consumed-flight-cancel",
      "nonconsuming-flight-cache",
      "cached-consumed-revert",
      "remount-generation",
      "late-old-generation",
      "always-mode",
      "focus-gates-resume",
      "focus-does-not-gate-first-start",
      "offline-first-retry",
      "nonconsuming-cancel-retry",
      "reentrant-unsubscribe-at-entry",
      "framework-unmount",
      "accepted-resume-then-offline",
      "detach-after-resume-queued",
      "independent-query-keys",
      "dependency-config-preserved",
      "cached-prior-consumed-success",
      "cached-prior-consumed-cancelled",
      "retained-context-query-flag"
    ],
    "unknown": []
  },
  {
    "B": "B2",
    "A": "A2",
    "improvements": [
      "offline-nonconsuming-detach"
    ],
    "regressions": [],
    "retained_successes": [
      "offline-detach-false",
      "offline-detach-true",
      "offline-detach-always",
      "active-offline-resume",
      "multiple-observers",
      "last-observer-offline",
      "unknown-unsubscribe",
      "consumed-flight-cancel",
      "nonconsuming-flight-cache",
      "cached-consumed-revert",
      "remount-generation",
      "late-old-generation",
      "always-mode",
      "focus-gates-resume",
      "focus-does-not-gate-first-start",
      "offline-first-retry",
      "nonconsuming-cancel-retry",
      "reentrant-unsubscribe-at-entry",
      "framework-unmount",
      "accepted-resume-then-offline",
      "detach-after-resume-queued",
      "independent-query-keys",
      "dependency-config-preserved",
      "cached-prior-consumed-success",
      "cached-prior-consumed-cancelled",
      "retained-context-query-flag"
    ],
    "unknown": []
  }
]
```

本案例属于 hit 子集；全体结果与该子集相同，另一个子集没有案例，不补零效果。

成本（开发费用仅列参考，未计入本轮新增）：
```json
{
  "preanalysis": {
    "sessions_started": 1,
    "requests_started": 2,
    "tool_attempts": 2,
    "known_usage_subtotal": {
      "input_tokens": 43223,
      "cached_input_tokens": 20864,
      "cache_write_input_tokens": 0,
      "output_tokens": 942,
      "reasoning_output_tokens": 75,
      "total_tokens": 44165
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 43223,
      "cached_input_tokens": 20864,
      "cache_write_input_tokens": 0,
      "output_tokens": 942,
      "reasoning_output_tokens": 75,
      "total_tokens": 44165
    },
    "seconds": 31.64452362060547,
    "money": null
  },
  "AUTO": {
    "sessions_started": 2,
    "requests_started": 17,
    "tool_attempts": 15,
    "known_usage_subtotal": {
      "input_tokens": 224980,
      "cached_input_tokens": 184576,
      "cache_write_input_tokens": 0,
      "output_tokens": 7127,
      "reasoning_output_tokens": 2706,
      "total_tokens": 232107
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 224980,
      "cached_input_tokens": 184576,
      "cache_write_input_tokens": 0,
      "output_tokens": 7127,
      "reasoning_output_tokens": 2706,
      "total_tokens": 232107
    },
    "seconds": 262.82602643966675,
    "money": null
  },
  "ROUTED": {
    "sessions_started": 2,
    "requests_started": 17,
    "tool_attempts": 15,
    "known_usage_subtotal": {
      "input_tokens": 258801,
      "cached_input_tokens": 211200,
      "cache_write_input_tokens": 0,
      "output_tokens": 8185,
      "reasoning_output_tokens": 3124,
      "total_tokens": 266986
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 258801,
      "cached_input_tokens": 211200,
      "cache_write_input_tokens": 0,
      "output_tokens": 8185,
      "reasoning_output_tokens": 3124,
      "total_tokens": 266986
    },
    "seconds": 199.70628094673157,
    "money": null
  },
  "new_total": {
    "sessions_started": 5,
    "requests_started": 36,
    "tool_attempts": 32,
    "known_usage_subtotal": {
      "input_tokens": 527004,
      "cached_input_tokens": 416640,
      "cache_write_input_tokens": 0,
      "output_tokens": 16254,
      "reasoning_output_tokens": 5905,
      "total_tokens": 543258
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 527004,
      "cached_input_tokens": 416640,
      "cache_write_input_tokens": 0,
      "output_tokens": 16254,
      "reasoning_output_tokens": 5905,
      "total_tokens": 543258
    },
    "seconds": 494.1768310070038,
    "money": null
  },
  "previous_stopped_batch_reference_only_not_in_test_cost": {
    "sessions_started": 4,
    "requests_started": 18,
    "tool_attempts": 15,
    "known_usage_subtotal": {
      "input_tokens": 302841,
      "cached_input_tokens": 193152,
      "cache_write_input_tokens": 0,
      "output_tokens": 11653,
      "reasoning_output_tokens": 5461,
      "total_tokens": 314494
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 302841,
      "cached_input_tokens": 193152,
      "cache_write_input_tokens": 0,
      "output_tokens": 11653,
      "reasoning_output_tokens": 5461,
      "total_tokens": 314494
    },
    "seconds": 318.0014262199402,
    "money": null
  },
  "engineering": {
    "tokens": null,
    "money": null
  },
  "money": null
}
```

原始候选和每槽独立工作区、真实提示、模型原始输出、工具/请求事件、最终源码、Python生成补丁、原评分和计量均归档。完整反馈在 summary.json，每次完整原始检查及事件轨迹在 archive/score/stdout.json。
预分析摘要和运行器在首次调用前冻结；Contract、分类及路由结果、两组完整提示在首次维护前冻结。没有测试后反思、额外候选、重试、补跑或评分规则改变。
两次重复只作描述。该案例已经暴露且与训练来自同一来源单元；开发通过不并入测试分母，本轮不能证明独立泛化、统计显著或稳定效果。
未创建提交、修改历史或更新生产经验库。本批结束即停止。

执行核查：B1 的新增取消分支保留旧缓存状态边界；B2 仅区分 entered/online，遗漏该边界。B2 自测未覆盖已有缓存、暂停且未进入执行的后台刷新。对应原评分显示请求数0而要求1，最终数据未刷新。B2仍损失原始候选的两项正确行为。详见 EXECUTION_REVIEW.md 与 execution-review.json；这是源码/轨迹核查，不是受控因果消融。

结论：{"actual_experience_delivered": true, "all_vectors_identical": false, "observed_incremental_behavior_gain": true, "observed_behavior_regression": false, "interpretation": "AUTO has observed repair headroom. Report every pairwise gain/loss and whole-task result descriptively; two repeats do not establish stable or causal benefit.", "cost_differences_are_descriptive_only": true}
成本描述：A 17请求/232107 tokens；B 17请求/266986 tokens。两次重复及固定顺序不足以把这次成本差异解释为稳定节省。
实际源码及验证字节码差异见 execution-audit.json；评分向量相同不等于所有未覆盖行为或实现完全相同。
