Note 1
step: S4
change: Require source-based meaning for status flags across interim and final states.
feedback_basis: A pending snapshot had a scheduled retry and no completion, but lacked the assessed waiting indication. The exact flag contract remains source dependent.

Note 2
step: S6
change: Inspect and assert snapshots at each transition, including the pending interval.
feedback_basis: Eventual completion occurred, so checking only the final outcome missed the intermediate difference.

Note 3
step: S8
change: Tie verification claims to observed behavior and rerun after failures.
feedback_basis: Visible verification was a syntax check; dependencies were missing, and no behavioral check ran.

Note 4
step: S3–S7
change: Retain separate ownership, cancellation, effect, and preservation checks.
feedback_basis: Several assessed lifecycle paths passed; the record does not establish a unique root cause or universal correctness.