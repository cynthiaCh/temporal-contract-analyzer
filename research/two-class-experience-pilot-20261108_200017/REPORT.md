# 2+2 分类经验工具试验：归档故障后停止

**本轮没有可用的A/B效果比较。** 已完成两例开发、冻结及两个测试例分类路由；首个测试维护会话流断连后触发归档错误，立即停止。1个维护槽位已启动但未评分，其余7个未启动。不能把缺失项写成失败率。

Task 1：实现复用、离线预检与四例来源

起始HEAD为938076ab4f06a496348d15b7d8d6f11b5ae453c7，起始工作区干净。指定v1规范已补齐，旧设计的run_enabled=false不替代本次用户明确授权。所有新实现与实验留档位于本目录，旧实验、原案例、评分、生产经验库和全局配置未改；未安装依赖，未创建提交。
复用既有runner.session、native CLI命令、host-owned guard计量及Python快照/补丁/日志归档；没有导入或启动旧调度器。新增toolflow.py和control.py，打通同次Contract提取/机制分类、源绑定事实、保守路由、共享prompt、通用评分差异、反思和冻结。
零模型检查：31项归档/路由检查通过；四例AST全部解析；实际四例bwrap隔离、JS/Python正文读取、hook IPC、预算计数与自动归档均用假CLI通过。44份原始/参考/退化校准与本批base/task/oracle精确摘要对应并复用，未冒充新训练。Node18.17.0与JS manifest的Node16有差异，Python3.8.10匹配；未声称原Node16环境重现。

| alias | case | source unit |
|---|---|---|
|D1|query-paused-initial-fetch-10266-vanilla|query-paused-initial-fetch-10266|
|D2|document-submit-snapshot-vanilla|debounced-submit-flush|
|T1|query-paused-initial-fetch-10266-python3|query-paused-initial-fetch-10266|
|T2|document-submit-snapshot-python3-eval-v2|debounced-submit-flush|

两对均为同源跨语言，旧暴露永久保留；T2的事后评分v2与求解暴露见manifest/exposure.json。不是独立新来源泛化测试。原任务/README/docs/源码提供政策依据，policy-review.md明确哪些解释由当前执行Agent核查；没有伪造人工批准。通用反馈只抽取实际/标准差异，未包装旧query专用诊断。旧E2正文未提供给本批反思器。

Task 2：两例开发、经验冻结和两例测试

| 训练例 | AUTO整题 | 开发回验 | 经验处理 |
|---|---|---|---|
| D1 | 0/2；行为18/29、27/29 | 0/1；行为27/29 | 按有据关系改善入库T4候选，完整记录退步 |
| D2 | 2/2 | 按规则不做 | T3本批不生成经验，保持空 |

D1主类T4。预分析辅助Contract把“不得重连后以live signal启动”反向写成应恢复；它原样共享给两次AUTO和开发回验，未人工纠正。此处是Contract质量错误，不是输入版本漂移。
D1唯一反思产生一份原样候选，未润色或生成第二份。候选有一句错误归因：声称第一次按执行归属修改修好了离线退出，实际AUTO-1仍失败。这是证据归因缺陷，已明确记录，不能因之后有改善而隐去。
D1回验相对AUTO-1改善9项、无新增退步；相对AUTO-2改善缓存暂停后台与后续消费两项，同时退步prior-consumed-success和retained-context两项。仍未整题通过。入库依据是预先允许的关系改善，当前可见文档/源码支持其生命周期分离和条件性边界结算，没有确认的新增无据业务政策；不是因回验稳定成功而接纳。详见development/D1/admission.json及完整comparison。
候选结构化excludes为空，但正文列有不适用政策，这是路由元数据不完整的局限。所需三项前提仅能支持机制适用，不证明全文语义必然正确。
D2主类T3，两个AUTO均通过原评分，因此没有反思和回验槽位。不能为了两条经验而人为补齐。
冻结库仅一条T4经验：正文SHA256 89aefe23f09ad539fe74e0257d44fb6da53028f5bcd7bf781abaa7ec27ee39b6；含适用元数据的entry SHA256 0629d9502c3f9fb7bff3a0ca5d6dcef78424ae48b319a64cdf905d893c482356。版本pilot-1，原文见frozen-library.json和development/D1/experience-original.md。

| 测试例 | 实际主类 | 前提/路由 | A/B维护状态 |
|---|---|---|---|
| T1 | T4 | 共享寿命、异步恢复、惰性消费均known，源绑定核查后命中 | A1已启动但未评分；其余3槽未启动 |
| T2 | T3 | 同类经验为空，回退AUTO；A/B提示字节相同 | 4槽均未启动 |

分类仅使用原任务、当前候选相对源码/文档、AST、四类定义及通用前提；无case ID到类别查表。路由不接收case/cluster/历史成绩/评分器/参考补丁。具体证据、前提状态、摘要与回退理由见testing/*/route.json、derived/*/analysis.json。
实现限制：路由只核对结构化前提的字面源证据，没有对Contract正文与原任务/源码进行语义一致性校验；T1虽有相反的辅助Contract，仍按三个known机制前提命中。这个观测不能被称为完整的语义冲突检测已通过。冻结后未改变路由或人工改投放。
T1自动Contract也反向复述了原任务，并把消费归属写为单次执行；原文未改，A/B共享。已记录在derived/T1/quality-review.json。即使后续另批得到差异，也不能忽略辅助Contract错误的混杂。
固定测试调度种子2026110804，只控制块内A/B顺序，不控制模型采样。顺序为T1 A1/B1/A2/B2，T2 B1/A1/B2/A2。经验库冻结后才进行两个测试预分析，随后开始首个维护。没有测试成绩回流学习，也没有测试成绩可用于调参。

**停止链与缺失情况**

T1/A1第4请求流断连，CLI exit=1、turn.failed。原始hook记录status=failed且token_usage=null；archive.collect错误地对显式null调用.get，引发AttributeError。快照、最终源码、补丁、原事件和账本已保存，collect阶段失败、归档状态ERROR；没有调用评分器。触发的是归档完整性立即停止规则，不是把单次网络异常当成连续两次异常。
未修复冻结代码后续跑，未重试该槽，也未补跑其他槽。原失败档案保持原样；诊断和从原ledger提取的观测用量放在外部diagnostics与usage-reconciliation.json，不伪造成功归档。
计划8槽仍全部保留：1槽已启动未评分，7槽未启动。行为向量、整题通过和退步均未知；不是0/8失败。没有任何完整测试A/B对，不能比较经验得失。训练回验不进测试分母。

每个测试例的预分析与A/B成本（未启动没有用量观测；失败请求用量未知）：

```json
{
  "T1": {
    "preanalysis": {
      "sessions": 1,
      "requests_started": 3,
      "session_seconds": 40.235108375549316,
      "observed_total_token_subtotal": 43876,
      "total_tokens": 43876,
      "usage_incomplete": false,
      "status": "started",
      "monetary_cost": null
    },
    "A": {
      "sessions": 1,
      "requests_started": 4,
      "session_seconds": 74.75812888145447,
      "observed_total_token_subtotal": 34555,
      "total_tokens": null,
      "usage_incomplete": true,
      "status": "started",
      "monetary_cost": null
    },
    "B": {
      "sessions": 0,
      "requests_started": 0,
      "session_seconds": 0,
      "observed_total_token_subtotal": null,
      "total_tokens": null,
      "usage_incomplete": false,
      "status": "not_started_no_usage",
      "monetary_cost": null
    }
  },
  "T2": {
    "preanalysis": {
      "sessions": 1,
      "requests_started": 3,
      "session_seconds": 37.40908241271973,
      "observed_total_token_subtotal": 41542,
      "total_tokens": 41542,
      "usage_incomplete": false,
      "status": "started",
      "monetary_cost": null
    },
    "A": {
      "sessions": 0,
      "requests_started": 0,
      "session_seconds": 0,
      "observed_total_token_subtotal": null,
      "total_tokens": null,
      "usage_incomplete": false,
      "status": "not_started_no_usage",
      "monetary_cost": null
    },
    "B": {
      "sessions": 0,
      "requests_started": 0,
      "session_seconds": 0,
      "observed_total_token_subtotal": null,
      "total_tokens": null,
      "usage_incomplete": false,
      "status": "not_started_no_usage",
      "monetary_cost": null
    }
  }
}
```

Task 3：完整得失、成本、限制与下一步

按全体、命中、回退分别列出计划/启动/评分/缺失：

```json
{
  "all": {
    "cases": [
      "T1",
      "T2"
    ],
    "A": {
      "passed": null,
      "started": 1,
      "planned": 4,
      "missing": 3,
      "scored": 0,
      "started_unscored": 1,
      "pass_rate": null,
      "passes_observed": 0,
      "missing_means": "unstarted planned slots, not behavior failures"
    },
    "B": {
      "passed": null,
      "started": 0,
      "planned": 4,
      "missing": 4,
      "scored": 0,
      "started_unscored": 0,
      "pass_rate": null,
      "passes_observed": 0,
      "missing_means": "unstarted planned slots, not behavior failures"
    }
  },
  "hit": {
    "cases": [
      "T1"
    ],
    "A": {
      "passed": null,
      "started": 1,
      "planned": 2,
      "missing": 1,
      "scored": 0,
      "started_unscored": 1,
      "pass_rate": null,
      "passes_observed": 0,
      "missing_means": "unstarted planned slots, not behavior failures"
    },
    "B": {
      "passed": null,
      "started": 0,
      "planned": 2,
      "missing": 2,
      "scored": 0,
      "started_unscored": 0,
      "pass_rate": null,
      "passes_observed": 0,
      "missing_means": "unstarted planned slots, not behavior failures"
    }
  },
  "fallback": {
    "cases": [
      "T2"
    ],
    "A": {
      "passed": null,
      "started": 0,
      "planned": 2,
      "missing": 2,
      "scored": 0,
      "started_unscored": 0,
      "pass_rate": null,
      "passes_observed": 0,
      "missing_means": "unstarted planned slots, not behavior failures"
    },
    "B": {
      "passed": null,
      "started": 0,
      "planned": 2,
      "missing": 2,
      "scored": 0,
      "started_unscored": 0,
      "pass_rate": null,
      "passes_observed": 0,
      "missing_means": "unstarted planned slots, not behavior failures"
    }
  }
}
```

分角色成本（token采用原hook；失败请求未知用量保持null，subtotal仅含已观测部分；货币与当前工程助手token未知）：

```json
{
  "preanalysis": {
    "sessions": 4,
    "requests_started": 13,
    "post_request_hooks": 13,
    "successful_requests": 13,
    "failed_requests": 0,
    "usage_unknown_requests": 0,
    "session_seconds": 141.4632375240326,
    "session_seconds_complete": true,
    "observed_token_subtotal": {
      "input_tokens": 187535,
      "cached_input_tokens": 142336,
      "cache_write_input_tokens": 0,
      "output_tokens": 5137,
      "reasoning_output_tokens": 661,
      "total_tokens": 192672
    },
    "total_tokens": {
      "input_tokens": 187535,
      "cached_input_tokens": 142336,
      "cache_write_input_tokens": 0,
      "output_tokens": 5137,
      "reasoning_output_tokens": 661,
      "total_tokens": 192672
    },
    "usage_incomplete": false,
    "monetary_cost": null,
    "note": "Derived from raw hook ledgers; completed hook counts include failed responses. Reasoning tokens are a subset of output; cached tokens a subset of input."
  },
  "reflection": {
    "sessions": 1,
    "requests_started": 1,
    "post_request_hooks": 1,
    "successful_requests": 1,
    "failed_requests": 0,
    "usage_unknown_requests": 0,
    "session_seconds": 41.61487579345703,
    "session_seconds_complete": true,
    "observed_token_subtotal": {
      "input_tokens": 19687,
      "cached_input_tokens": 0,
      "cache_write_input_tokens": 0,
      "output_tokens": 1119,
      "reasoning_output_tokens": 461,
      "total_tokens": 20806
    },
    "total_tokens": {
      "input_tokens": 19687,
      "cached_input_tokens": 0,
      "cache_write_input_tokens": 0,
      "output_tokens": 1119,
      "reasoning_output_tokens": 461,
      "total_tokens": 20806
    },
    "usage_incomplete": false,
    "monetary_cost": null,
    "note": "Derived from raw hook ledgers; completed hook counts include failed responses. Reasoning tokens are a subset of output; cached tokens a subset of input."
  },
  "maintenance": {
    "sessions": 6,
    "requests_started": 44,
    "post_request_hooks": 44,
    "successful_requests": 43,
    "failed_requests": 1,
    "usage_unknown_requests": 1,
    "session_seconds": 651.449714422226,
    "session_seconds_complete": true,
    "observed_token_subtotal": {
      "input_tokens": 610015,
      "cached_input_tokens": 485120,
      "cache_write_input_tokens": 0,
      "output_tokens": 25017,
      "reasoning_output_tokens": 11407,
      "total_tokens": 635032
    },
    "total_tokens": {
      "input_tokens": null,
      "cached_input_tokens": null,
      "cache_write_input_tokens": null,
      "output_tokens": null,
      "reasoning_output_tokens": null,
      "total_tokens": null
    },
    "usage_incomplete": true,
    "monetary_cost": null,
    "note": "Derived from raw hook ledgers; completed hook counts include failed responses. Reasoning tokens are a subset of output; cached tokens a subset of input."
  },
  "engineering": {
    "tokens": null,
    "monetary_cost": null,
    "preparation_script_seconds": 2.5515600070357323,
    "offline_seconds": 1.2122614001855254,
    "note": "Current executing assistant engineering usage unavailable; offline fixtures excluded from model sessions."
  }
}
```

共11个实验会话、58个底层请求启动：4个预分析、1个反思、6个维护。最后一个失败请求有终止hook但未知token，不能把58个hook都称为成功请求。没有额外预跑、模型评委、第二反思、重试或补跑。
已观察到的开发收益是D1部分关系改善，损失是两项保留关系退步、反思归因错误，以及D1/T1辅助Contract方向错误。工程检查虽通过，未覆盖“API失败且usage显式null”的真实归档分支，这是本轮具体暴露的缺口。
测试结果不足，不能宣称稳定效果、分类器准确率已确定、独立泛化或四类全部验证。T3没有本批经验；T2本应作为同提示回退子集保留，不能以后因无增益而剔除。
下一步应在另立冻结版本前，增加null用量/失败流的离线归档检查，并审查Contract与原任务禁止方向的一致性；本批冻结代码不改、不续跑。若开展新批次，必须保留本批测试暴露，不重标为未见。
推荐Git提交文本见COMMIT_MESSAGE.txt；未创建提交或更新生产经验库。
