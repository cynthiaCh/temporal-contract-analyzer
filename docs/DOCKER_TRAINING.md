# Docker preparation and execution

Use this guide to provision and launch research runs. See
[WORKFLOW.md](WORKFLOW.md) for conditions, budgets and evaluation semantics.
Commands run from the repository root; replace paths and image placeholders.
Reading this guide or preparing a trajectory does not authorize model calls.

## Runtime and images

The batch preparation/launch path documented here uses Docker. The core backend
also retains a native isolated execution branch; Docker is not a universal CLI
configuration gate. Native setup depends on its own Linux isolation/runtime
requirements and is not provisioned by this guide. The host schedules Docker
stages and retains archives;
model stages, optional AST extraction and assessments run in containers. Use a
local Linux Docker engine and provisioned solver/grader images. Inspect immutable
IDs instead of treating a mutable tag or an image's historical name as a model
configuration:

```sh
docker image inspect --format '{{.Id}}' YOUR_SOLVER_IMAGE
docker image inspect --format '{{.Id}}' YOUR_GRADER_IMAGE
```

If the base required by `containers/tempoevo/Dockerfile` is locally available,
build the solver explicitly (no benchmark source is copied):

```sh
DOCKER_BUILDKIT=0 docker build --network none --pull=false -t tempoevo-solver:v4 containers/tempoevo
```

The derived image supplies language runtimes/dependencies. Inspect the Dockerfile
and current environment for versions; select the model separately with
`--model-config` / `--model-profile`. Profile resolution and frozen values are in
`_session_runtime/model_settings.py` and each prepared `protocol.json`.

The public Linux agent executable and, for Codex code-mode use, its
`codex-code-mode-host` companion must be available to the solver. Existing offline
preflight probes the companion's IPC/engine without model calls; this does not
establish successful live provider or delegated-tool execution.

## Prepare a registered batch

The preparer defaults to `cases/train70.csv` for learning and `cases/test30.csv`
for testing. Set `TCA_BENCH_ROOT` to the provisioned benchmark when needed; it is
not a global configuration change. Use a fresh root:

```sh
TCA_BENCH_ROOT=/absolute/benchmark python3 -B tools/tempoevo-docker/prepare_selected.py \
  --root /new/batch --limit 10 \
  --solver-image sha256:ACTUAL_SOLVER_ID --grader-image sha256:ACTUAL_GRADER_ID \
  --mode learning --condition structured --store experience-memory/library
```

Preparation makes no model calls. Learning scores original/reference/negative
controls before preparing each case; reference must pass and original/negative
must fail. Testing does not pre-score candidates with hidden Gold; if a visible
evaluator is supplied, preparation checks its original candidate. Invalid controls
or missing inputs leave preparation failed rather than starting a model.

Useful preparation options (see `prepare_selected.py --help` for the full set):

| Option | Purpose |
|---|---|
| `--selection-file`, `--start-rank`, `--limit` | Select ranked cases |
| `--model-config`, `--model-profile`, `--binary` | Select profiles and Linux agent executable |
| `--mode testing --condition structured` | Frozen standard testing |
| `--condition baseline` / `contract` | Explicit no-memory conditions |
| `--condition latent_experience --frozen-selections PATH` | Testing-only replay without a new selection model call or Contract |
| `--memory-snapshot PATH` | Validate an explicit approved snapshot against the store |
| `--with-ast` | Enable optional AST; default is disabled |
| `--visible-evaluators PATH` | Optional existing public evaluator mapping |
| `--training-feedback PATH` / `--training-feedback-by-family PATH` | Learning-only public checkpoint mappings |
| `--learning-policy online --online-memory PATH` | Structured learning with a separate provisional pool |

Current experience retrieval requires reviewed, current Abstracts. Missing AST
coverage for Go/Ruby/PHP/Java remains `unsupported_language`, not inferred syntax
facts; full public-source reading is still available. Testing forbids online pools
and training acceptance feedback. No automatic case promotion or review occurs.

## Execute and inspect

For a batch produced directly by the preparer (`progress.json` at its root):

```sh
python3 -B tools/tempoevo-docker/run_selected.py --root /new/batch --execute
```

This launcher runs cases serially through the public CLI and publishes success
candidates as unapproved proposals. Each case retains its own trajectory and logs.
For an individually prepared trajectory, the equivalent public commands are:

```sh
python3 -B -m temporal_contract_analyzer tempoevo run --root /new/batch/CASE_ID/trajectory --execute
python3 -B -m temporal_contract_analyzer tempoevo status --root /new/batch/CASE_ID/trajectory
```

The parallel `run_testing.py` is for roots that already contain `plan.json` and
`batch/progress.json`; it is not interchangeable with the direct preparer's root:

```sh
python3 -B tools/tempoevo-docker/run_testing.py --root /prepared/testing-plan --workers 4 --execute
```

Workers count concurrent cases, not attempts per case. Inspect `protocol.json`,
`state.json`, `summary.json` and logs for actual settings, usage and failures.
`status` reads retained results without rewriting old bindings; executing/resuming
verifies them. Never blindly replay an incomplete started stage or resume an old
root after changing its frozen implementation inputs.

## Evaluator contracts and isolation

Examples of single-trajectory configuration live in `examples/tempoevo-v4/`.
Each container evaluator declares `image`, `command`, `seconds` and an `inputs`
mapping from frozen host regular files to container destinations. The candidate
is appended as `/submission`. Dependencies must be declared inputs or already in
the image; inputs cannot replace submission/runtime mounts. Learning requires
`training_evaluator`; testing requires separate `gold_evaluator`. A visible
result supplies `passed`, `observations`, `regressions`, `unknowns`; explicit
`valid:false` means execution invalid. See `tempoevo_backend.py` and
`tempoevo_docker.py` for validation, rather than inventing evaluator fields.

Solver containers receive public candidates, runtime/guard/schema files and
provider authentication. They do not mount scorers, references, archives, grader
images or the Docker socket. Existing transport uses host networking and forwarded
proxy settings; it is not a provider-only firewall. Evaluators and AST containers
have networking disabled and no model credentials. Grading inputs/submissions are
read-only; temporary compilation/cache paths are disposable. Containers must stop
before snapshots or scores are finalized; unconfirmed cleanup invalidates execution.

Only Action edits business code; analysis sessions are read-only. Raw and partial
outputs, measured usage and original errors stay in the run archive. Transport
restarts share frozen stage caps; infrastructure/boundary errors are not repair
failures. Existing internal bindings remain required, but ordinary runs need no
additional hand-written checksum inventories.

## Separate offline compatibility API

`docker_backend.offline(config, new_root, calibrate=False|True)` retains legacy
`legacy-js` / Python runtime and three-control calibration support. Its config
includes a registered `case_id`, public `binary`, runtime `node` and a `backend`
with immutable solver/grader IDs; calibration also takes `degenerate_candidate`.
It neither calls models nor supports every current benchmark adapter. For current
registered language cases use the batch preparation path above. Inspect
`docker_backend.py` for this separate API before using it; do not revive a retired
scheduler from historical examples.
