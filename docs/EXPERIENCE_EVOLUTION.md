# Experience development: human content review, measured effects

New preparations default to `review_policy=human-content-only-v1` in the existing
v3 controller. This replaces the extra AI audit stages. Historical frozen batches
retain their original policy, costs, stopped slots and results.

```text
Task/source → AST → one Contract analysis → frozen old-bank retrieval
→ two independent starting repairs and actual scores
→ one reflection: no_update or one incremental candidate
→ HUMAN CONTENT REVIEW / EDITING
→ accepted exact version → two source repairs + two-peer old/new comparison
→ actual effect gate + exact-version human enable grant → enable
```

## Removed from the default path

- No Contract evidence-check model session.
- No candidate support/novelty/conflict-check model session.
- Quote/line mismatches are nonblocking notes, not repair admission failures.
- No exhaustive increment-comparison object or second model review of reflection.

AST evidence, the original task/source, raw analysis, patches, full scores and
reflection remain archived. The Contract is an unreviewed model proposal: repairs
must inspect its basis against actual source. Skipped checks are `not_run`, never
`passed`, and analysis has `approved=false`. The retained compatibility filename
`approved-visible.json` means the frozen public input, not approval under this policy.
Quotation warnings appear in `cases/CASE/analysis/analysis-notes.json`. No quote is
silently corrected, no uncertain premise is promoted, and no human is impersonated.

Routing uses current source-bound labels and mechanism premises, not case IDs or
history. Invalid evidence, unknown prerequisites, exclusions or conflicts can
cause AUTO fallback; they do not stop repair. Valid source anchors permit routing
without claiming independent semantic review. At most one experience is delivered.
The same original code and frozen public analysis are shared across old/new views;
new candidate text/results never enter the old-condition prompt or shared analysis.
Preanalysis has no circular experience retrieval.

## Prepare and explicitly execute

```sh
python3 -B -m temporal_contract_analyzer experience-evolution prepare config.json --root /path/to/NEW_BATCH
python3 -B -m temporal_contract_analyzer experience-evolution run --root /path/to/NEW_BATCH --execute
python3 -B -m temporal_contract_analyzer experience-memory review --store /path/to/SHARED_MEMORY
python3 -B -m temporal_contract_analyzer experience-evolution work --root /path/to/NEW_BATCH --execute --watch
```

Preparation is offline. No paid task starts from page reads, edits or review
submissions. An explicitly authorized worker continues after an exact-version
human decision, subject to the frozen budget. Completed slots are reused; started
incomplete slots are not retried. `cancel --root PATH` stops future dispatch.
This change does not resume or reclassify a previously stopped batch. A new
preparation is needed to use the new policy; any real execution needs authorization.

## Configuration and fixed scope

Keep `case_id`, `store`, `binary`, `node`, `calibration`, `source_relationship`,
optional `visible`/`backend`, and the existing `cohort`:

- Source: source_unit, derived_from, actual prior_exposure, critical obligations.
- Transfers: exactly two other registered development sources, each with case_id,
  visible or null, calibration, lineage and source-supported critical obligations.
- Boundaries: at least one supplied task/source/analysis and actual lineage.

Related variants do not count as independent sources. Record authored/shared
components honestly. Critical preservation obligations and the complete schedule
are fixed before execution. These peers select experience, so they are development
data, not final holdouts. Default `max_candidate_versions=2` reserves one initial
candidate and one edit; allowed range1..20. Further revisions need declared budget
and explicit execution. `candidate_sha256` can bind an existing eligible proposal
to a fresh batch; it never transfers acceptance or old effect results to a child.

## Reflection and human review

Both success and failure permit one reflection; two successes cap reflection at2
requests, otherwise12. Valid `no_update` is normal. Invalid, incomplete or
infrastructure-failed reflection is not no_update. The model compares relevant
prior rules in its reason: use revise for a supported delta to an exact parent,
new for an independent addition, no_update when there is no supported increment.
Python still checks that the typed delta can be applied to existing rules and
source evidence IDs. It does not invent policies, repair missing output, or
manufacture evidence. There is no second candidate AI reviewer in this policy.

A generated/edited candidate goes directly to the existing Experience Review
page. The human checks source support, increment, interactions, bounds and claims.
Saving an edit creates an immutable child; it is not acceptance. Only the exact
version actually accepted can enter effect validation. An edit inherits neither
parent acceptance nor effect qualification. Unchanged eligible rule findings may
still reference accepted parent findings, with explicit provenance.

Review-only does not enable. A human may instead accept the exact SHA and persist
an enable-after-validation grant with the expected active version. Actual source
and cross-source screening, latest acceptance, unwithdrawn authorization and a
compatible active pointer are required for automatic enable. Locks, atomic writes,
CAS and idempotent task bindings remain. Reject/revise/revoke blocks enable;
concurrent activity cannot silently overwrite another active version.

## Models, costs and remaining execution constraints

|Role|Model / effort|Request cap|Time|
|---|---|---:|---:|
|Missing public analysis|gpt-6-sol / low|12 per case|600 s|
|Maintenance|gpt-5.6-terra / low|24|600 s|
|Reflection: two PASS / otherwise|gpt-5.6-terra / medium|2 /12|600 s|

No extra review call is budgeted. With N missing public analyses, one candidate's
full maximum is300+12N requests. Each further admitted version reserves240 requests
for its ten fresh effect repairs. Three missing analyses and two versions cap at
576 requests/26 sessions, serial. Unknown token use stays unknown; report known
subtotals and unknown-request counts separately. Request caps are not actual use.

Do not remove runtime/isolation checks, input identity, calibrated original scoring,
request/time limits, tool permissions, completed-candidate scoring admission,
full behavior vectors, critical behavior protection or exact-version authorization.
These enforce executable, interpretable results rather than duplicate semantic
approval. Infrastructure errors stop without retry; invalid/unstarted slots are
not behavioral failures.

Actual effect screening is unchanged: two source revalidations without a new
all-PASS requirement, then each peer in NEW1/OLD1/OLD2/NEW2 order. The new bank may
not lose whole-task passes on either peer and must gain at least2 overall, with
no confirmed critical preservation loss. Unknown or mixed benefit stays pending.
No LLM self-score substitutes for execution. Budget and boundary failures do not
enable. Final frozen evaluation uses excluded-source/holdout guards, fixed views
and two repeats; it does not reflect, learn or write back.

## Historical compatibility

Missing `review_policy` retains the old AI evidence workflow. Diagnostic
`review_policy=ai-evidence-v3` can reproduce it explicitly, including its frozen
check schemas and original limits. `review-analysis` / `review-candidate` and
`recover-candidate` remain legacy tools, not required steps in new training.
Legacy accepted, active and exploratory statuses are not retroactively qualified
under a new protocol. No existing real record is approved, edited or enabled by
this implementation change. Offline fake-backend tests establish controller
behavior only; they establish no real repair improvement.
