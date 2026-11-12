# Automated evidence workflow — v3

The English figures/specs/temporal_workflow.json and SVG are the target design.
New CLI preparations implement it with the existing Coding Agent and runner:

```text
Task/source → AST → analysis LLM → automatic AI contract evidence check
→ frozen M_old retrieval → two independent repairs → actual scores/run records
→ one reflection: no_update, or one immutable candidate
→ automatic AI support/novelty/conflict check
→ HUMAN CONTENT REVIEW / EDITING (the only business checkpoint)
→ accepted exact version → automatic source/two-transfer effect screening
→ exact-version authorization + effect gate + active-pointer CAS → enable

Human edit → immutable child → automatic AI check → same human checkpoint
```

Saving, accepting, passing validation and enabling are separate events. Review-only
acceptance never enables automatically. Page reads, edits and decisions never
dispatch a model. A separately authorized worker performs continuation.

## Prepare, authorize and run

```sh
python3 -B -m temporal_contract_analyzer experience-evolution prepare config.json --root /path/to/NEW_BATCH
python3 -B -m temporal_contract_analyzer experience-evolution run --root /path/to/NEW_BATCH --execute
python3 -B -m temporal_contract_analyzer experience-memory review --store /path/to/SHARED_MEMORY
python3 -B -m temporal_contract_analyzer experience-evolution work --root /path/to/NEW_BATCH --execute --watch
```

Preparation is offline. The initial run normally returns at awaiting_human_review.
The worker command keeps a process waiting and continues after exact-version
decisions/edits; without --watch it drains eligible work once. It actually calls
the existing NativeBackend/Docker backend and scorer, subject to their runtime
and calibration requirements. Merely saving pending data is not called execution.
Restarting it reuses persisted authorization, task bindings and completed slots.
An interrupted started slot with uncertain completion stops without retry. Use
cancel --root PATH to cancel future dispatch; an in-flight session archives first.

## Configuration and source constraints

Development retains case_id, store, binary, node, calibration,
source_relationship, optional visible/backend, and the existing cohort:

- source: source_unit, derived_from, prior_exposure and critical obligations.
- transfers: exactly two other independent registered sources, each with case_id,
  visible (null or a supplied analysis), calibration and lineage/critical basis.
- boundaries: at least one visible task/source/analysis and lineage. Its AI check
  is budgeted; no human analysis-review file is required.

A critical obligation names a scorer relation with literal task/source anchors.
Families/ancestry cannot overlap, duplicate source snapshots cannot count as
independent, and language variants are not independent sources. Record exposure
honestly, including zero-repair boundaries. Source metadata never enters routing.

Optional max_candidate_versions is 1..20, default 2: initial candidate plus one
edited version. It bounds admitted checks/validation tasks, not successful
candidates. Further human edits can be saved but need remaining declared budget
or a new explicitly authorized batch; they cannot expand an old budget.

Optional candidate_sha256 attaches an existing legacy/unbound candidate to a
fresh v3 batch in this store. That batch checks public analyses and runs its own
starting repairs, without reflection. Old uncontrolled baselines are not reused.
Review and execution use one unified store. V3 bound jobs cannot silently move
their authorization or acceptance into another store. Legacy/unbound candidate
submission remains supported; use a fresh v3 batch in the target store if needed.

Original inputs, ancestry/exposure, critical obligations, M_old, tools, models,
limits and schedule are frozen before dependent work. One public analysis per
case is shared by old/new conditions. Supplied analysis is labeled supplied and
still AI-checked. AST hints are not defect/safety proofs, and an AST miss is not
mechanism absence. Nonblocking unknowns remain unknown.

Preanalysis retrieval records AUTO: there are not yet independently checked
mechanism facts, so it cannot query the analysis it is about to generate. After
the check, existing routing verifies current-source premises/exclusions and
selects zero or one frozen experience. No match/unknown/conflict means AUTO.
Only M_old is available to starting repairs. All transfer public analyses finish
before reflection. Candidate guidance/results never enter old-condition prompts
or shared analysis. Old/new repairs share task, code, Contract, model/effort,
tools, limits, scorer and common template; only experience policy/text differs.

## Real AI checks and budgets

|Role|Model / effort|Requests|Time|
|---|---|---:|---:|
|Missing public analysis|gpt-6-sol / low|12 per case|600 s|
|AI contract check|gpt-6-sol / low|4 per case/boundary|600 s|
|Maintenance|gpt-5.6-terra / low|24|600 s|
|Reflection: two PASS starts / otherwise|gpt-5.6-terra / medium|2 / 12|600 s|
|AI candidate check|gpt-5.6-terra / medium|4 per admitted version|600 s|

With N missing analyses and B boundaries, the initial worst-case cap is
300 + 12N + 4(3+B) + 4 requests. Each further admitted edited version reserves
244 (one AI check plus ten repairs). Default N=3, B=1 and two versions means at
most 600 requests/32 model sessions, serial. These are ceilings, not actual cost.
Success reflection, no_update, rejection and blockers reduce consumption. No
extra judge, regeneration, model switch, hidden retry or candidate search exists.

Checks are bounded semantic model calls, not citation validators or renamed human
decisions. Full raw responses precede parsing. Claims/findings, reasons, evidence,
unknowns and blockers bind the exact source/analysis or candidate SHA. Mechanical
citation/ID checks are additional gates, never semantic approval by themselves.

The contract check tests task/requirement support, defects versus preservation,
ordering/negation, ownership, current citations, uncertainty and retained effects.
Unknown facts cannot be promoted. Unsupported/drifted evidence or semantic
blockers stop repairs. Historical guidance is not supplied to this check; its
applicability is subsequently audited by the source-bound router.

The candidate check reads source-side task/docs/code, actual starting patches,
complete scores, prior guidance and edit provenance. It checks every rule's
normative support, increment, conflicts, bounds and causal claims. Observations,
test names, human edits or agent claims alone cannot justify policy. No transfer
feedback/reference patch enters it. A failed, invalid or incomplete check is not
no_update. AI checking never creates named human acceptance.

## One human checkpoint and exact-version continuation

Experience Review shows AI findings, Before/current text, evidence, parents,
edits, human decisions, effect state, enable intent, active version and blockers.
Body/category and label/predicate edits create immutable children, retaining the
actual editor/reason and original evidence. Request IDs make repeated saves
idempotent. Saving accepts nothing and inherits no effect qualification. An
authorized worker checks the child before content acceptance becomes available.
Incremental review may reference unchanged accepted parent findings, but changed
rules/affected context need explicit review and interaction checking. Acceptance
of a parent never becomes acceptance of its edited descendant.

Choose review-only, or accept and authorize enable after validation. The latter
persists SHA, authorizer and expected active pointer. Rejection/revision stops
remaining repair slots. Withdrawal retains content acceptance but prevents
enable. Decisions and enable/revoke/reject actions serialize under decision.lock.
If enable wins just before withdrawal/rejection, that automatic selection is
removed; if the human update wins first, later enable is blocked. Concurrent
active-pointer changes wait with a reason instead of overwriting another version.
Repeated requests/restarts do not repeat tasks or enable events. Technical worker
identity remains distinct from the actual human authorizer. Legacy activate and
rollback are maintenance commands, not mandatory new workflow stages.

|Stored state / field|Meaning|
|---|---|
|ai_contract_checking / ai_candidate_checking|Actual budgeted AI check in progress|
|ai_contract_failed / ai_candidate_failed|Blocked evidence or consistency check|
|ai_check_incomplete|Invalid, interrupted or incomplete check; not no_update|
|awaiting_human_review|The sole normal human checkpoint|
|revision_requested / rejected|Named human requires revision or rejects this version|
|content_accepted_waiting_validation|Exact-version acceptance saved, execution still needs permission|
|effect_validation_running|The version-bound worker task is executing|
|validation_status: failed / unknown / passed|Actual gate outcome, distinct from human acceptance|
|waiting_enable_conditions|Valid effects, but active-pointer or enable conditions block selection|
|authorization_revoked|A persisted enable grant was withdrawn|
|enabled|This exact version is selected; current activity remains separately visible|
|no_update|Valid reflection found no supported increment|
|cancelled / budget_exhausted / infrastructure_error|Explicit stop, not behavioral failure|

The CLI reports AI/infrastructure/budget stop states with a nonzero exit status.
The worker stops on a failed/incomplete AI check instead of polling it as success.

Each version gets a new protocol under BATCH/validations/SHA. Candidate, human
acceptance, AI check, actual screening and enable name that same SHA. Edited
tasks reuse frozen public inputs/M_old and the two valid starting scores, with
their original costs separate. They never reuse parent new-condition scores or
overwrite the original batch protocol/candidate/results. Each version receives
two source repairs and per transfer NEW1 / OLD1 / OLD2 / NEW2, all original starts.

The existing gate requires new whole-task passes no lower at either transfer,
at least two additional passes overall, no confirmed critical loss or unknown,
credible complete scores and in-budget accounting. Source critical loss blocks;
ordinary unresolved items do not add a two-PASS requirement. Boundaries do not
run extra repairs. Identical-prompt/fallback differences are not experience effects.
Same-source repeats are not independent transfer evidence. This is an engineering
screen, not statistical significance. Execution/program checks determine effects.

Version state, edit receipts, withdrawals and exact-task screens use the existing
store's workflow subtree. Historical screening/SHA.json is not overwritten.
Root execution authorization/aggregate budgets are persisted. Completed slots
are reused without dispatch; ambiguous started slots stop. Unknown usage stays
null, with known subtotals and unknown counts separate. All raw/partial/errors,
tool events, patches, full vectors and costs remain archived. Invalid/unstarted
slots are not behavioral failures. Infrastructure, cancellation and budget stops
are explicit and do not silently reset on restart.
At an execution/resume boundary the current task's approved analysis is compared
with its original snapshot and actual retained AI receipt. Edited validation
tasks must retain that same public analysis. This does not add per-call walks or
hash chains over historical batches. Reports separate root reservations, actual
version tasks, reused starts and aggregate actual workflow usage.

## Frozen evaluation, compatibility and offline demonstration

New evaluations use experience-evaluation-v3 with automatic analysis/checks and
the existing holdout/source-exclusion, two-repeat and exact-prompt-alias rules.
They share checked analysis across all frozen AUTO/milestone conditions and never
reflect, edit, accept or enable experience. Sources used for generation/selection,
including boundaries, cannot become final holdouts. Feedback used for tuning
becomes development data and requires another final cohort.

V1/v2 frozen protocols/results remain their own versions. V2 review-analysis and
review-candidate remain compatibility operations; v3 cannot use them to bypass
automatic checks. Old stopped batches, unknown costs and approvals are not
rewritten. Startup checks input/calibration correspondence once; no new repeated
whole-history hashing or executable hash lock is introduced.

```sh
python3 -B examples/workflow_v3_demo.py --root /tmp/tca-v3-new-demo
python3 -B -m unittest discover -s tests -p test_workflow_v3.py
```

The demo is synthetic: temporary cases/store, fake backend and simulated human
actions, with native/model execution explicitly blocked. It exercises editing,
fresh AI checking, exact acceptance/intent, source/two-transfer validation,
automatic enable and cost-free resume. Its scores/counters are control-flow
fixtures, not measured model usage, repair gains or generalization evidence.
