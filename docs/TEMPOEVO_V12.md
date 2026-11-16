# TempoEvo V12: advisory preparation validation

V12 keeps source validation but no longer treats an unusable model-generated
analysis, Contract or review as a reason to abandon code repair. Original tasks
and public source remain authoritative; automatic Contracts and experience are
fallible guidance. New trajectories bind `advisory-source-validation-v1`.

## Recoverable preparation output

- A known or contradicted routing premise without matching public evidence becomes
  `unknown`, with its unsupported evidence removed. Unsupported labels are omitted.
  Unknown cannot satisfy a required premise or prove an exclusion false. No citation
  is invented, and raw model output remains in the stage archive.
- Invalid routing output, experience assessment, initial Contract, Contract review
  or training diagnosis receives at most one explicit validation correction.
  That new call shares the original stage's request/time budget. Testing Contract
  generation, review versions and corrections all share its existing 12-request
  budget; corrections do not add Contract versions or Action sessions.
- If correction is invalid or its preparation budget is exhausted, discard the
  proposed guidance. Invalid selection delivers no experience. Invalid review or
  diagnosis keeps the previous draft and does not install an unsupported revision.
- If no usable initial Contract exists, pass `contract: null` to Action with the
  original task/source/AST and any otherwise eligible frozen guidance. Skip public
  Contract review without claiming review success. A later training diagnosis can
  also be skipped without preventing the next budgeted Action.

The strict validators still reject ungrounded quotes, unsupported Contract changes
and missing change declarations. Recovery is implemented at their callers: rejection
of guidance is distinct from rejection of the whole repair trajectory. An accepted
review is a fallible public-source conclusion, not a correctness certificate.

## Hard boundaries

Recovery never admits unreviewed memory into an approved snapshot and never bypasses
frozen input/runtime hashes, source/path restrictions, tool authorization, model
identity, measured usage, protected tests/configuration, or evaluator isolation.
Timeouts and infrastructure failures remain execution errors. A malformed preparation
response is recoverable only when the call's model identity and measured request
count are known and within bounds. Invalid Action output or invalid Gold execution
remains an execution error.

Action and Gold budgets are unchanged. Testing submits once, scores once after final
submission, and never receives Gold feedback or performs diagnosis/extraction. Failure
of Gold is a scored failure; preparation recovery cannot cause another testing Action.

## Audit and compatibility

`validation/<stage>.json` records accepted/rejected preparation attempts.
`state.json` and `summary.json` expose `preparation_warnings` and the summary counts
`preparation_corrections`. Invalid raw output, correction input, request/time usage
and the final fallback remain inspectable. Action receives concise warnings and an
explicit reminder that the original task and source establish requirements.

The shared execution and session runtime now require `tempoevo-trajectory-v12`.
V11 and earlier trajectories remain read-only; their bindings, invalid states and
scores must not be rewritten. Comparisons after this change require newly prepared
roots for both arms and must identify the new validation policy. Existing test data
are historically exposed, diagnostic cases, not a new unseen holdout.

The regression fixtures in `tests/fixtures/preparation-validation/` contain only
original public inputs and model review output for three observed V11 refusals.
They contain no Gold output, oracle schedules or reference implementation. Replay
uses synthetic scoring to check continuation and rejection of invalid revisions,
not to claim that any product repair is correct.
