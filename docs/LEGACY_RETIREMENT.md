# V1–V3 execution retirement

The sole public model-execution entrypoint is `tempoevo run --execute`, using
`tempoevo-trajectory-v4`. `experience-evolution` no longer exists in the CLI.
The shared native backend and packaged runner also reject live V1–V3 protocols.

Removed: `experience_evolution.py`, `experience_development.py`,
`experience_evaluation.py`, `experience_workflow.py`,
`experience_candidate_handoff.py`, `evolution_cli.py`, the V3 demo and tests
specific to those retired engines. Removed old lifecycle cancel/validation-worker
functions; manual review/edit/activation/revocation and immutable evidence remain.
Orphan `.pyc` files for retired modules are also removed, so sourceless imports
cannot accidentally restore an old engine.

`evolution_backend.py` is now **execution_backend.py**. V4, the Docker adapter and
shared backend tests import that independent infrastructure. AST extraction,
scoring/calibration, sandboxing, request accounting, failure evidence, memory,
review/version editing and source retrieval are shared facilities, not old engines.
No historical model scheduler is imported by them.

```
python3 -m temporal_contract_analyzer history status --root /old/batch
python3 -m temporal_contract_analyzer history report --root /old/batch
```

Both commands read only retained `protocol.json`, `state.json`, `summary.json` and
`REPORT.md`. They do not recompute scores, check old batches against current
implementation hashes, write reports, migrate data or call models. Output goes to
stdout; explicit shell redirection to a new destination is the operator's choice.
New V4 roots use `tempoevo status` instead.

Historical batch files, scores, candidates, approval decisions and memory records
were not deleted or rewritten. Old approvals still participate in the approved
retrieval snapshot under the existing eligibility rules. Reviewing an old
experience is allowed; running its original repair trajectory is not.

Tests are reorganized by responsibility: old controller tests removed; isolation,
scorer, calibration, cleanup and request guard tests retained under shared backend
tests. `test_history_readonly.py` checks byte/mtime preservation, absence of old
modules and rejection of retired execution paths.

Verification: 485 remaining offline tests passed; 82 targeted shared/V4/history/review tests and 11 browser interaction tests passed. The V4 synthetic demo passed on Action 2. An actual V3 batch was inspected without byte or mtime changes. No real model, paid experiment, historical replay or approval action was run.
