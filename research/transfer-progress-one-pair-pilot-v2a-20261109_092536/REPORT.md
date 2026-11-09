修复已完成并推进到真实开发回验；停止原因现为“没有开发改善”，不是引用或读取接口错误。

- 源码引用改为合法片段 ID，Python 只转换文件/行号/引文，Contract、分类、声明和事实状态未改写。对应原始模型对象、派生视图、逐字绑定及摘要完整保存。
- 原 v2 的联合 cat 命令因虚拟 TASK 缺失返回 1，但输出包含七个完整当前 JS 文件。以更严格的完整正文/命令文件名证据离线纠正读取误判，复用同一输出，没有再次付费预分析。原 v2 失败回执和停止记录仍原样保存；新的准入状态是明确标注的程序重验结果和 AI 语义核查。
- 启动维护前发生过一次冻结清单装配错误：把可变调度日志当成输入。该次调用在模型启动之前拦截，0 请求，保存在 prelaunch-correction/。输入冻结已排除可变控制日志，业务输入、评分和预算未改；没有将它计作一次模型失败或隐藏重试。
- 最终 36 项离线检查通过。两次 AUTO 均 17/20；一次反思生成六条新经验，内容核查通过；两次独立开发回验仍均 17/20。相对 AUTO，每份新增通过 0、新增退步 0；相对原始候选，各保留全部 12 个成功关系并改善 5 项。
- 四份候选均缺失启动期间重开、隐藏后事件和切换后事件三个关系。没有观察到目标或整题改善，因此不符合预先冻结的开发入库规则；并非因为要求两次整题全过。测试预分析和四个测试维护槽位均未启动，通过率不可计算。

本次 fix 授权合计（含复用预分析只计一次）：6 个模型会话、32 请求、623,304 tokens、366.9 秒；其中离线读取修复后新调用 5 会话、30 请求、568,990 tokens。v1 的 3 请求/46,733 tokens 单独保留，不混算。未知请求用量 0；工程 tokens 和金额未知。

结论仅是同题开发的零改善观察，不能断言经验普遍有效或无效；同 cluster 跨语言测试仍未执行。没有换题、第二份候选、额外评委、测试反馈回流、提交或生产经验库更新。已停止。

详细原始阶段报告：

本轮已修复预分析的机械引用接口，并执行独立 v2 批次。旧 v1 输出、费用与停止记录保持不变。

模型只选择源码片段 ID；Python 将其转换为文件/行号/逐字引文，保留全部 Contract、分类、声明和前提状态。原始对象与程序派生分析分开归档。已知 ID 只证明绑定，不能替代语义核查。旧失败输出没有被回填或冒充新分析。接口说明见 FIX.md。

固定案例：训练 transfer-progress-maintenance-v2-vanilla；测试 transfer-progress-maintenance-v2-python3，同属 transfer-retry-abort-handoff。只从本批训练生成经验，不用旧 E2、旧 query/transfer 经验或测试反馈作种子。已有暴露与同来源设计关系保留，不称独立泛化。

模型和预算沿用：预分析 gpt-6-sol/low、12 请求；维护 gpt-5.6-terra/low、24 请求；反思 gpt-5.6-terra/medium、12 请求；各 600 秒，并发 1；v2 最多 11 会话/228 请求，不重试、不换题、不追加候选。

状态：stopped；停止：{"time": 1794188943.171471, "reason": "No evidenced target/overall improvement in two fixed development trials", "kind": "no_development_improvement", "no_retry": true, "no_more_model_calls": true}

|阶段|计划|启动|有效评分|整题通过/有效评分|
|---|---|---|---|---|
|训练 AUTO|2|2|2|0/2|
|开发回验|2|2|2|0/2|
|测试 A|2|0|0|通过率不可计算|
|测试 B|2|0|0|通过率不可计算|

预分析及全部实际槽位：

|名称|角色|启动|准入/评分|整题|满足关系|丢失原通过行为|
|---|---|---|---|---|---|---|
|D-analysis|extract|True|True|未评分|—|未知|
|AUTO-1|repair|True|True|UNDERREACH|17/20|无|
|AUTO-2|repair|True|True|UNDERREACH|17/20|无|
|reflection|reflect|True|False|未评分|—|未知|
|development-1|repair|True|True|UNDERREACH|17/20|无|
|development-2|repair|True|True|UNDERREACH|17/20|无|
|T-analysis|extract|False|None|未评分|—|未知|
|test-B1|repair|False|False|未评分|—|未知|
|test-A1|repair|False|False|未评分|—|未知|
|test-A2|repair|False|False|未评分|—|未知|
|test-B2|repair|False|False|未评分|—|未知|

完整行为向量 D：

|关系|AUTO-1|AUTO-2|development-1|development-2|
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
|progress-reopen-during-start|失败|失败|失败|失败|
|progress-hide-emit-during-start|失败|失败|失败|失败|
|progress-switch-emit-during-start|失败|失败|失败|失败|
|progress-accepted-decode-after-hide|通过|通过|通过|通过|
|progress-accepted-decode-live|通过|通过|通过|通过|
|progress-accepted-decode-after-reopen|通过|通过|通过|通过|
|progress-live-retry|通过|通过|通过|通过|
|record-byte-count-included|通过|通过|通过|通过|

开发与路由：

候选核查：{"structure_valid": true, "mechanism_facts_claimed_not_verified": true, "semantic_status": "supported_by_execution_agent", "admitted": false, "version": "single-source-rules-1", "candidate_sha256": "244eb39bccd3d0d2dcb668094787a0ff6f9a2898c0e761bdb92348459d0967f3", "rendered_sha256": "250e4360b0af7ba502f0692b1c1639be63da2dedee35cd64787923dfbb7f8f3e", "rendering": "program_derived_numbering_and_exact_body_concatenation", "development_eligible": true}

开发接纳：{"eligible": false, "AI_assisted": true, "no_confirmed_unsupported_policy": true, "regressions_fully_recorded": true, "both_full_passes_required": false, "production_admitted": false}

空经验原因：null

测试路由：null

开发逐项改善和退步见 development/comparisons.json；完整原始检查与轨迹、补丁、最终候选、用量与异常分开保留在各 runs/*/archive。没有评分的槽位不是行为失败，没有有效评分时通过率不可计算。

成本：

```json
{
  "preanalysis": {
    "sessions_started": 1,
    "requests_started": 2,
    "tool_attempts": 1,
    "known_usage_subtotal": {
      "input_tokens": 53371,
      "cached_input_tokens": 25472,
      "cache_write_input_tokens": 0,
      "output_tokens": 943,
      "reasoning_output_tokens": 154,
      "total_tokens": 54314
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 53371,
      "cached_input_tokens": 25472,
      "cache_write_input_tokens": 0,
      "output_tokens": 943,
      "reasoning_output_tokens": 154,
      "total_tokens": 54314
    },
    "seconds": 23.601972103118896,
    "money": null
  },
  "reflection": {
    "sessions_started": 1,
    "requests_started": 1,
    "tool_attempts": 0,
    "known_usage_subtotal": {
      "input_tokens": 155710,
      "cached_input_tokens": 0,
      "cache_write_input_tokens": 0,
      "output_tokens": 2177,
      "reasoning_output_tokens": 1034,
      "total_tokens": 157887
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 155710,
      "cached_input_tokens": 0,
      "cache_write_input_tokens": 0,
      "output_tokens": 2177,
      "reasoning_output_tokens": 1034,
      "total_tokens": 157887
    },
    "seconds": 63.23932409286499,
    "money": null
  },
  "maintenance": {
    "sessions_started": 4,
    "requests_started": 29,
    "tool_attempts": 25,
    "known_usage_subtotal": {
      "input_tokens": 402117,
      "cached_input_tokens": 318208,
      "cache_write_input_tokens": 0,
      "output_tokens": 8986,
      "reasoning_output_tokens": 2489,
      "total_tokens": 411103
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 402117,
      "cached_input_tokens": 318208,
      "cache_write_input_tokens": 0,
      "output_tokens": 8986,
      "reasoning_output_tokens": 2489,
      "total_tokens": 411103
    },
    "seconds": 280.08477330207825,
    "money": null
  },
  "new_model_total": {
    "sessions_started": 6,
    "requests_started": 32,
    "tool_attempts": 26,
    "known_usage_subtotal": {
      "input_tokens": 611198,
      "cached_input_tokens": 343680,
      "cache_write_input_tokens": 0,
      "output_tokens": 12106,
      "reasoning_output_tokens": 3677,
      "total_tokens": 623304
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 611198,
      "cached_input_tokens": 343680,
      "cache_write_input_tokens": 0,
      "output_tokens": 12106,
      "reasoning_output_tokens": 3677,
      "total_tokens": 623304
    },
    "seconds": 366.92606949806213,
    "money": null
  },
  "previous_batch_model_cost_separate": {
    "sessions_started": 1,
    "requests_started": 3,
    "tool_attempts": 2,
    "known_usage_subtotal": {
      "input_tokens": 45187,
      "cached_input_tokens": 28032,
      "cache_write_input_tokens": 0,
      "output_tokens": 1546,
      "reasoning_output_tokens": 29,
      "total_tokens": 46733
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 45187,
      "cached_input_tokens": 28032,
      "cache_write_input_tokens": 0,
      "output_tokens": 1546,
      "reasoning_output_tokens": 29,
      "total_tokens": 46733
    },
    "seconds": 34.471593618392944,
    "money": null
  },
  "calibration": {
    "reused": 18,
    "new_native_calibration_invocations": 0,
    "model_calls": 0
  },
  "engineering": {
    "batch_wall_seconds": 824.3179919719696,
    "tokens": null,
    "money": null
  }
}
```

复用 18 份相同输入/评分版本校准，不重复历史评分。离线引用修复验证包含旧真实失败回放、完整原始响应保存、ID/源码摘要篡改、部分 JSON 拒绝和实际隔离；测试数量见 initial-freeze.json。新增校准调用 0，工程 tokens 与金额未知，保持 null。

本批维护和评分只验证同来源 JS 到 Python 的开发/迁移流程；有限重复不证明稳定效果，训练回验不进测试分母。同类主标签不强制命中；前提不足或分类不同则回退，提示相同的随机差异不能归因为经验。未更新生产经验库、创建 Git 提交或自动开始下一轮。

推荐 Git commit subject: `research: bind preanalysis citations to frozen source IDs`

推荐 Git commit body:

```text
Replace model-transcribed citation triples with enumerated source-span IDs.
Derive compatibility citation fields without editing any model statement.
Replay prior rejection offline and retain semantic review and isolation gates.
Run a separately authorized fixed transfer pair with unchanged role budgets.
Preserve prior costs, all real outcomes and unstarted slots without retries.
```
