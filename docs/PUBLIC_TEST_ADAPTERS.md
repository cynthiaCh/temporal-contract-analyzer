# Repair evaluation

Training and testing use the same loop: generate a patch, run the Oracle, retry on
failure and stop on acceptance, within three total attempts. There is no extra final
scoring call. Testing receives only the pass/fail verdict and keeps experience frozen.
Hidden assertions and reference patches never enter model input.

No built-in public behavioral suite is generated or required. The model can run
project tests during repair. An existing evaluator may optionally supply auxiliary
feedback through `visible_evaluator` (`--visible-evaluators` for batch preparation);
its result never determines acceptance. No public evaluator means unverified, not PASS.

Historical final-only-Gold records remain read-only. Report new results under the
Oracle-guided protocol; do not relabel historical outcomes.
