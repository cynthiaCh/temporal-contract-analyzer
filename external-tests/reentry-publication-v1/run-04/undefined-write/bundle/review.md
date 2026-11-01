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
      "assigned_names": [
        "occupied"
      ],
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
      ],
      "write_roots": [
        "occupied"
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

## Heuristic interpretations and review questions

The following text is rule-authored guidance, not a defect verdict or an oracle.

```json
{
  "classification": "heuristic_review_hint",
  "condition": "Bounded JavaScript evaluation prefix on the selected normal path; direct IIFEs and unique local functions only. Callback reentry, runtime types, state value meaning, exceptions and full control flow are not proven. .call/.apply are invocation candidates; overridden methods remain unresolved.",
  "interpretation": "在进入用户函数之前，已对入口读取的闭包状态写入。",
  "locations": [
    "L0001",
    "L0002",
    "L0003"
  ],
  "review_question": "若该用户函数同步重入当前入口，状态是否已表示工作正在执行？调用前写入不等于保护充分；需核对写入值、清理和异常路径。可用立即重入测试检查执行次数、排队及拒绝结果。",
  "rule": "reentrant-state-publication",
  "state_publication": {
    "binding_scope": "<module>/make",
    "callback": "index.js::e7",
    "execution_path": [],
    "guard": "index.js::e4",
    "state": "occupied",
    "status": "write_before_call",
    "uncertainties": [],
    "write": "index.js::e6",
    "write_value": "undefined"
  }
}
```
