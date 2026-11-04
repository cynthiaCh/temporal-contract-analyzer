# Assumption Ledger

ASK mode: never

| ID | Under-determined by the request | Chosen | Class | Source |
|---|---|---|---|---|
| A-001 | Control starts from base or previous patch? | Both arms start from the same immutable evaluated failed patch; D-only control measures another attempt from that patch, not a fresh-base rerun. | semantic | default |
| A-002 | What counts as same budget? | Inherit explicit model/effort overrides, sandbox/config route and per-job wall-clock timeout; one attempt per arm. Prompt/token counts may differ and are reported, not declared equal. Local-default parents inherit the current local config route, without pinning or proving historical resolved model/effort; the 11-pair matrix uses explicit overrides. | semantic | default |
| A-003 | Which feedback is disclosed? | Hypothesis arm receives failed effect identifiers/polarities and candidate explanations, never hidden expected payloads, test implementation or reference code. Feedback is development-only, not new public requirements. D control receives no feedback or parent answer. | semantic | default |
| A-004 | How to judge regression? | Compare explicit boolean observed effects using frozen required/forbidden rule sets and identical oracle provenance; missing/changed oracle fields make comparison unverified. Any loss of a prior passing check rejects automatic adoption; retain candidate evaluation separately. | semantic | user |
| A-005 | Which earlier runs are followed up? | Prior matrix's 11 original D failures, same source model/effort, one matched pair each. Original A/D and v1 retries remain untouched. | semantic | default |
| A-006 | How are causes generated and checked? | Deterministic feedback-to-source hypothesis construction with predicted event order and falsification steps; actual truth is unresolved until a source-backed reproducer is run. Unsupported relations and contract ambiguity remain explicit. | semantic | default |
| A-007 | Context/interface shape? | New `hypothesis_review` only via a dedicated retry-pair preparation API; keep v1 `learned_review` behavior. Source character budget 12000, relation depth 2, include reverse lexical callers and state-identifier evidence, label syntactic candidates. | interface | default |
| A-008 | How to preserve original passing behavior? | Continue saved patch in independent workspaces; both arms get the same instruction to preserve behavior. Research-side comparison checks prior passes after evaluation; only nonregressing candidates are eligible, without deleting failed attempts. | semantic | user |
| A-009 | How to treat already passing parent jobs? | Require a calibrated semantic failure to prepare the pair; reject successful, errored, timed-out or unverified parents. | interface | default |
| A-010 | How do existing browser services discover the new endpoint? | Advertise `hypothesis_repair=matched-patch-v2`; the launcher upgrades only idle older services and preserves active experiments. | interface | default |
| A-011 | What execution order is used? | Order the two arms by parent-ID last-digit parity, fixed and auditable but not randomized or guaranteed balanced; no statistical order-effect claim. | semantic | sweep |
