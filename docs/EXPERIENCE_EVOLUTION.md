# Experience development: human content review, measured effects

V3 uses one workflow: `review_policy=human-content-only-v1`. Contract and candidate
AI audit stages have been removed. Older configuration values do not re-enable
them. Historical costs, stopped slots and raw results remain retained.

```text
Task/source → AST → one Contract analysis → frozen old-bank retrieval
→ two independent starting repairs and actual scores
→ fix each failed implementation and rescore (up to two corrective attempts per failed start)
→ one reflection with original failures, actual corrective patches and full scores
→ no rule delta: no_update if all original starts PASS, repaired if defects are fixed, otherwise repair_exhausted
→ proposed rule delta: HUMAN CONTENT REVIEW / EDITING
→ accepted guidance becomes eligible for retrieval
→ authorized worker may measure source/peer effects and record follow-up evidence
```

## Removed stages

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

New batches also retain a failure-learning record. Each valid source repair is
recorded before reflection, so a later interrupted repair or invalid reflection
cannot erase an earlier observed failure. Reflection must cover every failed or
unknown behavior once, cite its execution observation, compare the actual patch
with the guidance that was actually delivered, and propose a concrete next check.
Diagnoses are `retrieval_gap`, `execution_gap`, `rule_gap`, or `unknown`; non-unknown
attributions also need task/source evidence. These are model hypotheses, not
verified causal findings. An execution-gap claim must name a delivered rule.

`no_update` means no proposed rule change, not permission to leave a bug uncorrected.
New preparations default to `max_fix_attempts=2` per failed starting implementation.
The controller copies the actual failed candidate, sends it to the repair agent
with the original public task and approved guidance, and scores the correction
using the unchanged full evaluator. A failed correction becomes the next attempt's
input. Grader internals and hidden failure lists are not supplied to the agent.
Passing candidates stop immediately; failures may use the next reserved attempt.
Infrastructure-invalid sessions are never retried as a behavioral correction.
The setting accepts 0..5; zero explicitly disables corrective execution.

Corrective attempts are separate `FIX-*` slots, never independent source starts.
The original patches and scores remain intact, and reflection receives both the
original failure and the corrective patch/score. All required behaviors must pass
without losing originally correct behavior before a defect is marked fixed.
Without a rule delta, the final state is `repaired` when corrections pass, or
`repair_exhausted` when the declared attempts did not fix the defect. Exhaustion
returns a failing CLI exit status and never masquerades as success. A legacy
batch without reserved fix slots is not silently given a larger paid budget.
An accepted candidate is likewise not proof that the failures are resolved.
The summary exposes `followup_required` and the failure record. All-PASS runs can
still finish with ordinary `no_update` and an empty failure review.

Records live at `failure-learning.json` in the run and
`STORE/failure-learning/BATCH_ID.json`. New preparation snapshots up to 20 prior
failure records for the same original task/source into `prior-failures.json`;
the next reflection receives them and their proposed checks. They never become
repair instructions or approved experience automatically. Repair prompts instead
ask the agent to map the delivered approved rules to the patch and check actual
implementation before finishing. The declared corrective slots execute within the authorized batch budget.
Measured source correction does not by itself certify an experience effect. Existing frozen batches keep their original schema.
When the existing authorized source-validation stage actually executes, its two
scores and critical-preservation check are attached to the originating failure
record under the candidate identity. `not_reproduced` is an observation, not proof
that the experience caused improvement; prompt equivalence is recorded explicitly.

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

Human acceptance makes the reviewed content eligible for default retrieval,
including review-only decisions and historical records. Neither an AI check nor
positive cross-source results are admission requirements. Optional preferred
selection remains separate from eligibility; a human can authorize the worker to
update it. Writes retain locking and stale-view protection. Reject/revise/revoke
prevents automatic selection, and execution cancellation stops future dispatch.

## Models, costs and remaining execution constraints

|Role|Model / effort|Request cap|Time|
|---|---|---:|---:|
|Missing public analysis|gpt-6-sol / low|12 per case|600 s|
|Maintenance|gpt-5.6-terra / low|24|600 s|
|Reflection: two PASS / otherwise|gpt-5.6-terra / medium|2 /12|600 s|

No extra AI review call is budgeted. With N missing public analyses, one candidate's
full maximum is396+12N requests with the default corrective budget (up to96
requests across four fix sessions). Each further admitted version reserves240 requests
for its ten fresh effect repairs. Three missing analyses and two versions cap at
672 requests/30 sessions, serial. Unknown token use stays unknown; report known
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
These thresholds describe measured effectiveness, not admission to retrieval.
No LLM self-score substitutes for execution. Budget and boundary failures stop
further execution. Final frozen evaluation uses excluded-source/holdout guards, fixed views
and two repeats; it does not reflect, learn or write back.

## Historical records and configuration

Old review-policy fields are accepted as configuration input and normalized to
human content review. They do not dispatch Contract or candidate AI audits.
Historical raw analyses and scores remain readable, and completed sessions are
not retried. An explicitly executed old batch may reuse retained public inputs;
it cannot re-enable removed audit stages. Stopped batches are not automatically
resumed by this change. New preparations use the current failure-review schema.

`review-analysis` and `review-candidate` are V2 diagnostic commands; V3 does not
need intermediate review files. `recover-candidate` can materialize a complete
historical proposal for human content review without a model call. Offline fake
backends establish controller behavior, not real repair improvement.
