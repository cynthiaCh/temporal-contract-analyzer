# Seven temporal obligation classes

The seven classes describe temporal obligations; they are not the current retrieval
algorithm. See [construction and frozen testing](WORKFLOW.md) and
[everyday MCP use](PERSONAL_MCP.md) for execution flows.

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

## Use in current workflows

- **Construction and frozen testing:** reviewed Abstract recall and full-text
  business applicability selection choose experience. Labels organize obligations;
  they do not authorize delivery, select one universal repair policy, or launch A/B
  comparisons. Current task/source evidence supplies the business requirements.
- **Everyday MCP:** general temporal guidance and project corrections are recalled
  together. The host agent checks full conditions and exclusions. Personal
  corrections may cover any coding topic and need no temporal classification.
- **Review:** general research guidance and its Abstract require content review.
  Explicit user corrections enter personal memory directly. These are different
  stores and publication policies.

Language, framework, source family and obligation class are separate attributes.
Different case IDs or labels do not establish independent train/test sources.
Historical T1–T4 labels remain historical data; they are not automatically renamed
or treated as current seven-class annotations.

## Standalone offline utilities

These remain available for explicit-input analysis and inspection. They do not
implement the current construction/testing selector or launch models:

```sh
python3 -B -m temporal_contract_analyzer taxonomy
python3 -B -m temporal_contract_analyzer taxonomy --format json
python3 -B -m temporal_contract_analyzer taxonomy --format schema
python3 -B -m temporal_contract_analyzer experience-prompt public-input.json --output analysis-prompt.txt
python3 -B -m temporal_contract_analyzer experience-review-template analyzed-input.json --output review.json
python3 -B -m temporal_contract_analyzer route-experience route-input.json --output route.json
python3 -B -m temporal_contract_analyzer maintenance-prompt analyzed-input.json --output maintenance-prompt.txt
```

`public-input.json` contains `task`, `sources` and optional `AST`. Analysis and
review utilities use explicit public task/source citations; quotations alone do
not establish semantic correctness. `route-experience` accepts an explicit
library and review for offline routing. It is separate from Abstract-based
business selection and combined MCP recall. Existing output files are not
replaced. See `taxonomy_cli.py` and `experience_routing.py` for input validation.

[contract-reminders.json](../temporal_contract_analyzer/contract-reminders.json)
contains prewritten class-specific review questions used by `maintenance-prompt`.
They are not learned experience, and the current trajectory controller does not
implicitly append them. Their effect cannot be attributed to learned experience
without an appropriate comparison.
