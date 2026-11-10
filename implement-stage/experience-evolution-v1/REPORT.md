# Expert-gated experience evolution v1

The automatic development path and expert activation boundary are implemented.
The new `experience-evolution` CLI reuses source-reviewed visible inputs, freezes
an active memory snapshot, retrieves zero/one body, executes independent starting
repairs, builds full feedback, reflects once per bounded round and validates the
candidate twice. It then pauses and exports a readable expert review page and an
unapproved decision template. All new prompts and UI text are English.

Only an explicit named operator's per-rule decision on the exact candidate and
complete outcome report activates a version. Programmatic structural checks and
model self-checks are not described as semantic expert approval. Accepted
candidate bodies remain unchanged; activation is a separate append-only record.

Unapproved/rejected children no longer displace active parents. Explicit rejection
of the exact active version disables it without silently restoring an older one.
Evaluation freezes active versions, runs fixed B1/A1/A2/B2 slots and cannot
reflect, approve or write learning feedback. Later activations do not alter an
already frozen snapshot. No-case, unknown-premise and conflicting selections
remain honest AUTO fallbacks.

## What was actually executed

Sixty offline checks passed: 17 memory, 6 expert-decision, 11 lifecycle, 4 native
bridge/scoring, 14 existing taxonomy/routing and 8 reused runtime/archive checks.
Raw logs and counts are in `VALIDATION.json` and adjacent log files.

Lifecycle tests cover the whole synthetic path through operator acceptance and
retrieval by the next prepared task; bounded revision; invalid reflection;
infrastructure interruption, partial output and unknown usage; zero-improvement
exploratory acceptance; target gains with preserved regression reporting; frozen
evaluation; and refusal of unfilled or mismatched expert decisions.

The native adapter's bridge is tested with a fake process, and its trusted
single-score interface is exercised against explicitly synthetic fixtures.
Original/reference/degenerate evidence and runtime must match the case version.
The existing high-level evaluator's per-call reference calibration is deliberately
not rerun. The scorer itself and scoring rules are unchanged.

**No live model session, real training/test repair or actual expert acceptance was
performed.** Synthetic outcomes and request counters are interface fixtures, not
claims of model repair benefit. The actual unified store still contains the
original three legacy English bundles and has zero expert-activated entries.
There is no automatic taxonomy migration or retrospective approval.

## Review interface and use

See `docs/EXPERIENCE_EVOLUTION.md` for preparation, explicit `--execute`, expert
review and frozen evaluation. A saved preview is
`offline-demo/batch/round-1/expert-review.html`. It is marked SYNTHETIC and is for
inspection only. No approval was applied to it. Prepared fixtures retain their
original code hashes; after implementation changes they are not live-resumable.

The new backend copies only named dependencies of the single-session research
runner. It does not import old schedulers or launch the weaker legacy Web
workbench. Its namespace isolation, request gates, no-tool reflection and
null-safe archive paths are reused. Each maintenance slot has 24 requests/600
seconds; reflection has 12/600. One/two development rounds allocate at most
108/168 requests respectively. Infrastructure failure stops without retries;
unstarted/invalid slots are not counted as behavioral failures.

## Scope and assumptions

This is a bounded workflow implementation, not a demonstration of useful learned
experience, improved retrieval or generalization. The analysis and source-bound
review must already be valid. Native runs require the explicit executable,
runtime, credentials and raw calibration artifacts. Existing minimum runtime
requirements are retained; missing prerequisites stop before paid dispatch.

Full semantic/interface choices are recorded before dependent work in
`ASSUMPTIONS.md`: expert activation (E-01/E-02/E-08), explicit offline/live scope
(E-03/E-04/E-09), supplied analysis and starting experience (E-05/E-06), separate
content/effect admission (E-07), frozen evaluation and honest failures
(E-10/E-12), evidence handoff (E-11), review UI scope (E-13), explicit revocation
(E-14), calibration reuse (E-15), and active-plus-candidate discovery (E-16).

There is no all-pass or zero-regression admission gate. With no observed gain,
expert acceptance must explicitly be exploratory. All normative rules still need
support findings; the software does not independently certify expert credentials
or establish support from a valid ID alone.

The implementation received executor inspection and deterministic checks only.
No additional model judge or independent expert review was performed. No commit,
production library update, installation or global configuration write was made.
