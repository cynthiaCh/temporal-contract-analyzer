# Build Note

| Rung | Feature | Acceptance check | Tier | Status |
|---|---|---|---|---|
| F0 | Existing scored archive → inspectable failure data | `python3 results/ad-model-effort-20261104/analyze_partial.py` | MUST | passed |
| F1 | Per-failure hypotheses and bounded source relations | `python3 -m unittest discover -s tests -p test_hypothesis_repair.py` | MUST | passed |
| F2 | Same-patch matched D/feedback pair and regression evaluation | same accumulated integration suite | MUST | passed |
| F3 | CLI/API/browser entry and full verification | workbench, failure-learning, context, browser checks | MUST | passed targeted checks; broad-suite environment limitations recorded |
| F4 | Live 11-pair follow-up and fresh assumption sweep | saved oracle summaries and reviewer output | MUST | passed run/verification; same-family review provisional |

## Run record

- F0: prior archive inspection ran, exit 0; no new model calls.
- F1/F2: seven synthetic integration tests passed, including real CLI → fake model process → calibrated oracle → regression checks; no live model measurements. The fresh review found a local-default effort rejection; fixed and covered by the seventh test.
- F3: failure learning 8/8, context 20/20, workbench 16/16 (TCA_PYTHON_BIN=/home/sribd/anaconda3/bin/python3.11), launcher 4/4, browser check including matched repair all passed.
- Host default python3 is 3.8; existing oracle fixtures require 3.9+. Evaluation uses installed Python 3.11 for those tests. Browser Playwright 1.51.1 installed only under ignored results runtime; existing cached Chromium used.
- Broader suite: 331 tests ran; 5 failures and 26 errors under default Python 3.8, including unchanged macOS-only Node paths in behavior-probe tests and `/usr/local/bin/node` in listener-split fixtures. These environment-dependent suites are outside this change; targeted affected tests passed with the supported runtime. No claim of a clean full suite.
- Final fresh-context sweep: no unresolved undeclared assumptions; same-family provisional. Two rounds saved in reviewer-raw.json. Live results are not covered by this implementation review.
- Reviewer route: host-default native gpt-6-astra/xhigh, fresh context. Same-family review is provisional.

- F4: 11 matched pairs / 22 real model jobs completed normally. All 11 reference calibrations PASS and all regression comparisons verified against the parent oracle/runtime. Independent recomputation in results/hypothesis-repair-v2-20261104/finalize.py checked identical scored inputs, budgets and gain/loss records.
- Live outcome: D-only 2/11 full repairs, hypothesis 4/11. Two hypothesis-only repairs; two shared repairs; seven shared failures. Hypothesis candidates regress in 2/11 (4 previously passing checks lost); D control regresses in 0/11.
- Raw required effects: D 79/100, hypothesis 77/100. Applying the declared reject-regression/retain-parent policy gives D 79/100, hypothesis 81/100. These policy totals are explicit candidate selection, not automatic patch promotion.
- Same caps, unequal consumption: both arms inherited explicit model/effort and 600-second per-job timeout. Actual CLI usage and durations are in campaign/summary.json; hypothesis input/output use was higher. No equal-token or equal-compute claim.
- Generated 29 failure-specific hypothesis records; 3 are explicitly unclassified/insufficient. All remain candidate explanations, not automatically verified root causes. No live stubs.
- No general efficacy, blinding, statistical-significance or cross-project claim. This is a single-run developer-exposed matched comparison on previously seen cases.

## Deferred

No automatic patch promotion, no inferred proof of root causes, no full dynamic call graph. Hypothesis verification uses candidate-visible reproductions and trusted post-run evaluation, not hidden test contents in prompts.

## Blockers

None.

## Final semantic assumptions (full ledger)

# Assumption Ledger

ASK mode: never

| ID | Under-determined by the request | Chosen | Class | Source |
|---|---|---|---|---|
| A-001 | Control starts from base or previous patch? | Both arms start from the same immutable evaluated failed patch; D-only control measures another attempt from that patch, not a fresh-base rerun. | semantic | default |
| A-002 | What counts as same budget? | Inherit explicit model/effort overrides, sandbox/config route and per-job wall-clock timeout; one attempt per arm. Prompt/token counts may differ and are reported, not declared equal. Local-default parents inherit the current local config route, without pinning or proving historical resolved model/effort; the 11-pair matrix uses explicit overrides. | semantic | default |
| A-003 | Which feedback is disclosed? | Hypothesis arm receives failed effect identifiers/polarities and candidate explanations, never hidden expected payloads, test implementation or reference code. Feedback is development-only, not new public requirements. D control receives no feedback or parent answer. | semantic | default |
| A-004 | How to judge regression? | Compare explicit boolean observed effects using frozen required/forbidden rule sets and identical oracle provenance; missing/changed oracle fields make comparison unverified. Any loss of a prior passing check rejects automatic adoption; retain candidate evaluation separately. | semantic | user |
| A-005 | Which earlier runs are followed up? | Prior matrix's 11 original D failures, same source model/effort, one matched pair each. Original A/D and v1 retries remain untouched. | semantic | default |
| A-006 | How are causes generated and checked? | Deterministic feedback-to-source hypothesis construction with predicted event order and falsification steps; actual truth is unresolved until a source-backed reproducer is run. Unsupported relations and contract ambiguity remain explicit. | semantic | default |
| A-007 | Context/interface shape? | New `hypothesis_review` only via a dedicated retry-pair preparation API; keep v1 `learned_review` behavior. Source character budget 12000, relation depth 2, include reverse lexical callers and state-identifier evidence, label syntactic candidates. | interface | default |
| A-008 | How to preserve original passing behavior? | Continue saved patch in independent workspaces; both arms get the same instruction to preserve behavior. Research-side comparison checks prior passes after evaluation; only nonregressing candidates are eligible, without deleting failed attempts. | semantic | user |
| A-009 | How to treat already passing parent jobs? | Require a calibrated semantic failure to prepare the pair; reject successful, errored, timed-out or unverified parents. | interface | default |
| A-010 | How do existing browser services discover the new endpoint? | Advertise `hypothesis_repair=matched-patch-v2`; the launcher upgrades only idle older services and preserves active experiments. | interface | default |
| A-011 | What execution order is used? | Order the two arms by parent-ID last-digit parity, fixed and auditable but not randomized or guaranteed balanced; no statistical order-effect claim. | semantic | sweep |
