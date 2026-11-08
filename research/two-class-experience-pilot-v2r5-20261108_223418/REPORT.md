# 原定两案例A/B工具试验：最终结果

**状态：STOPPED**。最终测试修订只运行固定8个维护槽位；准备模型输出和全部停止记录保留并单独计费。

本批已启动6/8槽，5个有效原评分全部UNDERREACH，1个服务断流无效未评分，2个未启动。有效评分A=2、B=3；对应整题通过A=0/2、B=0/3。空经验库使A/B逐字相同，没有经验效果估计。归档在实际null用量断流下正常完成。

## Task 1：实现、修复与语义审计

复用Python归档、隔离和host-owned请求计量，修复null用量、内嵌JSON字符串上限、角色schema绑定及安全只读重定向。原始服务/错误/部分输出与归档状态分开保存；仅完整候选准入评分。49项离线检查、四例namespace/JS/Python正文读取、两种历史失败回放及16条真实读取请求验证通过。原评分器/原候选/依赖/生产经验库/全局配置未改，没有提交。
原D1/T1方向错误确认：Repair后的错误现象被改成保留义务；原文没有字面must-not，旧报告的该措辞属于解释。原反思声称第一次补丁已修复离线退出，与实际检查/调用记录相反。为何模型作此错误归因仍未知。反馈接口漏读checks而只读assertions、把原始成功与保留成功混义，均已修复；不能说原布尔向量本身错误。
D1新自动对象明确区分共享消费记录与单次取消资源；T1新对象方向、归属和引用可核对。其自评栏中的“冲突/未知”有些是资源-记录区别、当前缺陷-预期行为区别或未穷尽路径声明，并非互斥业务政策。模型原文和自评列表全部保留；由当前可见任务/源码的执行Agent否决记录判定是否存在核心冲突，不把自评栏名当真值，也不手工改写自动材料。真实核心未知仍必须拒绝。
四例均为既有暴露：D1/T1共享query-paused-initial-fetch-10266，D2/T2共享debounced-submit-flush；T2既往求解和事后评分v2保持披露。44份校准按原始base/task/oracle摘要精确匹配复用；Node18.17与JS manifest Node16差异披露，Python3.8.10匹配。没有连接模型预跑，没有第三例。

## Task 2：开发、拒绝入库与冻结测试

D1以修正后公共Contract从原始候选独立运行两次新AUTO，均27/29行为通过，整题UNDERREACH。两次均保留缓存暂停后台/后续消费失败；反馈含每次75条实际检查、7条失败检查、完整原有成功/改善/退步，没有从断言名称推断唯一原因。v1错误Contract下的基线不混入受控比较。
唯一一次新反思生成的候选未人工润色，但明确要求消费记录归属单次执行、并泛化结算所有已接纳未开始工作，与当前共享记录/缓存保留政策冲突。因此按“无确认无据业务政策”的准入条件拒绝，在付费回验前剔除，未生成第二候选或借用旧E2。两次开发回验上限未消耗；这不是恢复“两次全对”门槛。候选原文/原始输出/完整拒绝依据在development/。
D2/T3在原开发中两次AUTO已通过，本次不开展额外T3经验搜索，正确Contract保持逐字复用。经验库为空，源修订在T1预分析前已锁定；空库仍执行固定8槽。所有测试Contract、源审查、路由、预算和调度在首个测试维护前再次冻结。测试不学习。

| 测试例 | 实际机制主类 | 路由 | A整题/有效评分 | B整题/有效评分 |
|---|---|---|---|---|
|T1|T4|empty_library|0/2|0/2|
|T2|T3|empty_library|0/0|0/1|

A/B对每个案例提示字节相同，因为没有可投放经验。所有结果均保留；相同提示的随机差异不能归因于经验，也不能证明经验效果等价。当前模型都是gpt-5.6-terra/low、24请求/600s、相同工具、并发1，从同一原始候选独立开始。种子2026110804只固定块内顺序，不控制采样。

### T1 证据与完整结果

分类源证据：[{"file": "src/workflow.py", "line": 49, "quote": "else:q.state['fetchStatus']='paused'"}, {"file": "src/workflow.py", "line": 59, "quote": "else:a.retry_cancelled=True"}, {"file": "src/workflow.py", "line": 39, "quote": "self.invoke(q,a)"}]
路由：{"condition": "AUTO", "reason": "empty_library", "selected": null, "checks": [], "primary_class": "T4"}
前提状态：[{"predicate": "shared_lifetime", "state": "known", "evidence": [{"file": "README.md", "line": 16, "quote": "The component owns observer scope; the cache remains outside individual views."}]}, {"predicate": "observer_lifetime", "state": "known", "evidence": [{"file": "src/workflow.py", "line": 44, "quote": "self.handles[handle]=q;q.observers.add(handle)"}]}, {"predicate": "attempt_resource", "state": "known", "evidence": [{"file": "README.md", "line": 7, "quote": "Each actual access records consumption; each fetch owns its controller"}]}, {"predicate": "lazy_consumption", "state": "known", "evidence": [{"file": "src/workflow.py", "line": 16, "quote": "def consume(_):q.consumed=True;return None"}]}, {"predicate": "async_resume", "state": "known", "evidence": [{"file": "src/workflow.py", "line": 40, "quote": "self.env.call('defer',self.env.bind(continuation))"}]}, {"predicate": "deferred_batch", "state": "unknown", "evidence": []}, {"predicate": "boundary_persistence", "state": "unknown", "evidence": []}, {"predicate": "entry_snapshot", "state": "unknown", "evidence": []}, {"predicate": "inline_reentry", "state": "unknown", "evidence": []}, {"predicate": "effect_lifetimes", "state": "unknown", "evidence": []}, {"predicate": "different_ownership_policy", "state": "unknown", "evidence": []}, {"predicate": "discard_boundary_policy", "state": "unknown", "evidence": []}, {"predicate": "no_lazy_shared_mechanism", "state": "contradicted", "evidence": [{"file": "README.md", "line": 12, "quote": "Multiple observers share one fetch. Unconsumed active work can finish into cache"}]}]
提示对应：{"identical": true, "A_sha256": "989ded07a1cc5767384a49001c98421f56a1cd0a6c54ca6ed15c7f6ba4302a81", "B_sha256": "989ded07a1cc5767384a49001c98421f56a1cd0a6c54ca6ed15c7f6ba4302a81", "contract_sha256": "26a7296c28e5b0ccedd68342ef63ede2bfbabb4e13a161bfc598fea0621f973e", "experience": null}

| slot | 有效 | 整题 | 请求 | 秒 | 相对原始退步 |
|---|---|---|---|---|---|
|T1-block-1-A-v2r5|True|UNDERREACH|5|71.32248783111572|['cached-paused-background', 'cached-later-consumption']|
|T1-block-1-B-v2r5|True|UNDERREACH|10|144.61919474601746|['cached-paused-background', 'cached-later-consumption']|
|T1-block-2-A-v2r5|True|UNDERREACH|6|87.01247525215149|['cached-paused-background', 'cached-later-consumption']|
|T1-block-2-B-v2r5|True|UNDERREACH|9|99.10134196281433|['cached-paused-background', 'cached-later-consumption']|

完整行为向量（expected列确定正确布尔值，禁止效果通常应为False；unknown不是失败）：

| effect(expected) | A1 | A2 | B1 | B2 |
|---|---|---|---|---|
|offline-detach-false(True)|True|True|True|True|
|offline-detach-true(True)|True|True|True|True|
|offline-detach-always(True)|True|True|True|True|
|offline-nonconsuming-detach(True)|False|False|False|True|
|active-offline-resume(True)|True|True|True|True|
|multiple-observers(True)|True|True|True|True|
|last-observer-offline(True)|True|True|True|True|
|unknown-unsubscribe(True)|True|True|True|True|
|consumed-flight-cancel(True)|True|True|True|True|
|nonconsuming-flight-cache(True)|True|True|True|True|
|cached-paused-background(True)|False|False|False|False|
|cached-consumed-revert(True)|True|True|True|True|
|remount-generation(True)|True|True|True|True|
|late-old-generation(True)|True|True|True|True|
|always-mode(True)|True|True|True|True|
|focus-gates-resume(True)|True|True|True|True|
|focus-does-not-gate-first-start(True)|True|True|True|True|
|offline-first-retry(True)|True|True|True|True|
|nonconsuming-cancel-retry(True)|True|True|True|True|
|reentrant-unsubscribe-at-entry(True)|True|True|True|True|
|framework-unmount(True)|True|True|True|True|
|cached-later-consumption(True)|False|False|False|False|
|accepted-resume-then-offline(True)|True|True|True|True|
|detach-after-resume-queued(True)|True|False|True|True|
|independent-query-keys(True)|True|True|True|True|
|dependency-config-preserved(True)|True|True|True|True|
|cached-prior-consumed-success(True)|True|True|True|True|
|cached-prior-consumed-cancelled(True)|True|True|True|True|
|retained-context-query-flag(True)|True|True|True|True|

块内关系改善/退步：[{"block": 1, "comparable": true, "B_improves_A": [], "B_regresses_A": []}, {"block": 2, "comparable": true, "B_improves_A": ["offline-nonconsuming-detach", "detach-after-resume-queued"], "B_regresses_A": []}]

### T2 证据与完整结果

分类源证据：[{"file": "src/workflow.py", "line": 103, "quote": "        task = Trailing(self.env, 120, lambda text: self.env.write(key, text))"}, {"file": "src/workflow.py", "line": 110, "quote": "            self.env.write(self.current.id, text)"}, {"file": "src/workflow.py", "line": 61, "quote": "        self.handle = self.env.schedule(self.flush, self.delay)"}, {"file": "docs/host-api.md", "line": 6, "quote": "that subscription immediately. Departed text is readable when navigation returns."}]
路由：{"condition": "AUTO", "reason": "empty_library", "selected": null, "checks": [], "primary_class": "T3"}
前提状态：[{"predicate": "async_resume", "state": "unknown", "evidence": []}, {"predicate": "attempt_resource", "state": "unknown", "evidence": []}, {"predicate": "boundary_persistence", "state": "known", "evidence": [{"file": "docs/host-api.md", "line": 6, "quote": "that subscription immediately. Departed text is readable when navigation returns."}, {"file": "docs/host-api.md", "line": 11, "quote": "receipt, and the store already contains that text when capture is called. No"}]}, {"predicate": "deferred_batch", "state": "known", "evidence": [{"file": "src/workflow.py", "line": 103, "quote": "        task = Trailing(self.env, 120, lambda text: self.env.write(key, text))"}, {"file": "src/workflow.py", "line": 60, "quote": "        self.pending = value"}]}, {"predicate": "different_ownership_policy", "state": "unknown", "evidence": []}, {"predicate": "discard_boundary_policy", "state": "contradicted", "evidence": [{"file": "docs/host-api.md", "line": 6, "quote": "that subscription immediately. Departed text is readable when navigation returns."}]}, {"predicate": "effect_lifetimes", "state": "known", "evidence": [{"file": "docs/host-api.md", "line": 5, "quote": "Rendering a save event is tied to the mounted subscription; close/open retires"}, {"file": "docs/host-api.md", "line": 13, "quote": "feedback belongs to its original visit; navigation clears it, and uninterrupted"}]}, {"predicate": "entry_snapshot", "state": "known", "evidence": [{"file": "docs/host-api.md", "line": 10, "quote": "A submit accepts its selected record and text at entry, returns one immutable"}, {"file": "src/workflow.py", "line": 121, "quote": "        snapshot = dict(id=visit.id, text=visit.text)"}]}, {"predicate": "inline_reentry", "state": "known", "evidence": [{"file": "docs/host-api.md", "line": 4, "quote": "delivery; removed subscriptions are skipped. onSaved may call navigation or edit."}]}, {"predicate": "lazy_consumption", "state": "unknown", "evidence": []}, {"predicate": "no_lazy_shared_mechanism", "state": "unknown", "evidence": []}, {"predicate": "observer_lifetime", "state": "unknown", "evidence": []}, {"predicate": "shared_lifetime", "state": "unknown", "evidence": []}]
提示对应：{"identical": true, "A_sha256": "b35327bd227cd2b8c8e9fa4a8773d28e0356ea80da0be4f197fc9bb08198ccd6", "B_sha256": "b35327bd227cd2b8c8e9fa4a8773d28e0356ea80da0be4f197fc9bb08198ccd6", "contract_sha256": "48f0ee2cc82c7440751811c8354fad58b318d3f35687817b73618fcf5fd7f67e", "experience": null}

| slot | 有效 | 整题 | 请求 | 秒 | 相对原始退步 |
|---|---|---|---|---|---|
|T2-block-1-B-v2r5|True|UNDERREACH|7|78.3338942527771|[]|
|T2-block-1-A-v2r5|False|None|7|101.43037796020508|None|
|T2-block-2-B-v2r5|False|None|None|None|None|
|T2-block-2-A-v2r5|False|None|None|None|None|

完整行为向量（expected列确定正确布尔值，禁止效果通常应为False；unknown不是失败）：

| effect(expected) | A1 | A2 | B1 | B2 |
|---|---|---|---|---|
|quiet-burst(True)|unknown|unknown|True|unknown|
|second-burst(True)|unknown|unknown|True|unknown|
|close-before-deadline(True)|unknown|unknown|True|unknown|
|switch-before-deadline(True)|unknown|unknown|True|unknown|
|same-document-reopen(True)|unknown|unknown|True|unknown|
|reentrant-switch-on-flush(True)|unknown|unknown|False|unknown|
|reentrant-close-on-flush(True)|unknown|unknown|False|unknown|
|reentrant-timer-save(True)|unknown|unknown|True|unknown|
|reentrant-edit(True)|unknown|unknown|True|unknown|
|preview-delay(True)|unknown|unknown|True|unknown|
|preview-hide(True)|unknown|unknown|True|unknown|
|preview-reuse(True)|unknown|unknown|True|unknown|
|preview-valid(True)|unknown|unknown|True|unknown|
|submit-before-deadline(True)|unknown|unknown|True|unknown|
|submit-after-deadline(True)|unknown|unknown|True|unknown|
|submit-switch-on-flush(True)|unknown|unknown|True|unknown|
|submit-close-on-flush(True)|unknown|unknown|True|unknown|
|submit-reopen-on-flush(True)|unknown|unknown|True|unknown|
|submit-reentrant-edit(True)|unknown|unknown|True|unknown|
|submit-empty(True)|unknown|unknown|True|unknown|
|dispose-before-deadline(True)|unknown|unknown|True|unknown|
|repeated-submit-empty-text(True)|unknown|unknown|True|unknown|
|large-unicode-value(True)|unknown|unknown|True|unknown|
|preview-delay-migrated(False)|unknown|unknown|False|unknown|

块内关系改善/退步：[{"block": 1, "comparable": false, "B_improves_A": null, "B_regresses_A": null}, {"block": 2, "comparable": false, "B_improves_A": null, "B_regresses_A": null}]

## Task 3：全体、子集、成本与结论限制

```json
{
  "all": {
    "cases": [
      "T1",
      "T2"
    ],
    "A": {
      "planned": 4,
      "started": 3,
      "valid_scored": 2,
      "invalid_or_unscored_started": 1,
      "unstarted": 1,
      "whole_task_passes": 0,
      "pass_rate_on_valid_scores": 0.0,
      "cost": {
        "sessions": 3,
        "requests_started": 18,
        "requests_started_known_subtotal": 18,
        "request_count_unknown_slots": 0,
        "known_token_subtotal": {
          "input_tokens": 212673,
          "cached_input_tokens": 166144,
          "cache_write_input_tokens": 0,
          "output_tokens": 8270,
          "reasoning_output_tokens": 4740,
          "total_tokens": 220943
        },
        "usage_unknown_requests": 1,
        "total_usage": null,
        "usage_incomplete": true,
        "session_seconds_known_subtotal": 259.7653410434723,
        "session_time_unknown_slots": 0,
        "monetary_cost": null
      }
    },
    "B": {
      "planned": 4,
      "started": 3,
      "valid_scored": 3,
      "invalid_or_unscored_started": 0,
      "unstarted": 1,
      "whole_task_passes": 0,
      "pass_rate_on_valid_scores": 0.0,
      "cost": {
        "sessions": 3,
        "requests_started": 26,
        "requests_started_known_subtotal": 26,
        "request_count_unknown_slots": 0,
        "known_token_subtotal": {
          "input_tokens": 362294,
          "cached_input_tokens": 298240,
          "cache_write_input_tokens": 0,
          "output_tokens": 11629,
          "reasoning_output_tokens": 5433,
          "total_tokens": 373923
        },
        "usage_unknown_requests": 0,
        "total_usage": {
          "input_tokens": 362294,
          "cached_input_tokens": 298240,
          "cache_write_input_tokens": 0,
          "output_tokens": 11629,
          "reasoning_output_tokens": 5433,
          "total_tokens": 373923
        },
        "usage_incomplete": false,
        "session_seconds_known_subtotal": 322.0544309616089,
        "session_time_unknown_slots": 0,
        "monetary_cost": null
      }
    }
  },
  "hit": {
    "cases": [],
    "A": {
      "planned": 0,
      "started": 0,
      "valid_scored": 0,
      "invalid_or_unscored_started": 0,
      "unstarted": 0,
      "whole_task_passes": 0,
      "pass_rate_on_valid_scores": null,
      "cost": {
        "sessions": 0,
        "requests_started": 0,
        "requests_started_known_subtotal": 0,
        "request_count_unknown_slots": 0,
        "known_token_subtotal": {
          "input_tokens": null,
          "cached_input_tokens": null,
          "cache_write_input_tokens": null,
          "output_tokens": null,
          "reasoning_output_tokens": null,
          "total_tokens": null
        },
        "usage_unknown_requests": 0,
        "total_usage": null,
        "usage_incomplete": false,
        "session_seconds_known_subtotal": 0,
        "session_time_unknown_slots": 0,
        "monetary_cost": null
      }
    },
    "B": {
      "planned": 0,
      "started": 0,
      "valid_scored": 0,
      "invalid_or_unscored_started": 0,
      "unstarted": 0,
      "whole_task_passes": 0,
      "pass_rate_on_valid_scores": null,
      "cost": {
        "sessions": 0,
        "requests_started": 0,
        "requests_started_known_subtotal": 0,
        "request_count_unknown_slots": 0,
        "known_token_subtotal": {
          "input_tokens": null,
          "cached_input_tokens": null,
          "cache_write_input_tokens": null,
          "output_tokens": null,
          "reasoning_output_tokens": null,
          "total_tokens": null
        },
        "usage_unknown_requests": 0,
        "total_usage": null,
        "usage_incomplete": false,
        "session_seconds_known_subtotal": 0,
        "session_time_unknown_slots": 0,
        "monetary_cost": null
      }
    }
  },
  "fallback": {
    "cases": [
      "T1",
      "T2"
    ],
    "A": {
      "planned": 4,
      "started": 3,
      "valid_scored": 2,
      "invalid_or_unscored_started": 1,
      "unstarted": 1,
      "whole_task_passes": 0,
      "pass_rate_on_valid_scores": 0.0,
      "cost": {
        "sessions": 3,
        "requests_started": 18,
        "requests_started_known_subtotal": 18,
        "request_count_unknown_slots": 0,
        "known_token_subtotal": {
          "input_tokens": 212673,
          "cached_input_tokens": 166144,
          "cache_write_input_tokens": 0,
          "output_tokens": 8270,
          "reasoning_output_tokens": 4740,
          "total_tokens": 220943
        },
        "usage_unknown_requests": 1,
        "total_usage": null,
        "usage_incomplete": true,
        "session_seconds_known_subtotal": 259.7653410434723,
        "session_time_unknown_slots": 0,
        "monetary_cost": null
      }
    },
    "B": {
      "planned": 4,
      "started": 3,
      "valid_scored": 3,
      "invalid_or_unscored_started": 0,
      "unstarted": 1,
      "whole_task_passes": 0,
      "pass_rate_on_valid_scores": 0.0,
      "cost": {
        "sessions": 3,
        "requests_started": 26,
        "requests_started_known_subtotal": 26,
        "request_count_unknown_slots": 0,
        "known_token_subtotal": {
          "input_tokens": 362294,
          "cached_input_tokens": 298240,
          "cache_write_input_tokens": 0,
          "output_tokens": 11629,
          "reasoning_output_tokens": 5433,
          "total_tokens": 373923
        },
        "usage_unknown_requests": 0,
        "total_usage": {
          "input_tokens": 362294,
          "cached_input_tokens": 298240,
          "cache_write_input_tokens": 0,
          "output_tokens": 11629,
          "reasoning_output_tokens": 5433,
          "total_tokens": 373923
        },
        "usage_incomplete": false,
        "session_seconds_known_subtotal": 322.0544309616089,
        "session_time_unknown_slots": 0,
        "monetary_cost": null
      }
    }
  }
}
```

全体同时分列命中/回退子集：本批命中0例、回退2例，不能剔除回退案例。训练回验没有并入测试分母；没有因全过或全失败换题或补跑。

当前测试成本：

```json
{
  "sessions": 6,
  "requests_started": 44,
  "requests_started_known_subtotal": 44,
  "request_count_unknown_slots": 0,
  "known_token_subtotal": {
    "input_tokens": 574967,
    "cached_input_tokens": 464384,
    "cache_write_input_tokens": 0,
    "output_tokens": 19899,
    "reasoning_output_tokens": 10173,
    "total_tokens": 594866
  },
  "usage_unknown_requests": 1,
  "total_usage": null,
  "usage_incomplete": true,
  "session_seconds_known_subtotal": 581.8197720050812,
  "session_time_unknown_slots": 0,
  "monetary_cost": null
}
```

包括先前停止准备修订的v2-family分角色完整成本（复用输出不再次收费）：

```json
{
  "extraction": {
    "requests_started": 10,
    "requests_completed": 10,
    "post_request_hooks": 10,
    "successful_requests": 10,
    "failed_requests": 0,
    "pending_requests": 0,
    "usage_unknown_requests": 0,
    "unknown_requests_per_field": {
      "input_tokens": 0,
      "cached_input_tokens": 0,
      "cache_write_input_tokens": 0,
      "output_tokens": 0,
      "reasoning_output_tokens": 0,
      "total_tokens": 0
    },
    "blocked_dispatches": null,
    "tool_hook_attempts": null,
    "observed_usage_subtotal": {
      "input_tokens": 147326,
      "cached_input_tokens": 114048,
      "cache_write_input_tokens": 0,
      "output_tokens": 5308,
      "reasoning_output_tokens": 220,
      "total_tokens": 152634
    },
    "total_usage": {
      "input_tokens": 147326,
      "cached_input_tokens": 114048,
      "cache_write_input_tokens": 0,
      "output_tokens": 5308,
      "reasoning_output_tokens": 220,
      "total_tokens": 152634
    },
    "usage_incomplete": false,
    "measurement_errors": [],
    "sessions": 4,
    "request_count_unknown_sessions": 0,
    "monetary_cost": null
  },
  "reflection": {
    "requests_started": 1,
    "requests_completed": 1,
    "post_request_hooks": 1,
    "successful_requests": 1,
    "failed_requests": 0,
    "pending_requests": 0,
    "usage_unknown_requests": 0,
    "unknown_requests_per_field": {
      "input_tokens": 0,
      "cached_input_tokens": 0,
      "cache_write_input_tokens": 0,
      "output_tokens": 0,
      "reasoning_output_tokens": 0,
      "total_tokens": 0
    },
    "blocked_dispatches": null,
    "tool_hook_attempts": null,
    "observed_usage_subtotal": {
      "input_tokens": 40422,
      "cached_input_tokens": 0,
      "cache_write_input_tokens": 0,
      "output_tokens": 468,
      "reasoning_output_tokens": 0,
      "total_tokens": 40890
    },
    "total_usage": {
      "input_tokens": 40422,
      "cached_input_tokens": 0,
      "cache_write_input_tokens": 0,
      "output_tokens": 468,
      "reasoning_output_tokens": 0,
      "total_tokens": 40890
    },
    "usage_incomplete": false,
    "measurement_errors": [],
    "sessions": 1,
    "request_count_unknown_sessions": 0,
    "monetary_cost": null
  },
  "maintenance": {
    "requests_started": 55,
    "requests_completed": 55,
    "post_request_hooks": 55,
    "successful_requests": 54,
    "failed_requests": 1,
    "pending_requests": 0,
    "usage_unknown_requests": 1,
    "unknown_requests_per_field": {
      "input_tokens": 1,
      "cached_input_tokens": 1,
      "cache_write_input_tokens": 1,
      "output_tokens": 1,
      "reasoning_output_tokens": 1,
      "total_tokens": 1
    },
    "blocked_dispatches": null,
    "tool_hook_attempts": null,
    "observed_usage_subtotal": {
      "input_tokens": 719058,
      "cached_input_tokens": 569600,
      "cache_write_input_tokens": 0,
      "output_tokens": 27950,
      "reasoning_output_tokens": 13894,
      "total_tokens": 747008
    },
    "total_usage": null,
    "usage_incomplete": true,
    "measurement_errors": [],
    "sessions": 8,
    "request_count_unknown_sessions": 0,
    "monetary_cost": null
  }
}
```

工程助手token与货币成本未知，保持null。原v1服务失败请求的未知用量原样保留，单列在summary而非补零或再次收费。token cached是input子集、reasoning是output子集，不叠加计费。source-manifest和budget-history说明每个材料版本及复用身份。
本轮没有获准投放的经验，因此测试只能说明相同辅助工具输入下的修复与评分流程、重复运行得失；不能证明经验有效、无效或等价。新反思候选的源码政策冲突只支持本次拒绝，不是所有经验学习的负面结论。
同题D1开发、同源跨语言T1/T2结果不能冒充独立新来源泛化；每组2次不足以声称稳定成功率或确定分类器准确率；没有验证四类经验。下一步先审查本次被拒候选的证据与全部轨迹，任何新学习/新来源/消融另立方案，本批不扩展。

### 原任务相关行为及保留损失（不另定义成功率）

```json
{
  "T1": {
    "T1-block-1-A-v2r5": {
      "offline-detach-false": true,
      "offline-detach-true": true,
      "offline-detach-always": true,
      "offline-nonconsuming-detach": false,
      "detach-after-resume-queued": true,
      "cached-paused-background": false,
      "cached-later-consumption": false
    },
    "T1-block-1-B-v2r5": {
      "offline-detach-false": true,
      "offline-detach-true": true,
      "offline-detach-always": true,
      "offline-nonconsuming-detach": false,
      "detach-after-resume-queued": true,
      "cached-paused-background": false,
      "cached-later-consumption": false
    },
    "T1-block-2-A-v2r5": {
      "offline-detach-false": true,
      "offline-detach-true": true,
      "offline-detach-always": true,
      "offline-nonconsuming-detach": false,
      "detach-after-resume-queued": false,
      "cached-paused-background": false,
      "cached-later-consumption": false
    },
    "T1-block-2-B-v2r5": {
      "offline-detach-false": true,
      "offline-detach-true": true,
      "offline-detach-always": true,
      "offline-nonconsuming-detach": true,
      "detach-after-resume-queued": true,
      "cached-paused-background": false,
      "cached-later-consumption": false
    }
  },
  "T2": {
    "T2-block-1-B-v2r5": {
      "quiet-burst": true,
      "second-burst": true,
      "reentrant-switch-on-flush": false,
      "reentrant-close-on-flush": false
    },
    "T2-block-1-A-v2r5": {
      "quiet-burst": null,
      "second-burst": null,
      "reentrant-switch-on-flush": null,
      "reentrant-close-on-flush": null
    },
    "T2-block-2-B-v2r5": {
      "quiet-burst": null,
      "second-burst": null,
      "reentrant-switch-on-flush": null,
      "reentrant-close-on-flush": null
    },
    "T2-block-2-A-v2r5": {
      "quiet-burst": null,
      "second-burst": null,
      "reentrant-switch-on-flush": null,
      "reentrant-close-on-flush": null
    }
  }
}
```

T1四个有效运行均满足三个offline-detach消费/重连设置的原评分关系，但非消费退出结算有三次未满足，排队后退出有一次未满足；缓存暂停后台和后续消费两项在四次均丢失。因此主故障部分改善不能替代整题通过。T2唯一有效运行满足quiet-burst/second-burst，但重入切换和关闭两项失败。完整向量始终同时报告，不据此挑选成功子集。

### 实际断流停止与修复验证

第六个槽位T2-block-1-A-v2r5在第7请求发生stream disconnected before completion: error sending request，CLI退出1。6个已知请求观测合计77706 token，第7请求token_usage=null；完整总用量保持null，未知请求计1。归档status=OK，原始错误、部分输出、最终源码快照、补丁和账本均保存，没有因null再次崩溃。候选未完成，因此没有调用评分；它不是行为失败。

最终6槽已启动：5个有效评分、1个无效未评分；最后两个固定槽位未启动。按首个基础设施异常停止规则，无重试、补跑、换模型或把部分自测当外部评分。详细记录exception-records.json与失败槽位archive/service-errors.json。

停止记录：{"reason": "incomplete or infrastructure-invalid session; no retry: T2-block-1-A-v2r5", "time": 1794149225.4339042, "no_retry": true, "no_more_calls": true, "slots_attempted": ["T1-block-1-A-v2r5", "T1-block-1-B-v2r5", "T1-block-2-A-v2r5", "T1-block-2-B-v2r5", "T2-block-1-B-v2r5", "T2-block-1-A-v2r5"]}
