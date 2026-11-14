# V8: online provisional learning and frozen evaluation

V8 defines the online provisional channel. New execution uses [V9](TEMPOEVO_V9.md), which explicitly forwards cumulative within-task diagnoses. V8 roots used `tempoevo-trajectory-v8`; historical roots remain readable and cannot
silently resume under the new runtime. Model weights, three-Action limits,
deterministic scoring, controlled training feedback, transport recovery and human
expert identity requirements remain unchanged.

## Two explicit policies

- `learning_policy: frozen` (default): use the approved snapshot prepared for this
  trajectory. Training ablations and held-out testing do not read a temporary pool.
- `learning_policy: online`: requires `mode: learning`, condition `structured` or
  `bm25`, a nonempty `task_id` and an explicit `online_memory` path separate from
  candidate/trajectory and long-term store. A fresh unreviewed candidate is immediately
  eligible for subsequent training tasks; no effectiveness or human-approval gate
  precedes that trial use. Existing applicability/exclusion routing and the combined
  delivery cap of five still apply. Eligibility does not guarantee a match.

```sh
python3 -m temporal_contract_analyzer tempoevo prepare \
  examples/tempoevo-v4/online-learning.json --root /new/task-run
```

Replace example absolute paths before preparing. The Docker batch helper supports:

```sh
TCA_BENCH_ROOT=/absolute/benchmark python3 -B tools/tempoevo-docker/prepare_selected.py \
  --root /new/batch --start-rank 1 --limit 25 --condition structured \
  --learning-policy online --online-memory /new/batch/provisional \
  --solver-image sha256:ACTUAL_SOLVER_ID --grader-image sha256:ACTUAL_GRADER_ID
python3 -B tools/tempoevo-docker/run_selected.py --root /new/batch --execute
```

These commands are examples, not authorization to run paid experiments. The launcher
is sequential; all model calls still belong to the public `tempoevo run --execute` CLI.

## Actual feedback loop

1. Keep the approved base library frozen at preparation.
2. At task execution start, capture the shared provisional pool into an immutable,
   digest-bound `online-snapshot.json`. Exclude this trajectory and the same `task_id`
   so independent repeats cannot consume their own prior answers.
3. Match approved and provisional guidance together. Selected provisional hashes are
   recorded in `delivery.json`; LLM text explicitly says unreviewed training guidance
   with unknown effectiveness and requires checking public task/source evidence.
4. Each evaluated Action logs provisional usage plus acceptance outcome under the
   pool's `usage/`. These observations do not automatically prove causal effectiveness.
5. After training acceptance and successful extraction, automatically enqueue changed
   guidance before optional long-term candidate publication. A human-submitted expert
   failure summary can also enqueue; three failures alone never invent an expert summary.
6. Later tasks see these records even if they were prepared earlier. A running task
   never rereads concurrent pool updates; resume retains its original online snapshot.

Evidence-only supplements contain no new rules and do not create duplicate provisional
guidance. New/revised/merged temporary guidance is stored under `entries/` as immutable
standalone training candidates retaining the full reflection plan and source record.
Revisions targeting provisional records can be staged for long-term review as new
identities with source links when their parent is not in the long-term library; they
never silently install an unknown parent or inherit approval.

The temporary pool is not the default long-term experience library. Enqueueing writes
no approval, acceptance or activation decision. Human review remains immediately
available through normal candidate publication, without any effectiveness prerequisite;
acceptance controls future approved-library snapshots. Frozen ablations and testing
cannot specify an online pool. Online results are order-dependent training results,
not a matched frozen-memory ablation or independent held-out score.

## Budgets, failure and verification

No LLM stage is added: extraction uses the existing request/time budget, and storage,
snapshotting and usage logging are deterministic. Existing diagnosis still reaches the
next Action immediately. Candidate generation requires a valid accepted source for a
success experience, not proof of transfer effectiveness. Unknown/failed execution does
not create successful guidance. Cancellation and started-stage replay protections remain.
Pool and snapshot tampering fail explicitly; successful enqueue is idempotent. Existing
historical candidates are not automatically imported, approved or replayed.

Offline tests use synthetic models/evaluators, including pre-prepared sequential tasks,
real routing with known/unknown applicability, mid-task concurrent arrivals, frozen/test
isolation, expert submission, idempotence and digest checks. No live model or paid
training is started for this implementation.
