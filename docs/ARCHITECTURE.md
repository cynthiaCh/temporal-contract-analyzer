# Architecture and source map

The current protocol is `tempoevo-trajectory-v13`; see [WORKFLOW.md](WORKFLOW.md).
The fixed construction and testing paths are:

```text
Construction: public task/source -> AST evidence -> Abstract recall + full-text applicability
  -> Auto-Contract -> Action -> public + training Oracle acceptance
  -> failure: diagnosis/revision -> next Action, at most three total
  -> success: reflection -> candidate pool -> named content review -> approved bank
  -> three effective failures: expert-summary task -> candidate pool

Testing: original task/source + available AST -> business applicability selection
  -> Auto-Contract draft -> one bounded Action -> final submission
  -> Gold once -> recorded score, no solver feedback or learning
```

There is no automatic Contract Review. Draft validation checks structure and
quotations, with one bounded correction or a discard-guidance fallback. This is
separate from human Experience Review, which controls long-term publication.
Testing uses a frozen approved bank; provisional guidance is construction-only.

| Responsibility | Modules / commands |
|---|---|
| Trajectory state machine | `tempoevo_v4.py`, `tempoevo_cli.py`, `tempoevo` |
| Model/evaluator adapter | `tempoevo_backend.py` |
| Isolated sessions | `execution_backend.py`, `_session_runtime/` |
| Docker and scoring | `docker_backend.py`, `case_evaluation.py` |
| AST evidence | `core.py`, `preanalysis.py`, `javascript/` |
| Business applicability selection | `business_retrieval.py` |
| Preparation validation/fallback | `preparation_validation.py` |
| Standalone taxonomy analysis and memory utilities | `experience_routing.py`, `experience_updates.py` |
| Experience storage and review | `compact_experience.py`, `experience_memory.py`, `experience_approval.py`, `memory_review.py` |
| Training acceptance projection | `training_acceptance.py` |
| Historical inspection | `history_cli.py`, `history status/report` |

Module filenames do not select a historical execution protocol. Old data are
read-only; inspecting them does not schedule models, rewrite scores or approve
experience. See [retirement boundaries](LEGACY_RETIREMENT.md) and
[evaluation isolation](PUBLIC_TEST_ADAPTERS.md).
