# Bounded experience development and frozen evaluation — v2

TempoEvo enhances the existing general Coding Agent with source-grounded temporal
analysis and optional text experience. It does not change the Coding Agent,
train model weights, generate tasks or search agent architectures. The taxonomy,
fixed reminders, models, repair template, tools and routing rules stay fixed.
Manual checks are not learned experience. There is no new class-reminder delivery
policy in this implementation.

## One development task

```text
Capture original inputs, source lineage/exposure, critical obligations and M_old
  -> one reviewed public analysis for the source task
  -> two independent starting repairs using M_old (AUTO or ROUTED)
  -> one extraction: both PASS = 2 requests; otherwise valid failures = 12
       no_update -> stop normally
       one delta -> deterministic composition -> AI-assisted source/novelty review
         -> M_new: only this change; a revision replaces its parent identity
         -> two source validations
         -> critical loss/unknown or invalid material -> stop or pending
         -> public analyses of two preregistered independent transfer sources
         -> for each source: NEW1 / OLD1 / OLD2 / NEW2
         -> complete whole-task/critical/cost screening
         -> named expert content acceptance + screening -> explicit activation
```

Both successful starts still permit extraction. A success is not a verified cause;
a failure is not a causal explanation. `no_update` is a typed complete response
with a specific reason and existing basis IDs. Invalid, truncated, over-budget or
infrastructure-failed extraction is `reflection_incomplete`, never `no_update`.

The extraction schema permits one new bundle or one exact-parent delta: add,
replace or remove identified rules, and optionally update supported labels,
requires or excludes. Metadata-only revisions are possible. There is no five-rule
minimum or separate organizer call. Python validates IDs, applies explicit edits,
renumbers rules and renders text; it neither supplies missing evidence nor adds
business policy. Untouched rule bodies and unchanged applicability remain exact.
Necessary applicability, preservation, exclusions and verification must remain
supported and present in the delivered guidance where relevant; category counting
is not semantic approval.

Source-bound AI-assisted candidate review is a checkpoint before maintenance,
not named expert approval. The actual reviewer records a finding for every rule,
novelty, conflicts and blocking issues. A rejected candidate stops; it is not
rewritten or replaced automatically. Revisions need a separately prepared,
explicitly executed batch and budget. Historical v1 batches remain readable;
the CLI cannot resume them or start another v1 live loop.

After that AI-assisted check passes, the controller immediately writes the
immutable candidate record to the configured store, before source validations.
Validation reuses that exact record rather than creating or rewriting a version.
The report's `candidate_handoff` identifies this store. If it is an isolated
research store, use `experience-memory submit` to hand the exact candidate,
retained evidence, screen and development exposure to a shared review store.
This is an explicit zero-model operation; neither submission nor a pending
effect screen blocks content review. Submission never grants approval or changes
active retrieval. See [candidate submission](EXPERIENCE_MEMORY.md#submit-a-candidate-from-an-isolated-development-store).

## Preparation contract

Use the maintained CLI; preparation never calls a model:

```sh
python3 -B -m temporal_contract_analyzer experience-evolution prepare config.json --root /path/to/NEW_BATCH
python3 -B -m temporal_contract_analyzer experience-evolution status --root /path/to/NEW_BATCH
python3 -B -m temporal_contract_analyzer experience-evolution run --root /path/to/NEW_BATCH --execute
```

A development config has `kind: development` (default), `case_id`, `visible`
(optional/null), `store`, `binary`, `node`, `calibration`, `source_relationship`,
`cohort` and optional `backend`. `max_rounds` is currently 1. Backend fields and
real calibration are described in [DOCKER_BACKEND.md](DOCKER_BACKEND.md); the
same native/Docker backend and scoring adapters are reused.

`cohort` has:

- `source`: the source task lineage object.
- `transfers`: exactly two objects with `case_id`, `visible` (null or a reviewed
  public input), genuine `calibration`, and `lineage`.
- `boundaries`: at least one already reviewed visible input for an inapplicable,
  unknown-premise or excluded boundary check. These are zero-model checks, not
  extra analysis/repair slots. Missing boundary material blocks preparation;
  resolve it offline rather than enlarging the paid-call budget. Each boundary
  is `{visible, lineage}`, with the same lineage fields except `critical`.
  Boundary sources also count as development-used sources even with zero model
  calls and cannot later be advertised as independent final holdout.

Each development lineage object contains:

```json
{
  "source_unit": "REGISTERED_SOURCE_UNIT",
  "derived_from": [],
  "prior_exposure": "Actual known exposure and source relationship",
  "critical": [
    {
      "relation": "REGISTERED_PRESERVATION_RELATION",
      "basis": [{"file": "TASK", "line": 1, "quote": "EXACT CURRENT TASK TEXT"}]
    }
  ]
}
```

These are placeholders, not admission evidence. Critical relation keys must exist
in the original scorer, and their cited basis must match the visible task/source.
Source units, ancestry and exposure are management metadata, never routing input.
Shared declared ancestors, duplicate source units, identical candidate snapshots
and contradictions with registered source units are rejected. Metadata checks
cannot discover every undocumented derivation: accurate provenance registration
remains required. Language variants are not independent source units.

All original tasks/code, source units, analysis roles, critical obligations,
calibrations and branch budgets are captured before dependent repairs. Omitted
public analyses are generated once per case from task/source/AST only and pause
for an actual review. Source analysis comes first; transfer analysis is deferred
until a candidate passes its source checks. Do not adjust an analysis to match a
candidate. No mechanism finding is required for ordinary Coding Agent work;
unknown/empty labels can fall back to AUTO and extraction can return no_update.

Read the generated `cases/KEY/analysis/review-input.json`, supply its actual
AI-assisted or human source review, and submit a new review-input file:

```sh
python3 -B -m temporal_contract_analyzer experience-evolution review-analysis review.json --root /path/to/NEW_BATCH
```

The v2 review contains `case` (`source`, `transfer-1` or `transfer-2`) alongside
analysis/reviewer/approved/blocking_issues/scope_unknowns/evidence/reason. Raw
analysis is preserved; an approved public input and its common repair prompt are
then retained for both conditions. No repeated extraction or hidden reviewer.

After extraction, fill `candidate-review-input.json` with the actual executor's
per-rule source/novelty/boundary findings. This checkpoint is explicitly
`execution_agent_visible_input_only`, not independent human approval:

```sh
python3 -B -m temporal_contract_analyzer experience-evolution review-candidate candidate-review.json --root /path/to/NEW_BATCH
python3 -B -m temporal_contract_analyzer experience-evolution run --root /path/to/NEW_BATCH --execute
```

If execution ends at `transfer_analysis_prepared`, the next explicit run performs
only the two preregistered analyses, then pauses for review. Submit both reviews
and execute the fixed comparisons. No starting repair, extraction or source
validation is repeated. There is no implicit resume after failure.

## Evidence access and budgets

Models and effort remain:

|Role|Model / effort|Requests|Time|
|---|---|---:|---:|
|Public analysis|gpt-6-sol / low|12 per case|600 seconds|
|Maintenance|gpt-5.6-terra / low|24 per session|600 seconds|
|Extraction after two PASS starts|gpt-5.6-terra / medium|2|600 seconds|
|Extraction after a valid non-PASS start|gpt-5.6-terra / medium|12|600 seconds|

|Branch|Sessions excluding analysis|Request ceiling excluding analysis|
|---|---:|---:|
|Success then no_update|3|50|
|Failure then no_update|3|60|
|Success through comparisons|13|290|
|Failure through comparisons|13|300|

At most three analyses add 3 sessions/36 requests: full ceilings are 16 sessions
and 326/336 requests. These are ceilings, not actual cost. All sessions are serial.
The runner passes the branch cap to the real request guard; it is not merely a
post-hoc counter. There are no retries, extra judges, diagnostic model calls,
replacement tasks or hidden candidates.

Reflection defaults to the complete archived source evidence. Its isolated
read-only workspace contains this source task, the two actual starting patches,
full scores/schedules, deltas, public self-reports marked unverified, prior
experience/reviews frozen at preparation, and selected starting tool events.
The existing tool transport is restricted to its closed reader-command grammar.
Python/program execution, writes, out-of-workspace reads, network commands and
newline command injection are denied. No scorer/reference, transfer result or
final-test feedback is supplied. Any execution validation must use registered
controller slots; reading evidence does not authorize an extra validation session.

## Development qualification and activation

The source check blocks invalid structure, unsupported policy, confirmed loss of
preregistered critical preservation, and infrastructure/scorer errors. Unknown
critical behavior stays pending. Ordinary unresolved behavior does not impose a
new two-PASS requirement. Boundary checks never launch models and explicitly
record not_run; identical guidance is not an empirical equivalence result.

The two transfer sources receive the full M_old/M_new retrieval policy. A revised
identity is replaced, not double-activated. Independent additions retain real
conflicts; unresolved conditions/conflicts return AUTO rather than forced text.
Repair inputs share original source, public analysis, common prompt, tools,
models and budgets. Only selected guidance differs. All valid behavior failures
continue; infrastructure errors stop immediately. Summaries are formed after
all fixed comparisons, never fed into another repair condition.

A candidate passes the engineering screen only if:

1. New whole-task pass counts are no lower at either transfer source.
2. Across the four new repairs, there are at least two additional whole-task
   passes over the four old repairs.
3. No confirmed critical preservation loss or unknown critical behavior remains.
4. Every required score and request-accounting record is valid, complete and
   within the registered budget.

Whole-task outcomes, not assertion gains, determine this gate. Identical-prompt
random wins cannot establish experience benefit. If old passes are already 3/4
or 4/4, a two-pass gain is unattainable; retain pending status without changing
tasks or the threshold. This is a conservative development filter, not a
significance test or generalization result.

Screening is retained separately under `store/screening/VERSION_ID.json`, linked
to the immutable experience. Actual rule bodies are not rewritten after outcomes.
The review UI exposes the report and complete vectors. Expert content acceptance
can be recorded without activation; the CLI defaults to review-only. Explicit
`activate`, `rollback`, or UI accept-and-activate checks both content acceptance
and recomputed screening. A named expert cannot bypass missing effect evidence.
Historical acceptance/active pointers remain intact but are excluded from the new
default view unless they independently meet this protocol. M0 can be empty.

## Milestones and final evaluation

Save approved default snapshots with the existing `experience-memory freeze`
command and name them M0/M1/M2 in an evaluation config. Final config fields are
`kind: evaluation`, `store`, `binary`, `node`, optional `backend`, `milestones`,
`tasks`, and `excluded_source_units`. Each milestone is `{name, snapshot}`;
`snapshot` is the frozen snapshot object, not a changing live-store reference.
Each task has `case_id`, `visible` (null or reviewed), genuine `calibration`,
`lineage: {source_unit, derived_from, prior_exposure}`, and:

```json
{"holdout": {"used_for_generation": false, "used_for_selection": false, "used_for_tuning": false}}
```

Register the complete known excluded source set, including prior research outside
this store. The controller also excludes sources in its development usage and
screening records, and rechecks usage before final repairs. Honest exposure
registration is required; this is not a claim that a foundation model never saw
similar code. Selected transfer tasks are development data, never final holdout.

Prepare/run/review-analysis use the same CLI with an evaluation config. AUTO is
always present. One public analysis per task is shared by all milestone conditions.
Each distinct condition has two independent original starts; declared order then
reverse order is fixed before calls and does not control sampling randomness.
Conditions producing identical complete prompts across the fixed cohort merge
before repair; aliases explicitly have no extra executed/scored sessions.

Evaluation never extracts, updates memory or activates versions. It reports
whole-task passes/valid scores, per-source results, newly solved/failed cases,
full vectors, costs, delivery/fallback reasons and missing data. Assertion counts
are not independent samples. Two repeats remain descriptive. If final feedback
is used to revise the method, reclassify those sources as development and reserve
another final cohort. No final evaluation was launched by implementing this code.

## Lightweight records and historical compatibility

Keep original inputs, public analysis, memory versions, prompts, patches, scores,
usage and partial errors connected. Check input/calibration correspondence once
at batch startup; reuse the captured session runtime and trusted scoring source.
Do not walk/re-hash the entire batch or all approval history before every call.
Existing experience/source digests remain identity fields. There is no new log
hash chain or comprehensive implementation/executable hash lock. Per-candidate
archival/admission and atomic writes, source isolation and store locks remain.

v1 directories can still be inspected with status/report. Their stored outcomes,
unknown costs, freezes and stopped slots are not rewritten or resumed. New CLI
preparations require v2 metadata. Offline synthetic fixtures validate control
logic; they are neither new trained experiences nor real transfer evidence.
