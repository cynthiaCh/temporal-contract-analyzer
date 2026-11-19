# Seven temporal obligation classes and experience routing

The current development/frozen-testing entry point is the `tempoevo` CLI; see [the workflow](WORKFLOW.md). Open the shared experience library with `experience-memory review`. Offline material commands do not call models. Old Web v2, A/D routing and single-case failure-learning entry points have been removed.

Since 2026-11-09, current tool interfaces use `temporal-obligation-taxonomy-7-v1`. It adopts the seven obligation classes from the bench paper's coverage audit as a common vocabulary for classification, retrieval and presentation. This engineering choice uses existing definitions and coverage records; the accuracy or repair benefits of alternative taxonomies have not been compared.

## Questions asked by each class

| Label | Name | Plain-language question |
|---|---|---|
| R | Readiness coordination | Which step must wait until data, services or prerequisites are ready? |
| O | Prerequisite ordering and reentrant consistency | Which step must happen first? Is the original state still valid when a synchronous callback returns? |
| B | Commit and completion barriers | What must settle before return, handoff or a subsequent action? |
| L | Lifecycle-constrained admission and side effects | After close, cancellation or ownership changes, which work may still enter or produce effects? |
| I | Operation identity and snapshot binding | Which entry-time request, visit or data snapshot owns this result? |
| F | Result freshness and version consistency | Can an older result overwrite a newer one within the same logical owner? |
| A | Accepted-work preservation and effect cardinality | Must accepted work be preserved? May an effect occur zero, one or multiple times? |

Strict inclusion/exclusion conditions are defined by `codebook` in [contract-taxonomy.json](../temporal_contract_analyzer/contract-taxonomy.json). CLI, HTTP and browser read this same definition. Source files and SHA-256 digests are recorded in `provenance`; runtime does not depend on a neighboring repository.

A case may have multiple labels. Work that waits for service availability, stops admitting new inputs after close and preserves accepted results can involve R, L and A respectively. A real case still requires current task/source citations rather than classification from that description alone.

Three boundaries prevent double counting:

- Register-before-start is O, without additionally counting R. Actual readiness conditions belong to R.
- Settlement before return is B; ordinary async decoding alone is not B.
- Invalidating an old visit is L/I; competing result versions within the same retained owner are F. Equal regression-test results do not automatically constitute A.

## Historical four- and five-group schemes

| Record | Current interpretation | Treatment |
|---|---|---|
| T1–T4 in `refine-logs/experience-toolflow-v1-20261108` | Historical four-group mechanism routing | Retained as history, not current class definitions |
| Five groups in old `repair.py:FAMILIES` | Development failure-hypothesis prompt templates | Implementation removed; historical meaning is not a current class definition |
| Five original case-bank questions | Five retrievable materials | Entry count need not equal class count; original text is unchanged |
| D1/D2, Test-1/Test-2 | Development/test case aliases | Neither obligation labels nor independent source definitions |

T4 cannot simply be renamed L, nor T3 renamed B: historical groups can span multiple classes. Reusing an old experience requires separate cited seven-class metadata, without modifying its body, frozen digest, denominator or historical classification. Historical records retain their classifications rather than pretending old experiments used seven classes.

Language, framework, source cluster and obligation class are recorded separately. Different labels do not prove train/test source isolation; variants from the same cluster still require disclosure of historical exposure.

## End-to-end interface flow

1. **Development**: the agent reads the task, candidate source and optional AST, extracting candidate Contract, multiple obligation labels and mechanism premises. Reference Contracts remain on the development evaluation side.
2. **Comparison and reflection**: the runner organizes task/source evidence, actual outcomes, improvements, regressions and unknown causes, then calls the reflector under a bounded protocol to generate candidate experience. The maintenance agent does not read hidden scorers.
3. **Freezing**: bind the body, labels and applicability/exclusion conditions to a digest. Digest agreement establishes unchanged content, not correctness or acceptance.
4. **Testing**: extract labels from currently visible inputs only. Retrieve by label, then check mechanism premises, exclusions and semantic review. Select zero or one frozen experience; unknowns, an empty library or unresolved conflicts fall back to AUTO.
5. **Delivery and scoring**: A contains the original task and the same candidate automatic Contract; B additionally receives only the selected experience body. Tools, model, effort, budgets and scorer versions are frozen separately. Experience is not updated during testing, and reference answers are not delivered to the maintenance agent.

The seven classes organize obligations; they do not imply effective experience exists for each class. The mechanism-premise dictionary does not cover every implementation. Actual experience and activation state come from the designated shared library. When no experience is delivered, A/B are identical and differences cannot be attributed to experience.

Implementation is in [taxonomy.py](../temporal_contract_analyzer/taxonomy.py) and [experience_routing.py](../temporal_contract_analyzer/experience_routing.py). These modules provide offline material and routing validation; `tempoevo_v4.py` schedules the new learning/frozen-testing flow. Historical V1–V3 batches are read-only through `history status/report`, without the old engine's reproduction entry points.

## Appending class-specific general reminders

[contract-reminders.json](../temporal_contract_analyzer/contract-reminders.json) contains a common reminder and seven R/O/B/L/I/F/A review-question sections under `by_label`. Names and class boundaries still come from the single codebook rather than duplicate definitions. This is a prewritten initial checklist, not reflected experience or case-specific reference Contracts.

For multiple labels, append each corresponding reminder once in codebook order. Unknown classification retains only the common reminder and an unknown-status explanation, rather than appending all seven. Classify using current task/source, without reading test reference answers first.

`maintenance-prompt` builds the original task, candidate Contract, common reminder and matching class reminders from an analysis bound to visible citations, without starting a maintenance model:

```sh
python3 -B -m temporal_contract_analyzer maintenance-prompt analyzed-input.json --output maintenance-prompt.txt
```

When comparing incremental experience effects, A/B must share the automatic Contract, labels and reminder version; B adds only frozen experience text. Python calls are `maintenance_prompt(task, contract, obligation_labels=codes)` and `maintenance_prompt(task, contract, experience_text, obligation_labels=codes)`. Archive reminder version/digest using `reminders.material(codes)`. Evaluating class reminders alone requires a separate control rather than combining their effects with experience gains.

Calls without `obligation_labels` retain the prior shared prompt. Old archives, frozen scripts and historical E/F fixed reminders remain unchanged. New commands/parameters are explicit integration points. The bounded evolutionary controller currently uses its own `common()` prompt, without implicitly adding these static reminders or rewriting old experiments.

## Offline commands

```sh
python3 -B -m temporal_contract_analyzer taxonomy
python3 -B -m temporal_contract_analyzer taxonomy --format json
python3 -B -m temporal_contract_analyzer taxonomy --format schema
python3 -B -m temporal_contract_analyzer experience-prompt public-input.json --output analysis-prompt.txt
python3 -B -m temporal_contract_analyzer experience-review-template analyzed-input.json --output review.json
python3 -B -m temporal_contract_analyzer route-experience route-input.json --output route.json
```

These commands generate material or compute routing only. They do not call models, read hidden scores or start experiments; existing output files cannot be overwritten.

`public-input.json` contains only `task`, `sources` (candidate-relative paths mapped to source text), and optional `AST`. Supply `experience-prompt` output with `taxonomy --format schema` to the existing structured-output backend; this interface does not send requests on the caller's behalf.

The integrated alternative is `tempoevo prepare` with `visible` omitted: it builds AST evidence automatically, and the first `run --execute` performs the analysis model call and an automatic budgeted AI semantic evidence check before repairs. Supplied analyses receive the same check. No manual review-analysis step is needed in v3; that command remains a v2 compatibility entry point. The actual checker is recorded as model_evidence_check with current source citations, reasons, unknowns and blockers, not as human approval. See [the execution flow](WORKFLOW.md).

Model analysis objects must include `taxonomy_version`, `contract`, `obligation_labels`, `facts` and `unknowns`. Each label contains `code`, an obligation `statement` and `evidence`; mechanism facts contain `predicate`, `state` and `evidence`. States are `known` / `unknown` / `contradicted`. Citations use `{file, line, quote}`, with one-based lines and `TASK` for the original task. Quoted text must appear on that line. Source behavior does not automatically define policy to preserve; AST evidence does not establish complete reachability.

`analyzed-input.json` contains only `task`, `sources` and `analysis`. Generated review templates default to `approved: null`, to be filled after reviewing obligation direction, premises and unknown scope. Set `reviewer` truthfully to `execution_agent_visible_input_only` or `human_visible_input_only`, with `reason` and current `evidence`; AI self-review is not independent human review. Routing binds the complete input and codebook digest; any content change invalidates the old review. Citation existence is not semantic correctness, so actual review remains necessary.

`route-input.json` contains only `task`, `sources`, `analysis`, `library` and optional `review`. Unknown labels, missing review, unknown applicability premises, exclusions not refuted, digest mismatches or unresolved multiple candidates return AUTO with a reason. Malformed CLI input produces an error. Legacy fields such as `primary_class` cannot silently enter the new interface.

Python callers can use `freeze_entry(text, obligation_labels, requires, excludes, version)` to create an integrity-bound object for `route(...)`; it neither approves nor writes experience. Build A with `maintenance_prompt(task, contract)` and B with the same function plus only the selected entry's `text`. This public prompt is a new version, not a verbatim reproduction of old experiment prompts.

The current entry point is [WORKFLOW.md](WORKFLOW.md); old method descriptions are in the [research archive](ARCHIVE.md). Relabeling, semantic review and behavioral acceptance must be recorded separately; changing class names cannot bypass them.
