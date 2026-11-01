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
      "column": 111,
      "line": 1
    },
    "id": "L0002",
    "path": "index.js",
    "scope": "<module>/make/entry",
    "start": {
      "column": 96,
      "line": 1
    }
  },
  {
    "column_unit": "utf16_code_units",
    "end": {
      "column": 121,
      "line": 1
    },
    "id": "L0003",
    "path": "index.js",
    "scope": "<module>/make/entry",
    "start": {
      "column": 113,
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
    "source": "occupied = true",
    "syntax": {
      "assigned_names": [
        "occupied"
      ],
      "awaited": false,
      "block": "<module>/make/entry/then@86",
      "conditions": [
        "if flag"
      ],
      "declared_names": [],
      "kind": "write",
      "operator": "=",
      "references": [
        "occupied"
      ],
      "rhs_callee": "",
      "rhs_kind": "BooleanLiteral",
      "rhs_text": "true",
      "statement": 1,
      "target": "occupied",
      "value_references": [],
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
[]
```

## Heuristic interpretations and review questions

The following text is rule-authored guidance, not a defect verdict or an oracle.

```json
{
  "classification": "heuristic_review_hint",
  "condition": "Bounded JavaScript evaluation prefix on the selected normal path; direct IIFEs and unique local functions only. Callback reentry, runtime types, state value meaning, exceptions and full control flow are not proven. .call/.apply are invocation candidates; overridden methods remain unresolved.",
  "interpretation": "已定位入口状态读取和用户函数调用，当前同步前缀未建立对应写入关系。",
  "locations": [
    "L0001",
    "L0002",
    "L0003"
  ],
  "review_question": "若该用户函数同步重入当前入口，状态是否已表示工作正在执行？调用前写入不等于保护充分；需核对写入值、清理和异常路径。可用立即重入测试检查执行次数、排队及拒绝结果。",
  "rule": "reentrant-state-publication",
  "state_publication": {
    "binding_scope": "<module>/make",
    "callback": "index.js::e8",
    "execution_path": [],
    "guard": "index.js::e4",
    "state": "occupied",
    "status": "not_established",
    "uncertainties": [
      "conditional_state_write"
    ],
    "write": null,
    "write_value": null
  }
}
```
