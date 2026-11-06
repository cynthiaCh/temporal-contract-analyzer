# Selected candidate-source locations

This list is selected by fixed tool rules, not a complete repository inventory.

```json
[
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 6,
      "line": 35
    },
    "id": "L0001",
    "path": "src/BackgroundExportPanel.jsx",
    "scope": "<module>/BackgroundExportPanel/<callback>",
    "start": {
      "column": 4,
      "line": 22
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 22,
      "line": 23
    },
    "id": "L0002",
    "path": "src/BackgroundExportPanel.jsx",
    "scope": "<module>/BackgroundExportPanel/<callback>/<callback>#2",
    "start": {
      "column": 10,
      "line": 23
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 14,
      "line": 24
    },
    "id": "L0003",
    "path": "src/BackgroundExportPanel.jsx",
    "scope": "<module>/BackgroundExportPanel/<callback>/<callback>#2",
    "start": {
      "column": 10,
      "line": 24
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 61,
      "line": 32
    },
    "id": "L0004",
    "path": "src/BackgroundExportPanel.jsx",
    "scope": "<module>/BackgroundExportPanel/<callback>/<callback>#2",
    "start": {
      "column": 21,
      "line": 32
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 25,
      "line": 14
    },
    "id": "L0005",
    "path": "src/BackgroundExportPanel.jsx",
    "scope": "<module>/BackgroundExportPanel/componentWillUnmount",
    "start": {
      "column": 2,
      "line": 14
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 23,
      "line": 15
    },
    "id": "L0006",
    "path": "src/BackgroundExportPanel.jsx",
    "scope": "<module>/BackgroundExportPanel/componentWillUnmount",
    "start": {
      "column": 4,
      "line": 15
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 27,
      "line": 16
    },
    "id": "L0007",
    "path": "src/BackgroundExportPanel.jsx",
    "scope": "<module>/BackgroundExportPanel/componentWillUnmount",
    "start": {
      "column": 8,
      "line": 16
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 67,
      "line": 16
    },
    "id": "L0008",
    "path": "src/BackgroundExportPanel.jsx",
    "scope": "<module>/BackgroundExportPanel/componentWillUnmount",
    "start": {
      "column": 29,
      "line": 16
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 6,
      "line": 27
    },
    "id": "L0009",
    "path": "src/usePreparation.js",
    "scope": "<module>/usePreparation/check",
    "start": {
      "column": 4,
      "line": 23
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 16,
      "line": 25
    },
    "id": "L0010",
    "path": "src/usePreparation.js",
    "scope": "<module>/usePreparation/check/<callback>",
    "start": {
      "column": 10,
      "line": 25
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 12,
      "line": 32
    },
    "id": "L0011",
    "path": "src/usePreparation.js",
    "scope": "<module>/usePreparation/close",
    "start": {
      "column": 4,
      "line": 32
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 35,
      "line": 33
    },
    "id": "L0012",
    "path": "src/usePreparation.js",
    "scope": "<module>/usePreparation/close",
    "start": {
      "column": 6,
      "line": 33
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 22,
      "line": 36
    },
    "id": "L0013",
    "path": "src/usePreparation.js",
    "scope": "<module>/usePreparation/reopen",
    "start": {
      "column": 4,
      "line": 36
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 37,
      "line": 37
    },
    "id": "L0014",
    "path": "src/usePreparation.js",
    "scope": "<module>/usePreparation/reopen",
    "start": {
      "column": 6,
      "line": 37
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 34,
      "line": 38
    },
    "id": "L0015",
    "path": "src/usePreparation.js",
    "scope": "<module>/usePreparation/reopen",
    "start": {
      "column": 6,
      "line": 38
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
    "source": "api.checkPreparation(token).then((done) => {\n      if (!this.active) return;\n      if (done) {\n        this.retry = null;\n        this.setState((state) => ({\n          loading: false,\n          retryScheduled: false,\n          completed: state.completed.includes(token) ? state.completed : [...state.completed, token],\n        }));\n      } else {\n        this.retry = api.schedulePreparationRetry(this.start);\n        this.setState({ retryScheduled: true });\n      }\n    })",
    "syntax": {
      "argument_references": [
        []
      ],
      "arguments": [
        "(done) => {\n      if (!this.active) return;\n      if (done) {\n        this.retry = null;\n        this.setState((state) => ({\n          loading: false,\n          retryScheduled: false,\n          completed: state.completed.includes(token) ? state.completed : [...state.completed, token],\n        }));\n      } else {\n        this.retry = api.schedulePreparationRetry(this.start);\n        this.setState({ retryScheduled: true });\n      }\n    }"
      ],
      "block": "<module>/BackgroundExportPanel/<callback>/block@507",
      "branch_path": [],
      "callee": ".then",
      "conditional_path": [],
      "conditions": [],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "",
      "references": [
        "api.checkPreparation",
        "token"
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
    "source": "!this.active",
    "syntax": {
      "block": "<module>/BackgroundExportPanel/<callback>/<callback>#2/block@677",
      "branch_path": [],
      "condition_path_supported": false,
      "conditional_path": [],
      "conditions": [],
      "else_path_block": "<module>/BackgroundExportPanel/<callback>/<callback>#2/else@685",
      "expression": "!this.active",
      "guard_key": "<module>/BackgroundExportPanel/<callback>/<callback>#2/if@685",
      "kind": "guard",
      "linear_block": false,
      "references": [
        "this.active"
      ],
      "statement": 0,
      "then_path_block": "<module>/BackgroundExportPanel/<callback>/<callback>#2/then@685"
    }
  }
]
```

### L0003

```json
[
  {
    "source": "done",
    "syntax": {
      "block": "<module>/BackgroundExportPanel/<callback>/<callback>#2/block@677",
      "branch_path": [],
      "condition_identifier": "done",
      "condition_path_supported": true,
      "condition_truthy": true,
      "conditional_path": [],
      "conditions": [],
      "else_path_block": "<module>/BackgroundExportPanel/<callback>/<callback>#2/block@979",
      "expression": "done",
      "guard_key": "<module>/BackgroundExportPanel/<callback>/<callback>#2/if@717",
      "kind": "guard",
      "linear_block": false,
      "references": [
        "done"
      ],
      "reflective_branch_linear": false,
      "statement": 1,
      "then_path_block": "<module>/BackgroundExportPanel/<callback>/<callback>#2/block@727"
    }
  }
]
```

### L0004

```json
[
  {
    "source": "api.schedulePreparationRetry(this.start)",
    "syntax": {
      "argument_references": [
        [
          "this.start"
        ]
      ],
      "arguments": [
        "this.start"
      ],
      "block": "<module>/BackgroundExportPanel/<callback>/<callback>#2/block@979",
      "branch_path": [
        {
          "arm": "else",
          "key": "<module>/BackgroundExportPanel/<callback>/<callback>#2/if@717"
        }
      ],
      "callee": "api.schedulePreparationRetry",
      "conditional_path": [],
      "conditions": [
        "else of done"
      ],
      "construct": false,
      "kind": "call",
      "linear_block": true,
      "optional": false,
      "receiver": "api",
      "references": [
        "api.schedulePreparationRetry",
        "this.start"
      ],
      "statement": 0
    }
  }
]
```

### L0005

```json
[
  {
    "source": "componentWillUnmount() ",
    "syntax": {
      "block": "<module>/BackgroundExportPanel/class-body",
      "branch_path": [],
      "conditional_path": [],
      "conditions": [],
      "kind": "function_definition",
      "linear_block": false,
      "name": "componentWillUnmount",
      "statement": 1
    }
  }
]
```

### L0006

```json
[
  {
    "source": "this.active = false",
    "syntax": {
      "assigned_names": [],
      "awaited": false,
      "block": "<module>/BackgroundExportPanel/componentWillUnmount/block@390",
      "branch_path": [],
      "conditional_path": [],
      "conditions": [],
      "declared_names": [],
      "kind": "write",
      "linear_block": false,
      "operator": "=",
      "references": [
        "this.active"
      ],
      "rhs_callee": "",
      "rhs_kind": "BooleanLiteral",
      "rhs_text": "false",
      "statement": 0,
      "target": "this.active",
      "value_references": [],
      "write_roots": []
    }
  }
]
```

### L0007

```json
[
  {
    "source": "this.retry !== null",
    "syntax": {
      "block": "<module>/BackgroundExportPanel/componentWillUnmount/block@390",
      "branch_path": [],
      "condition_path_supported": false,
      "conditional_path": [],
      "conditions": [],
      "else_path_block": "<module>/BackgroundExportPanel/componentWillUnmount/else@421",
      "expression": "this.retry !== null",
      "guard_key": "<module>/BackgroundExportPanel/componentWillUnmount/if@421",
      "kind": "guard",
      "linear_block": false,
      "references": [
        "this.retry"
      ],
      "statement": 1,
      "then_path_block": "<module>/BackgroundExportPanel/componentWillUnmount/then@421"
    }
  }
]
```

### L0008

```json
[
  {
    "source": "api.cancelPreparationRetry(this.retry)",
    "syntax": {
      "argument_references": [
        [
          "this.retry"
        ]
      ],
      "arguments": [
        "this.retry"
      ],
      "block": "<module>/BackgroundExportPanel/componentWillUnmount/then@421",
      "branch_path": [
        {
          "arm": "then",
          "key": "<module>/BackgroundExportPanel/componentWillUnmount/if@421"
        }
      ],
      "callee": "api.cancelPreparationRetry",
      "conditional_path": [],
      "conditions": [
        "if this.retry !== null"
      ],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "api",
      "references": [
        "api.cancelPreparationRetry",
        "this.retry"
      ],
      "statement": 1
    }
  }
]
```

### L0009

```json
[
  {
    "source": "checkPreparation(requestToken).then((status) => {\n      state.current.loading = false;\n      if (status) state.current.completed.push(requestToken);\n      publish();\n    })",
    "syntax": {
      "argument_references": [
        []
      ],
      "arguments": [
        "(status) => {\n      state.current.loading = false;\n      if (status) state.current.completed.push(requestToken);\n      publish();\n    }"
      ],
      "block": "<module>/usePreparation/check/block@437",
      "branch_path": [],
      "callee": ".then",
      "conditional_path": [],
      "conditions": [],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "",
      "references": [
        "checkPreparation",
        "requestToken"
      ],
      "statement": 4
    }
  }
]
```

### L0010

```json
[
  {
    "source": "status",
    "syntax": {
      "block": "<module>/usePreparation/check/<callback>/block@621",
      "branch_path": [],
      "condition_identifier": "status",
      "condition_path_supported": true,
      "condition_truthy": true,
      "conditional_path": [],
      "conditions": [],
      "else_path_block": "<module>/usePreparation/check/<callback>/else@666",
      "expression": "status",
      "guard_key": "<module>/usePreparation/check/<callback>/if@666",
      "kind": "guard",
      "linear_block": false,
      "references": [
        "status"
      ],
      "reflective_branch_linear": true,
      "statement": 1,
      "then_path_block": "<module>/usePreparation/check/<callback>/then@666"
    }
  }
]
```

### L0011

```json
[
  {
    "source": "close() ",
    "syntax": {
      "block": "<module>/usePreparation/block@148",
      "branch_path": [],
      "conditional_path": [],
      "conditions": [],
      "kind": "function_definition",
      "linear_block": false,
      "name": "close",
      "statement": 4
    }
  }
]
```

### L0012

```json
[
  {
    "source": "state.current.visible = false",
    "syntax": {
      "assigned_names": [],
      "awaited": false,
      "block": "<module>/usePreparation/close/block@794",
      "branch_path": [],
      "conditional_path": [],
      "conditions": [],
      "declared_names": [],
      "kind": "write",
      "linear_block": true,
      "operator": "=",
      "references": [
        "state.current.visible"
      ],
      "rhs_callee": "",
      "rhs_kind": "BooleanLiteral",
      "rhs_text": "false",
      "statement": 0,
      "target": "state.current.visible",
      "value_references": [],
      "write_roots": [
        "state"
      ]
    }
  }
]
```

### L0013

```json
[
  {
    "source": "reopen(nextToken) ",
    "syntax": {
      "block": "<module>/usePreparation/block@148",
      "branch_path": [],
      "conditional_path": [],
      "conditions": [],
      "kind": "function_definition",
      "linear_block": false,
      "name": "reopen",
      "statement": 4
    }
  }
]
```

### L0014

```json
[
  {
    "source": "state.current.token = nextToken",
    "syntax": {
      "assigned_names": [],
      "awaited": false,
      "block": "<module>/usePreparation/reopen/block@879",
      "branch_path": [],
      "conditional_path": [],
      "conditions": [],
      "declared_names": [],
      "kind": "write",
      "linear_block": true,
      "operator": "=",
      "references": [
        "state.current.token",
        "nextToken"
      ],
      "rhs_callee": "",
      "rhs_kind": "Identifier",
      "rhs_text": "nextToken",
      "statement": 0,
      "target": "state.current.token",
      "value_references": [
        "nextToken"
      ],
      "write_roots": [
        "state"
      ]
    }
  }
]
```

### L0015

```json
[
  {
    "source": "state.current.visible = true",
    "syntax": {
      "assigned_names": [],
      "awaited": false,
      "block": "<module>/usePreparation/reopen/block@879",
      "branch_path": [],
      "conditional_path": [],
      "conditions": [],
      "declared_names": [],
      "kind": "write",
      "linear_block": true,
      "operator": "=",
      "references": [
        "state.current.visible"
      ],
      "rhs_callee": "",
      "rhs_kind": "BooleanLiteral",
      "rhs_text": "true",
      "statement": 1,
      "target": "state.current.visible",
      "value_references": [],
      "write_roots": [
        "state"
      ]
    }
  }
]
```

## Limited relations between selected locations/scopes

```json
[]
```
