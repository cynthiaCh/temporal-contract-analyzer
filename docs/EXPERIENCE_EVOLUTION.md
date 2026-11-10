# Bounded experience evolution with unified memory review

The controller connects retrieval, independent development repairs, complete
feedback, reflection, candidate validation and the experience-memory review page.
It never auto-approves itself. The library and model weights do not autonomously
change in the background. Opening a report, preparing a batch or searching never
launches a model.

```text
Approved visible analysis + original source + frozen active snapshot
  -> retrieve 0/1 experience
  -> two independent starting repairs and full external scores
  -> one reflection candidate
  -> mechanical/source-link checks (not semantic expert approval)
  -> two independent candidate-guided repairs and full scores
  -> save candidate in experience memory; PAUSE for memory review
       accept in memory review -> activate exact version -> usable by the next prepared task
       revise -> one more round only if budgeted and explicitly executed
       reject -> preserve evidence, stop; active parent remains available
```

Two successful starting repairs stop development without inventing a new
experience. Starting repairs use the preparation-time retrieved body if eligible,
and are labeled ROUTED; otherwise they are AUTO. They are never mislabeled as
experience-free baselines. Every repair starts from the same original source.

## Entry points

```bash
python3 -B -m temporal_contract_analyzer experience-evolution prepare config.json --root research/NEW_BATCH
python3 -B -m temporal_contract_analyzer experience-evolution status --root research/NEW_BATCH
python3 -B -m temporal_contract_analyzer experience-evolution run --root research/NEW_BATCH --execute
```

The explicit `--execute` is the live-call switch. This implementation task ran no
live models. Do not reuse a stopped historical scheduler or enlarge a budget.

An optional `backend` object selects the [SWE-TempoC Docker adapter](DOCKER_BACKEND.md).
`docker-check` and `docker-calibrate` are explicit zero-model environment/scorer
commands. Without that object, execution uses the existing native backend.

`config.json` requires the fields below except `visible`, with optional `kind`
(`development` or `evaluation`) and `max_rounds` (1 or 2):

| Field | Meaning |
|---|---|
| `case_id` | Registered case, management only; never a retrieval feature |
| `visible` (optional) | Original task, complete candidate `sources`, fixed seven-label `analysis`, source-bound `review`; omit for automatic AST-assisted analysis |
| `store` | Explicit unified research memory directory |
| `binary`, `node` | Explicit native Codex and Node executable paths |
| `calibration` | Reusable version/runtime-bound original/reference/degenerate evidence below |
| `source_relationship` | Source-unit/cluster relationship, exposure and interpretation limits; audit only |

When supplied, the visible task/source must exactly match the registered original
candidate and include a genuine source-bound analysis review. When omitted,
preparation captures those inputs automatically and generates AST materials.
R/O/B/L/I/F/A is the native taxonomy. Historical T1–T4 imports are not recoded.

### Automatic AST-assisted Auto Contract

Omit `visible` from the existing configuration to use this path:

```text
prepare: registered task/source → local AST scan → selected evidence + prompt
run --execute: one analysis LLM session → analysis_review (no repair or scoring)
review-analysis: explicitly supplied review → experience retrieval → prepared
run --execute: existing repair/reflection/validation workflow
```

```bash
python3 -B -m temporal_contract_analyzer experience-evolution prepare config.json --root research/NEW_BATCH
python3 -B -m temporal_contract_analyzer experience-evolution run --root research/NEW_BATCH --execute
# Read the analysis and fill analysis/review-input.json with an actual review.
python3 -B -m temporal_contract_analyzer experience-evolution review-analysis research/NEW_BATCH/analysis/review-input.json --root research/NEW_BATCH
python3 -B -m temporal_contract_analyzer experience-evolution run --root research/NEW_BATCH --execute
```

The review input contains `analysis`, `reviewer`, `approved`, `blocking_issues`,
`scope_unknowns`, `evidence`, and `reason`. Initially the reviewer and approval are
null. Supply the actual `human_visible_input_only` or
`execution_agent_visible_input_only` review, `approved: true`, no unresolved
blocking issues, a reason, and source/task citations. AI-assisted review is not
the separate named expert's experience activation. Corrections to analysis are
explicitly supplied in this file; the raw model result is preserved. Invalid
citations produce `analysis_citation_review` and must be corrected before review.
Other schema-valid analysis errors remain reviewable with explicit
`blocking_issues`; correct the analysis and clear resolved issues before approval.
Development needs at least one evidence-supported obligation label and one known
mechanism premise; unresolved labels remain reviewable rather than failing after
repair sessions. Evaluation may keep empty labels and fall back to AUTO.

Artifacts under `analysis/` include:

- `ast-report.json`: the complete local scan.
- `ast-evidence.json`: finding evidence events, conditions, selected relations,
  candidate call links/target locations, coverage, and limitations; raw trees and
  provenance hashes are omitted from this model-facing projection.
- `prompt.md`: the exact analysis prompt, including full numbered candidate
  source, task, selected AST evidence, and the taxonomy.
- `raw-analysis.json`, `citation-issues.json`, `validation-issues.json`, and `review-input.json`.
- `approved-visible.json`: the explicitly reviewed input used by training.

Evidence selection is rule-based, not LLM ranking. No findings does not mean no
risk. Partial or unavailable parser coverage remains visible; analysis can still
use the full source. Native preparation uses the configured Node executable;
Docker preparation uses the host Node for AST parsing, separately from the solver
runtime. No subject code is executed during AST preparation. Large source inputs
retain the existing full-source prompt behavior without silent truncation.

The packaged `prompts/MASTER_PROMPT.md` (also linked at the repository root) is
copied and pinned as `controller-prompt.md`. The protocol pins source, analysis,
model roles, evaluator, calibration,
retrieval snapshot, slot list, budgets and constraints before execution.
Analyzer code, runner source and executable contents are not locked by
preparation-time hashes. Code or prompt edits do not require a new batch;
legacy implementation hashes are ignored. Input/artifact integrity, calibration
and batch-state checks still apply, including the existing no-retry rule.

## Fixed budgets and isolated native execution

- Maintenance: `gpt-5.6-terra / low`, at most 24 requests and 600 seconds per slot.
- Reflection: `gpt-5.6-terra / medium`, at most 12 requests and 600 seconds; no tools.
- One round: 2 starting repairs + 1 reflection + 2 validations = 5 sessions, up to 108 requests.
- Two preauthorized rounds: same 2 starting repairs + two reflection/validation rounds = 8 sessions, up to 168 requests.
- Evaluation: B1/A1/A2/B2, 4 sessions, up to 96 requests, no reflection or library update.
- Omitting `visible` adds one analysis session: `gpt-6-sol / low`, at most 12
  requests and 600 seconds. Thus one-round development plans 6 sessions / 120
  requests, two rounds plan 9 / 180, and evaluation plans 5 / 108. Analysis usage
  is archived and included in the batch totals. Evaluation generates one common
  analysis before A/B repairs and never learns from evaluation feedback.

All slots are serial. A store execution lock prevents concurrent evolution
batches. There are no retries, replacement cases, hidden judges or automatic
unbounded rounds. A revision requires an explicit operator decision and another
execution action within the prepared maximum.

The backend copies only named dependencies of the existing single-session
research runner into each slot; it never loads `study.py` or another scheduler.
It reuses namespace isolation, request/tool gates, disabled reflection tools and
null-safe Python archival. Only candidate/public runtime files are mounted for
repair. The global Codex configuration is not edited or used as an unrelated
freeze guard. Real execution currently needs Linux/bwrap, the specified binary,
valid credentials, runtime and calibration; missing prerequisites stop before
model dispatch.

The CLI is the maintained development/evaluation entry point. The old Web v2
workbench, A/D experiments and single-case failure-learning commands have been
removed; see the [source map](ARCHITECTURE.md).

## Reused calibration and scoring

The normalized calibration object contains `case_id`, `candidate_sha256`,
`scoring_inputs_sha256`, `runtime` (`path` and `version`) and `evidence`.
Candidate hash is SHA256 of canonical JSON of the complete source mapping;
scoring hash is SHA256 of canonical JSON of the frozen scorer-input map.
`evidence` has `original`, `reference` and `degenerate` entries, each containing
`path` and `sha256` for its raw scorer JSON. Case IDs must match, all verdicts must
be valid, reference must PASS, degenerate must fail, and runtime must match.

These records must come from real, version-corresponding offline calibration;
the normalizer is not permission to fabricate them or a request for human
approval. Synthetic fixture records are labeled as such and are not real-case
calibration evidence. Live missing/conflicting evidence blocks execution.

The controller reuses the existing trusted single-score `invoke` adapter. It does
not recalibrate a reference on every call. The original
candidate is scored once per prepared batch; every admissible final candidate is
scored once. Full outcomes and actual/expected/event traces are retained. The
model sees neither the scorer/reference source nor the hidden failure list.

## One review interface

Development saves its candidate to the configured experience store and stops at
`awaiting_review`. Open the existing memory review page:

```bash
python3 -B -m temporal_contract_analyzer experience-memory review --store /path/to/memory
```

Review the exact candidate's rules, applicability and retained evidence. The
"All retained sources" section includes `reflection-input.json` (task, source,
actual patches and complete job feedback), `raw-reflection.json`,
`mechanical-review.json`, `comparisons.json` and validation scores. All successes,
regressions and unknowns remain available. Supply your actual name and a finding
for every rule, then accept, request revision or reject directly in this page.
Acceptance activates the exact version; unsupported rules cannot be accepted.
Without observed gained relations, acceptance requires `exploratory` scope.
Acceptance does not require both validation repairs to pass or zero regressions.

There is no separate batch expert HTML, packet, decision template or
`experience-evolution expert` submission. `summary.json` and `REPORT.md` remain
execution records. The memory-review decision is the single source of truth;
`status`, `report` and `run` synchronize it into the batch state. Reading status
never launches a model. The same memory decision can also be submitted using
`experience-memory expert-review`.

A requested revision runs only when another prepared round remains and the
operator explicitly executes it:

```bash
python3 -B -m temporal_contract_analyzer experience-evolution run --root research/NEW_BATCH --execute
```

Each revision creates an immutable child version; original rules, patches and
scores remain. Rejecting a child preserves the active parent. Rejecting the exact
active version disables it without implicit rollback.

After acceptance, prepare a new task with the same store to retrieve the accepted
version. Existing prepared tasks keep their frozen snapshots. Case selection and
execution remain explicit; the controller does not expand the cohort itself.

## Evaluation and failure boundaries

Evaluation takes an immutable active snapshot at preparation. Later expert
activations do not change it. A and B share source, task, automatic Contract and
public requirements; B alone appends the selected text, or is identical on
fallback. Evaluation never creates a reflection candidate or expert admission.
Its outcomes must not be passed into development as unseen test evidence.

Native archives retain raw/partial responses, events, request ledger, errors,
workspace/final candidate, diff and archive status. Bridge failures retain their
own stdout/stderr separately. Unknown usage stays null, with known request
subtotals and unknown-session counts. Incomplete slots are invalid, not behavior
failures. Infrastructure errors stop immediately without rerun. Valid behavioral
failures continue the fixed slots.

`summary.json` and `REPORT.md` report all slots and complete vectors. Pass rates
use only valid scores; zero denominator yields null. Source-bound rules and
synthetic workflow tests do not establish repair benefit or generalization.
