# TempoEvo V5: training acceptance and independent testing

This document preserves the V5 acceptance design. New execution uses [V6](TEMPOEVO_V6.md); V5 roots are read-only. V5 roots used `tempoevo-trajectory-v5`. Module names `tempoevo_v4.py` and
`tempoevo_backend.py` remain to avoid an unrelated rename. V4 frozen runs cannot
be resumed, cancelled or published through the new controller. `tempoevo status`
continues to inspect retained V4 summaries without rewriting them. No historical
score, experience, decision or trajectory is migrated or automatically rerun.

## Training state machine

A freezes original public task/code, AST evidence, approved experience snapshot,
model, stage limits, evaluator commands/images/inputs, behavioral feedback mapping,
and `required_visible_checks` (default true: the entire visible suite is required).
Learning requires an explicit `training_evaluator`; an old `gold_evaluator` alone
is insufficient. `training_feedback` defaults to `{}` (verdict-only).

B executes at most three Actions, each based on the real previous candidate:

```text
Action → visible checks → training acceptance (the original training Gold)
       → Gold PASS AND required visible suite PASS: stop, success candidate
       → effective nonacceptance with budget left: diagnose/retain-or-revise Contract
       → three effective nonacceptances: real expert-summary task
       → timeout/environment/malformed assessment: execution_invalid, no fake failure
```

Setting `required_visible_checks=false` makes public checks diagnostic only;
training Gold must still explicitly pass. All observations remain archived.
The Contract retains public source grounding, immutable obligation IDs/text,
implementation-only retention, source-supported rerouting within the same frozen
bank, and uncertainty. Scoring observations reveal gaps, not new business norms.

C extracts success candidates only after training acceptance. Candidate provenance
includes `training_accepted` and the normalized final acceptance. Publication also
checks acceptance. Three effective failures request a named human summary, never
an LLM impersonating an expert. Failed/invalid trajectories cannot produce success
candidates. All candidates remain unapproved; edits retain immutable versioning,
and acceptance of one task does not verify cross-task effectiveness or causality.

## Normalization and feedback

`training_acceptance.py` adapts raw `{verdict, observed_effects, schedules, ...}`,
the existing `{passed, verdict, full_score}` envelope, and explicit PASS/FAIL-only
boolean interfaces. PASS is recognized only from an explicit behavioral verdict;
missing/unknown verdicts, conflicting flags and runtime errors are invalid.
Transport exit 0 is not a pass. Direct scorer exit 1 may accompany a valid failure;
unexpected process exits remain execution errors. The unchanged benchmark probe
retains its criteria; `tools/tempoevo-docker/gold.py` checks exit/verdict consistency.

Every assessment retains separate `raw-result.json` and normalized `result.json`.
Default feedback is only a boolean acceptance verdict plus explicit unknowns.
For opt-in behavior feedback, freeze a mapping of scorer effect IDs to public
source-supported statements and boolean expectations:

```json
"training_feedback": {
  "checkpoint-id": {"summary": "Accepted text is durable before departure returns.", "expected": true}
}
```

Only the configured public summary, expected/actual boolean and pass flag enter
feedback. Scorer IDs, raw schedule descriptions/assertions, arbitrary strings,
paths, references, patches and code are never copied from scorer output. Unknown
or unmapped effects are not invented as explanations. Current mapping supports
boolean effects only; richer expected/actual payloads need a reviewed adapter,
not arbitrary JSON passthrough. `regressions` remains empty when the scorer cannot
provide a declared safe regression projection. No failure reason is fabricated.

Agent workspaces mount public source only, never scorer/reference directories.
Diagnosis, later Action and success extraction receive controlled feedback, not
raw results. Raw results remain available to human reviewers in separate archives.

## Independent testing

Testing has no training evaluator or training feedback. Only public checks drive
repair/selection; first public pass or the fixed Action limit ends repair. The
last selected candidate is scored once by independent Gold, even when public
checks exhausted the budget. Its result cannot trigger another Action, change
selection, or enter any model input. No extraction, expert task or memory writes.

Known training-exposed configuration and registered exposed development IDs are
rejected as independent tests. Existing `experiments/training-cases.json` labels
the ten selections exposed development, not held out. No audited independent
split registry was found. Other testing reports therefore keep
`held_out_eligible=false` and `split_status=unverified_no_independent_split_evidence`;
a frozen execution mode alone does not prove an independent dataset. New learning
roots record task/source exposure in `training-exposure.json`. Do not count such
cases in an independent test set, including renamed copies of the same source.
Cross-root/renamed-source exposure tracking is not automatically certified.

## Budget, reporting and recovery

Models remain `gpt-6.1-sol / medium`; weights are not updated. LLM limits remain
12 routing + 12 Contract + 3×24 Action + 2×12 diagnosis + 12 extraction = 132
requests for default structured learning. Without routing: 120; testing omits
extraction. No new LLM phase is introduced. New protocols additionally freeze
assessment counts: up to three visible plus three training evaluations in
learning; up to three visible plus one independent Gold in testing. Each
evaluator timeout is explicitly frozen (default 60s, maximum 600s).

Reports separate per-round visible and acceptance outcomes, final acceptance,
independent test Gold, first visible/acceptance pass, stop reason, valid attempts,
started/invalid/missing stages, Contract changes and actual request/token/time
records. A valid attempt requires both effective training assessments. Invalid
assessments consume execution time/budget but not a behavioral failure count.

Completed checkpoints are reused, including an accepted candidate archived before
finalization. Incomplete started steps cannot replay silently. Protocol mismatch
is rejected before creating an execution lock. New experiments require new roots.
