> 当前经验增长实验审查入口：[CURRENT_EXPERIMENT.md](CURRENT_EXPERIMENT.md)。本分支对应实际运行 v4，未合并后续 master 更新。

# TempoEvo

TempoEvo combines temporal-contract analysis, contract-guided repair and reusable experience. Its Temporal Contract Analyzer component extracts syntax facts, source locations and conservative review hints for JavaScript, TypeScript, Vue and Python. A parsed report is not a proof of a defect or of safety.

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

[Architecture and source map](docs/ARCHITECTURE.md), [memory format and retrieval](docs/EXPERIENCE_MEMORY.md), [taxonomy](docs/CONTRACT_TAXONOMY.md), and [current workflow](docs/WORKFLOW.md) document the interfaces. Experience Review accepts exact immutable candidate versions; edits require their own acceptance. Approved records, including historical records, are eligible for future frozen retrieval snapshots when public task/source evidence satisfies their applicability and exclusion predicates. Cross-case effect validation is not an eligibility gate. Success candidates and human failure summaries remain unapproved until reviewed. Opening or submitting the review page cannot start model execution. Held-out testing reads a frozen approved snapshot and cannot learn. No paid calls are authorized by reading this README.

## Optional integrations

The only training/testing execution entrypoint is `tempoevo run --execute`.
Prepare new V12 trajectories with `tempoevo prepare`. Historical V1–V3 batches are
read-only: `history status --root BATCH` or `history report --root BATCH`.
The retired `experience-evolution` command and old orchestration modules are removed.
Shared native/Docker/scoring infrastructure remains separate from trajectory policy.

- The report UI can be opened with `python3 -B -m temporal_contract_analyzer reports open`.
- On macOS, double-click `launch-ast-review.command` to open AST evidence review. It restarts the configured report service in the foreground; keep the terminal open and press Ctrl+C to stop it. Report annotations, analysis review and experience activation use separate records.
- Benchmark execution requires the separately provisioned benchmark, matching scoring runtime and calibration. Set `TCA_BENCH_ROOT` explicitly for reproducible use; checkout-based sibling discovery remains a compatibility convenience.
- The shared native runner requires explicit executables, isolation tools and frozen runtime/evaluator bindings; importing it cannot start a historical scheduler.
- The [Docker backend](docs/DOCKER_BACKEND.md) provides shared isolation, zero-model calibration and trusted scoring infrastructure using pinned SWE-TempoC images. All new V12 model stages, AST extraction and evaluators use Docker; `tempoevo run --execute` remains the sole training entrypoint. See [Docker training setup](docs/DOCKER_TRAINING.md).

## Offline verification

```sh
python3 -B -m unittest discover -s tests
python3 -B examples/tempoevo-v4/offline_demo.py /tmp/tca-v4-demo-new
python3 -B tools/export-release.py /path/to/new-clean-export
```

Tests use synthetic runners and fixtures. They do not establish repair benefit or generalization. Respect each case's minimum Python version; an unavailable scoring runtime is not a behavior failure.

## Distribution status

This is a prepared source tree, not a published release. The owner has not selected a project license. Preserve upstream notices for any separately redistributed third-party code. No license grant or venue acceptance is implied. The exported source excludes exposed research memory, original experiment data, installed dependencies and Git history.

## Current construction and testing

See [WORKFLOW.md](docs/WORKFLOW.md) for the single current description of stages,
feedback, budgets and memory review. The fixed construction recipe uses V8
source-bound routing, up to three Actions, and public checks plus the training
Oracle for acceptance. It updates external experience, not model weights.

Testing defaults to business applicability selection from the full frozen approved
library, an Auto-Contract draft, one bounded repair Action and one independent
final Gold score. There is no Contract Review, Gold-driven testing retry or
automatic A/B run. Existing project tests may be run inside the Action budget.
The [current test10 configuration](examples/tempoevo-v4/case-selections/swe-tempoc-paired10-sol6-20261116/testing-protocol-business-full-memory.json)
records the completed 39-entry, four-worker diagnostic run.

New runs require fresh V12 roots. Historical results and decisions stay unchanged.
CSV ranks 1–25 remain reserved for construction and 26–50 for testing; reserved
test IDs cannot run learning. Historical outcome-based selection and shared source
families mean this split is not certified unseen. Independent generalization
requires separate evidence.
