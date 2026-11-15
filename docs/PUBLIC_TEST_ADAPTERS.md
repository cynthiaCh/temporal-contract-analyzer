# Repair evaluation

Training evaluates each generated patch with its training Oracle, retries on failure
and stops on acceptance, within three total attempts. Testing runs one bounded Action
and submits its final patch before Gold is invoked once for independent scoring.
Neither Gold PASS/FAIL nor failure details return to the model or select another
candidate. Gold failure does not restart solving. Testing keeps experience frozen.

No built-in public behavioral suite is generated or required. The model can run
project tests during repair. An existing evaluator may optionally supply auxiliary
feedback through `visible_evaluator` (`--visible-evaluators` for batch preparation);
its result never determines acceptance or triggers another testing submission.
Within an Action, the model can run available project tests and revise code under
the same request/time cap. No public evaluator means unverified, not PASS.

Testing ends as `scored`, with `single_submission` as its repair stop reason and a
separate `gold_result`. Training retains its acceptance statuses. Historical results,
including Gold-guided testing, remain read-only and are not relabeled as blind tests.

Source-read evidence is optional process audit, not a scoring prerequisite. The
runner retains `source_body_proofs` and records `source_read_audit` as `observed`,
`not_observed` or `unavailable`. These describe recognized tool output, not whether
the model understood or received source (the stage prompt already includes it).
An empty proof list or audit-parser error cannot reject a complete repair candidate.
Candidate/output validity, archive completeness, model/tool boundaries and frozen
submitted-candidate integrity still apply; Gold remains the behavioral judge.

Git history first records the old proof gate in the packaged runner at `85f3ccd`
(2026-11-10, +08:00); the V4 adapter enforced it in `a38ad97` (2026-11-13, +08:00).
These are recorded commit dates, not proof of when uncommitted code was first written.
The gate was removed after a valid archived patch was rejected because a later
`rg` returned 1 and shell parsing attached `;` to the preceding source filename.
The optional audit now recognizes that combined read. Frozen historical receipts
and results remain unchanged; changed runtime bindings require a new execution root.
