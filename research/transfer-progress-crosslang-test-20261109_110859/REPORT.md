状态：completed。固定测试例 transfer-progress-maintenance-v2-python3；维护启动 4/4，有效评分 4。

完整沿用 Python 案例的 26 项原关系评分，不把训练例的20项删减或套用到此例。

经验为 locked-applicability 开发批次的规则正文，原文未改，登记类别来自原训练预分析。测试预分析没有收到该类别、开发轨迹、经验、历史成绩或评分材料。
实际测试分类：T1；路由：{"condition": "ROUTED", "primary_class": "T1", "reason": "source_bound_premises", "selected": {"version": "locked-parent-rules-crosslang-test-1", "sha256": "f830cadc309715a38b229e099de7c02f369b74fa82b64d127dc7b77c3b207f88", "text_sha256": "71363738e6be4a590761bda2145c4fc6f538f2a9c0462e0b3b75b002bdcb8138"}, "checks": [{"sha256": "f830cadc309715a38b229e099de7c02f369b74fa82b64d127dc7b77c3b207f88", "premises": [{"predicate": "shared_lifetime", "state": "known", "evidence": [{"file": "README.md", "line": 50, "quote": "Decoding may return a value or a Promise. The same file and source can be reused"}], "satisfied": true}, {"predicate": "observer_lifetime", "state": "known", "evidence": [{"file": "README.md", "line": 51, "quote": "by multiple panel visits. Each selected or retried attempt starts one subscripti"}], "satisfied": true}, {"predicate": "attempt_resource", "state": "known", "evidence": [{"file": "src/workflow.py", "line": 27, "quote": "        self.aborted=True;self.stop();self.env.call('cancel',self.file['token'],"}], "satisfied": true}, {"predicate": "entry_snapshot", "state": "known", "evidence": [{"file": "README.md", "line": 11, "quote": "An accepted retry always belongs to the file and visit present at entry, creates"}], "satisfied": true}, {"predicate": "inline_reentry", "state": "known", "evidence": [{"file": "README.md", "line": 59, "quote": "new visits remain live. `showProgress` may synchronously select or hide through"}], "satisfied": true}, {"predicate": "effect_lifetimes", "state": "known", "evidence": [{"file": "README.md", "line": 56, "quote": "finishes, including work accepted before the visit closes. A retired visit"}], "satisfied": true}], "exclusions": [], "eligible": true}]}。

类别、源码证据和每项前提判断见 derived/T/analysis.json、semantic-review.json 与 testing/route.json；核查为执行 Agent 的 AI 辅助核查，不是独立人工批准。
A/B提示相同：False。若回退，重复运行差异不能归因为经验，亦不证明经验效果等价。

|条件|计划|启动|有效|无效|未启动|整题通过/有效|
|---|---|---|---|---|---|---|
|A|2|2|2|0|0|2/2|
|B|2|2|2|0|0|2/2|

|槽位|满足关系|整题|相对原始候选新增通过|丢失原通过|
|---|---|---|---|---|
|B1|26/26|True|['progress-normal', 'progress-reopen-during-start', 'progress-hide-emit-during-start', 'progress-switch-emit-during-start', 'progress-accepted-decode-after-hide', 'progress-accepted-decode-live', 'progress-accepted-decode-after-reopen', 'progress-live-retry', 'progress-accepted-decode-after-dispose', 'progress-independent-workspaces', 'progress-framework-unmount', 'progress-retry-abort-switch', 'progress-retry-abort-reopen']|[]|
|A1|26/26|True|['progress-normal', 'progress-reopen-during-start', 'progress-hide-emit-during-start', 'progress-switch-emit-during-start', 'progress-accepted-decode-after-hide', 'progress-accepted-decode-live', 'progress-accepted-decode-after-reopen', 'progress-live-retry', 'progress-accepted-decode-after-dispose', 'progress-independent-workspaces', 'progress-framework-unmount', 'progress-retry-abort-switch', 'progress-retry-abort-reopen']|[]|
|A2|26/26|True|['progress-normal', 'progress-reopen-during-start', 'progress-hide-emit-during-start', 'progress-switch-emit-during-start', 'progress-accepted-decode-after-hide', 'progress-accepted-decode-live', 'progress-accepted-decode-after-reopen', 'progress-live-retry', 'progress-accepted-decode-after-dispose', 'progress-independent-workspaces', 'progress-framework-unmount', 'progress-retry-abort-switch', 'progress-retry-abort-reopen']|[]|
|B2|26/26|True|['progress-normal', 'progress-reopen-during-start', 'progress-hide-emit-during-start', 'progress-switch-emit-during-start', 'progress-accepted-decode-after-hide', 'progress-accepted-decode-live', 'progress-accepted-decode-after-reopen', 'progress-live-retry', 'progress-accepted-decode-after-dispose', 'progress-independent-workspaces', 'progress-framework-unmount', 'progress-retry-abort-switch', 'progress-retry-abort-reopen']|[]|

|完整行为向量（按原期望判断）|B1|A1|A2|B2|
|---|---|---|---|---|
|retry-normal|通过|通过|通过|通过|
|retry-double|通过|通过|通过|通过|
|retry-abort-observe|通过|通过|通过|通过|
|retry-abort-hide|通过|通过|通过|通过|
|retry-abort-switch|通过|通过|通过|通过|
|retry-abort-reopen|通过|通过|通过|通过|
|retry-hidden-noop|通过|通过|通过|通过|
|selection-cleanup|通过|通过|通过|通过|
|cancel-idempotent|通过|通过|通过|通过|
|independent-workspaces|通过|通过|通过|通过|
|record-scope|通过|通过|通过|通过|
|progress-normal|通过|通过|通过|通过|
|progress-reopen-during-start|通过|通过|通过|通过|
|progress-hide-emit-during-start|通过|通过|通过|通过|
|progress-switch-emit-during-start|通过|通过|通过|通过|
|progress-accepted-decode-after-hide|通过|通过|通过|通过|
|progress-accepted-decode-live|通过|通过|通过|通过|
|progress-accepted-decode-after-reopen|通过|通过|通过|通过|
|progress-live-retry|通过|通过|通过|通过|
|hide-cleanup-reentry|通过|通过|通过|通过|
|progress-accepted-decode-after-dispose|通过|通过|通过|通过|
|progress-independent-workspaces|通过|通过|通过|通过|
|progress-framework-unmount|通过|通过|通过|通过|
|progress-retry-abort-switch|通过|通过|通过|通过|
|progress-retry-abort-reopen|通过|通过|通过|通过|
|record-byte-count-included|通过|通过|通过|通过|

全部有效B与A的逐项描述性比较：
```json
[
  {
    "B": "B1",
    "A": "A1",
    "improvements": [],
    "regressions": [],
    "retained_successes": [
      "retry-normal",
      "retry-double",
      "retry-abort-observe",
      "retry-abort-hide",
      "retry-abort-switch",
      "retry-abort-reopen",
      "retry-hidden-noop",
      "selection-cleanup",
      "cancel-idempotent",
      "independent-workspaces",
      "record-scope",
      "progress-normal",
      "progress-reopen-during-start",
      "progress-hide-emit-during-start",
      "progress-switch-emit-during-start",
      "progress-accepted-decode-after-hide",
      "progress-accepted-decode-live",
      "progress-accepted-decode-after-reopen",
      "progress-live-retry",
      "hide-cleanup-reentry",
      "progress-accepted-decode-after-dispose",
      "progress-independent-workspaces",
      "progress-framework-unmount",
      "progress-retry-abort-switch",
      "progress-retry-abort-reopen",
      "record-byte-count-included"
    ],
    "unknown": []
  },
  {
    "B": "B1",
    "A": "A2",
    "improvements": [],
    "regressions": [],
    "retained_successes": [
      "retry-normal",
      "retry-double",
      "retry-abort-observe",
      "retry-abort-hide",
      "retry-abort-switch",
      "retry-abort-reopen",
      "retry-hidden-noop",
      "selection-cleanup",
      "cancel-idempotent",
      "independent-workspaces",
      "record-scope",
      "progress-normal",
      "progress-reopen-during-start",
      "progress-hide-emit-during-start",
      "progress-switch-emit-during-start",
      "progress-accepted-decode-after-hide",
      "progress-accepted-decode-live",
      "progress-accepted-decode-after-reopen",
      "progress-live-retry",
      "hide-cleanup-reentry",
      "progress-accepted-decode-after-dispose",
      "progress-independent-workspaces",
      "progress-framework-unmount",
      "progress-retry-abort-switch",
      "progress-retry-abort-reopen",
      "record-byte-count-included"
    ],
    "unknown": []
  },
  {
    "B": "B2",
    "A": "A1",
    "improvements": [],
    "regressions": [],
    "retained_successes": [
      "retry-normal",
      "retry-double",
      "retry-abort-observe",
      "retry-abort-hide",
      "retry-abort-switch",
      "retry-abort-reopen",
      "retry-hidden-noop",
      "selection-cleanup",
      "cancel-idempotent",
      "independent-workspaces",
      "record-scope",
      "progress-normal",
      "progress-reopen-during-start",
      "progress-hide-emit-during-start",
      "progress-switch-emit-during-start",
      "progress-accepted-decode-after-hide",
      "progress-accepted-decode-live",
      "progress-accepted-decode-after-reopen",
      "progress-live-retry",
      "hide-cleanup-reentry",
      "progress-accepted-decode-after-dispose",
      "progress-independent-workspaces",
      "progress-framework-unmount",
      "progress-retry-abort-switch",
      "progress-retry-abort-reopen",
      "record-byte-count-included"
    ],
    "unknown": []
  },
  {
    "B": "B2",
    "A": "A2",
    "improvements": [],
    "regressions": [],
    "retained_successes": [
      "retry-normal",
      "retry-double",
      "retry-abort-observe",
      "retry-abort-hide",
      "retry-abort-switch",
      "retry-abort-reopen",
      "retry-hidden-noop",
      "selection-cleanup",
      "cancel-idempotent",
      "independent-workspaces",
      "record-scope",
      "progress-normal",
      "progress-reopen-during-start",
      "progress-hide-emit-during-start",
      "progress-switch-emit-during-start",
      "progress-accepted-decode-after-hide",
      "progress-accepted-decode-live",
      "progress-accepted-decode-after-reopen",
      "progress-live-retry",
      "hide-cleanup-reentry",
      "progress-accepted-decode-after-dispose",
      "progress-independent-workspaces",
      "progress-framework-unmount",
      "progress-retry-abort-switch",
      "progress-retry-abort-reopen",
      "record-byte-count-included"
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
      "input_tokens": 49073,
      "cached_input_tokens": 23424,
      "cache_write_input_tokens": 0,
      "output_tokens": 924,
      "reasoning_output_tokens": 139,
      "total_tokens": 49997
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 49073,
      "cached_input_tokens": 23424,
      "cache_write_input_tokens": 0,
      "output_tokens": 924,
      "reasoning_output_tokens": 139,
      "total_tokens": 49997
    },
    "seconds": 28.75308609008789,
    "money": null
  },
  "AUTO": {
    "sessions_started": 2,
    "requests_started": 15,
    "tool_attempts": 13,
    "known_usage_subtotal": {
      "input_tokens": 214968,
      "cached_input_tokens": 172800,
      "cache_write_input_tokens": 0,
      "output_tokens": 7066,
      "reasoning_output_tokens": 2381,
      "total_tokens": 222034
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 214968,
      "cached_input_tokens": 172800,
      "cache_write_input_tokens": 0,
      "output_tokens": 7066,
      "reasoning_output_tokens": 2381,
      "total_tokens": 222034
    },
    "seconds": 193.38560724258423,
    "money": null
  },
  "ROUTED": {
    "sessions_started": 2,
    "requests_started": 14,
    "tool_attempts": 12,
    "known_usage_subtotal": {
      "input_tokens": 192391,
      "cached_input_tokens": 150528,
      "cache_write_input_tokens": 0,
      "output_tokens": 5179,
      "reasoning_output_tokens": 1900,
      "total_tokens": 197570
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 192391,
      "cached_input_tokens": 150528,
      "cache_write_input_tokens": 0,
      "output_tokens": 5179,
      "reasoning_output_tokens": 1900,
      "total_tokens": 197570
    },
    "seconds": 187.98222303390503,
    "money": null
  },
  "new_total": {
    "sessions_started": 5,
    "requests_started": 31,
    "tool_attempts": 27,
    "known_usage_subtotal": {
      "input_tokens": 456432,
      "cached_input_tokens": 346752,
      "cache_write_input_tokens": 0,
      "output_tokens": 13169,
      "reasoning_output_tokens": 4420,
      "total_tokens": 469601
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 456432,
      "cached_input_tokens": 346752,
      "cache_write_input_tokens": 0,
      "output_tokens": 13169,
      "reasoning_output_tokens": 4420,
      "total_tokens": 469601
    },
    "seconds": 410.12091636657715,
    "money": null
  },
  "training_development_reference_only_not_in_test_cost": {
    "sessions_started": 3,
    "requests_started": 18,
    "tool_attempts": 15,
    "known_usage_subtotal": {
      "input_tokens": 346474,
      "cached_input_tokens": 210176,
      "cache_write_input_tokens": 0,
      "output_tokens": 9921,
      "reasoning_output_tokens": 3408,
      "total_tokens": 356395
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 346474,
      "cached_input_tokens": 210176,
      "cache_write_input_tokens": 0,
      "output_tokens": 9921,
      "reasoning_output_tokens": 3408,
      "total_tokens": 356395
    },
    "seconds": 329.56228041648865,
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

四次完整行为向量相同，均整题通过；原三项启动内部关系在两组中全部通过，未观察到新增通过或行为退步。由于 AUTO 两次已全部修对，本轮不提供经验的额外行为收益证据，也不证明两组等价或经验普遍无效。
成本描述：A 15请求/222034 tokens；B 14请求/197570 tokens。两次重复及固定顺序不足以把这次成本差异解释为稳定节省。
实际源码及验证字节码差异见 execution-audit.json；评分向量相同不等于所有未覆盖行为或实现完全相同。
