# Current experience construction and testing workflow

The execution protocol is `tempoevo-trajectory-v13`. The only model-execution
entrypoint is `tempoevo run --execute`; preparation and inspection never call a
model. All model roles use a frozen profile, currently `gpt-6.1-sol / medium`.
Model weights do not change: experience construction updates external guidance.

## Experience construction

The fixed experiment recipe is `v8-compatible-v1`, with Abstract-based
`business-source-v1` retrieval by default and at most three repair Actions including
the first patch. Approved, version-bound abstracts are frozen with the guidance.
Local Abstract ranking recalls up to 6 entries; a model checks their full text
against the current task and source before delivering up to three. Missing or
unapproved abstracts use the existing extractive preview. Public check descriptions are explicit public inputs. Each candidate is evaluated by
public checks and the training Oracle; both must pass for acceptance. Failure
permits the next budgeted Action with diagnosis and, when supported, Contract
revision. This recipe passes the latest controlled feedback rather than cumulative
diagnosis explanations. Raw hidden assertions and reference repairs never reach
the model. Infrastructure errors are not behavioural failures.

First-Action successes skip experience extraction. Failed-to-successful trajectories
propose source-supported corrections; routine implementation-only fixes add no
guidance. Existing entries are updated in place under a stable ID, with renewed
content/Abstract review. Explicit merges retire other IDs only after acceptance.
Three effective failures request a real expert summary. Proposals remain pending
until a named reviewer accepts their exact content. Online construction can use a
separate provisional pool in later construction tasks; testing cannot access it.
The default structured recipe caps each trajectory at 156 requests: three Actions
at 24 each, two diagnoses at 12 each, one Contract draft at 12, up to three
applicability selections at 12 each, and extraction at 12. Each stage has a
600-second limit. Contract revisions reselect from the same frozen bank without
requiring a separate taxonomy analysis. Fixed-Contract training selects once.
Abstract-based business selection is the only training/testing retrieval route.
Taxonomy-routing and semantic-selection pipelines have been removed. Prepare a
new V13 trajectory; older protocols remain available for read-only inspection. Online training
keeps its existing provisional-pool lifecycle and uses extractive previews for
provisional guidance without approved abstracts.

## Testing

The current configuration is one group with all approved experience available
for retrieval, `condition=structured`, `retrieval_profile=business-source-v1`,
and frozen memory. It does not automatically launch A/B or no-memory groups.
The latest test10 run froze 39 approved entries and used four workers; these are
batch settings, not a fixed library size or four attempts on each task.

```text
Original task + public source + available AST evidence
  -> business applicability selection from a frozen approved bank
  -> Auto-Contract draft
  -> one bounded repair Action and final submission
  -> one independent Gold score
```

There is no separate taxonomy-routing stage or Contract Review. Experience
selection considers complete business applicability, exclusions, object/operation
mapping and supported obligations. It recalls at most 6 candidates and delivers
at most three entries / 8,000 characters, favouring additional obligation coverage
and suppressing redundancy. No applicable guidance means repair without experience.
Model applicability judgments remain fallible; unknown premises do not count as
satisfied. Requirements come from current task/source evidence, not experience.

The default testing budget is 48 requests: selection 12, Contract 12 and Action 24.
Each stage has a 600-second limit. The Action may inspect sources, run existing
public tests and revise code inside its budget, then submits one final candidate.
Gold runs once afterward. Neither its verdict nor failure details return to the
solver, control another repair or select a candidate. Testing performs no diagnosis,
experience extraction, expert-summary request or memory update. Public evaluation
is optional auxiliary feedback; it cannot trigger another testing Action.

## Preparation validation and recovery

`advisory-source-validation-v1` validates model output structure and source
quotations. Unsupported mechanism facts become unknown; unsupported labels are
omitted. Invalid preparation output gets at most one correction within the same
stage budget. If still unusable, discard the guidance or retain the previous
valid Contract. A missing draft permits Action with the original task/source and
otherwise eligible experience. This format/evidence correction is not a Contract
Review loop or a correctness certificate.

Business selection uses `business-source-coverage-v2` with per-entry validation.
Identical duplicate assessments are merged; conflicting duplicates, wrong predicates,
invalid citations and malformed rows reject only the affected candidate. Missing
assessments never imply applicability. Invalid or conflicting shared obligation IDs
also reject their dependent rows, while independently supported obligations survive.
Valid entries proceed directly to Contract and Action, with a partial-selection
warning and detailed `retrieval/selection-*-validation.json` audit. All applicability
requirements, exclusions and source-evidence checks still apply. An unusable envelope
or no independently valid assessments uses the existing single correction/fallback.
This policy applies to newly prepared runs; archived scores are unchanged.

Frozen hashes, approved-memory admission, paths, permissions, model identity,
measured usage, protected files and evaluator isolation remain hard boundaries.
Invalid Action output or scoring infrastructure remains an execution error.
Raw outputs, warnings, corrections and measured usage remain in the run archive.

## Review, records and interpretation

[Experience Review](EXPERIENCE_MEMORY.md) remains required for long-term publication;
it is separate from the removed automatic Contract Review. Opening the review UI
does not execute a model. Historical results, approvals and frozen run directories
are unchanged. V12 and earlier executions and old Contract Review policies are
read-only; changes require a new root, never rewriting an old score.

See [Docker setup](DOCKER_TRAINING.md), [evaluation boundaries](PUBLIC_TEST_ADAPTERS.md)
and the [final 70/30 case bundle](../cases/README.md).
The existing cases are historically exposed and share source families. Their
results describe diagnostic performance, not unseen-source generalization.
