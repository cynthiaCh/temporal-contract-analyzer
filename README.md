# Temporal Contract Analyzer

Source-derived temporal evidence for JavaScript, TypeScript, Vue and Python. The analyzer extracts syntax facts, source locations and conservative review hints. A parsed report is not a proof of a defect or of safety.

## Tool layout

- `temporal_contract_analyzer/`: analyzer, CLI, report UI, source retrieval, experience memory and bounded expert-gated evolution.
- `temporal_contract_analyzer/javascript/`: pinned Babel/Vue parser resources and npm lockfile.
- `MASTER_PROMPT.md`: link to the canonical [controller prompt](temporal_contract_analyzer/prompts/MASTER_PROMPT.md).
- `tests/`, `case-clusters/`, `templates/`, `examples/`: offline checks and small fixtures.
- `vscode-extension/`: optional editor integration source.
- `experience-memory/`: local exposed research candidates, when present in the development checkout. They are not shipped as expert-approved defaults in the clean source export.

Historical experiments, raw model outputs, interrupted runs, scores and publication material are preserved in a separate research archive. See [archive boundaries](docs/ARCHIVE.md) and the local cleanup record, when present. Removing working files does not rewrite Git history.

## Requirements and use

Python 3.9+ is the declared runtime. Node.js and the locked npm parser dependencies are needed for JS/TS/Vue analysis. Python analysis does not require Node. No installation or model execution occurs on import.

From a source checkout:

```sh
python3 -B -m temporal_contract_analyzer --help
python3 -B -m temporal_contract_analyzer scan /path/to/candidate --format json --output /path/to/new-report.json
```

Install parser dependencies explicitly if absent (not performed by the cleanup):

```sh
npm ci --prefix temporal_contract_analyzer/javascript --ignore-scripts --no-audit --no-fund
```

For a wheel installation, the parser scripts and lockfile are inside the installed `temporal_contract_analyzer/javascript` directory; provision those locked Node dependencies explicitly in your deployment. Python wheels exclude `node_modules`.

## Experience workflow

Use one experience collection with multiple R/O/B/L/I/F/A obligation labels. Mechanism predicates and exclusion boundaries determine applicability; matching a label alone does not authorize delivery. Source-context retrieval and experience retrieval remain distinct inputs.

On macOS, double-click [launch-experience-review.command](launch-experience-review.command) to open this repository's experience review queue. The page shows pending and reviewed versions with counts and filters. Keep the terminal open while reviewing; press Ctrl+C to stop the service. Opening the page does not submit a decision, activate an experience, or call a model.

```sh
python3 -B -m temporal_contract_analyzer taxonomy
python3 -B -m temporal_contract_analyzer experience-memory init --store /path/to/new-memory
python3 -B -m temporal_contract_analyzer experience-memory verify --store /path/to/memory
python3 -B -m temporal_contract_analyzer experience-memory review --store /path/to/memory
```

[Architecture and source map](docs/ARCHITECTURE.md), [memory format and retrieval](docs/EXPERIENCE_MEMORY.md), [taxonomy](docs/CONTRACT_TAXONOMY.md), and [bounded evolution](docs/EXPERIENCE_EVOLUTION.md) document the interfaces. Experience Review is the sole human business checkpoint: edit or accept exact candidate content, Approved records enter default retrieval immediately, including historical records and approved revisions; taxonomy/protocol versions and cross-case effect validation do not gate eligibility. Task evidence must still satisfy their applicability and exclusion predicates. New batches omit extra AI audit calls and blocking citation-format checks; the separately authorized worker can collect optional effect validation and update the preferred selection; opening or submitting the page cannot start models. Evaluation uses a frozen snapshot and cannot learn. No paid calls are authorized by reading this README.

## Optional integrations

For automatic AST-assisted Auto Contract extraction, omit `visible` from an
`experience-evolution prepare` configuration. The first `run --execute` performs
one analysis session, then starts repairs. Quote/line mismatches are nonblocking
notes. Reflection candidates go directly to the single human content review.
`experience-evolution work --root BATCH --execute --watch` continues an authorized
batch after edits/decisions; it never invents human acceptance. See the
[execution flow](docs/EXPERIENCE_EVOLUTION.md).

- The report UI can be opened with `python3 -B -m temporal_contract_analyzer reports open`.
- On macOS, double-click `launch-ast-review.command` to open AST evidence review. It restarts the configured report service in the foreground; keep the terminal open and press Ctrl+C to stop it. Report annotations, analysis review and experience activation use separate records.
- Benchmark execution requires the separately provisioned benchmark, matching scoring runtime and calibration. Set `TCA_BENCH_ROOT` explicitly for reproducible use; checkout-based sibling discovery remains a compatibility convenience.
- The native evolution runner requires explicit executables, isolation tools and version-bound evidence; importing it cannot start a historical scheduler.
- The [Docker backend](docs/DOCKER_BACKEND.md) reuses pinned SWE-TempoC public solver and trusted grading images, with zero-model checks and calibration and the same bounded evolution and expert activation rules.

## Offline verification

```sh
python3 -B -m unittest discover -s tests
python3 -B examples/workflow_v3_demo.py --root /tmp/tca-v3-demo-new
python3 -B tools/export-release.py /path/to/new-clean-export
```

Tests use synthetic runners and fixtures. They do not establish repair benefit or generalization. Respect each case's minimum Python version; an unavailable scoring runtime is not a behavior failure.

## Distribution status

This is a prepared source tree, not a published release. The owner has not selected a project license. Preserve upstream notices for any separately redistributed third-party code. No license grant or venue acceptance is implied. The exported source excludes exposed research memory, original experiment data, installed dependencies and Git history.

The current [v3 development protocol](docs/EXPERIENCE_EVOLUTION.md) preregisters
one source task, two other independent transfer sources and a boundary
input. Both successful and failed starts may yield one increment or no_update.
Default activation requires cross-source whole-task improvement and exact content
acceptance with persisted authorization. Review-only never enables automatically.
Edits receive their own exact-version human content decision and fresh effect task. AI audit steps are not part of the new default policy. Historical
active records are retained without automatic new-protocol
qualification. Frozen milestone evaluation shares public analyses and never learns.
Real training/evaluation must be explicitly launched; offline fixtures are not
repair-benefit evidence.

## TempoEvo V4

The new `tempoevo` CLI runs up to **three Actions per independent trajectory**,
with visible deterministic feedback, optional Contract revision and first-pass
stopping. Learning stages success candidates or waits for a real human failure
summary; held-out testing reads frozen approved memory and cannot learn.
All V4 LLM stages use `gpt-6.1-sol / medium`. Historical V1–V3 batches retain their
existing protocol semantics. See [V4 protocol, budgets and limitations](docs/TEMPOEVO_V4.md)
and [configuration examples](examples/tempoevo-v4/learning.json).
