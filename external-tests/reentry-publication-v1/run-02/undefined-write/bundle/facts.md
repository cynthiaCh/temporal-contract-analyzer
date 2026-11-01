# Selected candidate-source locations

This list is selected by fixed tool rules, not a complete repository inventory.

```json
[
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 76,
      "line": 1
    },
    "id": "L0001",
    "path": "index.js",
    "scope": "<module>/make/entry",
    "start": {
      "column": 68,
      "line": 1
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 106,
      "line": 1
    },
    "id": "L0002",
    "path": "index.js",
    "scope": "<module>/make/entry",
    "start": {
      "column": 86,
      "line": 1
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 116,
      "line": 1
    },
    "id": "L0003",
    "path": "index.js",
    "scope": "<module>/make/entry",
    "start": {
      "column": 108,
      "line": 1
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
    "source": "occupied",
    "syntax": {
      "block": "<module>/make/entry/block@62",
      "conditions": [],
      "expression": "occupied",
      "kind": "guard",
      "references": [
        "occupied"
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
    "source": "occupied = undefined",
    "syntax": {
      "awaited": false,
      "block": "<module>/make/entry/block@62",
      "conditions": [],
      "declared_names": [],
      "kind": "write",
      "operator": "=",
      "references": [
        "occupied",
        "undefined"
      ],
      "rhs_callee": "",
      "rhs_kind": "Identifier",
      "rhs_text": "undefined",
      "statement": 1,
      "target": "occupied",
      "value_references": [
        "undefined"
      ]
    }
  }
]
```

### L0003

```json
[
  {
    "source": "invoke()",
    "syntax": {
      "argument_references": [],
      "arguments": [],
      "block": "<module>/make/entry/block@62",
      "callee": "invoke",
      "conditions": [],
      "construct": false,
      "kind": "call",
      "optional": false,
      "receiver": "",
      "references": [
        "invoke"
      ],
      "statement": 2
    }
  }
]
```

## Limited relations between selected locations/scopes

```json
[
  {
    "after": "L0003",
    "before": "L0002",
    "kind": "state_write_before_external_call",
    "qualification": "Bounded JS evaluation prefix: shared-state write before a candidate external call; value meaning and protection remain unproven."
  }
]
```
