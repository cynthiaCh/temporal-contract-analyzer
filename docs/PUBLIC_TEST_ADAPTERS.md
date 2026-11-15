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
