# Build note

| Rung | Feature | Acceptance command | Tier | Status |
| --- | --- | --- | --- | --- |
| F0 | Real CLI loads two callable modules, generates repeat scenario, writes observations | `python3 -B -m unittest discover -s tests -p test_behavior_probe.py -k spine` | MUST | passed |
| F1 | Generic reentry, overlap, failure/retry and emitter mutation scenario generation | `python3 -B -m unittest discover -s tests -p test_behavior_probe.py -k generation` | MUST | passed |
| F2 | Contract-aware comparison, error boundaries and replayable scenario artifacts | `python3 -B -m unittest discover -s tests -p test_behavior_probe.py` | MUST | passed |
| F3 | Declarative campaign on existing upstream pairs and controls | `python3 external-tests/behavior-probe-feasibility-v1/run.py --output external-tests/behavior-probe-feasibility-v1/run-02` | MUST | passed |

## Run record

No rung commits: user requested prepared commit text only.

- F0: command exited 0, one test passed. Real candidate callback executed twice per side and a smoke artifact was written in an isolated temporary directory. Assessment explicitly pending; no fabricated result.
- F1: accumulated scoped command exited 0, three tests passed. Shared scenario generation and real synchronous reentry observed; no contract judgement yet. No candidate-name branches were added.
- F2: nine scoped tests passed before campaign. Includes observation-only versus explicit contract, correct post-compute cache, method/export bindings, setup failure and timeout. Ordinary emitter/completion baseline checks were subsequently made explicit and the accumulated suite is rerun before F3.
- F3: run-01 completed, then a source-frame path-normalization correction removed macOS's /private alias prefix. No scenario or contract changed. Final run-02 completed with the same observations: 10 plans, 57 scenarios/114 side executions, no inconclusive outcomes. Eight generated scenes distinguish a declared pre-fix failure from a passing post-fix scene across five known upstream issue pairs. One additional two-once-listener scene fails on both historical eventemitter3 versions; retained and separately confirmed. Five passing control plans (four implementations, including ordinary/strict once) have no violated requirements or same-version behavior differences.
- Final scoped suite: nine tests passed, including reversed and persistent contract transitions. No new dependencies, static-rule edits or commits. No live stubs remain.
- Fresh silent-assumption sweep: SWEEP_UNAVAILABLE because the canonical reviewer-route helper is not installed. Unknown undeclared count; not a positive or provisional review. Draft assurance does not convert this into a semantic claim.

## Deferred

Natural-language contract inference, arbitrary API discovery, LLM comparison, fresh held-out campaign, UI/MCP integration and publication-level claims.

## Blockers

No deterministic build blocker. Missing review helper limits assurance; natural-language contract inference and unseen effectiveness remain unverified.
