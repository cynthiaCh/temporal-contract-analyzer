Note 1
step: Evidence
change: Add call, return, startup, teardown, and callback ordering to source inspection.
feedback_basis: The read set included those paths, while the reported switch during startup still failed.

Note 2
step: Contract
change: Require separate validity decisions for history and current effects across ownership changes.
feedback_basis: Grounded feedback identifies the required combination of history and current-panel effects.

Note 3
step: Validation
change: Require a driven startup switch and post-return effect assertions; limit claims to exercised orders.
feedback_basis: Visible local checks passed but did not establish whole behavior; the reported score was 0.0.

Note 4
step: Uncertainty
change: Keep observation, contract, implementation, and verification causes distinct.
feedback_basis: Feedback does not isolate a single cause of failure.