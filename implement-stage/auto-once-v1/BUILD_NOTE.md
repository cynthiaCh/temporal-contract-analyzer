# Build note

| Rung | Feature | Check | Tier | Status |
| --- | --- | --- | --- | --- |
| F0 | CLI paths → non-executing artifact | CLI smoke, exclusive output | MUST | passed |
| F1 | Syntax-only wrapper binding | scoped discovery tests | MUST | passed |
| F2 | Confirmed paired reentry and replay | scoped integration tests | MUST | passed |
| F3 | Frozen new-repository and baseline comparison | external migration audit | MUST | passed; development revalidation after sweep |

## Run record

- F0: auto_once CLI on existing emitter source produced F0-smoke.json, exit 0. This historical artifact explicitly marks discovery_not_implemented; the live placeholder was retired in F1.
- F1: first discovery suite exit 1 (arrow-expression body handled as a statement array). Fixed body-kind handling; 3 tests passed, exit 0. No external source had been selected/executed.
- F2: 6 scoped tests passed, exit 0: syntax/refusal, no unconfirmed subject execution, paired late/early synthetic guard behavior, generated replay, inconclusive setup, bounded correct control, existing-output refusal. Existing probe suite 9/9 passed.
- F3: engines frozen before selecting 3rd-Eden/one-time. Four fixed cases include a dependency failure, upstream behavior-preserving refactor, control, and explicitly artificial regression. First measurement run stopped on comparing temporary paths in inconclusive errors; retained run-01. Corrected measurement-only comparison for run-02; frozen engines unchanged.
- Sweep round 1: fresh native requested gpt-6-astra/xhigh; exact returned model not exposed, same-family provisional. Five undeclared decisions (2 semantic) and stale A3. Added A8-A11, corrected A3, and added adapter validity checks for construction callbacks plus explicit reentry_attempted. Added two targeted tests (8 total). Original freeze retained as FROZEN-pre-sweep.json, new frozen version revalidated on same sources as run-03; not a new holdout. No live stubs.
- Sweep round 2: prior findings declared consistently; one additional semantic input convention found. Added A12: outer input is 0, nested input follows the callback's first received value. This is a documentation clarification of the unchanged runner, checked by executor against runner.mjs:52-55,69-71. Two-round budget exhausted; no further sweep. Last reviewer verdict remains gaps (semantic_undeclared=1 at review time), not clean; post-review documentation is executor-verified only. Review independence: same-family; acceptance: provisional with documented last-round finding, never independent acquittal. Requested route was host-default codex/native gpt-6-astra/xhigh, actual exact model identity unavailable; agent /root/auto_once_assumption_sweep.

## Deferred

Emitter discovery, arbitrary exports, dependency inference, natural-language contract discovery and human productivity claims.

## Blockers

No Git commits are created: user authorization is required for commits and overrides the skill's rung-commit instruction.
