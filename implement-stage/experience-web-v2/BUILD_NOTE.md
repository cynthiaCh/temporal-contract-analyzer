# Build note

| Rung | Feature | Acceptance | Tier | Status |
|---|---|---|---|---|
| F0 | HTTP entry to persisted campaign | `test_spine_http_persists_visible_snapshot_without_launching` | MUST | passed |
| F1 | Development analysis/review/AUTO/reflection | `test_development_review_freeze_and_full_test` | MUST | passed |
| F2 | Candidate review/revalidation/freeze | `test_no_improvement_stops_before_freeze_or_test` | MUST | passed |
| F3 | Frozen A/B and lifecycle controls | `test_unknown_premise_falls_back_to_identical_prompts` | MUST | passed |
| F4 | Browser controls, docs and assumption sweep | scoped Python and browser checks | MUST | passed |

## Run record

F0: HTTP creation/read and disk snapshot verified with synthetic inputs, no model invocation. F1–F3: 11 synthetic tests passed, including full development and frozen test path, rejection, no-gain stop, input/scorer drift, unknown observations, fallback, cancellation and restart.

F4: actual browser controls walked development → analysis review → AUTO/reflection → candidate review → revalidation → freeze → independent A/B; desktop/mobile and cancellation passed. Existing report-comparison and repair browser test also passed. Browser tests use an existing Playwright install via NODE_PATH and Chrome, with no dependency changes. Screenshots are temporary synthetic views at `/tmp/tca-experience-v2-desktop.png` and `/tmp/tca-experience-v2-mobile.png`.

The first assumption sweep reported one undeclared scoring convention, a prelaunch-stop mismatch, and lifecycle persistence/cancellation defects. A-011 now declares satisfaction/unknown handling. Cancellation retains selected campaign. Running-state persistence and terminal prelaunch errors were fixed; targeted checks rerun. Review is same-family and provisional, never independent approval. Raw first review is SWEEP_ROUND_1.json; followup clean with 0 undeclared semantic assumptions; final raw reply saved as SILENT_ASSUMPTION_SWEEP.json. Exact reviewer model identity is unavailable (requested gpt-6-astra/xhigh, reported GPT-6 family). Native reviewer selected by default; no project override.

No Git commits were created, per user instruction. No paid experiment/model calls were made by implementation verification. No historical research or production experience files changed.

Initial status/diff clean. Memory registry has no relevant entries. Existing local Codex runner and calibrated evaluator selected for reuse. Historical research scripts are evidence, not imported executable plugins.

## Deferred

Hermetic read isolation and request-hook metering are not provided by the existing Web runner; the UI will state the actual limits. Official GEPA, multiple-entry optimization and production publication are outside this request.

## Blockers

None.

Final checks: 64 scoped Python tests passed (experience 11, existing experiment runner 16, report server 8, seven-label routing 11, class reminders 6, launcher 5, development archive 7). New full-flow/mobile/cancellation browser check and existing experiment/repair browser check passed using synthetic CLI/oracles. JavaScript syntax and git diff --check passed. New targeted assertions verify live running persistence and terminal scoring-version rejection after review fixes. No live stubs remain.

Semantic choices: operator-declared source relation (not independent split proof); fixed two-AUTO/one-reflection/two-revalidation development and any-evidenced-gain admission with all losses retained; operator semantic review and research-only freeze; exploratory non-hermetic local execution with timeout/session budget, not request caps; no automatic retry/resume; training-only reflection evidence; fixed identical A/B common material and sampling-uncontrolled order; oracle-list satisfaction and unknown transitions. Full statements and sources are A-001–A-011 in ASSUMPTIONS.md.

Interface choices: separate Web/API/store, explicit models and effort, immutable stage materials with mutable journals excluded, and cross-stage code/CLI drift rejection. No external approval was requested (ASK=never). This reports executable workflow checks, not scientific effectiveness.

Live service: confirmed the prior service was idle, restarted with the new capability, then loaded `/experience` in Chrome without browser errors or creating campaigns. URL: http://127.0.0.1:49302/experience. Health reports seven-label-web-v2; campaign count 0 and no active experiment.
