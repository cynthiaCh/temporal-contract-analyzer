> Shared offline Docker/calibration infrastructure is retained. For deterministic checks use
> `docker_backend.offline(config, new_root, calibrate=False|True)` from Python;
> V4 model execution remains `tempoevo run --execute`. This document retains
> image/isolation details, not an executable legacy workflow.

# SWE-TempoC Docker backend

The evolution controller reuses existing public solver and trusted grading
images. It keeps its own guarded single-session runner, schemas, accounting,
archival, expert gate and stop rules. It never imports a SWE experiment scheduler.
The adapter covers the current registered `legacy-js`/`python` probe contracts;
it does not claim support for every SWE-TempoC task. Initial admission is limited
to self-contained vanilla-js and Python. Frontend/upstream dependency mounting
has not been validated on the solver side and is rejected before model dispatch.

## Images and zero-model preparation

Use a local Linux Docker engine and locally available images. Commands never
pull, build or install dependencies. Obtain immutable IDs explicitly:

```sh
docker image inspect --format '{{.Id}}' YOUR_SOLVER_IMAGE
docker image inspect --format '{{.Id}}' YOUR_BENCHMARK_IMAGE
```

Create `check.json` with these fields (the image values below are placeholders):

```json
{
  "case_id": "REGISTERED_CASE",
  "binary": "/absolute/path/to/public/codex",
  "node": "/runtime/node16/bin/node",
  "backend": {
    "kind": "docker",
    "solver_image": "sha256:FULL_64_HEX_IMAGE_ID",
    "grader_image": "sha256:FULL_64_HEX_IMAGE_ID",
    "grader_node": "/opt/swe-tempoc/.swe-tempoc/toolchains/node-v16.20.2/bin/node"
  }
}
```

For the separate corpus, set `TCA_BENCH_ROOT` for the process; no global change:

```sh
# Python API: docker_backend.offline(config, Path('/new/check'), calibrate=False)
```

This checks actual runtime versions, solver isolation, the supplied public CLI,
image IDs and scorer/input hashes. Benchmark cases must match scoring sources
inside the frozen image. Self-contained local cases mount only their case
directory into the trusted grader. Streams, errors and container state are saved.

The public CLI's `codex-code-mode-host` companion must also exist and be mounted
at `/opt/codex-code-mode-host`, the sibling path used by the CLI. Preflight starts
that executable inside the solver image, negotiates IPC version 1, opens a session
and executes a deterministic JavaScript expression without tools, credentials or
model access. Its frames and hashes are saved separately in
`solver-code-host.json`; grading-runtime identity remains unchanged, allowing
valid original/reference/negative calibration to be reused. Missing companions,
unknown protocol shapes and engine errors block before model dispatch.
This startup/engine probe does not establish end-to-end delegated tool operation
with a model. CLI `--version`, `--help` and fake-CLI transport checks alone do not
establish that capability.

For three-control calibration, add `degenerate_candidate` to the same JSON object
with an explicit negative-control directory, then run:

```sh
# Python API: docker_backend.offline(config, Path('/new/calibration'), calibrate=True)
```

It scores the original, the original plus its registered bounded reference, and
the supplied negative control once each. Synthetic controls must be labeled and
cannot count as model repairs. Reference must pass with complete known behavior,
degenerate must fail, and behavior keys must match. Failed attempts remain
separate records. `calibration.json` binds source/scorer hashes, both image IDs,
runtime paths/versions and evidence digests. Runtime errors are infrastructure
errors. No model is called and no reference patch is sent to a solver.

## V4 integration

Use the [V4 configuration and CLI](TEMPOEVO_V4.md) for new learning and testing.
`tempoevo run --execute` is the only model-execution entrypoint. Its current
`NativeV4Backend` uses isolated native model sessions; adding the Docker `backend`
object above to a V4 configuration does not select containerized model execution.
The shared Docker adapter remains available for deterministic preparation and
trusted scoring. Historical V1–V3 batches are read-only through `history status/report`.

V4 accepts separate visible and gold evaluator commands, each receiving the
candidate path as its final argument. A trusted evaluator wrapper can invoke
`DockerBackend.raw_score(protocol, candidate, output_directory)` with frozen case,
image and scoring-input identities for independent gold scoring. Keep its output
directory outside the candidate. Gold scores and hidden behavior details cannot
be used as visible feedback; public checks must be supplied separately.

All V4 model stages use `gpt-6.1-sol / medium`. Each independent trajectory has at
most three Actions and stops at the first visible pass. Success experience remains
a candidate until human acceptance; three valid failures request a real human
expert summary. Testing reads frozen approved memory and cannot write experience.
See the V4 protocol for stage budgets, feedback boundaries and recovery semantics.

## Isolation and retained results

Solver containers have a read-only root, dropped capabilities, resource limits,
one writable candidate, public CLI/schema/guard files, an ephemeral auth-only
profile and a Unix hook decision socket. No archive, meter, scorer, benchmark
source or Docker socket is mounted. Host networking follows the existing SWE
solver arrangement for provider/proxy compatibility; it is not provider-only
network filtering. Proxy values are forwarded by name without command-log secrets.

Graders have network disabled, no model credentials, read-only submissions and
the original trusted probe. Its authorization, verdict and 60-second scoring
limit remain unchanged. Additional runtime/dependency needs must pass offline
calibration; isolation is not silently relaxed.

Raw stdout/stderr and full scores are retained. For probes with explicit
`schedules[*].passed` but no `observed_effects`, the returned score adds a clearly
derived `behavior_states` vector and raw digest. It copies literal values;
missing/null stays unknown. Raw scores and verdicts are unchanged. Existing
observed-effect semantics remain unchanged. Schedule names are not root causes
or business-policy evidence.

Containers must stop before snapshots/scoring, including on bridge timeout.
Cleanup errors are separate from original service errors and invalidate the
session. An actor whose stop is unconfirmed is not snapshotted as complete.
Partial responses and null usage remain unknown. There are no hidden retries,
replacement slots or implicit expert approvals. Offline/synthetic validation
does not establish live provider availability, repair benefit or generalization.

## Limits and evidence reads

V4 freezes the original source, approved experience snapshot, evaluator inputs,
model configuration and stage limits when preparing each trajectory. Actions have
at most 24 requests each; routing, Contract, diagnosis and success extraction have
at most 12 requests each. Every model stage has a 600-second upper bound.
The [V4 budget calculation](TEMPOEVO_V4.md#budgets-recovery-and-outputs) includes
all applicable stages; historical starting-repair and correction budgets do not apply.

Contract analysis, diagnosis and extraction use independent read-only sessions;
only Action edits a candidate workspace. Raw and partial responses, actual usage,
original errors and cleanup evidence remain archived. Historical Docker runs,
budgets, scores and frozen inputs are unchanged.
