# Architecture, terminology and archive boundaries

Use this reference to locate code or interpret obligation labels. Execution flows
and budgets live in [WORKFLOW.md](WORKFLOW.md), not in module filenames.
The current trajectory protocol is V13; `tempoevo_v4.py` retains a historical name.

## Implementation map

Paths below are relative to `temporal_contract_analyzer/`.

| Responsibility | Modules |
|---|---|
| CLI and trajectory state machine | `tempoevo_cli.py`, `tempoevo_v4.py` |
| Stage prompt assembly and model/evaluator adapter | `tempoevo_backend.py` |
| Isolated sessions and model configuration | `execution_backend.py`, `_session_runtime/` |
| Docker transport and evaluation | `docker_backend.py`, `tempoevo_docker.py`, `case_evaluation.py` |
| Source parsing and optional AST preparation | `core.py`, `preanalysis.py`, `javascript/` |
| Business selection/replay | `business_retrieval.py` |
| Preparation validation and recovery | `preparation_validation.py`, `stage_retry.py` |
| Experience storage/review | `compact_experience.py`, `experience_memory.py`, `experience_approval.py`, `memory_review.py` |
| Learning, reflection and acceptance | `experience_learning.py`, `experience_reflection.py`, `training_acceptance.py` |
| Reports, source context and presentation | `hub.py`, `context.py`, `review.py`, `boundary_cards.py` |
| Bounded reentry/state-order checks | `publication.py`, `countdown.py`, `reflective.py`, `protocols.py`, `reentrancy.py`, `lifecycle.py` |
| General guidance and personal corrections | `general_memory.py`, `personal_memory.py`, `mcp_server.py` |
| Historical inspection | `history_cli.py` |

[MASTER_PROMPT.md](../MASTER_PROMPT.md) is explicitly supplied coordinator guidance;
the runner does not load it. Runtime instructions and schemas are assembled in
Python. The MCP server supplies tools to the current host agent rather than
introducing a separate model runner. Report scans and memory operations do not
launch research training.

## Seven obligation classes

The shared vocabulary is `temporal-obligation-taxonomy-7-v1`. Definitions and
inclusion/exclusion rules come from
[contract-taxonomy.json](../temporal_contract_analyzer/contract-taxonomy.json), not
a neighboring repository. Labels describe obligations, not a retrieval algorithm.

| Label | Name | Question |
|---|---|---|
| R | Readiness coordination | What must wait for data, services or prerequisites? |
| O | Prerequisite ordering and reentrant consistency | What must happen first, and is state still valid after synchronous callbacks? |
| B | Commit and completion barriers | What must settle before return or handoff? |
| L | Lifecycle-constrained admission and side effects | What may enter or produce effects after close, cancellation or ownership changes? |
| I | Operation identity and snapshot binding | Which request, visit or entry-time snapshot owns the result? |
| F | Result freshness and version consistency | Can an old result overwrite a newer result for the same owner? |
| A | Accepted-work preservation and effect cardinality | Must accepted work survive, and how many effects are permitted? |

Cases can have multiple labels. Register-before-start is O, not also R without a
readiness condition. Settlement before return is B; async decoding alone is not.
Visit invalidation is L/I; competing versions for a retained owner are F. Equal
test outcomes do not establish A. Language, framework, source family and class
are separate attributes; different IDs/labels do not prove independent sources.
Historical T1–T4 labels are not automatically converted.

Standalone offline utilities remain available; they do not launch model stages or
replace current business selection:

```sh
python3 -B -m temporal_contract_analyzer taxonomy
python3 -B -m temporal_contract_analyzer taxonomy --format schema
python3 -B -m temporal_contract_analyzer experience-prompt public-input.json --output analysis-prompt.txt
python3 -B -m temporal_contract_analyzer experience-review-template analyzed-input.json --output review.json
python3 -B -m temporal_contract_analyzer route-experience route-input.json --output route.json
python3 -B -m temporal_contract_analyzer maintenance-prompt analyzed-input.json --output maintenance-prompt.txt
```

See `taxonomy_cli.py` / `experience_routing.py` for input contracts. Public input
contains `task`, `sources` and optional `AST`; routing uses an explicit library and
review. Existing outputs are not overwritten. `contract-reminders.json` supplies
prewritten questions for `maintenance-prompt`; these are not learned experience
and are not implicitly appended by the current trajectory.

## Historical records and interpretation

Historical experiments, raw/partial outputs, failed or interrupted runs, scores,
approvals and publication material are retained research records, excluded from
clean source exports. Preserve their original inputs and execution bindings. Use
the corresponding revision/environment to inspect retired methods; current tools
do not resume retired pipelines or rewrite their scores. New experiments require
fresh preparation through the maintained workflow.

The removed measurement workbench and behavior-probe prototype are not current
entrypoints. Historical paths in provenance are attributions, not promises of
runnable files in this checkout. Report annotations are human judgments, delivery
receipts do not prove model attention, and development regressions do not establish
unseen-project accuracy. Version-specific narratives remain in Git history.

## Archive boundaries

Historical experiments, raw/partial outputs, failed or interrupted runs, scores,
approvals and publication material remain research records. They are excluded
from clean source exports; consolidation of these guides does not delete or
rewrite them. Old paths and source IDs describe their original environment,
not executable entrypoints in today's checkout. Use the corresponding Git
revision and environment to inspect historical methods.

Retired protocols and Contract Review runs are read-only. Current execution does
not revive their schedulers or relabel their results; new experiments require
fresh preparation. The old report measurement workbench is not part of current
interfaces. Report annotations/deliveries and personal corrections are separate
from frozen experimental evidence. Preserve existing internal execution bindings;
do not create extra integrity reports for routine use.
