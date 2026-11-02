# Frozen automatic-binding migration pilot

Freeze implementation before selecting new source. The new repository is 3rd-Eden/one-time, absent from previous local external-test README records. Second candidate jonschlinkert/one-time returned 404; it is not a tested implementation.

Keep the first selected release aa7ced4 (1.0.0), including its fn.name runtime dependency. Do NOT install it, stub it or drop this outcome if setup fails. Also test historical upstream refactor 8e075514→646e3445, which predates that dependency. The earlier snapshot is deliberately a runtime-compatibility selection after reading source, not a random blind sample. Preserve both attempts.

Before execution fix four cases: release→same-release (dependency boundary); historical upstream refactor; earlier→same-earlier control; earlier→a documented artificial late-guard regression. The artificial change moves called=true below callback evaluation, and is NOT an upstream historical bug. Use independent ordinary Node assertions as the bounded count reference, not tool answers.

For each case supply only two file paths plus --confirm-at-most-once. Preserve the unconfirmed static proposal and confirm no target execution before opt-in. Compare generated plans (8 leaf fields) against the existing manual wrapper format; count entered domain values (2 paths + 1 requirement confirmation) separately from output path/runtime options common to both workflows. Counts measure interface inventory, not human effort, correctness rates or productivity.

Run each supported case once through auto_once, then run its generated replay command. Feed exactly the generated plan to the unchanged independent fast-check model, seed17, with paired mode=reenter/times=2 on each side. The baseline also runs its existing broader property search; do not conflate its extra failure/overlap coverage with this frontend's single synchronous reentry. Missing dependency failures remain inconclusive and are retained; never repair source or engine after observing external outcomes.

The frontend can benefit either engine; make no detection-superiority claim. New repository ≠ unknown natural bug, blind experiment or human study. Stop after the fixed cases and report refusals/errors as prominently as success.

## Recorded amendment after execution

run-01/02 use the pre-selection implementation retained in FROZEN-pre-sweep.json. The skill-mandated assumption sweep then found a construction-time callback validity issue in the accepted source domain. The frontend now classifies such traces inconclusive and reports whether reentry was attempted; existing probe/baseline engines are unchanged. run-03 revalidates the same four inputs on the updated frontend in FROZEN.json. It is development revalidation, not a new frozen holdout. Last-round documentation additionally clarifies that outer input is 0 while nested input follows the callback's first actual argument. Original protocols, outputs and reviewer findings remain available.
