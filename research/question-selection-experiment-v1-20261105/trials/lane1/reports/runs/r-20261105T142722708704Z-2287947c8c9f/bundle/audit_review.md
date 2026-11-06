# Temporal-risk audit

Before editing, inspect the candidate-visible repository for evidence that code
being removed, replaced, or reordered may incidentally delay, sequence, cancel,
invalidate, or wait for another operation. Consider at least two feasible event
orders and preserve every evidence-supported behavior and authorization
boundary. Do not assume that such a coupling exists, and do not invent a
requirement without repository evidence. Then complete the maintenance task.

## Incomplete source-derived review aid

Treat the D-style locations, syntax facts, interpretations, and questions below as
incomplete by default. They are heuristic leads, not a complete repository inventory
or a closed causal path. Do not limit inspection to the listed locations. Independently
inspect the maintenance target, its call entries and consumers, synchronous callbacks,
identity or capability capture, and final persistent and visible effects. Resolve the
required behavior from repository evidence before editing.

# Selected candidate-source locations

This list is selected by fixed tool rules, not a complete repository inventory.

```json
[
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 32,
      "line": 27
    },
    "id": "L0001",
    "path": "src/channel.js",
    "scope": "<module>/observeChannel",
    "start": {
      "column": 2,
      "line": 27
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 83,
      "line": 28
    },
    "id": "L0002",
    "path": "src/channel.js",
    "scope": "<module>/observeChannel",
    "start": {
      "column": 2,
      "line": 28
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 65,
      "line": 9
    },
    "id": "L0003",
    "path": "src/presence-panel.js",
    "scope": "<module>/createPresencePanel/show",
    "start": {
      "column": 6,
      "line": 9
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 65,
      "line": 9
    },
    "id": "L0004",
    "path": "src/presence-panel.js",
    "scope": "<module>/createPresencePanel/show",
    "start": {
      "column": 16,
      "line": 9
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 25,
      "line": 23
    },
    "id": "L0005",
    "path": "src/presence-panel.js",
    "scope": "<module>/renderPresence",
    "start": {
      "column": 2,
      "line": 23
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 15,
      "line": 25
    },
    "id": "L0006",
    "path": "src/presence-panel.js",
    "scope": "<module>/renderPresence",
    "start": {
      "column": 2,
      "line": 25
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 32,
      "line": 9
    },
    "id": "L0007",
    "path": "src/subscription.js",
    "scope": "<module>/subscribeChannel",
    "start": {
      "column": 2,
      "line": 9
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 55,
      "line": 10
    },
    "id": "L0008",
    "path": "src/subscription.js",
    "scope": "<module>/subscribeChannel",
    "start": {
      "column": 2,
      "line": 10
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 71,
      "line": 11
    },
    "id": "L0009",
    "path": "src/subscription.js",
    "scope": "<module>/subscribeChannel/<callback>",
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
    "id": "L0010",
    "path": "src/subscription.js",
    "scope": "<module>/subscribeChannel/listener",
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
    "id": "L0011",
    "path": "src/subscription.js",
    "scope": "<module>/subscribeChannel/listener",
    "start": {
      "column": 55,
      "line": 6
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
    "source": "channel.connect(bootstrapMode)",
    "syntax": {
      "argument_references": [
        [
          "bootstrapMode"
        ]
      ],
      "arguments": [
        "bootstrapMode"
      ],
      "block": "<module>/observeChannel/block@622",
      "branch_path": [],
      "callee": "channel.connect",
      "conditional_path": [],
      "conditions": [],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "channel",
      "references": [
        "channel.connect",
        "bootstrapMode"
      ],
      "statement": 2
    }
  }
]
```

### L0002

```json
[
  {
    "source": "channel.target.addEventListener(\"presence\", (event) => events.push(event.detail))",
    "syntax": {
      "argument_references": [
        [],
        []
      ],
      "arguments": [
        "\"presence\"",
        "(event) => events.push(event.detail)"
      ],
      "block": "<module>/observeChannel/block@622",
      "branch_path": [],
      "callee": "channel.target.addEventListener",
      "conditional_path": [],
      "conditions": [],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "channel.target",
      "references": [
        "channel.target.addEventListener"
      ],
      "statement": 3
    }
  }
]
```

### L0003

```json
[
  {
    "source": "release = subscribeChannel(channel, bootstrapMode, publish)",
    "syntax": {
      "assigned_names": [
        "release"
      ],
      "awaited": false,
      "block": "<module>/createPresencePanel/show/block@242",
      "branch_path": [],
      "conditional_path": [],
      "conditions": [],
      "declared_names": [],
      "kind": "write",
      "linear_block": true,
      "operator": "=",
      "references": [
        "release",
        "subscribeChannel",
        "channel",
        "bootstrapMode",
        "publish"
      ],
      "rhs_callee": "subscribeChannel",
      "rhs_kind": "CallExpression",
      "rhs_text": null,
      "statement": 1,
      "target": "release",
      "value_references": [
        "subscribeChannel",
        "channel",
        "bootstrapMode",
        "publish"
      ],
      "write_roots": [
        "release"
      ]
    }
  }
]
```

### L0004

```json
[
  {
    "source": "subscribeChannel(channel, bootstrapMode, publish)",
    "syntax": {
      "argument_references": [
        [
          "channel"
        ],
        [
          "bootstrapMode"
        ],
        [
          "publish"
        ]
      ],
      "arguments": [
        "channel",
        "bootstrapMode",
        "publish"
      ],
      "block": "<module>/createPresencePanel/show/block@242",
      "branch_path": [],
      "callee": "subscribeChannel",
      "conditional_path": [],
      "conditions": [],
      "construct": false,
      "kind": "call",
      "linear_block": true,
      "optional": false,
      "receiver": "",
      "references": [
        "subscribeChannel",
        "channel",
        "bootstrapMode",
        "publish"
      ],
      "statement": 1
    }
  }
]
```

### L0005

```json
[
  {
    "source": "await Promise.resolve()",
    "syntax": {
      "block": "<module>/renderPresence/block@466",
      "branch_path": [],
      "conditional_path": [],
      "conditions": [],
      "kind": "await",
      "linear_block": false,
      "statement": 4
    }
  }
]
```

### L0006

```json
[
  {
    "source": "panel.close()",
    "syntax": {
      "argument_references": [],
      "arguments": [],
      "block": "<module>/renderPresence/block@466",
      "branch_path": [],
      "callee": "panel.close",
      "conditional_path": [],
      "conditions": [],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "panel",
      "references": [
        "panel.close"
      ],
      "statement": 6
    }
  }
]
```

### L0007

```json
[
  {
    "source": "channel.connect(bootstrapMode)",
    "syntax": {
      "argument_references": [
        [
          "bootstrapMode"
        ]
      ],
      "arguments": [
        "bootstrapMode"
      ],
      "block": "<module>/subscribeChannel/block@226",
      "branch_path": [],
      "callee": "channel.connect",
      "conditional_path": [],
      "conditions": [],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "channel",
      "references": [
        "channel.connect",
        "bootstrapMode"
      ],
      "statement": 1
    }
  }
]
```

### L0008

```json
[
  {
    "source": "channel.target.addEventListener(\"presence\", listener)",
    "syntax": {
      "argument_references": [
        [],
        [
          "listener"
        ]
      ],
      "arguments": [
        "\"presence\"",
        "listener"
      ],
      "block": "<module>/subscribeChannel/block@226",
      "branch_path": [],
      "callee": "channel.target.addEventListener",
      "conditional_path": [],
      "conditions": [],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "channel.target",
      "references": [
        "channel.target.addEventListener",
        "listener"
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
    "source": "channel.target.removeEventListener(\"presence\", listener)",
    "syntax": {
      "argument_references": [
        [],
        [
          "listener"
        ]
      ],
      "arguments": [
        "\"presence\"",
        "listener"
      ],
      "block": "<module>/subscribeChannel/<callback>/body",
      "branch_path": [],
      "callee": "channel.target.removeEventListener",
      "conditional_path": [],
      "conditions": [],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "channel.target",
      "references": [
        "channel.target.removeEventListener",
        "listener"
      ],
      "statement": 0
    }
  }
]
```

### L0010

```json
[
  {
    "source": "decoded && typeof decoded.then === \"function\"",
    "syntax": {
      "block": "<module>/subscribeChannel/listener/block@258",
      "branch_path": [],
      "condition_path_supported": false,
      "conditional_path": [],
      "conditions": [],
      "else_path_block": "<module>/subscribeChannel/listener/else@314",
      "expression": "decoded && typeof decoded.then === \"function\"",
      "guard_key": "<module>/subscribeChannel/listener/if@314",
      "kind": "guard",
      "linear_block": false,
      "references": [
        "decoded",
        "decoded.then"
      ],
      "statement": 1,
      "then_path_block": "<module>/subscribeChannel/listener/then@314"
    }
  }
]
```

### L0011

```json
[
  {
    "source": "decoded.then(receive)",
    "syntax": {
      "argument_references": [
        [
          "receive"
        ]
      ],
      "arguments": [
        "receive"
      ],
      "block": "<module>/subscribeChannel/listener/then@314",
      "branch_path": [
        {
          "arm": "then",
          "key": "<module>/subscribeChannel/listener/if@314"
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
        "receive"
      ],
      "statement": 1
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
    "kind": "lexical_before_same_block",
    "qualification": "Source statement order within the same syntax block; execution is not established."
  },
  {
    "after": "L0003",
    "before": "L0004",
    "kind": "rhs_before_assignment",
    "qualification": "Assignment follows successful RHS evaluation; asynchronous completion is not established."
  },
  {
    "after": "L0008",
    "before": "L0007",
    "kind": "lexical_before_same_block",
    "qualification": "Source statement order within the same syntax block; execution is not established."
  },
  {
    "basis": "import_binding_candidate",
    "call": "L0004",
    "kind": "candidate_call_target",
    "qualification": "Lexical/import binding candidate only; dynamic dispatch and execution are unresolved.",
    "target_scope": "src/subscription.js::<module>/subscribeChannel"
  }
]
```

## Heuristic interpretations and review questions

The following text is rule-authored guidance, not a defect verdict or an oracle.

```json
{
  "classification": "heuristic_review_hint",
  "condition": "接收者语法表达式相同；需确认对象类型、别名稳定性、同步通知与是否允许漏收。",
  "interpretation": "同一语法块中连接调用位于监听注册之前。",
  "locations": [
    "L0001",
    "L0002"
  ],
  "review_question": "若 connect 同步发消息，这个消费者是否应接收初始消息？统计消费者可能有意忽略它。",
  "rule": "connect-before-listen"
}
```

```json
{
  "classification": "heuristic_review_hint",
  "condition": "若调用内可能执行用户回调，须另查回调是否重入；本条不声称重入已发生。",
  "interpretation": "清理句柄名称的赋值发生在右侧调用成功求值之后。",
  "locations": [
    "L0003",
    "L0004"
  ],
  "review_question": "回调先切换/关闭时，旧操作返回后会覆盖新清理句柄吗？",
  "rule": "cleanup-handle-after-call"
}
```

```json
{
  "classification": "heuristic_review_hint",
  "condition": "接收者语法表达式相同；需确认对象类型、别名稳定性、同步通知与是否允许漏收。",
  "interpretation": "同一语法块中连接调用位于监听注册之前。",
  "locations": [
    "L0007",
    "L0008"
  ],
  "review_question": "若 connect 同步发消息，这个消费者是否应接收初始消息？统计消费者可能有意忽略它。",
  "rule": "connect-before-listen"
}
```

```json
{
  "classification": "heuristic_review_hint",
  "condition": "仅是共现线索；需追踪是否属于同一工作、同一生命周期。",
  "interpretation": "同一文件中同时存在完成回调登记和监听移除。",
  "locations": [
    "L0009",
    "L0011"
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
    "L0005",
    "L0006"
  ],
  "review_question": "关闭、卸载和切换是否是不同边界？哪些边界应使旧结果失效，哪些工作应继续？需从仓库证据确认。",
  "rule": "continuation-lifecycle-boundaries"
}
```

```json
{
  "classification": "heuristic_review_hint",
  "condition": "仅表示同一词法函数/类命名空间中的语法共现；名称不保证 API 类型，未证明属于同一请求、实例或生命周期，也未证明回调可达、重试循环或保护充分。",
  "interpretation": "完成回调/等待点与关闭、重新打开或清理边界名称线索出现在同一词法单元。",
  "locations": [
    "L0009",
    "L0011"
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
    "L0009",
    "L0010",
    "L0011"
  ],
  "review_question": "回调检查了什么状态？关闭、卸载、重开分别更新了什么？只取消计时器能否约束已发请求？相同标识重新使用时判断是否仍适用？",
  "rule": "continuation-guard-state-review"
}
```
