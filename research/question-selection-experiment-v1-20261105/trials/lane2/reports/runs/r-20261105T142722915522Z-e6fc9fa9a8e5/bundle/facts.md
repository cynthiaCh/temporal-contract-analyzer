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
