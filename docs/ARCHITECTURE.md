# Architecture and source map

The only model-execution protocol is `tempoevo-trajectory-v11`. Failed-attempt diagnoses and controlled observations are cumulative task-local working memory passed explicitly to the next Action, independently of cross-task matching. See [V9](TEMPOEVO_V9.md). [Online learning](TEMPOEVO_V8.md) adds a training-only provisional channel: generation → immediate eligibility in subsequent tasks → actual usage feedback, with human acceptance separately controlling the long-term library. Frozen experiments/testing never read this channel. Model/provider settings come from a frozen profile; transient stage restarts share the original request/time cap. See [V7 reflection](TEMPOEVO_V7.md) and [V6 profiles](TEMPOEVO_V6.md).

```text
Public task/source → deterministic AST → approved mechanism/BM25 recall → source-grounded semantic selection
→ initial Auto-Contract → Action → visible + training Gold assessment
                  ↑ diagnosis/revision ← failure, at most three Actions total
Gold PASS + required public PASS → compare frozen related guidance → evidence/revise/merge/new proposal → unapproved candidate pool → named human content review → long-term bank
Three effective training nonacceptances → real expert summary task → candidate pool
Testing → same bounded repair, frozen memory, separate final gold, no learning
```

| Responsibility | Modules / commands |
|---|---|
| V11 state machine | `tempoevo_v4.py`, `tempoevo_cli.py`, `tempoevo` |
| V11 model/evaluator adapter | `tempoevo_backend.py` |
| Shared isolated sessions | `execution_backend.py`, `_session_runtime/` |
| Shared Docker/calibration/scoring | `docker_backend.py`, `case_evaluation.py` |
| AST and public source evidence | `core.py`, `preanalysis.py`, `javascript/` |
| Immutable experience/retrieval | `experience_memory.py`, `experience_routing.py`, `experience_updates.py` |
| Named content review/versioning | `experience_approval.py`, `experience_lifecycle.py`, `memory_review.py` |
| Read-only V1–V3 inspection | `history_cli.py`, `history status/report` |

No shared backend imports an old execution engine. Old metadata and evidence
remain data: inspecting them never schedules a model, recomputes a report, applies
a patch or modifies an approval. See [V6](TEMPOEVO_V6.md) and
[legacy retirement](LEGACY_RETIREMENT.md).

Training verdict normalization and controlled boolean behavior projection live in
`training_acceptance.py`. Raw scorer results are separately archived. Testing has
no training feedback, and scores its selected candidate once at the end. Existing
exposed development records are not evidence of an independent test split.

V11 retrieval stages, budgets and continuation boundaries: [semantic selection](TEMPOEVO_V11.md). The semantic model does not replace deterministic behavioral evaluators.
