# Build ladder

| Rung | Scope | Acceptance | Status |
|---|---|---|---|
| F0 | Explicit expert activation and active-only retrieval | Expert gate tests | passed |
| F1 | Frozen snapshots and candidate-independent active parent | Memory and approval tests | passed |
| F2 | Bounded development/reflection/validation controller | Synthetic end-to-end loop | passed |
| F3 | Expert report, revision and frozen evaluation | Synthetic review/evaluation tests | passed |
| F4 | Explicit native adapter, CLI and docs | Offline adapter/CLI and accumulated tests | passed |

No model calls or commits. No extra model reviewer; executor inspection and
deterministic checks will not be described as independent expert approval.

## Run record

F0/F1 were executed before the controller: 5 initial expert checks and 17 memory
checks passed. F2/F3 first ran nine synthetic lifecycle checks successfully;
additional regression and CLI checks expanded these to eleven. F4 checks the
native bridge using a fake process, plus the real trusted scorer on synthetic
fixtures and reused raw calibration. It makes no model connection.

Final accumulated suite: 60 passing checks (17 memory, 6 approval, 11 lifecycle,
4 native bridge/scorer, 14 existing taxonomy/routing, 8 reused archival/runtime).
The reused runtime checks use their existing offline fake CLI mechanism.

The final bookkeeping assertion caught an incorrectly hand-summed total of 70.
The suite logs and `VALIDATION.json` consistently total 60; the report was
corrected without changing any test or experiment result.

A calibration inspection found the high-level evaluator repeats reference
calibration. The adapter now uses its unchanged single-score invocation function
with pinned raw calibration evidence. Runtime errors are rejected as calibration
failures rather than credited as credible degenerate behavior failures.

The synthetic HTML preview in `offline-demo/` is a saved interface demonstration,
not a live campaign or real expert decision. Its candidate remains unactivated.
It was generated during implementation; code fingerprint checks intentionally
prevent executing an old prepared fixture after implementation changes.

## Deferred and limitations

No paid/native model run, real case repair or real expert review was performed.
Native dispatch still requires valid runtime, credentials, executable versions
and real calibration evidence. The default environment's Python 3.8 must not be
silently accepted for cases declaring a newer minimum. Source-only analyses and
their genuine reviews are supplied, not automatically blessed by this controller.

New case selection/preparation remains explicit. No learned ranking, taxonomy
recoding, class-prompt evolution, legacy scheduler restart or old Web workflow
replacement is included. There are no remaining execution stubs; synthetic
adapters exist only in tests and the explicitly labeled demo.

## Assumption review

Executor inspection only, not an independent model/human audit. All consequential
choices are in `ASSUMPTIONS.md`; no external approval is inferred from passing
checks. A fresh-model sweep is not performed under the no-extra-judge scope.
