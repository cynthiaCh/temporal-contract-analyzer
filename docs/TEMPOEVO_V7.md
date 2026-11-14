# TempoEvo V7: reflection as reviewed experience maintenance

V7 describes frozen reflection maintenance. New execution uses [V8](TEMPOEVO_V8.md); V7 roots are read-only. V7 used `tempoevo-trajectory-v7`. V1–V6 batches remain read-only. V7
retains V6 model profiles, bounded transport recovery, request/time budgets and
V5 training-versus-testing acceptance boundaries.

After training acceptance, the existing single extraction request receives at most
five related, approved records from the trajectory's frozen snapshot, prioritizing
delivered experience then BM25 task matches. It returns a complete experience and
a structured `update`: operation, exact target hashes, reason, change summary,
failure attribution and supporting attempt numbers. No additional model call is
added. Baseline and Contract-only conditions do not read cross-task experience;
their reflection shortlist stays empty to preserve experiment boundaries.

| Operation | Result awaiting human review |
|---|---|
| `new` | New experience identity for distinct reusable guidance |
| `evidence` | Separate evidence supplement; no duplicate guidance record |
| `revise` | New immutable version with the same ID and exact parent hash |
| `merge` | New version of the first target, retaining all other source hashes |

Exact normalized rules, labels, requires and excludes are deterministically
recognized within the frozen shortlist and diverted to `evidence`, even when the
model proposes `new`. An explicit multi-target merge retains its lineage proposal even if its rules are unchanged, so reviewers can consolidate duplicate IDs. Different wording is not automatically proven equivalent;
semantic deduplication remains a fallible model proposal subject to human review.
Evidence-only proposals cannot quietly change guidance. Target hashes must belong
to the supplied shortlist. Revisions/merges require a delta and real attempt
references. An implementation gap alone cannot justify rewriting an experience.
Unknown causes remain hypotheses; using experience and failing does not prove it
wrong, nor does one pass prove causal or cross-task effectiveness.

All revised and merged versions start as unapproved candidates. They do not inherit
parent acceptance, replace a frozen snapshot or alter original records. Existing
exact-version content review and lineage/delta views apply. Approved-only retrieval
already prefers later applicable reviewed versions of the same identity. After explicit content acceptance, a merge consolidates its exact source versions
for future default retrieval: accepted sources remain readable and keep their
review history, but are omitted from new default snapshots while the accepted
merge covers them. Rejecting that merge restores their eligibility. Pending merges
do not suppress anything, and historical frozen snapshots remain valid.

Evidence supplements are immutable records under
`workflow/evidence-proposals/`; named human decisions are stored separately under
`workflow/evidence-reviews/`. The review page shows these proposals and their target,
trajectory and source evidence. Accepting a supplement acknowledges its evidence;
it does not approve new guidance, modify the target rules, establish effectiveness
or inject supplement text into later repair prompts. This keeps evidence growth
separate from approved guidance growth. `publish-candidate` reports
`kind=evidence_proposal` or `kind=experience_version`; batch summaries distinguish
the proposal digest from a candidate experience digest.

Three effective failures still create an `awaiting_expert_summary` task containing
the frozen related records and update schema. No model impersonates the expert.
A real submitted summary may include `reflection_update` with the same fields;
if omitted, publication defaults to new guidance, with exact duplicate detection
still applied. Failed expert summaries never become successful repair evidence.
Testing performs no reflection, expert task or memory publication.

## Inspection and validation

Use the existing `tempoevo status`, `publish-candidate` and `experience-memory
review` entrypoints. Inspect `candidate-pool/success.json` or `expert.json` for
`reflection_update`, `related_experiences` and publication kind. Each new version's
retained evidence includes the plan, original/final Contract, patch/result trajectory
and source identities. New batches require a new root; old trajectories are not
replayed or rewritten automatically.

Offline tests exercise each operation, duplicate diversion, unknown/forged targets,
immutable lineage, repeated publication, approval isolation, single extraction-call
budget, HTTP evidence review and real-expert-only failure flow. Model quality and
cross-task benefit remain unverified; no paid runs or historical retraining are
performed for this implementation.
