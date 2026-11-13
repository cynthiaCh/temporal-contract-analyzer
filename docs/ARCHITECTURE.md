# Architecture and source map

The only model-execution protocol is `tempoevo-trajectory-v4`.

```text
Public task/source → deterministic AST → frozen approved retrieval
→ initial Auto-Contract → Action → visible assessment
                  ↑ diagnosis/revision ← failure, at most three Actions total
Success → unapproved candidate pool → named human content review → long-term bank
Three failures → real expert summary task → candidate pool
Testing → same bounded repair, frozen memory, separate final gold, no learning
```

| Responsibility | Modules / commands |
|---|---|
| V4 state machine | `tempoevo_v4.py`, `tempoevo_cli.py`, `tempoevo` |
| V4 model/evaluator adapter | `tempoevo_backend.py` |
| Shared isolated sessions | `execution_backend.py`, `_session_runtime/` |
| Shared Docker/calibration/scoring | `docker_backend.py`, `case_evaluation.py` |
| AST and public source evidence | `core.py`, `preanalysis.py`, `javascript/` |
| Immutable experience/retrieval | `experience_memory.py`, `experience_routing.py`, `experience_updates.py` |
| Named content review/versioning | `experience_approval.py`, `experience_lifecycle.py`, `memory_review.py` |
| Read-only V1–V3 inspection | `history_cli.py`, `history status/report` |

No shared backend imports an old execution engine. Old metadata and evidence
remain data: inspecting them never schedules a model, recomputes a report, applies
a patch or modifies an approval. See [V4](TEMPOEVO_V4.md) and
[legacy retirement](LEGACY_RETIREMENT.md).
