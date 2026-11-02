# Assumption Ledger — temporal behavior probe

ASK mode: never. Effort: balanced. Assurance: draft.

| ID | Under-determined by request | Chosen | Class | Source |
| --- | --- | --- | --- | --- |
| A-001 | What counts as automatic generation? | Generate bounded scenario programs from reusable API profiles and declared contracts. Operator supplies API names/signatures, never test-function bodies. This tests template-based instantiation, not novel arbitrary test synthesis. | semantic | default |
| A-002 | Where do correctness expectations come from? | Explicit typed contracts grounded in existing docs/upstream fixes. Observation differences alone are never defects. | semantic | default |
| A-003 | What data demonstrates feasibility? | Reuse previously inspected cases, preserving independent runtime labels. These are development data, not unseen validation or general accuracy evidence. | semantic | default |
| A-004 | What is the baseline? | Ordinary sequential probes generated from the same API bindings, compared with additional reentry/overlap/failure probes. This is not a Codex/LLM baseline. | semantic | default |
| A-005 | Which API shapes? | Callable wrappers (once, memo, promise memo), event emitters, keyed completion registration. Declarative export path, construction style and method bindings. | interface | default |
| A-006 | How bounded is execution? | Fresh process per scenario and side; reentry at most once, finite scenario grid, per-process timeout. Timeouts/loader failures are inconclusive, not contract violations. No absence-of-bug verdict. | semantic | default |
| A-007 | Runtime and source preparation? | Existing Node, pinned existing fixture dependencies, existing type-only Flow eraser for legacy inputs, native TS erasure. No patching implementation behavior. | interface | default |
| A-008 | How is the output interpreted? | Report scenario-specific contract failures, transitions and reproducible source paths/traces. A fixed version passing tested contracts is not globally correct; additional failures are retained. | semantic | default |
| A-009 | Can the prototype execute candidate code? | Yes, only explicitly supplied local modules in isolated temporary processes. Temporary directories are for repeatability, not a security sandbox. | interface | default |
| A-010 | Which concrete values are valid? | Generated wrapper arguments are integers 0/1; event and request keys are fixed strings. Operators must confirm this input domain is valid for the bound API. No inference of arbitrary business inputs. | semantic | default |

## Notes

- A-001 is the key limit: API/contract information is manual input. A positive result cannot establish autonomous comprehension or novelty beyond existing test-generation methods.
- A-006 excludes arbitrary concurrency schedules and environment-dependent effects. Only callback-triggered reentry, repeated calls and observed promise settlement are modeled initially.
