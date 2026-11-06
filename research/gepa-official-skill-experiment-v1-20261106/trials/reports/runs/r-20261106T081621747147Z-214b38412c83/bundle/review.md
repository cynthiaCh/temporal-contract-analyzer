# Selected candidate-source locations

This list is selected by fixed tool rules, not a complete repository inventory.

```json
[
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 57,
      "line": 21
    },
    "id": "L0001",
    "path": "src/progress-source.js",
    "scope": "<module>/createProgressFeed/<callback>#2",
    "start": {
      "column": 31,
      "line": 21
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 69,
      "line": 21
    },
    "id": "L0002",
    "path": "src/progress-source.js",
    "scope": "<module>/createProgressFeed/<callback>#2",
    "start": {
      "column": 59,
      "line": 21
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 68,
      "line": 11
    },
    "id": "L0003",
    "path": "src/progress.js",
    "scope": "<module>/watchTransferProgress/<callback>",
    "start": {
      "column": 15,
      "line": 11
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 53,
      "line": 6
    },
    "id": "L0004",
    "path": "src/progress.js",
    "scope": "<module>/watchTransferProgress/listener",
    "start": {
      "column": 8,
      "line": 6
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 76,
      "line": 6
    },
    "id": "L0005",
    "path": "src/progress.js",
    "scope": "<module>/watchTransferProgress/listener",
    "start": {
      "column": 55,
      "line": 6
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 68,
      "line": 11
    },
    "id": "L0006",
    "path": "src/telemetry.js",
    "scope": "<module>/collectProgressTelemetry/<callback>",
    "start": {
      "column": 15,
      "line": 11
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 53,
      "line": 6
    },
    "id": "L0007",
    "path": "src/telemetry.js",
    "scope": "<module>/collectProgressTelemetry/listener",
    "start": {
      "column": 8,
      "line": 6
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 76,
      "line": 6
    },
    "id": "L0008",
    "path": "src/telemetry.js",
    "scope": "<module>/collectProgressTelemetry/listener",
    "start": {
      "column": 55,
      "line": 6
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 20,
      "line": 9
    },
    "id": "L0009",
    "path": "src/transfer.js",
    "scope": "<module>/createTransfer",
    "start": {
      "column": 2,
      "line": 6
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 59,
      "line": 10
    },
    "id": "L0010",
    "path": "src/transfer.js",
    "scope": "<module>/createTransfer",
    "start": {
      "column": 2,
      "line": 10
    }
  }
]
```

## Syntax observations at the selected locations

These observations do not establish runtime behavior or business obligations.

### L0001

```json
[
  {
    "source": "listeners.delete(listener)",
    "syntax": {
      "argument_references": [
        [
          "listener"
        ]
      ],
      "arguments": [
        "listener"
      ],
      "block": "<module>/createProgressFeed/<callback>#2/conditional@819",
      "branch_path": [],
      "callee": "listeners.delete",
      "conditional_path": [],
      "conditions": [
        "conditional expression type === \"progress\""
      ],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "listeners",
      "references": [
        "listeners.delete",
        "listener"
      ],
      "statement": 1
    }
  }
]
```

### L0002

```json
[
  {
    "source": "onDetach()",
    "syntax": {
      "argument_references": [],
      "arguments": [],
      "block": "<module>/createProgressFeed/<callback>#2/then@815",
      "branch_path": [
        {
          "arm": "then",
          "key": "<module>/createProgressFeed/<callback>#2/if@815"
        }
      ],
      "callee": "onDetach",
      "conditional_path": [],
      "conditions": [
        "if type === \"progress\" && listeners.delete(listener)"
      ],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "",
      "references": [
        "onDetach"
      ],
      "statement": 1
    }
  }
]
```

### L0003

```json
[
  {
    "source": "feed.target.removeEventListener(\"progress\", listener)",
    "syntax": {
      "argument_references": [
        [],
        [
          "listener"
        ]
      ],
      "arguments": [
        "\"progress\"",
        "listener"
      ],
      "block": "<module>/watchTransferProgress/<callback>/body",
      "branch_path": [],
      "callee": "feed.target.removeEventListener",
      "conditional_path": [],
      "conditions": [],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "feed.target",
      "references": [
        "feed.target.removeEventListener",
        "listener"
      ],
      "statement": 0
    }
  }
]
```

### L0004

```json
[
  {
    "source": "decoded && typeof decoded.then === \"function\"",
    "syntax": {
      "block": "<module>/watchTransferProgress/listener/block@170",
      "branch_path": [],
      "condition_path_supported": false,
      "conditional_path": [],
      "conditions": [],
      "else_path_block": "<module>/watchTransferProgress/listener/else@288",
      "expression": "decoded && typeof decoded.then === \"function\"",
      "guard_key": "<module>/watchTransferProgress/listener/if@288",
      "kind": "guard",
      "linear_block": false,
      "references": [
        "decoded",
        "decoded.then"
      ],
      "statement": 2,
      "then_path_block": "<module>/watchTransferProgress/listener/then@288"
    }
  }
]
```

### L0005

```json
[
  {
    "source": "decoded.then(deliver)",
    "syntax": {
      "argument_references": [
        [
          "deliver"
        ]
      ],
      "arguments": [
        "deliver"
      ],
      "block": "<module>/watchTransferProgress/listener/then@288",
      "branch_path": [
        {
          "arm": "then",
          "key": "<module>/watchTransferProgress/listener/if@288"
        }
      ],
      "callee": "decoded.then",
      "conditional_path": [],
      "conditions": [
        "if decoded && typeof decoded.then === \"function\""
      ],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "decoded",
      "references": [
        "decoded.then",
        "deliver"
      ],
      "statement": 2
    }
  }
]
```

### L0006

```json
[
  {
    "source": "feed.target.removeEventListener(\"progress\", listener)",
    "syntax": {
      "argument_references": [
        [],
        [
          "listener"
        ]
      ],
      "arguments": [
        "\"progress\"",
        "listener"
      ],
      "block": "<module>/collectProgressTelemetry/<callback>/body",
      "branch_path": [],
      "callee": "feed.target.removeEventListener",
      "conditional_path": [],
      "conditions": [],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "feed.target",
      "references": [
        "feed.target.removeEventListener",
        "listener"
      ],
      "statement": 0
    }
  }
]
```

### L0007

```json
[
  {
    "source": "decoded && typeof decoded.then === \"function\"",
    "syntax": {
      "block": "<module>/collectProgressTelemetry/listener/block@177",
      "branch_path": [],
      "condition_path_supported": false,
      "conditional_path": [],
      "conditions": [],
      "else_path_block": "<module>/collectProgressTelemetry/listener/else@279",
      "expression": "decoded && typeof decoded.then === \"function\"",
      "guard_key": "<module>/collectProgressTelemetry/listener/if@279",
      "kind": "guard",
      "linear_block": false,
      "references": [
        "decoded",
        "decoded.then"
      ],
      "statement": 2,
      "then_path_block": "<module>/collectProgressTelemetry/listener/then@279"
    }
  }
]
```

### L0008

```json
[
  {
    "source": "decoded.then(deliver)",
    "syntax": {
      "argument_references": [
        [
          "deliver"
        ]
      ],
      "arguments": [
        "deliver"
      ],
      "block": "<module>/collectProgressTelemetry/listener/then@279",
      "branch_path": [
        {
          "arm": "then",
          "key": "<module>/collectProgressTelemetry/listener/if@279"
        }
      ],
      "callee": "decoded.then",
      "conditional_path": [],
      "conditions": [
        "if decoded && typeof decoded.then === \"function\""
      ],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "decoded",
      "references": [
        "decoded.then",
        "deliver"
      ],
      "statement": 2
    }
  }
]
```

### L0009

```json
[
  {
    "source": "controller.signal.addEventListener(\"abort\", () => {\n    stopProgress();\n    onCancel({ file, attemptId, signal: controller.signal });\n  }, { once: true })",
    "syntax": {
      "argument_references": [
        [],
        [],
        []
      ],
      "arguments": [
        "\"abort\"",
        "() => {\n    stopProgress();\n    onCancel({ file, attemptId, signal: controller.signal });\n  }",
        "{ once: true }"
      ],
      "block": "<module>/createTransfer/block@140",
      "branch_path": [],
      "callee": "controller.signal.addEventListener",
      "conditional_path": [],
      "conditions": [],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "controller.signal",
      "references": [
        "controller.signal.addEventListener"
      ],
      "statement": 2
    }
  }
]
```

### L0010

```json
[
  {
    "source": "transport({ file, attemptId, signal: controller.signal })",
    "syntax": {
      "argument_references": [
        [
          "file",
          "attemptId",
          "controller.signal"
        ]
      ],
      "arguments": [
        "{ file, attemptId, signal: controller.signal }"
      ],
      "block": "<module>/createTransfer/block@140",
      "branch_path": [],
      "callee": "transport",
      "conditional_path": [],
      "conditions": [],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "",
      "references": [
        "transport",
        "file",
        "attemptId",
        "controller.signal"
      ],
      "statement": 3
    }
  }
]
```

## Limited relations between selected locations/scopes

```json
[
  {
    "after": "L0002",
    "before": "L0001",
    "kind": "lexical_write_before_direct_call",
    "qualification": "Source order within one function; execution, callback identity and synchronous reentry are not established."
  },
  {
    "after": "L0010",
    "before": "L0009",
    "kind": "lexical_write_before_direct_call",
    "qualification": "Source order within one function; execution, callback identity and synchronous reentry are not established."
  }
]
```

## Heuristic interpretations and review questions

The following text is rule-authored guidance, not a defect verdict or an oracle.

```json
{
  "classification": "heuristic_review_hint",
  "condition": "仅是共现线索；需追踪是否属于同一工作、同一生命周期。",
  "interpretation": "同一文件中同时存在完成回调登记和监听移除。",
  "locations": [
    "L0003",
    "L0005"
  ],
  "review_question": "若二者相关，移除监听后，已开始的工作完成时是否还有有效性检查？",
  "rule": "continuation-and-listener-removal"
}
```

```json
{
  "classification": "heuristic_review_hint",
  "condition": "仅是共现线索；需追踪是否属于同一工作、同一生命周期。",
  "interpretation": "同一文件中同时存在完成回调登记和监听移除。",
  "locations": [
    "L0006",
    "L0008"
  ],
  "review_question": "若二者相关，移除监听后，已开始的工作完成时是否还有有效性检查？",
  "rule": "continuation-and-listener-removal"
}
```

```json
{
  "classification": "heuristic_review_hint",
  "condition": "仅表示同一词法函数/类命名空间中的语法共现；名称不保证 API 类型，未证明属于同一请求、实例或生命周期，也未证明回调可达、重试循环或保护充分。",
  "interpretation": "完成回调/等待点与关闭、重新打开或清理边界名称线索出现在同一词法单元。",
  "locations": [
    "L0003",
    "L0005"
  ],
  "review_question": "关闭、卸载和切换是否是不同边界？哪些边界应使旧结果失效，哪些工作应继续？需从仓库证据确认。",
  "rule": "continuation-lifecycle-boundaries"
}
```

```json
{
  "classification": "heuristic_review_hint",
  "condition": "仅表示同一词法函数/类命名空间中的语法共现；名称不保证 API 类型，未证明属于同一请求、实例或生命周期，也未证明回调可达、重试循环或保护充分。",
  "interpretation": "列出相关词法单元中的条件判断，以及关闭/返回清理函数内的状态写入；存在判断不等于有效性保护。",
  "locations": [
    "L0003",
    "L0004",
    "L0005"
  ],
  "review_question": "回调检查了什么状态？关闭、卸载、重开分别更新了什么？只取消计时器能否约束已发请求？相同标识重新使用时判断是否仍适用？",
  "rule": "continuation-guard-state-review"
}
```

```json
{
  "classification": "heuristic_review_hint",
  "condition": "仅表示同一词法函数/类命名空间中的语法共现；名称不保证 API 类型，未证明属于同一请求、实例或生命周期，也未证明回调可达、重试循环或保护充分。",
  "interpretation": "完成回调/等待点与关闭、重新打开或清理边界名称线索出现在同一词法单元。",
  "locations": [
    "L0006",
    "L0008"
  ],
  "review_question": "关闭、卸载和切换是否是不同边界？哪些边界应使旧结果失效，哪些工作应继续？需从仓库证据确认。",
  "rule": "continuation-lifecycle-boundaries"
}
```

```json
{
  "classification": "heuristic_review_hint",
  "condition": "仅表示同一词法函数/类命名空间中的语法共现；名称不保证 API 类型，未证明属于同一请求、实例或生命周期，也未证明回调可达、重试循环或保护充分。",
  "interpretation": "列出相关词法单元中的条件判断，以及关闭/返回清理函数内的状态写入；存在判断不等于有效性保护。",
  "locations": [
    "L0006",
    "L0007",
    "L0008"
  ],
  "review_question": "回调检查了什么状态？关闭、卸载、重开分别更新了什么？只取消计时器能否约束已发请求？相同标识重新使用时判断是否仍适用？",
  "rule": "continuation-guard-state-review"
}
```

```json
{
  "classification": "heuristic_review_hint",
  "condition": "回调未位于另一个嵌套函数体，且此前未发现 await/yield；只是源码上的候选直接通知路径。名称、循环元素和路径可达性未作类型/控制流证明，未证明它与其他文件中的订阅者是同一实例。",
  "interpretation": "成员写入或集合/持久化名称调用之后，同一非 async 函数直接调用参数回调或循环取出的可调用项。",
  "locations": [
    "L0001",
    "L0002"
  ],
  "review_question": "该调用是否通知外部消费者？消费者能否在返回前重新进入当前对象？调用后继续使用的状态是否仍有效，最新请求如何决定优先级？",
  "rule": "state-write-inline-notification"
}
```

```json
{
  "classification": "heuristic_review_hint",
  "condition": "回调未位于另一个嵌套函数体，且此前未发现 await/yield；只是源码上的候选直接通知路径。名称、循环元素和路径可达性未作类型/控制流证明，未证明它与其他文件中的订阅者是同一实例。",
  "interpretation": "成员写入或集合/持久化名称调用之后，同一非 async 函数直接调用参数回调或循环取出的可调用项。",
  "locations": [
    "L0009",
    "L0010"
  ],
  "review_question": "该调用是否通知外部消费者？消费者能否在返回前重新进入当前对象？调用后继续使用的状态是否仍有效，最新请求如何决定优先级？",
  "rule": "state-write-inline-notification"
}
```
