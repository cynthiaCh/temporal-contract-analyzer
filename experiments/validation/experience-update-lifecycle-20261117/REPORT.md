# Experience update lifecycle

The compact-library adapter previously retained every accepted candidate in fresh
retrieval snapshots, including accepted revisions and merges. Current-guidance
resolution now supersedes sources only within unambiguous accepted lineages. New
publications bind exact source versions and review refuses stale replacements.
Historical ambiguous lineages remain available with explicit diagnostics.

The read-only audit of the existing library finds 73 accepted archive entries and
68 current retrieval entries. Five superseded source IDs leave fresh retrieval:
`cache-attempt-isolation`, `editor-submit-entry`, `logical-admission`,
`progress-admission-window`, `reentrant-ownership`.
There are 17 diagnostic issues affecting 26 retained IDs (overlapping branches and
missing targets). They are not silently resolved, merged or deleted. Source file
hashes, current IDs and all issues are in `audit.json`. The original library JSON,
reviewers and historical experimental snapshots are unchanged.

The training reflection search is now independent from the five-entry solver
selection: 16 full candidates plus a frozen-bank discovery catalog. New independent
guidance requires an increment and attempt evidence when existing candidates exist;
exact duplicates remain evidence-only. Preservation obligations must be retained or
explicitly accounted for in proposed updates. No automatic semantic deletion or
model-based historical consolidation was run.

Offline tests cover accepted/pending/rejected updates, chains, merges, original
snapshot validity, branch/cycle/missing-target/stale-hash handling, publication
idempotence, concurrent stale-branch rejection and expanded frozen reflection context.
No model calls, scores or experience text were generated.

Reproduce the read-only audit:
`python3 experiments/validation/experience-update-lifecycle-20261117/audit.py`

Validation: the full regression rerun ran 686 tests; 685 passed. The sole failure
is the pre-existing unrelated incremental-review browser DOM fixture
(`replaceChildren` on an undefined element). The final additional accepted-branch-merge
regression was then run with all six lifecycle tests and passed. Related compact
library, approval, reflection and business-delivery suites were rerun after that
addition. Training acceptance's 33 tests also passed after correcting new-entry
metadata compatibility. `git diff --check` passes.
