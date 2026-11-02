# Build note

Using research-implement-feature, OpenAI Docs, and Sites local-only workflow. No publication.

| Rung | Feature | Check | Tier | Status |
|---|---|---|---|---|
| F0 | Freeze candidate, archive report, prepare exact prompts | preparation tests | MUST | passed |
| F1 | Sequential Codex jobs, cancellation, logs, changes and receipts | execution lifecycle tests with labeled fake CLI | MUST | passed |
| F2 | Local experiment page and server API | HTTP and browser integration tests | MUST | passed |
| F3 | Regression checks and fresh assumption sweep | Python suite, extension runner/browser checks | MUST | passed; same-family provisional sweep |

## Run record

Reference inspected: ../temporal-contract-bench/web/case-atlas/runner.py and temporal_evidence/experiment.py. Reuse the analyzer's archive and frozen layers; do not import or modify bench runner/scoring code.
Codex integration checked against local `codex exec --help` and https://developers.openai.com/codex/noninteractive/ (redirects to learn.chatgpt.com/docs/non-interactive-mode).

F0 ran before the runner/UI: captured Python source, archived report, prepared two prompt artifacts with no model calls. Initial `python3` resolves to an unsupported 3.7 installation; reran and consistently use `/usr/bin/python3` (3.9+) as documented.

Checks: full Python suite 274/274 passed before the two final executable-bit/descendant regression tests were added; current focused experiment suite 9/9 passed, report-hub suite 7/7 passed. Extension runner 9/9 and existing report-browser integration passed. Final experiment-browser integration passed after replacing an async browser-predicate timing assumption with explicit HTTP polling. It checks exact condition prompts, explicit start, two independent synthetic executions, answer/log inspection, unchanged original code, mobile layout and absence of browser exceptions. CLI --experiments routing passed a mocked-service check; git diff --check and Node syntax check passed. All generated inputs and CLI outputs in these checks are labeled synthetic and live only in temporary directories.

Fresh native reviewer ran two rounds. First reproduced surviving descendants on cancellation, and observed lost executable bits; both fixed with focused regression tests. Second found no remaining issues. The routing helper was unavailable; native default review completed and remains same-family provisional, not independent validation (REVIEW_ROUTE.json). No live model calls or research success measurements.

Changes remain uncommitted for user inspection. No bench files, historical results, global Codex config, installed extension package, or credentials were modified.

## Case-picker simplification

User requested case list and model selection matching bench instead of manual directory/task configuration. Added a data-only bench catalog adapter, server-selected base/core prompt, dropdown models, one Run action and collapsed advanced/history sections. Default web mode is workspace-write and A/D comparison. Case metadata records the original prompt path/digest, latent-maintenance/ungranted condition and exposure note. Study corpus currently contains 94 entries, 86 supported after adapter/admission filters; this is an inventory, not a quality or effectiveness result.

Focused Python suite now 10/10, report hub 7/7, browser flow passed using a synthetic bench fixture and fake Codex. Real `async-search-freshness-python` and `stale-search-response-react18` bench tasks each prepared two conditions offline successfully, with no model call or copied oracle/reference. Startup script syntax and diff checks passed; launcher health marker updated to preserve active older jobs during UI upgrade. New-service reuse, refusal to stop active legacy experiments, and waiting for idle legacy shutdown were checked with temporary services/mocked browser and upgrade responses.

Fresh native reviewer /root/case_picker_review (configured gpt-6-astra/xhigh, no separate returned provider identity) checked current supported case-input resolution, latent/ungranted core-prompt semantics, exclusions, routes/UI and active-service branch. CASE_PICKER_SWEEP.json records no remaining findings; same-family provisional. Reviewer did not rerun suites or a live model/old-service restart. No model calls or effectiveness claims were made.

## Local Codex discovery fix

User encountered missing CLI when launching outside the shell PATH and requested case selection with existing local Codex. Bench's discover_codex searches VS Code bundles; the initial implementation only used shutil.which. Discovery now also searches CODEX_BIN, valid bench pin, Codex.app and VS Code/Insiders bundles. Existing case-only web runs load local Codex config and omit model/effort overrides; explicit-model backend runs retain the original controlled invocation. UI model/effort selection removed. A-015 records the new exploratory semantics and inherited MCP/tool configuration; prior sweeps predate this change.

Current focused suite 11/11 and synthetic browser flow passed. A real local discovery check with PATH=/usr/bin:/bin found the VS Code Codex 0.164.0-alpha.11.1; local login status returned available without printing credentials. No model call was made. Launcher health marker advanced to local-codex-v1 so old idle services upgrade while active jobs remain protected.

## Deferred

Formal isolation/blinding/randomization; benchmark-specific oracle integration; MCP delivery comparison; behavior-probe timeline. These are outside this exploratory execution page.

## Blockers

None at initialization.
