Note 1
step: Evidence
change: Make scheduling APIs and intermediate consumers explicit reading targets.
feedback_basis: The read covered the hook and adjacent component; the reported difference concerns the pending interval.

Note 2
step: Contract
change: Require a phase-by-phase account of pending, scheduled, retrying, and ready states.
feedback_basis: Feedback reports a waiting-state mismatch but does not establish a specific state recipe.

Note 3
step: Validation
change: Assert intermediate observable state as well as final effects and ownership.
feedback_basis: Visible verification was a syntax check; whole behavior failed, and self-written checks prove only driven orders.

Note 4
step: Uncertainty
change: Separate observed mismatch from its unisolated cause.
feedback_basis: The feedback does not isolate missing observation, interpretation, implementation, or verification.