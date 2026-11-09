固定经验单例直接测试

状态：completed。案例 `cached-feed-lifecycle-repair-python3`；来源单元 `listener-registration-order`。

本例未参与两份冻结经验训练，来源单元与两份训练来源不同；但为作者构造的派生案例，既往广泛暴露不认证为零，不称为未见样本或已证明泛化。选例在本轮评分前由对话固定。

计划2会话；启动2，未启动0。维护计划1，启动1，有效评分1；整题结果：1/1。

T1与T4两条既有登记项逐字段原样组合；正文、版本、适用条件和摘要均未修改。没有新训练、反思、候选搜索、重试、补跑或额外评委。

模型与预算：提取 gpt-6-sol/low，12请求；维护 gpt-5.6-terra/low，24请求；每会话600秒，并发1，总上限36请求。

实际自动分类与来源证据见 derived/analysis.json；Contract与前提核查见 derived/semantic-review.json（执行Agent的AI辅助核查，非独立人工批准）。提取器只收到当前任务/候选/文档、AST、公共分类词典和词法提示，未收到经验或测试标准。

路由结果：
```json
{
  "condition": "AUTO",
  "reason": "insufficient_or_contradictory_premises",
  "selected": null,
  "checks": [
    {
      "sha256": "f830cadc309715a38b229e099de7c02f369b74fa82b64d127dc7b77c3b207f88",
      "premises": [
        {
          "predicate": "shared_lifetime",
          "state": "unknown",
          "evidence": [],
          "satisfied": false
        },
        {
          "predicate": "observer_lifetime",
          "state": "unknown",
          "evidence": [],
          "satisfied": false
        },
        {
          "predicate": "attempt_resource",
          "state": "unknown",
          "evidence": [],
          "satisfied": false
        },
        {
          "predicate": "entry_snapshot",
          "state": "unknown",
          "evidence": [],
          "satisfied": false
        },
        {
          "predicate": "inline_reentry",
          "state": "known",
          "evidence": [
            {
              "file": "README.md",
              "line": 12,
              "quote": "synchronously navigate or hide the panel. It can return a Promise for layout"
            }
          ],
          "satisfied": true
        },
        {
          "predicate": "effect_lifetimes",
          "state": "known",
          "evidence": [
            {
              "file": "README.md",
              "line": 18,
              "quote": "accepted by the subscriber remains useful to history after leaving the panel;"
            }
          ],
          "satisfied": true
        }
      ],
      "exclusions": [],
      "eligible": false
    }
  ],
  "primary_class": "T1"
}
```

路由先过滤主类，再核对适用前提与排除条件；unknown不算满足。修复器仅追加命中经验正文，不接收类别、账本ID、来源身份、历史成绩或评分器。实际提示差异见 testing/prompt-difference.json。

最终原评分：PASS，满足27/27项关系（26个场景＋1项禁止效果）。每份有效候选只评分一次。

|原关系|期望|原始|本次|满足|
|---|---|---|---|---|
|bootstrap-sync|True|False|True|True|
|bootstrap-deferred|True|True|True|True|
|live-delta|True|False|True|True|
|decode-live|True|True|True|True|
|decode-hide|True|False|True|True|
|decode-switch|True|False|True|True|
|decode-reopen|True|False|True|True|
|decode-reopen-live|True|False|True|True|
|paint-live|True|True|True|True|
|paint-hide|True|False|True|True|
|paint-switch|True|False|True|True|
|paint-reopen|True|False|True|True|
|paint-reopen-live|True|False|True|True|
|paint-hook-hide|True|False|True|True|
|paint-hook-switch|True|False|True|True|
|bootstrap-hook-hide|True|False|True|True|
|bootstrap-hook-switch|True|False|True|True|
|bootstrap-hook-reopen|True|False|True|True|
|history-after-retire|True|False|True|True|
|metrics-scope|True|True|True|True|
|independent-workspaces|True|False|True|True|
|closed-empty|True|True|True|True|
|hide-before-bootstrap|True|True|True|True|
|retire-after-count|True|False|True|True|
|shared-feed-workspaces|True|False|True|True|
|dispose-inflight|True|False|True|True|
|metrics-bootstrap-included|False|False|False|True|

相对原始候选新增通过：['bootstrap-sync', 'live-delta', 'decode-hide', 'decode-switch', 'decode-reopen', 'decode-reopen-live', 'paint-hide', 'paint-switch', 'paint-reopen', 'paint-reopen-live', 'paint-hook-hide', 'paint-hook-switch', 'bootstrap-hook-hide', 'bootstrap-hook-switch', 'bootstrap-hook-reopen', 'history-after-retire', 'independent-workspaces', 'retire-after-count', 'shared-feed-workspaces', 'dispose-inflight']
丢失原通过：[]
未知关系：[]

上述前后差异不能归因为经验增益：没有本例AUTO对照。单次PASS也不等于分类或经验效果已被稳定验证。完整实际值/要求值和事件轨迹保存在该会话 archive/score/stdout.json。

执行核查为AI辅助、只读既有记录；未增加模型、测试或评分调用。

实际维护条件为AUTO回退，没有投放任何经验。补丁先注册监听及清理能力再启动来源，在解码完成后先保留history，再核对准确visit身份决定是否paint；paint完成后再次核对身份决定count。独立metrics消费者和公共接口未修改。

自测事件16因合成解码结果缺少feed字段而失败；事件18修正后的生命周期断言通过，但后续git diff在无Git隔离目录中失败，整体退出129；事件21的同步绘制隐藏与同来源重开断言通过。所有失败/成功输出原样保留，不将组合命令描述成全部成功。

编译产生 src/__pycache__/workflow.cpython-38.pyc，已随最终快照、补丁与评分输入保留，没有按后缀删除或评分后清理。业务源码只改动 src/workflow.py；最终候选并非只含源码差异。

原26场景通过，禁止的metrics首批扩展未出现，没有丢失原始候选已通过项。由于没有AUTO与经验对照且本次没有经验投放，不能宣称经验效果。


新增费用（旧训练费用不重计；未知不补零）：
```json
{
  "extract": {
    "sessions_started": 1,
    "requests_started": 4,
    "tool_attempts": 3,
    "known_usage_subtotal": {
      "input_tokens": 83501,
      "cached_input_tokens": 61568,
      "cache_write_input_tokens": 0,
      "output_tokens": 878,
      "reasoning_output_tokens": 50,
      "total_tokens": 84379
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 83501,
      "cached_input_tokens": 61568,
      "cache_write_input_tokens": 0,
      "output_tokens": 878,
      "reasoning_output_tokens": 50,
      "total_tokens": 84379
    },
    "seconds": 43.67493414878845,
    "money": null
  },
  "maintenance": {
    "sessions_started": 1,
    "requests_started": 8,
    "tool_attempts": 7,
    "known_usage_subtotal": {
      "input_tokens": 106304,
      "cached_input_tokens": 72192,
      "cache_write_input_tokens": 0,
      "output_tokens": 3223,
      "reasoning_output_tokens": 1115,
      "total_tokens": 109527
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 106304,
      "cached_input_tokens": 72192,
      "cache_write_input_tokens": 0,
      "output_tokens": 3223,
      "reasoning_output_tokens": 1115,
      "total_tokens": 109527
    },
    "seconds": 114.74267745018005,
    "money": null
  },
  "new_total": {
    "sessions_started": 2,
    "requests_started": 12,
    "tool_attempts": 10,
    "known_usage_subtotal": {
      "input_tokens": 189805,
      "cached_input_tokens": 133760,
      "cache_write_input_tokens": 0,
      "output_tokens": 4101,
      "reasoning_output_tokens": 1165,
      "total_tokens": 193906
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 189805,
      "cached_input_tokens": 133760,
      "cache_write_input_tokens": 0,
      "output_tokens": 4101,
      "reasoning_output_tokens": 1165,
      "total_tokens": 193906
    },
    "seconds": 158.4176115989685,
    "money": null
  },
  "engineering_tokens": null,
  "money": null,
  "historical_training_costs_not_recharged": true,
  "offline_calibration_seconds": 38.23360872268677
}
```

45项离线检查通过，含原服务断流和null用量回放；11份原始/参考/退化校准均符合预期。离线校准不是模型修复效果。评分规则未改变。

原始模型对象、完整事件流、请求/工具记录、服务错误、候选快照、Python补丁、原评分及用量均保存。未启动/未评分不计行为失败。

HEAD、已有工作和历史输入保护摘要见 integrity.json。未创建提交、未更新生产经验库；本批结束即停止。
