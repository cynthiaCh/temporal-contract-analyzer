# Phase 1: observed outputs and their boundaries

Status: offline inventory of existing artifacts, not a new model experiment.
`samples/` contains exact JSON-pointer projections of historical data. `sources.json`
identifies the full originals and hashes. Projections are derived views, not fresh
model output. They are examples, not a representative performance sample.

| Component | Input | Actual output | What it does not establish |
|---|---|---|---|
| Source/AST preparation | Frozen candidate source and visible documentation | Parse status, named syntax nodes and source spans (`ast`) | Ownership, temporal requirements or absence of a mechanism |
| Preanalysis | Task, visible source/docs, AST, public definitions | Automatic Contract, mechanism classification, known/unknown/contradicted facts and citations (`analysis`) | Policy correctness merely because a quotation exists |
| Maintenance | Common instructions, task, candidate, fixed Contract; optionally experience body | Tool trace, edited candidate, public explanation; Python derives diff and archive | A claimed self-test is not external behavioral success |
| External evaluation | Admissible completed candidate, pinned evaluator | Original full check vector, actual/expected observations and events | Assertion names or PASS/FAIL do not establish causes |
| Feedback adapter | Original and repaired outcomes, patches, visible standards | Successes, improvements, regressions, unchanged failures, unknowns (`feedback`) | A failed check is not automatically a regression |
| Evidence ledger | Source anchors, requirements, observed feedback | Typed facts/observations, preservation constraints, counterevidence (`ledger`) | Observed correlation is not a verified cause |
| Reflection | Training-only ledger and complete feedback | Single-source rule bodies plus support, conditions, preservation and counterevidence IDs (`reflection-rule`) | Structural validity is not semantic admission |
| Composition/rendering | Model rules and separately locked applicability | Versioned rule object (`composed-experience`) and deterministic Markdown | Rendering does not create a second model-generated experience |
| Content review | Rule claims checked against actual evidence | AI-assisted acceptance/rejection and limitations (`semantic-review`) | Independent human approval or effectiveness |
| Registry freeze | Admitted object/body and applicability | Version, taxonomy, predicates, body hash, entry hash (`registry`) | Production admission or benefit on a new task |
| Retrieval/routing | Current candidate-visible analysis and frozen library | Selected hash or AUTO, premise/exclusion checks and reason (`route-hit`, `route-fallback`) | Similar category means unconditional applicability |
| Execution accounting | Request/tool events and responses | Started/completed/failed/pending requests, known usage subtotal, unknown counters (`usage`, `runner-receipt`) | Unknown usage is zero; incomplete work is behavioral failure |
| Stop/archive | Errors, partial response, workspace and guard state | Explicit reason and retained artifacts (`stop`) | Planned slots were executed |

## Prompt identity

There are three distinct artifacts: a shared prompt template, its per-case initial
message, and the full session context including subsequent source/tool messages.
Different task text does not imply a different learned prompt policy. Conversely,
sharing a template does not establish identical inputs across cases.

The current batch uses `toolflow.py:maintenance_prompt` and `study.py:common`.
Its AUTO and development initial messages are archived in `development/`; the
actually dispatched initial message is in the session archive. Source bodies are
also read through tools. The initial message is not the full backend transcript.
All referenced prompt files are hashed in `sources.json`.

## Observed incompatibilities and missing outputs

1. Historical experiments classify T1–T4. The current repository uses
   `temporal-obligation-taxonomy-7-v1` with R/O/B/L/I/F/A multi-label obligations.
   These are different taxonomies. No automatic equivalence has been established.
2. `rag.py` retrieves current candidate source/docs with BM25. It is not a unified
   cross-case experience store. Libraries are separately frozen per campaign.
3. Both the historical study and current workbench assemble injected text from
   `library[0]` after a selection. That agrees with their single-entry scope but
   must become selection-by-hash before supporting a multi-entry shared library.
4. The recent batch produced training artifacts and test analyses but stopped on
   a global configuration hash guard before test freezing. Its test routes,
   A/B prompts and eight maintenance outcomes do not exist. Historical hit and
   fallback examples here come from explicitly different batches.
5. The recent reflection input is about 496 KB. Some auxiliary analysis fields
   contain clipped text. Successful JSON parsing alone is therefore an inadequate
   interface acceptance test. Preserve originals and distinguish missing content
   from legitimate unknowns.

This inventory establishes artifact shapes and provenance only. It does not yet
validate a unified schema across every historical batch or score retrieval quality.
