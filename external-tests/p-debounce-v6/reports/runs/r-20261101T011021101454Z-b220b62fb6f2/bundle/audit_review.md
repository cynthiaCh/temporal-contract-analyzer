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
      "column": 4,
      "line": 125
    },
    "id": "L0001",
    "path": "index.js",
    "scope": "<module>/<callback>/run",
    "start": {
      "column": 10,
      "line": 116
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 27,
      "line": 2
    },
    "id": "L0002",
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
      "column": 25,
      "line": 7
    },
    "id": "L0003",
    "path": "index.js",
    "scope": "<module>/pDebounce",
    "start": {
      "column": 5,
      "line": 7
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 30,
      "line": 32
    },
    "id": "L0004",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>",
    "start": {
      "column": 7,
      "line": 32
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 51,
      "line": 37
    },
    "id": "L0005",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>",
    "start": {
      "column": 9,
      "line": 37
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 24,
      "line": 39
    },
    "id": "L0006",
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
      "line": 69
    },
    "id": "L0007",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>",
    "start": {
      "column": 3,
      "line": 41
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 11,
      "line": 69
    },
    "id": "L0008",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>",
    "start": {
      "column": 13,
      "line": 41
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 20,
      "line": 71
    },
    "id": "L0009",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>",
    "start": {
      "column": 7,
      "line": 71
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 74,
      "line": 74
    },
    "id": "L0010",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>",
    "start": {
      "column": 10,
      "line": 74
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 25,
      "line": 77
    },
    "id": "L0011",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>",
    "start": {
      "column": 4,
      "line": 77
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 54,
      "line": 97
    },
    "id": "L0012",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>",
    "start": {
      "column": 8,
      "line": 97
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 23,
      "line": 42
    },
    "id": "L0013",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 4,
      "line": 42
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 43,
      "line": 45
    },
    "id": "L0014",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 10,
      "line": 45
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 24,
      "line": 48
    },
    "id": "L0015",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 4,
      "line": 48
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 57,
      "line": 51
    },
    "id": "L0016",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 4,
      "line": 51
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 42,
      "line": 54
    },
    "id": "L0017",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 10,
      "line": 54
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 27,
      "line": 55
    },
    "id": "L0018",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 4,
      "line": 55
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 112,
      "line": 59
    },
    "id": "L0019",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 11,
      "line": 59
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 61,
      "line": 59
    },
    "id": "L0020",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 37,
      "line": 59
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 112,
      "line": 59
    },
    "id": "L0021",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 64,
      "line": 59
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 42,
      "line": 61
    },
    "id": "L0022",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 16,
      "line": 61
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 40,
      "line": 65
    },
    "id": "L0023",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>",
    "start": {
      "column": 16,
      "line": 65
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 21,
      "line": 80
    },
    "id": "L0024",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>#2",
    "start": {
      "column": 9,
      "line": 80
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 69,
      "line": 83
    },
    "id": "L0025",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>#2",
    "start": {
      "column": 6,
      "line": 83
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 69,
      "line": 83
    },
    "id": "L0026",
    "path": "index.js",
    "scope": "<module>/pDebounce/<callback>/<callback>/<callback>#2",
    "start": {
      "column": 21,
      "line": 83
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 23,
      "line": 15
    },
    "id": "L0027",
    "path": "index.js",
    "scope": "<module>/pDebounce/onAbort",
    "start": {
      "column": 17,
      "line": 15
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 23,
      "line": 16
    },
    "id": "L0028",
    "path": "index.js",
    "scope": "<module>/pDebounce/onAbort",
    "start": {
      "column": 2,
      "line": 16
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 21,
      "line": 17
    },
    "id": "L0029",
    "path": "index.js",
    "scope": "<module>/pDebounce/onAbort",
    "start": {
      "column": 2,
      "line": 17
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 25,
      "line": 20
    },
    "id": "L0030",
    "path": "index.js",
    "scope": "<module>/pDebounce/onAbort",
    "start": {
      "column": 2,
      "line": 20
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 21,
      "line": 22
    },
    "id": "L0031",
    "path": "index.js",
    "scope": "<module>/pDebounce/onAbort",
    "start": {
      "column": 13,
      "line": 22
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 22,
      "line": 26
    },
    "id": "L0032",
    "path": "index.js",
    "scope": "<module>/pDebounce/onAbort",
    "start": {
      "column": 2,
      "line": 26
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
    "source": "(async () => function_.apply(context, arguments_))().finally(() => {\n\t\t\t// Stay busy while the queued call runs, so calls never overlap, but settle this call's callers right away instead of after the whole queue.\n\t\t\tif (queuedCall) {\n\t\t\t\tconst call = queuedCall;\n\t\t\t\tqueuedCall = undefined;\n\t\t\t\tcall.resolve(run(call.context, call.arguments));\n\t\t\t} else {\n\t\t\t\tcurrentPromise = undefined;\n\t\t\t}\n\t\t})",
    "syntax": {
      "argument_references": [
        []
      ],
      "arguments": [
        "() => {\n\t\t\t// Stay busy while the queued call runs, so calls never overlap, but settle this call's callers right away instead of after the whole queue.\n\t\t\tif (queuedCall) {\n\t\t\t\tconst call = queuedCall;\n\t\t\t\tqueuedCall = undefined;\n\t\t\t\tcall.resolve(run(call.context, call.arguments));\n\t\t\t} else {\n\t\t\t\tcurrentPromise = undefined;\n\t\t\t}\n\t\t}"
      ],
      "block": "<module>/<callback>/run/block@3125",
      "callee": ".finally",
      "conditions": [],
      "construct": false,
      "kind": "call",
      "optional": false,
      "receiver": "",
      "references": [],
      "statement": 2
    }
  }
]
```

### L0002

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

### L0003

```json
[
  {
    "source": "wait > 2_147_483_647",
    "syntax": {
      "block": "<module>/pDebounce/block@62",
      "conditions": [],
      "expression": "wait > 2_147_483_647",
      "kind": "guard",
      "references": [
        "wait"
      ],
      "statement": 1
    }
  }
]
```

### L0004

```json
[
  {
    "source": "options.signal?.aborted",
    "syntax": {
      "block": "<module>/pDebounce/<callback>/<callback>/block@769",
      "conditions": [],
      "expression": "options.signal?.aborted",
      "kind": "guard",
      "references": [
        "options.signal.aborted"
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
    "source": "shouldCallNow = options.before && !timeout",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/block@769",
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

### L0006

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
      "block": "<module>/pDebounce/<callback>/<callback>/block@769",
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

### L0007

```json
[
  {
    "source": "timeout = setTimeout(async () => {\n\t\t\t\ttimeout = undefined;\n\n\t\t\t\t// Capture the current handlers for this execution\n\t\t\t\tconst currentHandlers = promiseHandlers;\n\n\t\t\t\t// Clear handlers for next cycle (new calls during execution will add to new list)\n\t\t\t\tpromiseHandlers = [];\n\n\t\t\t\t// Remove abort listener\n\t\t\t\toptions.signal?.removeEventListener('abort', onAbort);\n\n\t\t\t\t// Capture this window's leading call before a new window can replace it, and clear it so its value is not retained\n\t\t\t\tconst currentLeadingCall = leadingCall;\n\t\t\t\tleadingCall = undefined;\n\n\t\t\t\ttry {\n\t\t\t\t\t// The leading call can still be pending when the function is slower than `wait`.\n\t\t\t\t\tconst result = options.before ? await currentLeadingCall : await functionToDebounce.apply(this, arguments_);\n\n\t\t\t\t\tfor (const {resolve: resolveFunction} of currentHandlers) {\n\t\t\t\t\t\tresolveFunction(result);\n\t\t\t\t\t}\n\t\t\t\t} catch (error) {\n\t\t\t\t\tfor (const {reject: rejectFunction} of currentHandlers) {\n\t\t\t\t\t\trejectFunction(error);\n\t\t\t\t\t}\n\t\t\t\t}\n\t\t\t}, wait)",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/block@769",
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

### L0008

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
      "block": "<module>/pDebounce/<callback>/<callback>/block@769",
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

### L0009

```json
[
  {
    "source": "shouldCallNow",
    "syntax": {
      "block": "<module>/pDebounce/<callback>/<callback>/block@769",
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

### L0010

```json
[
  {
    "source": "{promise, resolve: resolveLeadingCall} = Promise.withResolvers()",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/block@2010",
      "conditions": [
        "if shouldCallNow"
      ],
      "kind": "write",
      "operator": "=",
      "references": [
        "promise",
        "resolveLeadingCall",
        "Promise.withResolvers"
      ],
      "rhs_callee": "Promise.withResolvers",
      "rhs_kind": "CallExpression",
      "statement": 0,
      "target": "{promise, resolve: resolveLeadingCall}",
      "value_references": [
        "Promise.withResolvers"
      ]
    }
  }
]
```

### L0011

```json
[
  {
    "source": "leadingCall = promise",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/block@2010",
      "conditions": [
        "if shouldCallNow"
      ],
      "kind": "write",
      "operator": "=",
      "references": [
        "leadingCall",
        "promise"
      ],
      "rhs_callee": "",
      "rhs_kind": "Identifier",
      "statement": 1,
      "target": "leadingCall",
      "value_references": [
        "promise"
      ]
    }
  }
]
```

### L0012

```json
[
  {
    "source": "options.signal && promiseHandlers.length === 1",
    "syntax": {
      "block": "<module>/pDebounce/<callback>/<callback>/block@2701",
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

### L0013

```json
[
  {
    "source": "timeout = undefined",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/block@1006",
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

### L0014

```json
[
  {
    "source": "currentHandlers = promiseHandlers",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/block@1006",
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

### L0015

```json
[
  {
    "source": "promiseHandlers = []",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/block@1006",
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

### L0016

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
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/block@1006",
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

### L0017

```json
[
  {
    "source": "currentLeadingCall = leadingCall",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/block@1006",
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

### L0018

```json
[
  {
    "source": "leadingCall = undefined",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/block@1006",
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

### L0019

```json
[
  {
    "source": "result = options.before ? await currentLeadingCall : await functionToDebounce.apply(this, arguments_)",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/block@1540",
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

### L0020

```json
[
  {
    "source": "await currentLeadingCall",
    "syntax": {
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/conditional@1649",
      "conditions": [
        "conditional expression options.before"
      ],
      "kind": "await",
      "statement": 0
    }
  }
]
```

### L0021

```json
[
  {
    "source": "await functionToDebounce.apply(this, arguments_)",
    "syntax": {
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/conditional@1649/else",
      "conditions": [
        "conditional expression options.before"
      ],
      "kind": "await",
      "statement": 0
    }
  }
]
```

### L0022

```json
[
  {
    "source": "{resolve: resolveFunction}",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/control@1749",
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

### L0023

```json
[
  {
    "source": "{reject: rejectFunction}",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>/control@1874",
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

### L0024

```json
[
  {
    "source": "leadingValue",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>#2/block@2452",
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

### L0025

```json
[
  {
    "source": "leadingValue = await functionToDebounce.apply(this, arguments_)",
    "syntax": {
      "awaited": true,
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>#2/block@2487",
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

### L0026

```json
[
  {
    "source": "await functionToDebounce.apply(this, arguments_)",
    "syntax": {
      "block": "<module>/pDebounce/<callback>/<callback>/<callback>#2/block@2487",
      "conditions": [],
      "kind": "await",
      "statement": 0
    }
  }
]
```

### L0027

```json
[
  {
    "source": "() => ",
    "syntax": {
      "block": "<module>/pDebounce/block@62",
      "conditions": [],
      "kind": "function_definition",
      "name": "onAbort",
      "statement": 5
    }
  }
]
```

### L0028

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
      "block": "<module>/pDebounce/onAbort/block@443",
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

### L0029

```json
[
  {
    "source": "timeout = undefined",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/onAbort/block@443",
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

### L0030

```json
[
  {
    "source": "leadingCall = undefined",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/onAbort/block@443",
      "conditions": [],
      "kind": "write",
      "operator": "=",
      "references": [
        "leadingCall",
        "undefined"
      ],
      "rhs_callee": "",
      "rhs_kind": "Identifier",
      "statement": 2,
      "target": "leadingCall",
      "value_references": [
        "undefined"
      ]
    }
  }
]
```

### L0031

```json
[
  {
    "source": "{reject}",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/onAbort/control@582",
      "conditions": [
        "ForOfStatement path; execution/repetition not proven"
      ],
      "kind": "write",
      "operator": "=",
      "references": [
        "reject"
      ],
      "rhs_callee": "",
      "rhs_kind": null,
      "statement": 3,
      "target": "{reject}",
      "value_references": []
    }
  }
]
```

### L0032

```json
[
  {
    "source": "promiseHandlers = []",
    "syntax": {
      "awaited": false,
      "block": "<module>/pDebounce/onAbort/block@443",
      "conditions": [],
      "kind": "write",
      "operator": "=",
      "references": [
        "promiseHandlers"
      ],
      "rhs_callee": "",
      "rhs_kind": "ArrayExpression",
      "statement": 4,
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
    "after": "L0007",
    "before": "L0008",
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
  "condition": "仅是共现线索；需追踪是否属于同一工作、同一生命周期。",
  "interpretation": "同一文件中同时存在完成回调登记和监听移除。",
  "locations": [
    "L0001",
    "L0016"
  ],
  "review_question": "若二者相关，移除监听后，已开始的工作完成时是否还有有效性检查？",
  "rule": "continuation-and-listener-removal"
}
```

```json
{
  "classification": "heuristic_review_hint",
  "condition": "仅表示同一词法函数/类命名空间中的语法共现；名称不保证 API 类型，未证明属于同一请求、实例或生命周期，也未证明回调可达、重试循环或保护充分。",
  "interpretation": "完成回调/等待点与调度、retry 或 poll 名称调用出现在同一词法单元。",
  "locations": [
    "L0008",
    "L0020",
    "L0021",
    "L0026"
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
    "L0006",
    "L0016",
    "L0020",
    "L0021",
    "L0026",
    "L0027",
    "L0028"
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
    "L0002",
    "L0003",
    "L0004",
    "L0005",
    "L0006",
    "L0007",
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
    "L0027",
    "L0028",
    "L0029",
    "L0030",
    "L0031",
    "L0032"
  ],
  "review_question": "回调检查了什么状态？关闭、卸载、重开分别更新了什么？只取消计时器能否约束已发请求？相同标识重新使用时判断是否仍适用？",
  "rule": "continuation-guard-state-review"
}
```
