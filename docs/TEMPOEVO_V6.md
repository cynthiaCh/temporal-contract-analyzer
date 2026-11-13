# TempoEvo V6: frozen model profiles and bounded connection recovery

New roots use `tempoevo-trajectory-v6`. Historical V1–V5 trajectories remain readable;
execution and publication through the current runtime cannot silently resume them.
Module names retain `tempoevo_v4.py` for import compatibility. The V5 learning and
independent-testing acceptance boundaries remain unchanged.

## Model configuration

The single default configuration is
[`model-profiles.json`](../temporal_contract_analyzer/_session_runtime/model-profiles.json).
It contains named profiles and a bounded retry policy. The default is
`sol61-medium`; `sol61-low` illustrates selecting another reasoning effort.
Add profiles with another model ID and its supported reasoning effort. Each
trajectory uses one profile across routing, Contract, diagnosis, Action and
experience extraction. Model weights remain unchanged.

```sh
python3 -m temporal_contract_analyzer tempoevo prepare /absolute/config.json \
  --root /new/trajectory --model-profile sol61-low
```

Preparation config may set `model_profile` and `model_config` (the latter is a path
to another profiles JSON). CLI flags override these fields. A legacy `model` object,
if supplied, must agree with the selected profile; remove it when switching profiles.
Resolved settings are copied into `protocol.json`, and every execution archives its
actual model/effort configuration. Editing an external profile file cannot switch
an already prepared trajectory. The packaged runtime and default profile files
remain hash-bound; edits to them require a new root.

For Docker batches, preparation accepts the same flags:

```sh
TCA_BENCH_ROOT=/absolute/benchmark python3 -B tools/tempoevo-docker/prepare_selected.py \
  --root /new/batch --start-rank 11 --limit 10 \
  --solver-image sha256:ACTUAL_SOLVER_ID --grader-image sha256:ACTUAL_GRADER_ID \
  --model-profile sol61-low
```

[`compatible-provider.json`](../examples/models/compatible-provider.json) illustrates
another Responses-compatible provider. Replace the placeholder endpoint/model ID,
export the named credential environment variable externally, and pass the file with
`--model-config`. Only the credential variable's name is stored/forwarded; its value
is not embedded in CLI arguments or protocol archives. `reasoning_effort: null` and
`service_tier: null` omit those CLI overrides for providers that do not support them.

This config selects models supported by the existing Codex Responses transport.
It does not implement native Anthropic/Gemini/Ollama API dialects, change model
availability, or certify that any example model/provider is accessible. No live
provider integration has been run for this change. Existing Docker images are reused.

## Recovery and budgets

Each logical LLM stage may restart at most twice after a classified transient
connection/stream failure, giving at most three executions of that stage. The CLI's
own request/stream retries remain disabled. Each restart:

1. Waits bounded backoff (default 2 then 4 seconds), checking cancellation.
2. Verifies the frozen bindings and starts from the same stage input snapshot.
3. Uses only the remaining original request and time budget.
4. Writes its own `stages/KEY/executions/N/` archive and measured usage.

A failed session's partial workspace never becomes an accepted patch or input to
an evaluation. After a completed Action and valid failed evaluation, the next
logical Action still starts from the previous real evaluated candidate as before.
There are at most three evaluated Action candidates. Infrastructure executions and
valid behavior attempts are reported separately; recovery is not a behavioral retry.

All failed requests count against the stage and trajectory caps, including requests
whose token usage is unknown. Unknown token totals remain null; known subtotals and
unknown request counts remain separate. Summaries include transport executions,
transport retries and per-execution limits. Interrupted started stages cannot be
silently replayed, even if an earlier restart had finished; completed results are
reused without another model call.

Malformed output, 400/configuration/authentication failures, timeout/resource limits,
unknown request counts, cancellation, unconfirmed cleanup and archive errors stop
without transport recovery. Exhausted recovery yields `execution_invalid`, never
three behavioral failures or a success experience. Only three effective learning
nonacceptances create an actual human expert-summary task.

With default caps, baseline learning remains 84 requests; Contract learning 120;
structured learning with routing 132. Testing excludes extraction and uses one final
independent Gold. Recovery does **not** multiply these totals: Action's 24 requests
and 600 seconds are shared across all its executions, not allocated afresh per restart.
Use `retry_policy.max_retries: 0` for an explicitly frozen no-recovery condition.
Fair comparisons must freeze the same retry policy and model settings across arms.

## Verification and scope

Offline synthetic models, fake CLI hooks and deterministic evaluators verify
recovery, exhaustion, remaining budgets, cancellation, usage gaps, profile propagation,
command construction, credential forwarding, model mismatch and V5 read-only behavior.
Training Gold/test Gold separation and human approval remain covered by existing tests.
This change launches no paid calls, reruns no historical failed cases and commits no Git changes.
