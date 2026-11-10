# Maintained workflow and source map

TempoEvo uses one versioned experience store. Obligation labels organize candidate
guidance; source-bound mechanism premises and exclusions govern delivery. The
refactor removes older execution paths without changing the current bounded
development or frozen evaluation protocol.

```text
Task + original candidate source
  ├─ optional AST report / archived source context
  └─ supplied automatic Contract + labels + facts + analysis review
       → frozen active experience snapshot
       → source-bound retrieval: zero or one experience
       ├─ development: starting repairs → feedback → reflection
       │    → candidate validation → named expert decision → next-task retrieval
       └─ evaluation: B1/A1/A2/B2 from original source; no memory updates
```

The controller requires the visible analysis as input. It does not silently run
AST analysis, source retrieval or a classifier. `experience-prompt` prepares
analysis material; callers supply the resulting reviewed analysis explicitly.
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
| Bounded development / frozen testing | `experience-evolution prepare/run/status/report/expert` | `experience_evolution.py`, `evolution_cli.py` |

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
| Expert decisions | `experience_approval.py`, `memory_review.py` | Exact-version decisions, active snapshots and pending/reviewed queue |
| Evolution | `experience_evolution.py`, `evolution_cli.py`, `evolution_backend.py` | Bounded sessions, candidate creation, validation, expert checkpoint and frozen evaluation |
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

Existing evolution protocols pin implementation hashes. A prepared batch from
before this refactor must not be resumed under the changed implementation; use
the matching revision or prepare a new batch with declared provenance.

Multi-case consolidation and automatic old-case replay are not implemented by
this refactor. Current development updates shared experience through bounded
per-case evidence and expert admission; generalization needs separate evidence.

`docker_backend.py` adds the optional pinned SWE-TempoC transport and offline
runtime/calibration entry points. `_session_runtime/docker_transport.py` replaces
the namespace envelope while retaining the original guarded runner and archiver.
See [Docker backend](DOCKER_BACKEND.md) for its explicit scope and isolation.

## Refactor validation

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
