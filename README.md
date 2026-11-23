# TempoEvo

TempoEvo combines temporal-contract analysis, contract-guided repair and reusable experience. Its Temporal Contract Analyzer component extracts syntax facts, source locations and conservative review hints for JavaScript, TypeScript, Vue and Python. A parsed report is not a proof of a defect or of safety.

## Tool layout

- `temporal_contract_analyzer/`: analyzer, CLI, report UI, source retrieval, experience memory and bounded expert-gated evolution.
- `temporal_contract_analyzer/javascript/`: pinned Babel/Vue parser resources and npm lockfile.
- `MASTER_PROMPT.md`: link to the canonical [controller prompt](temporal_contract_analyzer/prompts/MASTER_PROMPT.md).
- `tests/`, `case-clusters/`, `templates/`, `examples/`: offline checks and small fixtures.
- `vscode-extension/`: optional editor integration source.
- `experience-memory/`: local exposed research candidates, when present in the development checkout. They are not shipped as expert-approved defaults in the clean source export.

Historical experiments, raw model outputs, interrupted runs, scores and publication material are preserved in a separate research archive. See [archive boundaries](docs/ARCHIVE.md). Removing working files does not rewrite Git history.

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

[Architecture and source map](docs/ARCHITECTURE.md), [experience storage and review](experience-memory/README.md), [taxonomy](docs/CONTRACT_TAXONOMY.md), and [current workflow](docs/WORKFLOW.md) document the interfaces. Experience Review edits stable entries in place; content changes require renewed approval. Accepted, active entries enter frozen retrieval snapshots when current task/source evidence supports their applicability and exclusions. Cross-case effect validation is not an eligibility gate. Success candidates and human failure summaries remain unapproved until reviewed. Opening or submitting the review page cannot start model execution. Held-out testing reads a frozen approved snapshot and cannot learn. No paid calls are authorized by reading this README.

## Optional integrations

The only training/testing execution entrypoint is `tempoevo run --execute`.
Prepare new V13 trajectories with `tempoevo prepare`. Historical V1–V3 batches are
read-only: `history status --root BATCH` or `history report --root BATCH`.
The retired `experience-evolution` command and old orchestration modules are removed.
Shared native/Docker/scoring infrastructure remains separate from trajectory policy.

- The report UI can be opened with `python3 -B -m temporal_contract_analyzer reports open`.
- The local [training/testing workspace](tools/experience-lab/README.md) can be opened with `python3 -B tools/experience-lab/serve.py --open`, or `launch-tempoevo-workspace.command` on macOS. Prepare freezes a new batch without model requests; explicit Start invokes the public execution CLI.
- On macOS, double-click `launch-ast-review.command` to open AST evidence review. It restarts the configured report service in the foreground; keep the terminal open and press Ctrl+C to stop it. Report annotations, analysis review and experience activation use separate records.
- Benchmark execution requires the separately provisioned benchmark, matching scoring runtime and calibration. Set `TCA_BENCH_ROOT` explicitly for reproducible use; checkout-based sibling discovery remains a compatibility convenience.
- The shared native runner requires explicit executables, isolation tools and frozen runtime/evaluator bindings; importing it cannot start a historical scheduler.
- The [Docker backend](docs/DOCKER_BACKEND.md) provides shared isolation, zero-model calibration and trusted scoring infrastructure using pinned SWE-TempoC images. All new V13 model stages, AST extraction and evaluators use Docker; `tempoevo run --execute` remains the sole training entrypoint. See [Docker training setup](docs/DOCKER_TRAINING.md).

## Offline verification

```sh
python3 -B -m unittest discover -s tests
python3 -B tools/export-release.py /path/to/new-clean-export
```

Tests use synthetic runners and fixtures. They do not establish repair benefit or generalization. Respect each case's minimum Python version; an unavailable scoring runtime is not a behavior failure.

## Distribution status

This is a prepared source tree, not a published release. The owner has not selected a project license. Preserve upstream notices for any separately redistributed third-party code. No license grant or venue acceptance is implied. The exported source excludes exposed research memory, original experiment data, installed dependencies and Git history.

## Current construction and testing

See [WORKFLOW.md](docs/WORKFLOW.md) for the single current description of stages,
feedback, budgets and memory review. The fixed construction recipe uses Abstract-based
business applicability selection, up to three Actions, and public checks plus the
training Oracle for acceptance. It updates external experience, not model weights.

Testing defaults to business applicability selection from the full frozen approved
library, an Auto-Contract draft, one bounded repair Action and one independent
final Gold score. There is no Contract Review, Gold-driven testing retry or
automatic A/B run. Existing project tests may be run inside the Action budget.
The testing-only `latent_experience` ablation skips Auto-Contract and replays a
frozen business selection through `prepare_selected.py --frozen-selections`.
Public-source evidence and the exact delivery digest are revalidated before
execution; only the Action and final Gold run, with a 24-turn Action cap.
Historical retrieval usage is reused, not counted as new model calls.
The [final case bundle](cases/README.md) contains the complete 100 cases under
`cases/train70/` and `cases/test30/`. The [final results](experiments/testing-runs/gpt56-library-size-ablation-20261118/README.md)
record the frozen-library-size comparison.

The [paired bootstrap index generator](tools/generate_bootstrap_indices.py)
creates shared resampling indexes for model comparisons (1,000 replicates,
seed `20260925` by default). Supply a CSV containing unique `case_id` values and
an integer label column; replace `case-results.csv` below with your input file.
The script generates indexes and provenance metadata, not pass-rate statistics.

```sh
python3 tools/generate_bootstrap_indices.py --reference case-results.csv \
  --label-column passed --output-dir /tmp/tempoevo-bootstrap
```

New runs require fresh V13 roots. Historical results and decisions stay unchanged.
The sole current split is [cases/split.json](cases/split.json): 70 development
cases and 30 test cases, with no overlapping case IDs. Reserved test IDs cannot
run learning. The cases have historical exposure and shared source mechanisms;
this split is not certified unseen.
