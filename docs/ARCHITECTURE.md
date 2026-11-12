# Maintained workflow and source map

TempoEvo uses one versioned experience store. Obligation labels organize candidate
guidance; source-bound mechanism premises and exclusions govern delivery. The current v3 intervention evolves text experience only; Coding Agent models,
repair tools, common prompts, taxonomy and manual reminder delivery remain fixed.

```text
Task + original candidate source
  ├─ omit visible: AST scan → selected evidence → explicit analysis LLM call
  └─ or supply candidate Contract + labels + facts
       → frozen qualified default experience snapshot
       → source-bound retrieval: zero or one experience
       ├─ development: two starts → reflection: no_update or one delta
       │    → HUMAN content review / edit
       │    → exact-version source + two-source old/new comparisons
       │    → effect gate + persisted human enable authorization → auto-enable
       └─ evaluation: frozen AUTO/M0/M1/M2, two repeats; no learning
```

When `visible` is omitted from preparation, the controller captures the registered
task/source and generates AST evidence locally. The first explicit `run --execute`
calls the analysis LLM once and proceeds to repair. Supplied/generated analyses
remain unreviewed proposals. New batches use `review_policy=human-content-only-v1`:
no Contract/candidate AI audit sessions, no blocking quote/line admission and no
required exhaustive increment-comparison object. Source citation issues are
nonblocking notes; if they prevent reliable retrieval, use AUTO and keep repairing.
The only normal human wait is exact-version experience content review/editing.
An edit creates an immutable child requiring its own human acceptance and fresh
effect screening. Page actions never dispatch paid work. Skipped checks are
`not_run`, never AI approval. Input identity, budget, isolation, complete-candidate
scoring, critical behavior protection and exact-version activation guards remain.
Frozen older batches keep their original semantics; they are not upgraded or retried.
An explicitly authorized `experience-evolution work --execute --watch` process
continues after review and enables only when its exact-version grant and actual
cross-source effect gate pass. Review-only does not enable. Legacy v1/v2 batches
retain their own frozen protocols; manual semantic review remains diagnostic or
compatibility functionality.
`experience-prompt` remains an offline prompt generator and never calls a model.
See [taxonomy and analysis](CONTRACT_TAXONOMY.md), [experience storage and
retrieval](EXPERIENCE_MEMORY.md), and [execution protocol](EXPERIENCE_EVOLUTION.md).

## Entry points

| Purpose | Command | Implementation |
|---|---|---|
| AST evidence | `scan`, `compare`, `verify`, `freeze`, `verify-bundle` | `core.py`, `cli.py`, `layers.py` |
| Saved reports and source context | `reports …` | `archive.py`, `archive_cli.py`, `context.py` |
| Report browser / Codex MCP | `reports open`, `reports mcp` | `hub.py`, `mcp_server.py`, `hub_entry.py` |
| Analysis materials and offline routing | `taxonomy`, `experience-prompt`, `experience-review-template`, `route-experience`, `maintenance-prompt` | `taxonomy_cli.py`, `experience_routing.py` |
| Unified memory and activation | `experience-memory …` | `experience_memory.py`, `experience_approval.py`, `experience_memory_cli.py` |
| Human review queue | `experience-memory review --store PATH` | `memory_review.py`, `web/memory-review.*` |
| Bounded development / frozen testing | `experience-evolution prepare/run/work/cancel/status/report` | `experience_workflow.py`, `experience_development.py`, `experience_evaluation.py`, `evolution_cli.py` |

Opening a browser, reading memory, preparing prompts and preparing an evolution
batch do not call a model. Live execution requires the explicit execution switch
and the native backend's prerequisites.

## Module responsibilities

| Layer | Files | Responsibility |
|---|---|---|
| Package entry | `__init__.py`, `__main__.py`, `cli.py` | Module/console entry and command dispatch |
| Source evidence | `core.py`, `python_adapter.py`, `lifecycle.py`, `reentrancy.py`, `publication.py`, `reflective.py`, `countdown.py`, `protocols.py` | Parse source and extract conservative temporal clues |
| Evidence views | `review.py`, `boundary_cards.py`, `report.py`, `layers.py` | Review cards, report rendering and frozen layers |
| Reports and context | `archive.py`, `archive_cli.py`, `context.py`, `hub.py`, `hub_entry.py`, `mcp_server.py` | Immutable source snapshots, annotations, context expansion, report UI and MCP delivery |
| Vocabulary and static reminders | `taxonomy.py`, `taxonomy_cli.py`, `reminders.py` | Seven-label definitions, material commands and authored checklists; reminders are not learned experience |
| Shared knowledge | `experience_memory.py`, `experience_memory_cli.py`, `experience_recoding.py`, `experience_routing.py` | Immutable records, evidence closure, label recoding, discovery and conditional delivery |
| Expert decisions and effect gate | `experience_approval.py`, `experience_screening.py`, `memory_review.py` | Separate content acceptance, cross-source qualification and explicit active versions |
| Automatic evidence and continuation | `experience_checks.py`, `experience_workflow.py`, `experience_lifecycle.py`, `experience_candidate_handoff.py` | Human-only default review policy; legacy AI checks remain readable; one human checkpoint; immutable edit tasks, offline recovery of existing reflection proposals, persisted permission/enable intent, exact-version validation and locked enable/revoke |
| Development/evaluation | `experience_development.py`, `experience_updates.py`, `experience_evaluation.py`, `evolution_cli.py`, `evolution_backend.py`, `preanalysis.py` | Public analysis, typed incremental extraction, source/transfer screening and frozen milestone comparison; v1 reader remains in `experience_evolution.py` |
| Candidate snapshots | `candidate_files.py` | Candidate-visible file capture, hashes, modes and independent workspace copies |
| Trusted scoring | `case_catalog.py`, `case_evaluation.py` | Registered task inputs, scorer binding, runtime checks, oracle invocation, effect-vector comparisons and process termination |
| Shared HTTP transport | `http_common.py` | Loopback origin checks, JSON validation and security headers for both browsers |

`javascript/` contains the pinned parser scripts and npm manifest/lockfile.
`_session_runtime/` contains the explicitly copied native single-session runtime
and schemas. `prompts/MASTER_PROMPT.md` is the canonical controller prompt; the
root `MASTER_PROMPT.md` links to it. `web/` contains only the report browser and
the unified memory review browser.

The three shared responsibilities above used to be imported from the old
workbenches. The current controller and review browser no longer import those
implementations. Lexical experience discovery keeps its tokenizer directly in
`experience_memory.py`; it does not depend on the deleted task-only RAG runner.

## Removed paths and compatibility

- Old Codex A/D experiment workbench and Web v2 training/testing workbench.
- Same-case failure learning, failure-hypothesis repair, selective A/D routing,
  task-only lexical RAG experiments and their comparison scripts.
- Historical development browser, researcher profile sidecars, optional review
  packet wrapper, E/T/L/H measurement workbench and MeasurementBench v0.6 import.
- Their CLI/HTTP routes, browser assets, launcher, documentation and dedicated
  tests. Shared fixtures and candidate/scoring checks moved to current tests.

Old command names are intentionally unavailable. Existing external historical
measurements are left on disk but are no longer exposed or checked by the current
report API. Report snapshots, source context, boundary annotations and MCP
delivery remain supported. Research history and frozen result files are not
rewritten. Reproducing an old workflow requires its matching Git revision and
environment.

Prepared evolution batches do not lock the analyzer implementation, runner source
or executable contents to preparation-time hashes. Code and prompt edits do not
require preparing a new batch; legacy implementation hashes are ignored. Input
and saved-artifact integrity, scoring calibration and batch-state checks remain.

Automatic old-case replay beyond the preregistered source and two independent
transfer sources is not implemented. Development screens whole-task improvement
and critical losses before enable; generalization needs frozen holdout evidence.

`docker_backend.py` adds the optional pinned SWE-TempoC transport and offline
runtime/calibration entry points. `_session_runtime/docker_transport.py` replaces
the namespace envelope while retaining the original guarded runner and archiver.
See [Docker backend](DOCKER_BACKEND.md) for its explicit scope and isolation.

## Earlier refactor validation

- 355 Python tests passed, including bounded development, frozen evaluation,
  activation, retrieval, source evidence and shared transport checks.
- Nine editor adapter tests passed with VS Code's Node 24.22.1 runtime. The local
  Node 16 test runner lacks `t.after`; it cannot run that existing test suite.
- The report browser passed scan, evidence, annotation, handoff, comparison,
  filtering, historical snapshot and desktop/mobile checks in local Chromium.
- A clean source export built a wheel; an isolated import from the extracted
  wheel passed Python analysis, empty-memory review setup, packaged resource
  checks and all four CLI help groups.
- All 44 local experience-memory files retained their original SHA256 digests.

No live model session was run. Backend tests use synthetic scorer fixtures and
mock isolation-tool availability where required; missing isolation is tested as
a blocking error. These checks establish workflow integrity, not repair benefit.

## V3 offline verification

`tests/test_workflow_v3.py` exercises automatic checks, the sole human checkpoint,
immutable edits, exact-version effect tasks, review-only, automatic enable,
rejection/revocation races, active-pointer conflicts, cancellation, budget and
resume guards, and frozen evaluation. The HTTP test confirms that saving or
reviewing never calls a backend. `examples/workflow_v3_demo.py` runs the edited
branch in a new temporary store with native model dispatch explicitly disabled.
See the execution protocol for reproducible commands. These are synthetic control
flow checks, not real repair-effect measurements.
