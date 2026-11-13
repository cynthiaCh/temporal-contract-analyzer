# V4 Docker training

New live `tempoevo run --execute` runs require Docker. The host schedules bounded
stages and preserves archives; AST extraction, every model role and both
assessments execute in containers. Historical trajectories are not migrated.
`tempoevo status` reads retained results without rewriting or requiring current
runtime hashes; resuming/executing still verifies frozen bindings.

Build the public solver from the locally provisioned base (no benchmark copied):

```sh
DOCKER_BUILDKIT=0 docker build --network none --pull=false -t tempoevo-solver:v4 containers/tempoevo
docker image inspect --format '{{.Id}}' tempoevo-solver:v4
```

The base tag is only a build locator. Prepare trajectories with the actual immutable
image ID, not the tag. The provisioned base is
`sha256:ed6905e35d7447258027d595beb5f04ec902fd4235ceeac9e5eb120d40124b16`.
The derived image supplies `/runtime/node` and retains Node16/18/24, Python, Go,
Ruby, PHP, Java and frontend dependencies. Model configuration always comes from
V4 (`gpt-6.1-sol / medium`), never an image's historical name.

Configuration examples are under `examples/tempoevo-v4/`. `backend` selects the
solver/grader immutable IDs and `solver_node`. Each evaluator declares `image`,
container `command`, and an `inputs` mapping from frozen host regular files to
container destinations. The submission is appended as `/submission`. Evaluators
must emit JSON with `passed`; visible checks also emit complete `observations`,
`regressions`, and `unknowns`. Explicit `valid:false` aborts as execution invalid.
Evaluator input files cannot replace submission or runtime mounts. Their hashes
are frozen when preparing. Script dependencies must all be declared as inputs or
already belong to the frozen image.

The solver mounts only public candidate files, the CLI, schema, request guard and
an ephemeral authentication profile. It has no grader image, scorer, reference,
archive, or Docker socket mount. Model calls require network access; the existing
solver transport uses host networking and forwarded proxy settings, not a
provider-only firewall. Evaluators/AST have network disabled and no model credentials.
Grader sources and submissions remain read-only; only disposable `/tmp`, native
compilation caches and wire-log directories are writable. All owned containers
must stop before candidate snapshots or evaluation returns.

Go/Ruby/PHP/Java source reads now count toward body proof. Their AST coverage
remains explicitly `unsupported_language`, not invented syntax facts; Python and
JS/TS/Vue retain deterministic parsers. Missing AST coverage does not silently
invent contract premises. Public-source textual routing must still establish
applicability before any approved experience is delivered.

The first ten historical selections are registered through
`experiments/training-cases.json`. Registration does not certify runtime readiness:
perform original/reference/negative control calibration first. Public examples in
`tools/tempoevo-docker/public_checks.cjs` use task/README obligations. Trusted
language RPC scaffolding stays in the grader, separate from hidden assertions,
schedules and scoring. Gold uses the unchanged original probe independently.
Neither scaffold nor hidden gold is mounted into the model's solver workspace.

Each trajectory retains the same maximum three Actions, fixed model, first-visible-pass
stop, separate gold result, manual review and bounded request limits. There are no
automatic paid retries or extra attempts when infrastructure fails.

Prepare and run a selected prefix (preparation is zero-model):

```sh
TCA_BENCH_ROOT=/absolute/benchmark python3 -B tools/tempoevo-docker/prepare_selected.py \
  --root /new/batch --limit 10 --solver-image sha256:ACTUAL_SOLVER_ID \
  --grader-image sha256:ACTUAL_GRADER_ID
python3 -B tools/tempoevo-docker/run_selected.py --root /new/batch --execute
```

The launcher invokes the public V4 CLI serially. Partial started stages are never
replayed. Every case has a separate archive; the batch shares one approved frozen
snapshot and never approves its newly extracted candidates. Calibration failures
remain `not_started`; execution failures retain their actual requests and errors.
