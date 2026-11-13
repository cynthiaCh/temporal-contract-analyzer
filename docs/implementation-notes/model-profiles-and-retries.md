# Implementation assumptions

- New protocol V6 replaces V5 for new execution only; historical results remain readable and are never migrated or replayed automatically.
- One frozen model profile applies to all LLM roles. Profile selection does not certify model availability. The existing Codex transport supports Responses-compatible providers; other API dialects require a separate adapter.
- A transient transport failure may restart a stage at most twice, with its original input snapshot. Partial failed work is archived, not submitted. Retries share the original stage request and time caps and do not add visible/Gold evaluations or extra accepted Action candidates.
- Native CLI request and stream retries stay at zero so every restart is explicit and metered. Invalid output, authentication/configuration errors, unknown usage counters, timeout, cancellation, archive failure and unconfirmed cleanup are not retried.
- Interrupted started stages remain blocked from silent replay. This change does not rerun the Ruby/Vue2 historical failures or launch paid requests.

## Offline verification

`PYTHONPATH=tests:. python3 -m unittest test_model_profiles_and_retries test_tempoevo_v4 test_training_acceptance test_tempoevo_docker test_execution_backend test_docker_backend test_analysis_runner`

Result: 94 tests passed. `compileall` and `git diff --check` also passed. The original Ruby and Vue2 error archives both match the new transient transport classifier. No historical artifact was rewritten and neither case was rerun. Provider behavior beyond the fake CLI/command boundary remains unverified by live calls.
