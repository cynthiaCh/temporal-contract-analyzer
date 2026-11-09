Fixed new training/test pair:

- Train: draft-autosave-handoff-order-example-vanilla
- Test: draft-autosave-handoff-order-example-python3
- Cluster: draft-autosave-handoff; source unit: debounced-submit-flush.
- Python provenance explicitly names the JS case as parent. Authored, outcome-informed source; synthetic port with scaffold reuse; not unseen or independently sampled.

Status: stopped; stop: {"time": 1794203887.0040743, "reason": "Both training AUTO pass; no new experience generated", "kind": "training_all_pass", "no_retry": true, "no_more_model_calls": true}

The pair was chosen and announced before model calls, based on direct lineage and explicit candidate-visible policy. No matched Terra/low difficulty evidence was found. Ceiling risk was not claimed eliminated. The pair was not replaced based on outcomes.

|Stage|Planned|Started|Valid|Invalid|Unstarted|Whole-task pass / valid|
|---|---|---|---|---|---|---|
|training_AUTO|2|2|2|0|0|2/2|
|development|2|0|0|0|2|not calculable|
|test_A|2|0|0|0|2|not calculable|
|test_B|2|0|0|0|2|not calculable|

|Slot|Started|Satisfied relations|Verdict|Lost original successes|
|---|---|---|---|---|
|D-analysis|True|unscored|None|None|
|AUTO-1|True|14/14|PASS|[]|
|AUTO-2|True|14/14|PASS|[]|
|reflection|False|unscored|None|None|
|development-1|False|unscored|None|None|
|development-2|False|unscored|None|None|
|T-analysis|False|unscored|None|None|
|test-B1|False|unscored|None|None|
|test-A1|False|unscored|None|None|
|test-A2|False|unscored|None|None|
|test-B2|False|unscored|None|None|

Complete original behavior vector (D):

|Relation|AUTO-1|AUTO-2|
|---|---|---|
|quiet-burst|PASS|PASS|
|second-burst|PASS|PASS|
|close-before-deadline|PASS|PASS|
|switch-before-deadline|PASS|PASS|
|same-document-reopen|PASS|PASS|
|reentrant-switch-on-flush|PASS|PASS|
|reentrant-close-on-flush|PASS|PASS|
|reentrant-timer-save|PASS|PASS|
|reentrant-edit|PASS|PASS|
|preview-delay|PASS|PASS|
|preview-hide|PASS|PASS|
|preview-reuse|PASS|PASS|
|preview-valid|PASS|PASS|
|preview-delay-migrated|PASS|PASS|

No experience reason: {"reason": "Both AUTO pass; no observed failure to learn; no harder case or old experience substituted."}
Candidate eligibility: null
Test routing: null

No valid score means unknown effectiveness, not a behavioral failure. Training/development results are excluded from all test denominators. If both AUTO baselines pass, the predeclared rule generates no experience and stops before test; this is not a failed test or proof of universal ineffectiveness.

Costs (unknown engineering usage/money remain null):
```json
{
  "preanalysis": {
    "sessions_started": 1,
    "requests_started": 2,
    "tool_attempts": 1,
    "known_usage_subtotal": {
      "input_tokens": 44744,
      "cached_input_tokens": 21632,
      "cache_write_input_tokens": 0,
      "output_tokens": 862,
      "reasoning_output_tokens": 112,
      "total_tokens": 45606
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 44744,
      "cached_input_tokens": 21632,
      "cache_write_input_tokens": 0,
      "output_tokens": 862,
      "reasoning_output_tokens": 112,
      "total_tokens": 45606
    },
    "seconds": 23.76940155029297,
    "money": null
  },
  "reflection": {
    "sessions_started": 0,
    "requests_started": 0,
    "tool_attempts": 0,
    "known_usage_subtotal": {
      "input_tokens": 0,
      "cached_input_tokens": 0,
      "cache_write_input_tokens": 0,
      "output_tokens": 0,
      "reasoning_output_tokens": 0,
      "total_tokens": 0
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 0,
      "cached_input_tokens": 0,
      "cache_write_input_tokens": 0,
      "output_tokens": 0,
      "reasoning_output_tokens": 0,
      "total_tokens": 0
    },
    "seconds": 0,
    "money": null
  },
  "maintenance": {
    "sessions_started": 2,
    "requests_started": 15,
    "tool_attempts": 13,
    "known_usage_subtotal": {
      "input_tokens": 202287,
      "cached_input_tokens": 144384,
      "cache_write_input_tokens": 0,
      "output_tokens": 7639,
      "reasoning_output_tokens": 3524,
      "total_tokens": 209926
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 202287,
      "cached_input_tokens": 144384,
      "cache_write_input_tokens": 0,
      "output_tokens": 7639,
      "reasoning_output_tokens": 3524,
      "total_tokens": 209926
    },
    "seconds": 223.9312403202057,
    "money": null
  },
  "new_total": {
    "sessions_started": 3,
    "requests_started": 17,
    "tool_attempts": 14,
    "known_usage_subtotal": {
      "input_tokens": 247031,
      "cached_input_tokens": 166016,
      "cache_write_input_tokens": 0,
      "output_tokens": 8501,
      "reasoning_output_tokens": 3636,
      "total_tokens": 255532
    },
    "unknown_usage_requests": 0,
    "total_usage": {
      "input_tokens": 247031,
      "cached_input_tokens": 166016,
      "cache_write_input_tokens": 0,
      "output_tokens": 8501,
      "reasoning_output_tokens": 3636,
      "total_tokens": 255532
    },
    "seconds": 247.70064187049866,
    "money": null
  },
  "calibration": {
    "model_calls": 0,
    "valid_native_scores": 20,
    "invalid_unmaterialized_reference_precheck": 1
  },
  "engineering": {
    "tokens": null,
    "money": null
  }
}
```

Offline preparation: current exact candidate versions, 10 calibrated variants per case (base plus registered overlays), original scoring rules, source-visible policy audit and 36 checks of source reading/isolation/archival/meter/citation/routing interfaces. A reference was initially staged without its base and failed the precheck; raw error retained in offline-materialization-error/. The registered benchmark uses base+overlay; corrected staging did not alter cases/scoring and occurred before any model call. It is not an agent outcome or hidden paid retry.
Models: extract gpt-6-sol/low (12 requests), repair gpt-5.6-terra/low (24), reflect gpt-5.6-terra/medium (12); all 600s, serial, no provider retry. Maximum 11 sessions/228 requests. No old scheduler, external judge, prior experience seed, reference patch to learner, case swap, test learning or production update.
All raw responses/events, actual prompts, Python-generated diffs, final candidates, original scores and usage are under runs/*/archive. Frozen manifests and source/derivation metadata remain separate. Semantic reviews are AI-assisted execution-agent reviews, not independent human approvals.
Finished/stopped at the declared stage. No commit or automatic next batch.
