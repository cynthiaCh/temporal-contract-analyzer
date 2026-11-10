# Unified research experience memory v1

The offline spine and all four MUST rung checks pass. The CLI/API supports
immutable structured rule bundles, exact provenance copies, deterministic
Markdown, version lineage, BM25 discovery, source-bound seven-label delivery and
memory snapshot checks. There are no live stubs, dependencies, model calls,
experiment launches, commits, global configuration or production-registry edits.

The shared store contains three historical English bundles and 19 rules:
subscription retirement (T1, 7), paused shared work (T4, 6), and deferred boundary
binding (T3, 6). Original bodies, applicability and source files were checked
unchanged. The two translations retain their unvalidated-effect limitations. The
recent T3 batch's stop and missing test maintenance remain historical facts.

Search returns whole bundles with review/taxonomy status. Search text excludes
audit identity, source paths and outcomes. Delivery independently reuses the
current source-bound router, returns zero or one body, verifies the selected entry
by digest, and falls back on unknowns, exclusions or unresolved conflicts.

The initial records retain the legacy four-class taxonomy. They can be searched
and inspected but cannot automatically drive the current seven-label router.
There are zero recoded native records. Native successful delivery was exercised
with explicitly synthetic fixtures, not a new real-case repair experiment. The
library is not yet wired into existing experiment/workbench prompts.

## Verification

- New memory suite: 17 tests passed, including exact import, evidence IDs/pointers,
  incomplete records, source/body tampering, unknown and contradictory premises,
  exclusions, conflicts, selected-entry identity, metadata isolation, immutable
  lineage, snapshot drift and CLI no-overwrite behavior.
- Existing taxonomy/routing suite: 14 tests passed.
- Existing workbench suite: 13 tests run, 6 failed; the exact same failing test
  names reproduced on the unmodified base HEAD in a temporary extracted checkout.
  The reported scoring blocker is an unavailable minimum-version Python runtime;
  default Python is 3.8.10. No evaluator, test or environment workaround was added.
- Import source hashes and rendered-body hashes checked; three lexical discovery
  smoke queries ran. These do not establish retrieval quality or repair benefit.

Raw logs and comparison are in `VALIDATION.json` and adjacent `.log` files.

## Semantic assumptions and review limits

The research-only scope (A-003/A-004) retains three reviewed historical versions,
their translation limitations and taxonomy without treating import as learning.
Search/admission separation (A-005/A-009/A-013) allows inspection of candidate and
rejected knowledge but requires recorded research admission plus a source-bound
query review for delivery. Pointer/hash validity does not prove semantic support.

The conflict policy (A-006) uses conservative AUTO fallback rather than selecting
the best lexical score. The version policy (A-007) uses lineage tips; candidate or
rejected children do not silently reactivate a parent. These are explicit research
defaults, not established optimal retrieval or evolution policies.

The ledger records all choices, including two discovered late in executor
inspection. No extra model judge was invoked. Fresh assumption sweep status is
`SWEEP_UNAVAILABLE`; executor-only inspection is not independent approval.

## Next bounded work

Agree on and fixture-test the representation with additional archived records.
If native seven-label use is wanted, explicitly recode selected legacy entries
against their evidence as new reviewed versions. Then evaluate retrieval and
prompt composition separately under a frozen protocol. No automatic evolution,
recoding or experiments follow this implementation.
