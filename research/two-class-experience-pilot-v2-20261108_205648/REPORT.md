# v2 两案例 A/B 试验报告

**状态：STOPPED，首次准备提取的材料无效。** v2为新授权批次，v1失败与未知用量保持不变。

运行与归档修复已通过离线回放；本批首个模型会话也正常结束并完整归档。但内层JSON无法解析，尚无获准使用的新D1 Contract。没有启动开发基线、反思或测试维护，没有形成测试冻结库。不能将此描述为八个测试正常完成或模型行为失败。

## 1. 原语义问题的核实和处理

已核对原任务、源码、模型原文、实际补丁、checks/调用轨迹及反思输入输出，详见SEMANTIC_AUDIT.md与audit/semantic-evidence.json。D1/T1将Repair描述的实际缺陷写为保留义务，判断确认；原报告的“must not”不是原任务逐字引文，已收窄。T1把消费归属改为单次执行，与当前共享记录读写不符；不把物理控制器归属与共享历史混同。
反思错误描述第一次补丁已修好离线退出，实际no-live-at-entry检查与调用记录相反。错误结果归因成立，但为何模型这样写、哪个改动是唯一原因未证实。旧反馈本身的布尔效果向量准确；其checks遗漏和prior-success字段混义是具体接口缺陷，不能宣称反馈明确断言第一次修复成功。
计划只重新提取D1/T1；实际仅D1一次启动，材料无效；T1未启动。D2/T2正确原文复用。新自动输出未经人工重写，执行Agent只基于当前可见任务/源码否决冲突；分类和路由不读case ID、cluster、历史成绩、评分器或参考补丁。

## 2. v2改变的代码和材料

运行/归档修复见FIX.md：null/缺字段用量、部分响应、服务错误与归档错误分开保留；完整候选准入；首个基础设施异常即停。真实v1失败流离线回放与31项检查通过，实际四例namespace/JS/Python读取/IPC/归档通过，零连接预跑。
通用提取提示区分reported_defect/requirement/source_fact/preservation_inference，增加同次语义自查；当前执行Agent的源绑定veto只可接受或拒绝，不改类别/Contract。反馈同时支持checks/assertions，分别列实际成功、原始成功、保留成功、改善、退步、未知；原因假设不混入事实。
角色及时间/请求上限与v1实际命令核对一致：gpt-6-sol/low/12，gpt-5.6-terra/low/24，反思medium/12/no-tools；600秒，并发1，无重试。v2仅对完整候选评分且首个infra异常停止，与v1部分耗尽评分/连续两次infra规则不同，不混为同一条件。
44份校准按base/task/oracle精确摘要复用，原评分器与规则未变。Node18与JS manifest Node16差异保留；Python3.8.10匹配。来源分类与摘要见source-manifest.json，首次测试维护前冻结见test-freeze.json。

### D1开发与经验决定

```json
{
  "state": null,
  "admission": null,
  "library": null,
  "runs": []
}
```

D2/T3未新增搜索；v1正确材料及已知开发结果仅作为历史复用证据，不计v2新会话或受控D1基线。若D1两次新AUTO均通过则不强行生成经验；否则最多一份新候选、两次开发回验，按有据改善与无新增无据政策选择，不要求两次全对。空库仍执行固定测试槽位。

## 3. A/B有效评分、整题与行为结果

### T1 — query-paused-initial-fetch-10266-python3

分类/源证据：null
路由及前提：null
A/B提示对应：null

| slot | 状态 | 有效评分 | 整题 | 相对原始退步 | 请求 |
|---|---|---|---|---|---|
|T1-block-1-A-v2|NOT_STARTED|False|None|None|None|
|T1-block-1-B-v2|NOT_STARTED|False|None|None|None|
|T1-block-2-A-v2|NOT_STARTED|False|None|None|None|
|T1-block-2-B-v2|NOT_STARTED|False|None|None|None|

完整行为向量；缺失为unknown，不视为失败。false可能是所需的禁止效果。

| effect (expected) | A1 | A2 | B1 | B2 |
|---|---|---|---|---|
|offline-detach-false (True)|unknown|unknown|unknown|unknown|
|offline-detach-true (True)|unknown|unknown|unknown|unknown|
|offline-detach-always (True)|unknown|unknown|unknown|unknown|
|offline-nonconsuming-detach (True)|unknown|unknown|unknown|unknown|
|active-offline-resume (True)|unknown|unknown|unknown|unknown|
|multiple-observers (True)|unknown|unknown|unknown|unknown|
|last-observer-offline (True)|unknown|unknown|unknown|unknown|
|unknown-unsubscribe (True)|unknown|unknown|unknown|unknown|
|consumed-flight-cancel (True)|unknown|unknown|unknown|unknown|
|nonconsuming-flight-cache (True)|unknown|unknown|unknown|unknown|
|cached-paused-background (True)|unknown|unknown|unknown|unknown|
|cached-consumed-revert (True)|unknown|unknown|unknown|unknown|
|remount-generation (True)|unknown|unknown|unknown|unknown|
|late-old-generation (True)|unknown|unknown|unknown|unknown|
|always-mode (True)|unknown|unknown|unknown|unknown|
|focus-gates-resume (True)|unknown|unknown|unknown|unknown|
|focus-does-not-gate-first-start (True)|unknown|unknown|unknown|unknown|
|offline-first-retry (True)|unknown|unknown|unknown|unknown|
|nonconsuming-cancel-retry (True)|unknown|unknown|unknown|unknown|
|reentrant-unsubscribe-at-entry (True)|unknown|unknown|unknown|unknown|
|framework-unmount (True)|unknown|unknown|unknown|unknown|
|cached-later-consumption (True)|unknown|unknown|unknown|unknown|
|accepted-resume-then-offline (True)|unknown|unknown|unknown|unknown|
|detach-after-resume-queued (True)|unknown|unknown|unknown|unknown|
|independent-query-keys (True)|unknown|unknown|unknown|unknown|
|dependency-config-preserved (True)|unknown|unknown|unknown|unknown|
|cached-prior-consumed-success (True)|unknown|unknown|unknown|unknown|
|cached-prior-consumed-cancelled (True)|unknown|unknown|unknown|unknown|
|retained-context-query-flag (True)|unknown|unknown|unknown|unknown|

块内改善/退步：[{"block": 1, "comparable": false, "B_improves_A": null, "B_regresses_A": null}, {"block": 2, "comparable": false, "B_improves_A": null, "B_regresses_A": null}]

### T2 — document-submit-snapshot-python3-eval-v2

分类/源证据：{"primary_class": "T3", "secondary_tags": ["T1", "T2"], "evidence": [{"file": "src/workflow.py", "line": 103, "quote": "        task = Trailing(self.env, 120, lambda text: self.env.write(key, text))"}, {"file": "src/workflow.py", "line": 110, "quote": "            self.env.write(self.current.id, text)"}, {"file": "src/workflow.py", "line": 61, "quote": "        self.handle = self.env.schedule(self.flush, self.delay)"}, {"file": "docs/host-api.md", "line": 6, "quote": "that subscription immediately. Departed text is readable when navigation returns."}]}
路由及前提：null
A/B提示对应：null

| slot | 状态 | 有效评分 | 整题 | 相对原始退步 | 请求 |
|---|---|---|---|---|---|
|T2-block-1-B-v2|NOT_STARTED|False|None|None|None|
|T2-block-1-A-v2|NOT_STARTED|False|None|None|None|
|T2-block-2-B-v2|NOT_STARTED|False|None|None|None|
|T2-block-2-A-v2|NOT_STARTED|False|None|None|None|

完整行为向量；缺失为unknown，不视为失败。false可能是所需的禁止效果。

| effect (expected) | A1 | A2 | B1 | B2 |
|---|---|---|---|---|
|quiet-burst (True)|unknown|unknown|unknown|unknown|
|second-burst (True)|unknown|unknown|unknown|unknown|
|close-before-deadline (True)|unknown|unknown|unknown|unknown|
|switch-before-deadline (True)|unknown|unknown|unknown|unknown|
|same-document-reopen (True)|unknown|unknown|unknown|unknown|
|reentrant-switch-on-flush (True)|unknown|unknown|unknown|unknown|
|reentrant-close-on-flush (True)|unknown|unknown|unknown|unknown|
|reentrant-timer-save (True)|unknown|unknown|unknown|unknown|
|reentrant-edit (True)|unknown|unknown|unknown|unknown|
|preview-delay (True)|unknown|unknown|unknown|unknown|
|preview-hide (True)|unknown|unknown|unknown|unknown|
|preview-reuse (True)|unknown|unknown|unknown|unknown|
|preview-valid (True)|unknown|unknown|unknown|unknown|
|submit-before-deadline (True)|unknown|unknown|unknown|unknown|
|submit-after-deadline (True)|unknown|unknown|unknown|unknown|
|submit-switch-on-flush (True)|unknown|unknown|unknown|unknown|
|submit-close-on-flush (True)|unknown|unknown|unknown|unknown|
|submit-reopen-on-flush (True)|unknown|unknown|unknown|unknown|
|submit-reentrant-edit (True)|unknown|unknown|unknown|unknown|
|submit-empty (True)|unknown|unknown|unknown|unknown|
|dispose-before-deadline (True)|unknown|unknown|unknown|unknown|
|repeated-submit-empty-text (True)|unknown|unknown|unknown|unknown|
|large-unicode-value (True)|unknown|unknown|unknown|unknown|
|preview-delay-migrated (False)|unknown|unknown|unknown|unknown|

块内改善/退步：[{"block": 1, "comparable": false, "B_improves_A": null, "B_regresses_A": null}, {"block": 2, "comparable": false, "B_improves_A": null, "B_regresses_A": null}]

## 4. 全体、命中与回退子集、成本

```json
{
  "all": {
    "cases": [
      "T1",
      "T2"
    ],
    "A": {
      "planned": 4,
      "started": 0,
      "valid_scored": 0,
      "invalid_or_unscored_started": 0,
      "unstarted": 4,
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
      "planned": 4,
      "started": 0,
      "valid_scored": 0,
      "invalid_or_unscored_started": 0,
      "unstarted": 4,
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
  }
}
```

角色成本：

```json
{
  "roles": {
    "extraction": {
      "sessions": 1,
      "requests_started": 3,
      "requests_started_known_subtotal": 3,
      "request_count_unknown_slots": 0,
      "known_token_subtotal": {
        "input_tokens": 44717,
        "cached_input_tokens": 37888,
        "cache_write_input_tokens": 0,
        "output_tokens": 2049,
        "reasoning_output_tokens": 148,
        "total_tokens": 46766
      },
      "usage_unknown_requests": 0,
      "total_usage": {
        "input_tokens": 44717,
        "cached_input_tokens": 37888,
        "cache_write_input_tokens": 0,
        "output_tokens": 2049,
        "reasoning_output_tokens": 148,
        "total_tokens": 46766
      },
      "usage_incomplete": false,
      "session_seconds_known_subtotal": 38.79016041755676,
      "session_time_unknown_slots": 0,
      "monetary_cost": null
    },
    "reflection": {
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
    },
    "maintenance": {
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
  "total": {
    "sessions": 1,
    "requests_started": 3,
    "requests_started_known_subtotal": 3,
    "request_count_unknown_slots": 0,
    "known_token_subtotal": {
      "input_tokens": 44717,
      "cached_input_tokens": 37888,
      "cache_write_input_tokens": 0,
      "output_tokens": 2049,
      "reasoning_output_tokens": 148,
      "total_tokens": 46766
    },
    "usage_unknown_requests": 0,
    "total_usage": {
      "input_tokens": 44717,
      "cached_input_tokens": 37888,
      "cache_write_input_tokens": 0,
      "output_tokens": 2049,
      "reasoning_output_tokens": 148,
      "total_tokens": 46766
    },
    "usage_incomplete": false,
    "session_seconds_known_subtotal": 38.79016041755676,
    "session_time_unknown_slots": 0,
    "monetary_cost": null
  },
  "engineering": {
    "tokens": null,
    "monetary_cost": null,
    "prepare_seconds": 1.8858047453686595
  }
}
```

总token的已知合计不冒充完整合计；unknown请求另计，货币与工程助手token未知不补零。缓存token是input子集、reasoning是output子集。每槽完整用量在runs/*/archive/usage.json；原日志/部分响应/错误、源码、补丁与评分也在各archive。
## 5. 解释边界

D1开发只说明同题材料/工具流程。T1与D1同一来源单元，T2与D2同一来源单元；测试均已有暴露，包括T2评分v2事后修订。每例每组两次不能确立稳定收益、分类器准确率或独立新来源泛化；未验证四类完整分类学。
回退导致提示相同时，随机得失不能归为经验收益或经验效果等价。没有有效评分时不宣称经验有效/无效。训练回验不进入测试分母；没有按测试成绩改经验、Contract、路由、评分或调度。
测试结束或停止后不扩大范围；下一步先审查本批完整轨迹与语义审查边界，再另立后续方案。没有创建提交或修改生产经验库、全局配置。

停止记录：

```json
{
  "reason": "invalid extracted material; no retry",
  "time": 1794143561.3497636,
  "no_retry": true,
  "no_more_calls": true,
  "slots_attempted": [
    "D1-preanalysis-v2"
  ]
}
```

## 本批新的材料阻断（原始证据）

D1会话：CLI正常退出，3个请求全部终止且用量已报告，归档OK；但report字符串恰好6000字符，内层JSON在字符串内未闭合，json.loads返回Unterminated string。原报告末尾是未完成的源码引用，不是一个可接受的完整分析对象。外层schema只约束report为字符串，不能保证内嵌JSON的语法/字段完整性。这是此次暴露的提取接口缺口；没有证据证明具体是服务端截断，内部成因保留未知。

可逐字解码的Contract开头已经纠正禁止方向。对“对应执行尝试的消费”的新措辞，收窄为归属不够明确：它没有直接指定写入哪个对象，因此不能仅凭这句断言又要求改为attempt-local字段；同时也不足以确认共享历史记录语义已获保留。完整claims/consistency缺失，没有获准使用的Contract。本批未用手工补JSON或改写Contract绕过门槛。

实际状态：1个准备会话已启动，传输有效1、自动材料有效0；0个开发维护/反思；测试A计划4、启动0、有效评分0，B计划4、启动0、有效评分0；8槽全部未启动，测试通过率/目标行为/退步未知。全部用量见cost_total；没有未知请求用量，却不能把零测试会话解释为模型失败。

经验库尚未生成或冻结，不能将其称为训练后两类空库；正确的D2/T2复用身份保持，旧T4错误文本没有作为新候选交付。没有追加模型请求或恢复调度。

后续接口修复应采用角色专用的结构化对象schema，分别约束Contract长度、quote片段长度及claims/consistency字段，而不是把JSON塞进6000字符字符串。需要在新的执行版本中通过长度边界/嵌套JSON离线检查后，再获取完整自动材料并重新核对；本批保持停止，不以修复后续跑改写历史。

详细证据：diagnostics/preanalysis-material-failure.json；任何可解码片段只用于审计，明确标为NOT-ACCEPTED，没有进入维护prompt或冻结库。
