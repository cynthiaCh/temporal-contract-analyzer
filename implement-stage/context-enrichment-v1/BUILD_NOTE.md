# Build Note — context enrichment

| Rung | Feature | Acceptance check | Tier | Status |
|---|---|---|---|---|
| F0 | Archived report → CLI context JSON seed artifact | context CLI smoke test | MUST | passed |
| F1 | AST definitions, lexical references, module resolution, traversal and limits | 20 context enrichment tests | MUST | passed |
| F2 | MCP paging/receipts and report-center UI | 6 MCP + 8 hub tests, JS checks, headless browser click/source navigation | MUST | passed |
| F3 | Documentation, regression and assumption review | full suite with baseline comparison; fresh reviewer round 2 | MUST | passed with existing environment failures documented below |

## Run record

- Read existing analyzer/parser/archive/MCP and helper implementations. No AGENTS.md found in repository or inspected parent paths. External helper sources will remain unchanged.
- F0 ran before definition enrichment: `/usr/bin/python3 -B -m unittest discover -s tests -p test_context_enrichment.py` — 1 passed. Output artifact created by CLI in test temporary directory.
- F1 initial AST/expansion suite: 11 passed; subsequent integration suite: 15 passed. No placeholder remains.
- Independent-context, same-family review round 1 found six concrete defects and seven ledger omissions. Fixed export membership, computed method scopes, parameter initializer scopes, runtime TypeScript gaps, immutable-run output guard and Markdown provenance; recorded omitted decisions in A-010/A-011/A-013–A-017.
- Round 2 found an additional declaration-level type-export variant, fixed with a dedicated test. Reviewer verified 20 context tests, 6 MCP tests, 8 hub tests; final review is provisional clean with zero remaining undeclared assumptions. Actual exact reviewer model was not exposed to the reviewer; requested gpt-6-astra/xhigh and returned identity limitations are preserved in review files. This is not cross-family assurance or research validation.
- Node syntax checks passed for context.cjs, app.js and extension staging script. `git diff --check` passed.
- Headless Chromium exercised the actual local server: open archived example, click 补充相关源码, assert publish/columns definitions, then navigate to archived source. No page errors. Screenshot: `preview.png`.
- Real demo: `examples/context-enrichment` generated 3 merged snippets / 308 code characters, no recognized unresolved items. `DEMO_CONTEXT.json/md` are preserved illustrative exports; their temporary archive was cleaned after the run, so the example report ID is not a live report-center record. The docs provide reproducible commands to create a new one.
- Full suite final broad run: 308 tests, two erroring subcases in `test_listener_split.ListenerSplitTests.test_local_catalog_preparation_and_behavior_evaluation_without_bench`, both KeyError calibration_verdict. Isolated `git archive HEAD` baseline with original case registry, case fixtures and installed parser dependencies reproduces the exact two errors (5 tests in that baseline file). Cases require Node v16.20.2, current `/usr/local/bin/node` is v18.17.0. No evaluator, case or runtime requirement changed. The final new type-export test was added after broad discovery and passed in the separate 20-test context run.
- Changes remain in the working tree for review; no commits or old VSIX replacement were made. Runtime staging includes context.cjs for future extension builds.

- Follow-up launcher compatibility check (2026-11-03): health now advertises the context capability; the actual `.command` upgrades idle old servers and preserves active ones. Three launcher-payload tests plus eight hub tests passed. Launched the real configured service, verified `/experiments` HTTP 200 and a newly archived example's `/context` response, matching Python API output (3 snippets / 308 characters). Existing experimental conditions do not yet include enrichment. This follow-up was checked by the executor after the saved round-two review, not by a third reviewer round.

## Deferred


- Natural-language retrieval, vector index, full call/dataflow graphs, self-evolving rules and empirical effectiveness measurement.
- Existing VSIX rebuild and installation.

## Blockers

No blocker for this integration. The two baseline environment-dependent test subcases remain unresolved outside this change's scope.

## Interface decisions

ASK=never. CLI: `reports context`; MCP: `read_context`; HTTP: `GET /api/reports/REPORT_ID/context`; UI: source-context tab and per-finding action. New schema is temporal-context-1. All interface/semantic choices and their sources are in ASSUMPTIONS.md. Review findings are preserved verbatim in the two sweep JSON files.

## Semantic assumptions (full rows)

| ID | Under-determined | Chosen | Class | Source |
|---|---|---|---|---|
| A-001 | Source of context | Only the verified report snapshot, including overlays; never current working-tree files | semantic | default |
| A-002 | Seed selection | All finding evidence ranges, or one explicit finding ID; merge overlapping/adjacent source ranges; no finding means empty seeds | semantic | default |
| A-003 | Meaning of enrichment | Syntactic candidate definitions, not proven dataflow, executed calls, complete dependencies or bug verdicts; unresolved always accompanies snippets | semantic | default |
| A-004 | First relationship types | Lexical definitions and static local named/default ESM imports in JS/TS/Vue; unsupported Python, namespace imports, reexports, external modules, dynamic dependencies are gaps | semantic | default |
| A-007 | Budget and traversal | Seeds must fit or fail with actionable error; definitions added atomically in deterministic breadth-first order; merge overlaps, count code Unicode characters, record depth/budget omissions | semantic | default |
| A-008 | Experimental compatibility | Separate opt-in material; no changes to frozen B/C/D rendering or restricted MCP tool exposure; MCP context uses delivery receipts/pagination | semantic | default |
| A-010 | Module resolution | Explicit extensions must match snapshot paths exactly; extensionless resolution uses the fixed JS/TS/Vue/index candidate list, rejects multiple candidates, applies longest explicit alias prefix; no TS extension substitution or project resolver emulation | semantic | sweep |
| A-011 | Excerpt granularity and definition usage | Whole lines and whole variable/function/class declarations (including sibling declarators) may include unrelated references which are also traversed; counts merged snippets carrying reasons, including definitions already in seeds; not symbols or retrieval effectiveness | semantic | sweep |
| A-012 | Context seed size | Keep exact evidence line ranges rather than automatically including the enclosing function | semantic | default |
| A-016 | Unresolved inventory | Unbound names, parameter bindings and type-only references do not request definitions or individual gaps; unresolved covers recognized unsupported/omitted relationships only | semantic | sweep |
| A-017 | Vue boundary | Normal script and setup scopes stay separate; only normal script contributes exports; template/cross-block gap always recorded for selected Vue code; external template, custom blocks, external script or unsupported script language reject enrichment of the whole Vue file | semantic | sweep |
