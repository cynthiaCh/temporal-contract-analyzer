本批修复适用性字段漂移：结构化输出仅有 rules/unresolved；程序从已通过内容核查的父对象精确继承 version/requires/excludes/applicability。
模型规则修订原始对象与程序合成候选分别保存。不是修改上一批被拒对象，也不把程序继承字段冒充模型新输出。正文及逐规则依据仍接受 AI 辅助语义核查。
元数据保持不变：True；原始规则与合成规则相同：True。

新增通过与丢失行为（相对固定 AUTO）：
{"gains": {"evolved-development-1": ["progress-reopen-during-start", "progress-hide-emit-during-start", "progress-switch-emit-during-start"], "evolved-development-2": ["progress-reopen-during-start", "progress-hide-emit-during-start", "progress-switch-emit-during-start"]}, "losses": {"evolved-development-1": [], "evolved-development-2": []}}

两份实际补丁均修改 progress、queue、transfer 三个业务文件：监听先于启动；把当前访问有效性传到事件入口并在解码前核对；已接纳事件的审计仍在其解码完成时保留。第一份另有尝试取消/监听状态的显示门控，第二份沿用当前访问的显示门控；不把两份实现描述为完全相同。
第一份维护在启动内部隐藏后再发事件的自测中先观察到多记审计，随后补上访问接纳门控，自测通过。原始失败和通过输出均保留。其自测还出现 CustomEvent 不可用及非Git目录中 git diff 失败，均是会话内验证命令问题，未伪装为成功、未触发额外会话。正式补丁和归档由 Python 产生。完整命令/输出与源码解释见 execution-audit.json。
本轮为同题开发诊断；只演化一个候选，最多两次独立回验，不运行测试集。

状态：completed；维护启动 2/2，有效评分 2，未启动 0。

内容核查：supported_by_execution_agent。核查人为执行 Agent，AI 辅助；不是独立人工批准。

|条件|满足全部20项中的数量|整题|相对原始候选丢失|
|---|---|---|---|
|AUTO-1|17/20|False|[]|
|AUTO-2|17/20|False|[]|
|parent-development-1|17/20|False|[]|
|parent-development-2|17/20|False|[]|
|evolved-development-1|20/20|True|[]|
|evolved-development-2|20/20|True|[]|

|行为关系|AUTO-1|AUTO-2|父回验1|父回验2|新回验1|新回验2|
|---|---|---|---|---|---|---|
|retry-normal|通过|通过|通过|通过|通过|通过|
|retry-double|通过|通过|通过|通过|通过|通过|
|retry-abort-observe|通过|通过|通过|通过|通过|通过|
|retry-abort-hide|通过|通过|通过|通过|通过|通过|
|retry-abort-switch|通过|通过|通过|通过|通过|通过|
|retry-abort-reopen|通过|通过|通过|通过|通过|通过|
|retry-hidden-noop|通过|通过|通过|通过|通过|通过|
|selection-cleanup|通过|通过|通过|通过|通过|通过|
|cancel-idempotent|通过|通过|通过|通过|通过|通过|
|independent-workspaces|通过|通过|通过|通过|通过|通过|
|record-scope|通过|通过|通过|通过|通过|通过|
|progress-normal|通过|通过|通过|通过|通过|通过|
|progress-reopen-during-start|失败|失败|失败|失败|通过|通过|
|progress-hide-emit-during-start|失败|失败|失败|失败|通过|通过|
|progress-switch-emit-during-start|失败|失败|失败|失败|通过|通过|
|progress-accepted-decode-after-hide|通过|通过|通过|通过|通过|通过|
|progress-accepted-decode-live|通过|通过|通过|通过|通过|通过|
|progress-accepted-decode-after-reopen|通过|通过|通过|通过|通过|通过|
|progress-live-retry|通过|通过|通过|通过|通过|通过|
|record-byte-count-included|通过|通过|通过|通过|通过|通过|

相对 AUTO 观察到改善：True；观察到损失：False。所有逐项改善、保留与退步见 comparisons.json；每次原始检查和完整事件轨迹在各 archive/score/stdout.json。

成本分列（旧费用仅作参考，不计入新增）：

```json
{
  "new_reflection": {
    "sessions_started": 1,
    "requests_started": 1,
    "tool_attempts": 0,
    "known_usage_subtotal": {
      "input_tokens": 88180,
      "cached_input_tokens": 0,
      "cache_write_input_tokens": 0,
      "output_tokens": 1277,
      "reasoning_output_tokens": 199,
      "total_tokens": 89457
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 88180,
      "cached_input_tokens": 0,
      "cache_write_input_tokens": 0,
      "output_tokens": 1277,
      "reasoning_output_tokens": 199,
      "total_tokens": 89457
    },
    "seconds": 29.149765253067017,
    "money": null
  },
  "new_maintenance": {
    "sessions_started": 2,
    "requests_started": 17,
    "tool_attempts": 15,
    "known_usage_subtotal": {
      "input_tokens": 258294,
      "cached_input_tokens": 210176,
      "cache_write_input_tokens": 0,
      "output_tokens": 8644,
      "reasoning_output_tokens": 3209,
      "total_tokens": 266938
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 258294,
      "cached_input_tokens": 210176,
      "cache_write_input_tokens": 0,
      "output_tokens": 8644,
      "reasoning_output_tokens": 3209,
      "total_tokens": 266938
    },
    "seconds": 300.41251516342163,
    "money": null
  },
  "new_total": {
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
  "old_AUTO_reference_only_not_recharged": {
    "sessions_started": 2,
    "requests_started": 14,
    "tool_attempts": 12,
    "known_usage_subtotal": {
      "input_tokens": 193026,
      "cached_input_tokens": 152576,
      "cache_write_input_tokens": 0,
      "output_tokens": 3553,
      "reasoning_output_tokens": 499,
      "total_tokens": 196579
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 193026,
      "cached_input_tokens": 152576,
      "cache_write_input_tokens": 0,
      "output_tokens": 3553,
      "reasoning_output_tokens": 499,
      "total_tokens": 196579
    },
    "seconds": 118.05382132530212,
    "money": null
  },
  "parent_development_reference_only_not_recharged": {
    "sessions_started": 2,
    "requests_started": 15,
    "tool_attempts": 13,
    "known_usage_subtotal": {
      "input_tokens": 209091,
      "cached_input_tokens": 165632,
      "cache_write_input_tokens": 0,
      "output_tokens": 5433,
      "reasoning_output_tokens": 1990,
      "total_tokens": 214524
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 209091,
      "cached_input_tokens": 165632,
      "cache_write_input_tokens": 0,
      "output_tokens": 5433,
      "reasoning_output_tokens": 1990,
      "total_tokens": 214524
    },
    "seconds": 162.03095197677612,
    "money": null
  },
  "engineering": {
    "tokens": null,
    "money": null
  },
  "money_currency": null
}
```

候选原始响应、规则对象和程序派生正文分别保存；未人工改写模型规则。源事实、观测、解释和未知原因在训练账本及 window-review.md 中区分。
反思获得父候选、两份真实回验补丁、完整行为评分与事件顺序、自测实际命令及遗漏窗口说明。维护仅获得原任务、源码、固定自动 Contract、公共要求和冻结经验正文，未获得评分或训练账本。
完整输入先经既有交接器校验；模型输入使用可逆重复子树引用，展开与归档完整输入逐值一致。该操作没有删除成功项、false 期望、退步、未知或轨迹。
调用前34项离线检查及源摘要核对通过。准备阶段的通用驱动材料在任何调用前被本批显式规则修订协议替代，快照见 prelaunch-scope-snapshot/；当时0会话/0请求，无模型重试。

Stop after authorized slots; no automatic further evolution or test.

结果只描述本案例开发行为；案例已经暴露，不代表独立测试、稳定效果或同源跨语言迁移收益。没有创建提交、修改历史、更新生产经验库或自动进入下一轮。

上一被拒批次仅作历史费用：1请求、86,654 tokens、62.47秒，未计入本次新增费用。
