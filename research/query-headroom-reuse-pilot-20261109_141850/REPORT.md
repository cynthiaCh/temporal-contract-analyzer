Fixed new training/test pair:

- Train: query-paused-initial-fetch-10266-vanilla; two exact-condition historical AUTO baselines are reused (not fresh calls).
- Test: query-paused-initial-fetch-10266-python3
- Cluster and source unit: query-paused-initial-fetch-10266.
- Both variants and histories are extensively exposed. Same-source synthetic language variants, not unseen or independently sampled.

Status: stopped; stop: {"time": 1794206429.318346, "reason": "Core analysis conflict: unresolved_semantic_conflict", "kind": "semantic", "no_retry": true, "no_more_model_calls": true}

The pair was chosen and announced before model calls, based on direct lineage and explicit candidate-visible policy. Two genuine matching-model/low AUTO failures (27/29 each) were source-verified and reused. The historically overrestrictive Python Contract was excluded and will not be reused. No guarantee of difficulty for the newly analyzed test input is claimed. The pair was not replaced based on outcomes.

|Stage|Planned|Started|Valid|Invalid|Unstarted|Whole-task pass / valid|
|---|---|---|---|---|---|---|
|training_AUTO|2|2|2|0|0|0/2|
|development|2|2|2|0|0|1/2|
|test_A|2|0|0|0|2|not calculable|
|test_B|2|0|0|0|2|not calculable|

|Slot|Started|Satisfied relations|Verdict|Lost original successes|
|---|---|---|---|---|
|D-analysis|reused analysis|unscored|None|None|
|AUTO-1|True|27/29|UNDERREACH|['cached-paused-background', 'cached-later-consumption']|
|AUTO-2|True|27/29|UNDERREACH|['cached-paused-background', 'cached-later-consumption']|
|reflection|True|unscored|None|None|
|development-1|True|28/29|UNDERREACH|['accepted-resume-then-offline']|
|development-2|True|29/29|PASS|[]|
|T-analysis|True|unscored|None|None|
|test-B1|False|unscored|None|None|
|test-A1|False|unscored|None|None|
|test-A2|False|unscored|None|None|
|test-B2|False|unscored|None|None|

Complete original behavior vector (D):

|Relation|AUTO-1|AUTO-2|development-1|development-2|
|---|---|---|---|---|
|offline-detach-false|PASS|PASS|PASS|PASS|
|offline-detach-true|PASS|PASS|PASS|PASS|
|offline-detach-always|PASS|PASS|PASS|PASS|
|offline-nonconsuming-detach|PASS|PASS|PASS|PASS|
|active-offline-resume|PASS|PASS|PASS|PASS|
|multiple-observers|PASS|PASS|PASS|PASS|
|last-observer-offline|PASS|PASS|PASS|PASS|
|unknown-unsubscribe|PASS|PASS|PASS|PASS|
|consumed-flight-cancel|PASS|PASS|PASS|PASS|
|nonconsuming-flight-cache|PASS|PASS|PASS|PASS|
|cached-paused-background|FAIL|FAIL|PASS|PASS|
|cached-consumed-revert|PASS|PASS|PASS|PASS|
|remount-generation|PASS|PASS|PASS|PASS|
|late-old-generation|PASS|PASS|PASS|PASS|
|always-mode|PASS|PASS|PASS|PASS|
|focus-gates-resume|PASS|PASS|PASS|PASS|
|focus-does-not-gate-first-start|PASS|PASS|PASS|PASS|
|offline-first-retry|PASS|PASS|PASS|PASS|
|nonconsuming-cancel-retry|PASS|PASS|PASS|PASS|
|reentrant-unsubscribe-at-entry|PASS|PASS|PASS|PASS|
|framework-unmount|PASS|PASS|PASS|PASS|
|cached-later-consumption|FAIL|FAIL|PASS|PASS|
|accepted-resume-then-offline|PASS|PASS|FAIL|PASS|
|detach-after-resume-queued|PASS|PASS|PASS|PASS|
|independent-query-keys|PASS|PASS|PASS|PASS|
|dependency-config-preserved|PASS|PASS|PASS|PASS|
|cached-prior-consumed-success|PASS|PASS|PASS|PASS|
|cached-prior-consumed-cancelled|PASS|PASS|PASS|PASS|
|retained-context-query-flag|PASS|PASS|PASS|PASS|

No experience reason: null
Test semantic rejection: {"candidate_visible_task": "Repair the museum exhibit lookup cache: a fresh online-mode query mounted and unmounted entirely offline later calls its signal-consuming query function with a live signal after reconnect. This occurs independently of refetchOnReconnect. Preserve supported query behavior, interfaces, dependencies and build/test configuration. Change product source only.\n", "raw_automatic_contract": "A fresh online-mode query mounted and unmounted while offline must not later invoke its signal-consuming query function after reconnect, regardless of refetchOnReconnect. Preserve shared per-key caching, observer-scoped subscriptions, supported network modes, retries, cancellation and completion behavior, interfaces, dependencies, and build/test configuration. Change product source only. The candidate leaves the initial attempt paused; removing its last observer marks retry cancellation, but the deferred resume checks that marker only after a failure, so the unstarted request can still run.", "source_raw_response": "runs/session-06/archive/raw-answer.txt", "problem": "Dropped condition on the prohibited event: live-signal invocation became all invocation.", "classification": "T4 supported, Contract rejected", "test_maintenance_started": 0, "extra_extraction_calls": 0, "manual_contract_edit": false, "test_grader_or_reference_consulted_for_review": false, "AI_assisted": true, "independent_human_approval": false}
Candidate eligibility: {"eligible": true, "AI_assisted": true, "no_confirmed_unsupported_policy": true, "regressions_fully_recorded": true, "both_full_passes_required": false, "production_admitted": false}
Test routing: null

No valid score means unknown effectiveness, not a behavioral failure. Training/development results are excluded from all test denominators. If both AUTO baselines pass, the predeclared rule generates no experience and stops before test; this is not a failed test or proof of universal ineffectiveness.

Costs (unknown engineering usage/money remain null):
```json
{
  "preanalysis": {
    "sessions_started": 1,
    "requests_started": 2,
    "tool_attempts": 2,
    "known_usage_subtotal": {
      "input_tokens": 42460,
      "cached_input_tokens": 20352,
      "cache_write_input_tokens": 0,
      "output_tokens": 931,
      "reasoning_output_tokens": 109,
      "total_tokens": 43391
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 42460,
      "cached_input_tokens": 20352,
      "cache_write_input_tokens": 0,
      "output_tokens": 931,
      "reasoning_output_tokens": 109,
      "total_tokens": 43391
    },
    "seconds": 24.536619424819946,
    "money": null
  },
  "reflection": {
    "sessions_started": 1,
    "requests_started": 1,
    "tool_attempts": 0,
    "known_usage_subtotal": {
      "input_tokens": 42726,
      "cached_input_tokens": 0,
      "cache_write_input_tokens": 0,
      "output_tokens": 1567,
      "reasoning_output_tokens": 516,
      "total_tokens": 44293
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 42726,
      "cached_input_tokens": 0,
      "cache_write_input_tokens": 0,
      "output_tokens": 1567,
      "reasoning_output_tokens": 516,
      "total_tokens": 44293
    },
    "seconds": 47.8346688747406,
    "money": null
  },
  "maintenance": {
    "sessions_started": 2,
    "requests_started": 15,
    "tool_attempts": 13,
    "known_usage_subtotal": {
      "input_tokens": 217655,
      "cached_input_tokens": 172800,
      "cache_write_input_tokens": 0,
      "output_tokens": 9155,
      "reasoning_output_tokens": 4836,
      "total_tokens": 226810
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 217655,
      "cached_input_tokens": 172800,
      "cache_write_input_tokens": 0,
      "output_tokens": 9155,
      "reasoning_output_tokens": 4836,
      "total_tokens": 226810
    },
    "seconds": 245.63013792037964,
    "money": null
  },
  "new_total": {
    "sessions_started": 4,
    "requests_started": 18,
    "tool_attempts": 15,
    "known_usage_subtotal": {
      "input_tokens": 302841,
      "cached_input_tokens": 193152,
      "cache_write_input_tokens": 0,
      "output_tokens": 11653,
      "reasoning_output_tokens": 5461,
      "total_tokens": 314494
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 302841,
      "cached_input_tokens": 193152,
      "cache_write_input_tokens": 0,
      "output_tokens": 11653,
      "reasoning_output_tokens": 5461,
      "total_tokens": 314494
    },
    "seconds": 318.0014262199402,
    "money": null
  },
  "calibration": {
    "model_calls": 0,
    "reused_current_version_scores": 22,
    "new_scoring_calls": 0
  },
  "reused_AUTO_reference_only": {
    "sessions_started": 2,
    "requests_started": 11,
    "tool_attempts": 9,
    "known_usage_subtotal": {
      "input_tokens": 144091,
      "cached_input_tokens": 105216,
      "cache_write_input_tokens": 0,
      "output_tokens": 8051,
      "reasoning_output_tokens": 3721,
      "total_tokens": 152142
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 144091,
      "cached_input_tokens": 105216,
      "cache_write_input_tokens": 0,
      "output_tokens": 8051,
      "reasoning_output_tokens": 3721,
      "total_tokens": 152142
    },
    "seconds": 213.30908036231995,
    "money": null
  },
  "reused_training_analysis": {
    "new_requests_this_batch": 0,
    "historical_usage": null,
    "source_provenance": "derived/D/provenance.json",
    "not_recharged": true
  },
  "engineering": {
    "tokens": null,
    "money": null
  }
}
```

Offline preparation: source/task/Contract/full AUTO prompt/model/effort/tools/budget/scorer match for both reused baselines; 22 associated current-version calibrations reused, no rescoring. 36 checks cover source isolation, archival, metering, citations and routing. The initial and derived ledger freeze scopes were separated before the first fresh call; original ledger is pinned separately and augmented ledger is protected by reflection-freeze. Raw evidence and score policy were not changed; pre-call record remains in precall-ledger-phase-check/.
Models: extract gpt-6-sol/low (12 requests), repair gpt-5.6-terra/low (24), reflect gpt-5.6-terra/medium (12); all 600s, serial, no provider retry. Maximum 8 NEW sessions/168 requests; the correct training analysis and two baselines are reused and not charged again. No old scheduler, external judge, prior experience seed, reference patch to learner, case swap, test learning or production update.
The reused training analysis retains its original model provenance and prior offline admission; it is not a new extraction. Reused baseline costs are reference-only; fresh-call totals exclude them. The separate report-only hash gate interception before maintenance was corrected by restoring report.py to its original frozen bytes; the new reporter is report_query.py. All true experimental inputs/guard hashes stayed unchanged, no maintenance session had started at that interception, and the original stop record is retained in pre-maintenance-report-check/. All raw responses/events, actual prompts, Python-generated diffs, final candidates, original scores and usage are under runs/*/archive. Frozen manifests and source/derivation metadata remain separate. Semantic reviews are AI-assisted execution-agent reviews, not independent human approvals.
The two fresh development scores were 28/29 and 29/29 versus reused 27/29 baselines. Both cached target relationships improved; the first run lost accepted-resume-then-offline, while the second lost no baseline success. This is a same-case development observation, not a stable-effect or independent test claim. The experience remains frozen and content-supported; no A/B behavior result exists because test Contract semantic admission failed.
Next necessary repair is generic preservation of qualifiers when converting a reported defect into a normative Contract (forbidden action WITH a condition must not become forbidden action generally). Keep this selected pair and frozen experience; do not restart reflection or select another case to hide the extraction fault. A corrected extraction/test stage requires a separate declared authorization; this batch performs no extra extraction or test.
Finished/stopped at the declared stage. No commit or automatic next batch.
