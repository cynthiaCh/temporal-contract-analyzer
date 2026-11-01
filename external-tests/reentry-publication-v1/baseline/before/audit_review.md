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
      "column": 27,
      "line": 2
    },
    "id": "L0001",
    "path": "index.js",
    "scope": "<module>/pDebounce",
    "start": {
      "column": 5,
      "line": 2
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 51,
      "line": 35
    },
    "id": "L0002",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>",
    "start": {
      "column": 9,
      "line": 35
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 24,
      "line": 37
    },
    "id": "L0003",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>",
    "start": {
      "column": 3,
      "line": 37
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 11,
      "line": 67
    },
    "id": "L0004",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>",
    "start": {
      "column": 3,
      "line": 39
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 11,
      "line": 67
    },
    "id": "L0005",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>",
    "start": {
      "column": 13,
      "line": 39
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 20,
      "line": 69
    },
    "id": "L0006",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>",
    "start": {
      "column": 7,
      "line": 69
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 8,
      "line": 84
    },
    "id": "L0007",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>",
    "start": {
      "column": 4,
      "line": 72
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 54,
      "line": 90
    },
    "id": "L0008",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>",
    "start": {
      "column": 8,
      "line": 90
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 23,
      "line": 40
    },
    "id": "L0009",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 4,
      "line": 40
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 43,
      "line": 43
    },
    "id": "L0010",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 10,
      "line": 43
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 24,
      "line": 46
    },
    "id": "L0011",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 4,
      "line": 46
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 57,
      "line": 49
    },
    "id": "L0012",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 4,
      "line": 49
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 42,
      "line": 52
    },
    "id": "L0013",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 10,
      "line": 52
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 27,
      "line": 53
    },
    "id": "L0014",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 4,
      "line": 53
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 112,
      "line": 57
    },
    "id": "L0015",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 11,
      "line": 57
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 61,
      "line": 57
    },
    "id": "L0016",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 37,
      "line": 57
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 112,
      "line": 57
    },
    "id": "L0017",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 64,
      "line": 57
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 42,
      "line": 59
    },
    "id": "L0018",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 16,
      "line": 59
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 40,
      "line": 63
    },
    "id": "L0019",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 16,
      "line": 63
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 21,
      "line": 73
    },
    "id": "L0020",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>#2",
    "start": {
      "column": 9,
      "line": 73
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 69,
      "line": 76
    },
    "id": "L0021",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>#2",
    "start": {
      "column": 6,
      "line": 76
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 69,
      "line": 76
    },
    "id": "L0022",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>#2",
    "start": {
      "column": 21,
      "line": 76
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 23,
      "line": 10
    },
    "id": "L0023",
    "path": "index.js",
    "scope": "<module>/pDebounce/onAbort",
    "start": {
      "column": 17,
      "line": 10
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 23,
      "line": 11
    },
    "id": "L0024",
    "path": "index.js",
    "scope": "<module>/pDebounce/onAbort",
    "start": {
      "column": 2,
      "line": 11
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 21,
      "line": 12
    },
    "id": "L0025",
    "path": "index.js",
    "scope": "<module>/pDebounce/onAbort",
    "start": {
      "column": 2,
      "line": 12
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 22,
      "line": 17
    },
    "id": "L0026",
    "path": "index.js",
    "scope": "<module>/pDebounce/onAbort",
    "start": {
      "column": 14,
      "line": 17
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 23,
      "line": 21
    },
    "id": "L0027",
    "path": "index.js",
    "scope": "<module>/pDebounce/onAbort",
    "start": {
      "column": 3,
      "line": 21
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
    "source": "!Number.isFinite(wait)",
    "syntax": {
      "block": "<module>/pDebounce/block@62",
      "conditions": [],
      "expression": "!Number.isFinite(wait)",
      "kind": "guard",
      "references": [
        "Number.isFinite",
        "wait"
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
    "source": "shouldCallNow = options.before && !timeout",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/block@580",
      "conditions": [],
      "kind": "write",
      "operator": "=",
      "references": [
        "shouldCallNow",
        "options.before",
        "timeout"
      ],
      "rhs_callee": "",
      "rhs_kind": "LogicalExpression",
      "statement": 1,
      "target": "shouldCallNow",
      "value_references": [
        "options.before",
        "timeout"
      ]
    }
  }
]
```

### L0003

```json
[
  {
    "source": "clearTimeout(timeout)",
    "syntax": {
      "argument_references": [
        [
          "timeout"
        ]
      ],
      "arguments": [
        "timeout"
      ],
      "block": "<module>/pDebounce/<callback>/<callback>/block@580",
      "callee": "clearTimeout",
      "conditions": [],
      "construct": false,
      "kind": "call",
      "optional": false,
      "receiver": "",
      "references": [
        "clearTimeout",
        "timeout"
      ],
      "statement": 2
    }
  }
]
```

### L0004

```json
[
  {
    "source": "timeout = setTimeout(async () => {\n\t\t\t\ttimeout = undefined;\n\n\t\t\t\t// Capture the current handlers for this execution\n\t\t\t\tconst currentHandlers = promiseHandlers;\n\n\t\t\t\t// Clear handlers for next cycle (new calls during execution will add to new list)\n\t\t\t\tpromiseHandlers = [];\n\n\t\t\t\t// Remove abort listener\n\t\t\t\toptions.signal?.removeEventListener('abort', onAbort);\n\n\t\t\t\t// Capture this window's leading call before a new window can replace it, and clear it so its value is not retained\n\t\t\t\tconst currentLeadingCall = leadingCall;\n\t\t\t\tleadingCall = undefined;\n\n\t\t\t\ttry {\n\t\t\t\t\t// The leading call can still be pending when the function is slower than `wait`.\n\t\t\t\t\tconst result = options.before ? await currentLeadingCall : await functionToDebounce.apply(this, arguments_);\n\n\t\t\t\t\tfor (const {resolve: resolveFunction} of currentHandlers) {\n\t\t\t\t\t\tresolveFunction(result);\n\t\t\t\t\t}\n\t\t\t\t} catch (error) {\n\t\t\t\t\tfor (const {reject: rejectFunction} of currentHandlers) {\n\t\t\t\t\t\trejectFunction(error);\n\t\t\t\t\t}\n\t\t\t\t}\n\t\t\t}, wait)",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/block@580",
      "conditions": [],
      "kind": "write",
      "operator": "=",
      "references": [
        "timeout",
        "setTimeout",
        "wait"
      ],
      "rhs_callee": "setTimeout",
      "rhs_kind": "CallExpression",
      "statement": 3,
      "target": "timeout",
      "value_references": [
        "setTimeout",
        "wait"
      ]
    }
  }
]
```

### L0005

```json
[
  {
    "source": "setTimeout(async () => {\n\t\t\t\ttimeout = undefined;\n\n\t\t\t\t// Capture the current handlers for this execution\n\t\t\t\tconst currentHandlers = promiseHandlers;\n\n\t\t\t\t// Clear handlers for next cycle (new calls during execution will add to new list)\n\t\t\t\tpromiseHandlers = [];\n\n\t\t\t\t// Remove abort listener\n\t\t\t\toptions.signal?.removeEventListener('abort', onAbort);\n\n\t\t\t\t// Capture this window's leading call before a new window can replace it, and clear it so its value is not retained\n\t\t\t\tconst currentLeadingCall = leadingCall;\n\t\t\t\tleadingCall = undefined;\n\n\t\t\t\ttry {\n\t\t\t\t\t// The leading call can still be pending when the function is slower than `wait`.\n\t\t\t\t\tconst result = options.before ? await currentLeadingCall : await functionToDebounce.apply(this, arguments_);\n\n\t\t\t\t\tfor (const {resolve: resolveFunction} of currentHandlers) {\n\t\t\t\t\t\tresolveFunction(result);\n\t\t\t\t\t}\n\t\t\t\t} catch (error) {\n\t\t\t\t\tfor (const {reject: rejectFunction} of currentHandlers) {\n\t\t\t\t\t\trejectFunction(error);\n\t\t\t\t\t}\n\t\t\t\t}\n\t\t\t}, wait)",
    "syntax": {
      "argument_references": [
        [],
        [
          "wait"
        ]
      ],
      "arguments": [
        "async () => {\n\t\t\t\ttimeout = undefined;\n\n\t\t\t\t// Capture the current handlers for this execution\n\t\t\t\tconst currentHandlers = promiseHandlers;\n\n\t\t\t\t// Clear handlers for next cycle (new calls during execution will add to new list)\n\t\t\t\tpromiseHandlers = [];\n\n\t\t\t\t// Remove abort listener\n\t\t\t\toptions.signal?.removeEventListener('abort', onAbort);\n\n\t\t\t\t// Capture this window's leading call before a new window can replace it, and clear it so its value is not retained\n\t\t\t\tconst currentLeadingCall = leadingCall;\n\t\t\t\tleadingCall = undefined;\n\n\t\t\t\ttry {\n\t\t\t\t\t// The leading call can still be pending when the function is slower than `wait`.\n\t\t\t\t\tconst result = options.before ? await currentLeadingCall : await functionToDebounce.apply(this, arguments_);\n\n\t\t\t\t\tfor (const {resolve: resolveFunction} of currentHandlers) {\n\t\t\t\t\t\tresolveFunction(result);\n\t\t\t\t\t}\n\t\t\t\t} catch (error) {\n\t\t\t\t\tfor (const {reject: rejectFunction} of currentHandlers) {\n\t\t\t\t\t\trejectFunction(error);\n\t\t\t\t\t}\n\t\t\t\t}\n\t\t\t}",
        "wait"
      ],
      "block": "<module>/pDebounce/<callback>/<callback>/block@580",
      "callee": "setTimeout",
      "conditions": [],
      "construct": false,
      "kind": "call",
      "optional": false,
      "receiver": "",
      "references": [
        "setTimeout",
        "wait"
      ],
      "statement": 3
    }
  }
]
```

### L0006

```json
[
  {
    "source": "shouldCallNow",
    "syntax": {
      "block": "<module>/pDebounce/<callback>/<callback>/block@580",
      "conditions": [],
      "expression": "shouldCallNow",
      "kind": "guard",
      "references": [
        "shouldCallNow"
      ],
      "statement": 4
    }
  }
]
```

### L0007

```json
[
  {
    "source": "leadingCall = (async () => {\n\t\t\t\t\tlet leadingValue;\n\n\t\t\t\t\ttry {\n\t\t\t\t\t\tleadingValue = await functionToDebounce.apply(this, arguments_);\n\t\t\t\t\t} catch (error) {\n\t\t\t\t\t\treject(error);\n\t\t\t\t\t\treturn;\n\t\t\t\t\t}\n\n\t\t\t\t\tresolve(leadingValue);\n\t\t\t\t\treturn leadingValue;\n\t\t\t\t})()",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/block@1839",
      "conditions": [
        "if shouldCallNow"
      ],
      "kind": "write",
      "operator": "=",
      "references": [
        "leadingCall"
      ],
      "rhs_callee": "",
      "rhs_kind": "CallExpression",
      "statement": 0,
      "target": "leadingCall",
      "value_references": []
    }
  }
]
```

### L0008

```json
[
  {
    "source": "options.signal && promiseHandlers.length === 1",
    "syntax": {
      "block": "<module>/pDebounce/<callback>/<callback>/block@2317",
      "conditions": [
        "else of shouldCallNow"
      ],
      "expression": "options.signal && promiseHandlers.length === 1",
      "kind": "guard",
      "references": [
        "options.signal",
        "promiseHandlers.length"
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
    "source": "timeout = undefined",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/block@835",
      "conditions": [],
      "kind": "write",
      "operator": "=",
      "references": [
        "timeout",
        "undefined"
      ],
      "rhs_callee": "",
      "rhs_kind": "Identifier",
      "statement": 0,
      "target": "timeout",
      "value_references": [
        "undefined"
      ]
    }
  }
]
```

### L0010

```json
[
  {
    "source": "currentHandlers = promiseHandlers",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/block@835",
      "conditions": [],
      "kind": "write",
      "operator": "=",
      "references": [
        "currentHandlers",
        "promiseHandlers"
      ],
      "rhs_callee": "",
      "rhs_kind": "Identifier",
      "statement": 1,
      "target": "currentHandlers",
      "value_references": [
        "promiseHandlers"
      ]
    }
  }
]
```

### L0011

```json
[
  {
    "source": "promiseHandlers = []",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/block@835",
      "conditions": [],
      "kind": "write",
      "operator": "=",
      "references": [
        "promiseHandlers"
      ],
      "rhs_callee": "",
      "rhs_kind": "ArrayExpression",
      "statement": 2,
      "target": "promiseHandlers",
      "value_references": []
    }
  }
]
```

### L0012

```json
[
  {
    "source": "options.signal?.removeEventListener('abort', onAbort)",
    "syntax": {
      "argument_references": [
        [],
        [
          "onAbort"
        ]
      ],
      "arguments": [
        "'abort'",
        "onAbort"
      ],
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/block@835",
      "callee": "options.signal.removeEventListener",
      "conditions": [],
      "construct": false,
      "kind": "call",
      "optional": true,
      "receiver": "options.signal",
      "references": [
        "options.signal.removeEventListener",
        "onAbort"
      ],
      "statement": 3
    }
  }
]
```

### L0013

```json
[
  {
    "source": "currentLeadingCall = leadingCall",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/block@835",
      "conditions": [],
      "kind": "write",
      "operator": "=",
      "references": [
        "currentLeadingCall",
        "leadingCall"
      ],
      "rhs_callee": "",
      "rhs_kind": "Identifier",
      "statement": 4,
      "target": "currentLeadingCall",
      "value_references": [
        "leadingCall"
      ]
    }
  }
]
```

### L0014

```json
[
  {
    "source": "leadingCall = undefined",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/block@835",
      "conditions": [],
      "kind": "write",
      "operator": "=",
      "references": [
        "leadingCall",
        "undefined"
      ],
      "rhs_callee": "",
      "rhs_kind": "Identifier",
      "statement": 5,
      "target": "leadingCall",
      "value_references": [
        "undefined"
      ]
    }
  }
]
```

### L0015

```json
[
  {
    "source": "result = options.before ? await currentLeadingCall : await functionToDebounce.apply(this, arguments_)",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/block@1369",
      "conditions": [],
      "kind": "write",
      "operator": "=",
      "references": [
        "result",
        "options.before",
        "currentLeadingCall",
        "functionToDebounce.apply",
        "this",
        "arguments_"
      ],
      "rhs_callee": "",
      "rhs_kind": "ConditionalExpression",
      "statement": 0,
      "target": "result",
      "value_references": [
        "options.before",
        "currentLeadingCall",
        "functionToDebounce.apply",
        "this",
        "arguments_"
      ]
    }
  }
]
```

### L0016

```json
[
  {
    "source": "await currentLeadingCall",
    "syntax": {
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/conditional@1478",
      "conditions": [
        "conditional expression options.before"
      ],
      "kind": "await",
      "statement": 0
    }
  }
]
```

### L0017

```json
[
  {
    "source": "await functionToDebounce.apply(this, arguments_)",
    "syntax": {
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/conditional@1478/else",
      "conditions": [
        "conditional expression options.before"
      ],
      "kind": "await",
      "statement": 0
    }
  }
]
```

### L0018

```json
[
  {
    "source": "{resolve: resolveFunction}",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/control@1578",
      "conditions": [
        "ForOfStatement path; execution/repetition not proven"
      ],
      "kind": "write",
      "operator": "=",
      "references": [
        "resolveFunction"
      ],
      "rhs_callee": "",
      "rhs_kind": null,
      "statement": 1,
      "target": "{resolve: resolveFunction}",
      "value_references": []
    }
  }
]
```

### L0019

```json
[
  {
    "source": "{reject: rejectFunction}",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/control@1703",
      "conditions": [
        "catch path",
        "ForOfStatement path; execution/repetition not proven"
      ],
      "kind": "write",
      "operator": "=",
      "references": [
        "rejectFunction"
      ],
      "rhs_callee": "",
      "rhs_kind": null,
      "statement": 0,
      "target": "{reject: rejectFunction}",
      "value_references": []
    }
  }
]
```

### L0020

```json
[
  {
    "source": "leadingValue",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>#2/block@2069",
      "conditions": [],
      "kind": "write",
      "operator": "=",
      "references": [
        "leadingValue"
      ],
      "rhs_callee": "",
      "rhs_kind": null,
      "statement": 0,
      "target": "leadingValue",
      "value_references": []
    }
  }
]
```

### L0021

```json
[
  {
    "source": "leadingValue = await functionToDebounce.apply(this, arguments_)",
    "syntax": {
      "awaited": true,
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>#2/block@2104",
      "conditions": [],
      "kind": "write",
      "operator": "=",
      "references": [
        "leadingValue",
        "functionToDebounce.apply",
        "this",
        "arguments_"
      ],
      "rhs_callee": "functionToDebounce.apply",
      "rhs_kind": "AwaitExpression",
      "statement": 0,
      "target": "leadingValue",
      "value_references": [
        "functionToDebounce.apply",
        "this",
        "arguments_"
      ]
    }
  }
]
```

### L0022

```json
[
  {
    "source": "await functionToDebounce.apply(this, arguments_)",
    "syntax": {
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>#2/block@2104",
      "conditions": [],
      "kind": "await",
      "statement": 0
    }
  }
]
```

### L0023

```json
[
  {
    "source": "() => ",
    "syntax": {
      "block": "<module>/pDebounce/block@62",
      "conditions": [],
      "kind": "function_definition",
      "name": "onAbort",
      "statement": 4
    }
  }
]
```

### L0024

```json
[
  {
    "source": "clearTimeout(timeout)",
    "syntax": {
      "argument_references": [
        [
          "timeout"
        ]
      ],
      "arguments": [
        "timeout"
      ],
      "block": "<module>/pDebounce/onAbort/block@283",
      "callee": "clearTimeout",
      "conditions": [],
      "construct": false,
      "kind": "call",
      "optional": false,
      "receiver": "",
      "references": [
        "clearTimeout",
        "timeout"
      ],
      "statement": 0
    }
  }
]
```

### L0025

```json
[
  {
    "source": "timeout = undefined",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/onAbort/block@283",
      "conditions": [],
      "kind": "write",
      "operator": "=",
      "references": [
        "timeout",
        "undefined"
      ],
      "rhs_callee": "",
      "rhs_kind": "Identifier",
      "statement": 1,
      "target": "timeout",
      "value_references": [
        "undefined"
      ]
    }
  }
]
```

### L0026

```json
[
  {
    "source": "{reject}",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/onAbort/control@402",
      "conditions": [
        "catch path",
        "ForOfStatement path; execution/repetition not proven"
      ],
      "kind": "write",
      "operator": "=",
      "references": [
        "reject"
      ],
      "rhs_callee": "",
      "rhs_kind": null,
      "statement": 0,
      "target": "{reject}",
      "value_references": []
    }
  }
]
```

### L0027

```json
[
  {
    "source": "promiseHandlers = []",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/onAbort/block@397",
      "conditions": [
        "catch path"
      ],
      "kind": "write",
      "operator": "=",
      "references": [
        "promiseHandlers"
      ],
      "rhs_callee": "",
      "rhs_kind": "ArrayExpression",
      "statement": 1,
      "target": "promiseHandlers",
      "value_references": []
    }
  }
]
```

## Limited relations between selected locations/scopes

```json
[
  {
    "after": "L0004",
    "before": "L0005",
    "kind": "rhs_before_assignment",
    "qualification": "Assignment follows successful RHS evaluation; asynchronous completion is not established."
  }
]
```

## Heuristic interpretations and review questions

The following text is rule-authored guidance, not a defect verdict or an oracle.

```json
{
  "classification": "heuristic_review_hint",
  "condition": "仅表示同一词法函数/类命名空间中的语法共现；名称不保证 API 类型，未证明属于同一请求、实例或生命周期，也未证明回调可达、重试循环或保护充分。",
  "interpretation": "完成回调/等待点与调度、retry 或 poll 名称调用出现在同一词法单元。",
  "locations": [
    "L0005",
    "L0016",
    "L0017",
    "L0022"
  ],
  "review_question": "这些调度是否继续同一工作？结束、取消或切换后，仍可能登记或触发下一次吗？",
  "rule": "continuation-retry-scheduling"
}
```

```json
{
  "classification": "heuristic_review_hint",
  "condition": "仅表示同一词法函数/类命名空间中的语法共现；名称不保证 API 类型，未证明属于同一请求、实例或生命周期，也未证明回调可达、重试循环或保护充分。",
  "interpretation": "完成回调/等待点与关闭、重新打开或清理边界名称线索出现在同一词法单元。",
  "locations": [
    "L0003",
    "L0012",
    "L0016",
    "L0017",
    "L0022",
    "L0023",
    "L0024"
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
    "L0001",
    "L0002",
    "L0003",
    "L0004",
    "L0006",
    "L0007",
    "L0008",
    "L0009",
    "L0010",
    "L0011",
    "L0012",
    "L0013",
    "L0014",
    "L0015",
    "L0016",
    "L0017",
    "L0018",
    "L0019",
    "L0020",
    "L0021",
    "L0022",
    "L0023",
    "L0024",
    "L0025",
    "L0026",
    "L0027"
  ],
  "review_question": "回调检查了什么状态？关闭、卸载、重开分别更新了什么？只取消计时器能否约束已发请求？相同标识重新使用时判断是否仍适用？",
  "rule": "continuation-guard-state-review"
}
```
