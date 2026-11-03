# Failure-learning build

The CLI spine and all MUST acceptance checks passed. Changes remain in the working tree for review. No model experiment was launched.

## Semantic assumptions (ASK=never)

These are implementation defaults, not measured effectiveness claims.

| ID | Under-determined | Chosen | Class | Source |
|---|---|---|---|---|
| FL-001 | Meaning of evolution | Candidate experience memory and source-inspection recipe selection; no automatic rule/model training or correctness promotion | semantic | default |
| FL-002 | Learning trigger | After evaluation only when reference calibration PASS and a completed job has a scored failed outcome; timeouts, runner errors and unverified jobs are not semantic lessons | semantic | default |
| FL-003 | Feedback trust | Saved feedback is researcher-side evidence, not business truth; classify audit-related failed assertion names as an effect-separation clue; all other failures get a generic source-checking recipe | semantic | default |
| FL-005 | Retrieval scope | Same case ID, original candidate-file byte inventory and task text only; file permissions, model and oracle version are not matching keys, so applicability remains a candidate hypothesis; no cross-case or unseen-project transfer claim | semantic | default |
| FL-006 | Exposure | Lessons only enter explicit learned_review jobs; these are feedback-informed development retries, never blinded holdouts; A/D and restricted MCP frozen layers unchanged | semantic | default |
| FL-007 | Delivery content | Agent gets generic candidate review questions plus current snapshot excerpts, not oracle expected values, reference patches or failed assertion/schedule names; provenance IDs remain recorded | semantic | default |
| FL-008 | Context selection | Deterministic source search for recipe-related effect names, prioritize files containing both recording/display families absent from original report; full identified enclosing function or bounded nearby lines, max 6000 code chars; source-search candidates not proven callback dataflow | semantic | default |
| FL-011 | D prerequisite | learned_review adds to the original D report, so a substantive source finding is required even if lexical recipe context exists | semantic | sweep |

## Ladder

| Rung | Feature | Acceptance command | Tier | Status |
|---|---|---|---|---|
| F0 | failed evaluation → CLI candidate lesson | `/usr/bin/python3 -m unittest tests.test_failure_learning.FailureLearningTests.test_cli_spine_and_idempotent_candidate_memory` | MUST | Passed before F1 |
| F1 | recipe source retrieval and frozen learned_review | `/usr/bin/python3 -m unittest tests.test_failure_learning` | MUST | 8 passed |
| F2 | automatic extraction and browser controls | `node vscode-extension/test/experiment-browser.cjs` | MUST | Passed; live browser also checked |
| F3 | regression and documentation | `/usr/bin/python3 -m unittest tests.test_failure_learning tests.test_experiment_workbench tests.test_workbench_launcher tests.test_scenario_progress tests.test_report_archive tests.test_report_hub tests.test_report_mcp` | MUST | 56 passed in focused batches |

## Run record

- F0 CLI test passed before adding retrieval and UI. Candidate extraction is idempotent and preserves original records.
- Focused learning/workbench/launcher/progress suite: 31 passed. Report archive/hub/MCP suite: 25 passed.
- Synthetic browser exercise passed with fake CLI; no model calls. Live browser verified the archived transfer candidate, three prepared conditions, queue.js in the learned report, absence of the checked failed assertion name in delivered text, and no browser exceptions. Screenshot: preview.png.
- JavaScript syntax, launcher zsh syntax and git diff whitespace checks passed.
- Earlier full suite: 321 tests run, two known listener-split subcase errors (calibration_verdict missing), reproduced on unchanged baseline. Local Node is 18.17.0 while those cases require 16.20.2. These errors do not establish a regression in failure learning.
- One subsequent combined check initially named nonexistent tests.test_workbench; corrected to tests.test_experiment_workbench. This was a command error, not a product failure.
- Reviewer round 1 found optional-memory failure isolation defects and undeclared substantive-D prerequisite; fixed and added recovery/launch material regression coverage. Round 2 also found stale derived warnings after memory recovery; fixed with a regression assertion.
- Real candidate: l-9b2ea6ee205b30870688 from e-17fd00c46db24e49. Prepared, unstarted experiment: e-3991bcd2f92c41ba (none, review, learned_review). Its frozen context contains 4390 source characters across six files, including queue.js.
- Interface choices FL-004, FL-009, FL-010 and all semantic decisions are recorded in ASSUMPTIONS.md. FL-011 came from the sweep; remaining rows were autonomous defaults.

## Review

Two selected-review rounds; actual backend/model route in reviewer-route.json and raw findings in SILENT_ASSUMPTION_SWEEP*.json. Same-family review remains provisional and cannot independently establish method effectiveness. Final round status is recorded in its JSON. No live stubs.

## Deferred

Automatic analysis-rule generation, model weight updates, cross-case transfer, complete callback-argument dataflow recovery, effectiveness experiments and token/time comparisons for the new condition. They require separate implementation or actual evaluated runs.

## Blockers

None for this implementation. Improvement in repair success has not been measured.
