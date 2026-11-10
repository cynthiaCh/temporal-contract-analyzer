# Bounded experience evolution with expert activation

The controller connects retrieval, independent development repairs, complete
feedback, reflection, candidate validation and an external expert checkpoint.
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
  -> export expert report; PAUSE
       accept -> activate exact version -> usable by the next prepared task
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

`config.json` must contain exactly these required fields, with optional `kind`
(`development` or `evaluation`) and `max_rounds` (1 or 2):

| Field | Meaning |
|---|---|
| `case_id` | Registered case, management only; never a retrieval feature |
| `visible` | Original task, complete candidate `sources`, fixed seven-label `analysis`, source-bound `review` |
| `store` | Explicit unified research memory directory |
| `binary`, `node` | Explicit native Codex and Node executable paths |
| `calibration` | Reusable version/runtime-bound original/reference/degenerate evidence below |
| `source_relationship` | Source-unit/cluster relationship, exposure and interpretation limits; audit only |

The visible task/source must exactly match the registered original candidate.
The source-bound analysis review must already be supplied genuinely; this entry
point does not silently approve an analysis or make an extra classifier call.
R/O/B/L/I/F/A is the native taxonomy. Historical T1–T4 imports are not recoded.

The root master prompt is copied and pinned as `controller-prompt.md`. The
protocol pins source, analysis, model roles, code, evaluator, calibration,
retrieval snapshot, slot list, budgets and constraints before execution.

## Fixed budgets and isolated native execution

- Maintenance: `gpt-5.6-terra / low`, at most 24 requests and 600 seconds per slot.
- Reflection: `gpt-5.6-terra / medium`, at most 12 requests and 600 seconds; no tools.
- One round: 2 starting repairs + 1 reflection + 2 validations = 5 sessions, up to 108 requests.
- Two preauthorized rounds: same 2 starting repairs + two reflection/validation rounds = 8 sessions, up to 168 requests.
- Evaluation: B1/A1/A2/B2, 4 sessions, up to 96 requests, no reflection or library update.

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

The old Web v2 workbench is unchanged and has weaker request/read-isolation
guarantees. The new CLI does not launch it as an alternate backend.

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
not use the wrapper that recalibrates a reference on every call. The original
candidate is scored once per prepared batch; every admissible final candidate is
scored once. Full outcomes and actual/expected/event traces are retained. The
model sees neither the scorer/reference source nor the hidden failure list.

## Expert review interface

After development, open `round-N/expert-review.html`. It displays all outcome
groups and costs and links to the complete source/patch/feedback and raw model
object. Review every rule, preservation duty, exclusion and counterexample.
Enter your actual name and reasoning, confirm complete outcomes, and download a
decision JSON. The page performs no network/model/library action.

```bash
python3 -B -m temporal_contract_analyzer experience-evolution expert /path/to/expert-decision.json --root research/NEW_BATCH
```

The submission binds the exact candidate and expert-packet digest, confirms full
outcome review, and provides each rule's supported/unsupported finding. Overall
and per-rule reasons are optional text and may remain empty.
No default name, auto-checked approval or generated expert signature is supplied.
This records the named local operator's review; it does not independently verify
their professional qualifications or imply an independent external review.

Acceptance requires all rules be supported. It does **not** require both repairs
to pass or zero regressions. All losses remain visible. With no observed gained
relation, acceptance must explicitly choose `exploratory`; content admission is
separate from demonstrated effectiveness. Unsupported rules cannot be accepted.

For a requested revision, execute a remaining prepared round explicitly:

```bash
python3 -B -m temporal_contract_analyzer experience-evolution run --root research/NEW_BATCH --execute
```

Or pass `--execute` with the revision decision to continue immediately. New rules
receive new immutable versions with parent linkage; old raw objects, reports,
patches and scores remain. Rejecting a child preserves the active parent.
Rejecting the exact active version disables it, without implicit rollback.

After acceptance, prepare a new development task using the same store. It
retrieves the accepted version at preparation and feeds its actual repairs into
that task's bounded development process. Selecting/preparing new cases remains
explicit; the controller does not autonomously expand the case cohort.

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
