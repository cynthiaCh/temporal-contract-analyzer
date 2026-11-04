# Build Note

| Rung | Feature | Check | Status |
|---|---|---|---|
| F0 | Existing scored patch → feedback-free retrieval packet | synthetic retrieval test | passed |
| F1 | Single-job RAG preparation + existing regression evaluator | new integration and old repair suites | passed |
| F2 | 11 real RAG jobs + historical-control comparison | frozen artifacts and saved oracle checks | completed and verified |

## Run record

- New RAG 3 tests; existing repair 7, workbench 16 (Python 3.11 oracle override), context 20 all passed: 46 targeted tests. Browser JavaScript syntax and git diff whitespace checks passed.
- Read-only preflight: all 11 parents and 22 historical controls matched inputs, model/effort/mode/timeout/config route and effect provenance.
- Fresh gpt-6-astra/xhigh review: no undeclared material assumptions or feedback leakage found; same-family provisional. Legacy 11 paired manifests independently validated without mutation.
- Retrieval on all11 snapshots: 3583–10279 source/text characters, at most eight seeds. Small cases permit coverage of most source; no large-repository claim.
- Live 11-job RAG campaign completed normally. All 11 calibrations PASS; all parent regression comparisons verified; same-source/settings checks against 22 historical records passed again in independent recomputation.
- Result: RAG 3/11 whole tasks, D historical 2/11, hypothesis historical 4/11. Raw required-effect counts 76/100, 79/100, 77/100 respectively. RAG has one regressing candidate (two lost checks), marked ineligible. Reject-regression/retain-parent totals: RAG 78/100, D 79/100, hypothesis 81/100; no automatic promotion.
- RAG output tokens 43252 versus hypothesis 74233 (~42% lower); actual tokens are not equal and controls are historical. No causal-significance or general-RAG claim.
- Artifacts: results/rag-only-v1-20261104/campaign/{COMPARISON.md,summary.json,verified-results.json,results.csv,checks.csv,retrieval-coverage.json}. No live stubs; unselected/unsupported relations remain explicit.

## Scope and deferred

Lexical BM25 only. No external vector service, full semantic call graph, effect-proof claim, contemporaneous control rerun, or automatic adoption. Historical controls are explicit.

## Semantic and interface choices (full ledger)

# Assumption Ledger

ASK mode: never

| ID | Under-determined by request | Chosen | Class | Source |
|---|---|---|---|---|
| R-001 | Meaning of standalone RAG | Original task + retrieved candidate code/Markdown only; no D explanations, oracle feedback, hypothesis templates or memory in model inputs. | semantic | default |
| R-002 | Retrieval mechanism and corpus | Local BM25 over 48-line overlapping chunks of the frozen scored candidate; query is verbatim original task. Reuse parsed lexical/local-import definition expansion up to depth 2. No embeddings or external knowledge base. | semantic | default |
| R-003 | Which runs and controls | Same 11 original D failures as v2, one RAG attempt each; reuse historical v2 D/hypothesis controls, verify identical parent snapshot and settings. Not a fresh randomized paired campaign. | semantic | default |
| R-004 | Retrieval budget | Up to eight ranked chunks and 8000 seed code/text characters, then expand within 12000 total source characters; record omissions and incomplete parsing. Same model/effort/timeout caps, actual tokens measured separately. | interface | default |
| R-005 | Researcher-side oracle use | Scored source selection, calibration and regression checks remain oracle-informed outside model inputs. Retrieval accepts only task, public candidate bytes and lexical parser information. | semantic | default |
| R-006 | Integration | Add an opt-in single-job RAG preparation method; preserve the existing two-arm hypothesis-repair API and archived manifests. No UI redesign or automatic patch promotion. | interface | default |
