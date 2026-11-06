# Selected candidate-source locations

This list is selected by fixed tool rules, not a complete repository inventory.

```json
[
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 27,
      "line": 11
    },
    "id": "L0001",
    "path": "src/draft-store.js",
    "scope": "<module>/createDraftStore/write",
    "start": {
      "column": 6,
      "line": 11
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 35,
      "line": 14
    },
    "id": "L0002",
    "path": "src/draft-store.js",
    "scope": "<module>/createDraftStore/write",
    "start": {
      "column": 12,
      "line": 14
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 52,
      "line": 14
    },
    "id": "L0003",
    "path": "src/draft-store.js",
    "scope": "<module>/createDraftStore/write",
    "start": {
      "column": 37,
      "line": 14
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 67,
      "line": 5
    },
    "id": "L0004",
    "path": "src/workspace.js",
    "scope": "<module>/createWorkspace",
    "start": {
      "column": 15,
      "line": 5
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 40,
      "line": 5
    },
    "id": "L0005",
    "path": "src/workspace.js",
    "scope": "<module>/createWorkspace",
    "start": {
      "column": 31,
      "line": 5
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 40,
      "line": 5
    },
    "id": "L0006",
    "path": "src/workspace.js",
    "scope": "<module>/createWorkspace/<callback>",
    "start": {
      "column": 31,
      "line": 5
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 66,
      "line": 5
    },
    "id": "L0007",
    "path": "src/workspace.js",
    "scope": "<module>/createWorkspace/<callback>",
    "start": {
      "column": 40,
      "line": 5
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 12,
      "line": 10
    },
    "id": "L0008",
    "path": "src/workspace.js",
    "scope": "<module>/createWorkspace/close",
    "start": {
      "column": 4,
      "line": 10
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 13,
      "line": 8
    },
    "id": "L0009",
    "path": "src/workspace.js",
    "scope": "<module>/createWorkspace/open",
    "start": {
      "column": 4,
      "line": 8
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 39,
      "line": 12
    },
    "id": "L0010",
    "path": "src/workspace.js",
    "scope": "<module>/createWorkspace/submit",
    "start": {
      "column": 12,
      "line": 12
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 17,
      "line": 13
    },
    "id": "L0011",
    "path": "src/workspace.js",
    "scope": "<module>/createWorkspace/submit",
    "start": {
      "column": 10,
      "line": 13
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 75,
      "line": 14
    },
    "id": "L0012",
    "path": "src/workspace.js",
    "scope": "<module>/createWorkspace/submit",
    "start": {
      "column": 12,
      "line": 14
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 75,
      "line": 14
    },
    "id": "L0013",
    "path": "src/workspace.js",
    "scope": "<module>/createWorkspace/submit",
    "start": {
      "column": 22,
      "line": 14
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 31,
      "line": 15
    },
    "id": "L0014",
    "path": "src/workspace.js",
    "scope": "<module>/createWorkspace/submit",
    "start": {
      "column": 6,
      "line": 15
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
    "source": "records.set(id, text)",
    "syntax": {
      "argument_references": [
        [
          "id"
        ],
        [
          "text"
        ]
      ],
      "arguments": [
        "id",
        "text"
      ],
      "block": "<module>/createDraftStore/write/block@447",
      "branch_path": [],
      "callee": "records.set",
      "conditional_path": [],
      "conditions": [],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "records",
      "references": [
        "records.set",
        "id",
        "text"
      ],
      "statement": 0
    }
  }
]
```

### L0002

```json
[
  {
    "source": "listeners.has(listener)",
    "syntax": {
      "block": "<module>/createDraftStore/write/block@579",
      "branch_path": [],
      "condition_path_supported": false,
      "conditional_path": [],
      "conditions": [
        "ForOfStatement path; execution/repetition not proven"
      ],
      "else_path_block": "<module>/createDraftStore/write/else@589",
      "expression": "listeners.has(listener)",
      "guard_key": "<module>/createDraftStore/write/if@589",
      "kind": "guard",
      "linear_block": false,
      "loop_bindings": [
        {
          "iterable": "[...listeners]",
          "iterable_references": [
            "listeners"
          ],
          "target": "listener"
        }
      ],
      "references": [
        "listeners.has",
        "listener"
      ],
      "statement": 0,
      "then_path_block": "<module>/createDraftStore/write/then@589"
    }
  }
]
```

### L0003

```json
[
  {
    "source": "listener(event)",
    "syntax": {
      "argument_references": [
        [
          "event"
        ]
      ],
      "arguments": [
        "event"
      ],
      "block": "<module>/createDraftStore/write/then@589",
      "branch_path": [
        {
          "arm": "then",
          "key": "<module>/createDraftStore/write/if@589"
        }
      ],
      "callee": "listener",
      "conditional_path": [],
      "conditions": [
        "ForOfStatement path; execution/repetition not proven",
        "if listeners.has(listener)"
      ],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "loop_bindings": [
        {
          "iterable": "[...listeners]",
          "iterable_references": [
            "listeners"
          ],
          "target": "listener"
        }
      ],
      "optional": false,
      "receiver": "",
      "references": [
        "listener",
        "event"
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
    "source": "store.subscribe(event => onSaved(event, navigation))",
    "syntax": {
      "argument_references": [
        []
      ],
      "arguments": [
        "event => onSaved(event, navigation)"
      ],
      "block": "<module>/createWorkspace/block@191",
      "branch_path": [],
      "callee": "store.subscribe",
      "conditional_path": [],
      "conditions": [],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "store",
      "references": [
        "store.subscribe"
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
    "source": "event => ",
    "syntax": {
      "argument_index": 0,
      "block": "<module>/createWorkspace/block@191",
      "branch_path": [],
      "callee": "store.subscribe",
      "conditional_path": [],
      "conditions": [],
      "kind": "callback_argument",
      "linear_block": false,
      "statement": 0,
      "target_scope": "<module>/createWorkspace/<callback>"
    }
  }
]
```

### L0006

```json
[
  {
    "source": "event => ",
    "syntax": {
      "block": "<module>/createWorkspace/block@191",
      "branch_path": [],
      "conditional_path": [],
      "conditions": [],
      "kind": "function_definition",
      "linear_block": false,
      "name": "<callback>",
      "statement": 0
    }
  }
]
```

### L0007

```json
[
  {
    "source": "onSaved(event, navigation)",
    "syntax": {
      "argument_references": [
        [
          "event"
        ],
        [
          "navigation"
        ]
      ],
      "arguments": [
        "event",
        "navigation"
      ],
      "block": "<module>/createWorkspace/<callback>/body",
      "branch_path": [],
      "callee": "onSaved",
      "conditional_path": [],
      "conditions": [],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "",
      "references": [
        "onSaved",
        "event",
        "navigation"
      ],
      "statement": 0
    }
  }
]
```

### L0008

```json
[
  {
    "source": "close() ",
    "syntax": {
      "block": "<module>/createWorkspace/block@191",
      "branch_path": [],
      "conditional_path": [],
      "conditions": [],
      "kind": "function_definition",
      "linear_block": false,
      "name": "close",
      "object_target": "navigation",
      "statement": 2
    }
  }
]
```

### L0009

```json
[
  {
    "source": "open(id) ",
    "syntax": {
      "block": "<module>/createWorkspace/block@191",
      "branch_path": [],
      "conditional_path": [],
      "conditions": [],
      "kind": "function_definition",
      "linear_block": false,
      "name": "open",
      "object_target": "navigation",
      "statement": 2
    }
  }
]
```

### L0010

```json
[
  {
    "source": "origin = editor.selection()",
    "syntax": {
      "assigned_names": [
        "origin"
      ],
      "awaited": false,
      "block": "<module>/createWorkspace/submit/block@538",
      "branch_path": [],
      "conditional_path": [],
      "conditions": [],
      "declared_names": [
        "origin"
      ],
      "kind": "write",
      "linear_block": false,
      "operator": "=",
      "references": [
        "origin",
        "editor.selection"
      ],
      "rhs_callee": "editor.selection",
      "rhs_kind": "CallExpression",
      "rhs_text": null,
      "statement": 0,
      "target": "origin",
      "value_references": [
        "editor.selection"
      ],
      "write_roots": [
        "origin"
      ]
    }
  }
]
```

### L0011

```json
[
  {
    "source": "!origin",
    "syntax": {
      "block": "<module>/createWorkspace/submit/block@538",
      "branch_path": [],
      "condition_identifier": "origin",
      "condition_path_supported": true,
      "condition_truthy": false,
      "conditional_path": [],
      "conditions": [],
      "else_path_block": "<module>/createWorkspace/submit/else@587",
      "expression": "!origin",
      "guard_key": "<module>/createWorkspace/submit/if@587",
      "kind": "guard",
      "linear_block": false,
      "references": [
        "origin"
      ],
      "statement": 1,
      "then_path_block": "<module>/createWorkspace/submit/then@587"
    }
  }
]
```

### L0012

```json
[
  {
    "source": "receipt = archive.capture({ id: origin.id, text: origin.text })",
    "syntax": {
      "assigned_names": [
        "receipt"
      ],
      "awaited": false,
      "block": "<module>/createWorkspace/submit/block@538",
      "branch_path": [],
      "conditional_path": [],
      "conditions": [],
      "declared_names": [
        "receipt"
      ],
      "kind": "write",
      "linear_block": false,
      "operator": "=",
      "references": [
        "receipt",
        "archive.capture",
        "origin.id",
        "origin.text"
      ],
      "rhs_callee": "archive.capture",
      "rhs_kind": "CallExpression",
      "rhs_text": null,
      "statement": 2,
      "target": "receipt",
      "value_references": [
        "archive.capture",
        "origin.id",
        "origin.text"
      ],
      "write_roots": [
        "receipt"
      ]
    }
  }
]
```

### L0013

```json
[
  {
    "source": "archive.capture({ id: origin.id, text: origin.text })",
    "syntax": {
      "argument_references": [
        [
          "origin.id",
          "origin.text"
        ]
      ],
      "arguments": [
        "{ id: origin.id, text: origin.text }"
      ],
      "block": "<module>/createWorkspace/submit/block@538",
      "branch_path": [],
      "callee": "archive.capture",
      "conditional_path": [],
      "conditions": [],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "archive",
      "references": [
        "archive.capture",
        "origin.id",
        "origin.text"
      ],
      "statement": 2
    }
  }
]
```

### L0014

```json
[
  {
    "source": "renderSubmission(receipt)",
    "syntax": {
      "argument_references": [
        [
          "receipt"
        ]
      ],
      "arguments": [
        "receipt"
      ],
      "block": "<module>/createWorkspace/submit/block@538",
      "branch_path": [],
      "callee": "renderSubmission",
      "conditional_path": [],
      "conditions": [],
      "construct": false,
      "kind": "call",
      "linear_block": false,
      "optional": false,
      "receiver": "",
      "references": [
        "renderSubmission",
        "receipt"
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
    "after": "L0003",
    "before": "L0001",
    "kind": "lexical_write_before_direct_call",
    "qualification": "Source order within one function; execution, callback identity and synchronous reentry are not established."
  },
  {
    "after": "L0012",
    "before": "L0013",
    "kind": "rhs_before_assignment",
    "qualification": "Assignment follows successful RHS evaluation; asynchronous completion is not established."
  },
  {
    "after": "L0014",
    "before": "L0010",
    "kind": "lexical_capture_before_consumer",
    "qualification": "Local variable/member references and source order; runtime dataflow, ownership and immutability are not established."
  }
]
```
