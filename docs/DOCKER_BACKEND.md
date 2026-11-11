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
TCA_BENCH_ROOT=/path/to/swe-tempoc python3 -B -m temporal_contract_analyzer experience-evolution docker-check check.json --root /path/to/new-check
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
python3 -B -m temporal_contract_analyzer experience-evolution docker-calibrate calibration-input.json --root /path/to/new-calibration
```

It scores the original, the original plus its registered bounded reference, and
the supplied negative control once each. Synthetic controls must be labeled and
cannot count as model repairs. Reference must pass with complete known behavior,
degenerate must fail, and behavior keys must match. Failed attempts remain
separate records. `calibration.json` binds source/scorer hashes, both image IDs,
runtime paths/versions and evidence digests. Runtime errors are infrastructure
errors. No model is called and no reference patch is sent to a solver.

## Evolution integration

Use the existing [evolution configuration](EXPERIENCE_EVOLUTION.md), adding
`backend` above, selecting the container `node` path, supplying the host public
`binary`, and assigning the parsed calibration object to `calibration`. One reviewed public task/source/Contract/labels/facts analysis is shared per
case. Omitted analysis uses the existing AST-assisted extraction and review path. The controller's declared deployment requirement remains Python
>=3.9; case code and grading use the checked container runtimes.

Normal `prepare`, `run --execute`, `status` and `report` commands then
apply. Omitting `backend` retains native execution. Backend/image/runtime choices
are frozen before any session; do not change old prepared protocols or switch
backends after a failure. Code and transport changes invalidate old preparations.

Maintenance stays gpt-5.6-terra/low, 24 requests/600 seconds; reflection stays
gpt-5.6-terra/medium, 12 requests/600 seconds, no tools. One development round
remains five sessions/108 requests; evaluation remains B1/A1/A2/B2, four
sessions/96 requests. Independent original starts, serial execution, exact-version
expert activation and no-learning evaluation remain unchanged. A/B share the
actual container runtime instruction; only selected experience text differs.

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

## V2 development limits and evidence reads

The maintained CLI now prepares the [v2 protocol](EXPERIENCE_EVOLUTION.md).
Maintenance remains unchanged (gpt-5.6-terra/low, 24 requests, 600 seconds).
Extraction uses gpt-5.6-terra/medium, capped at 2 requests after two PASS starts
or 12 after valid non-PASS starts. Its evidence workspace is read-only. The
existing hook transport admits only closed-grammar workspace reader commands;
execution, writes, external reads and newline command injection are blocked.
The exact lower cap is passed to the runner/guard. No tools are expanded for
maintenance or analysis and no extra execution framework is introduced.

Input/calibration correspondence and the original candidate score are checked
once at batch startup, before model calls. Captured runtime/scorer files are
reused; per-call whole-batch/approval-history hash walks are not added. Raw and
partial responses, usage, original errors and cleanup errors remain archived by
Python. Historical Docker runs and their freezes are unchanged.
