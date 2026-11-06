Note 1
step: State contract
change: Distinguish request settlement from overall completion and define waiting state between attempts.
feedback_basis: Pending work retried and eventually completed, but the intermediate snapshot lacked the assessed waiting indication.

Note 2
step: Event checks
change: Require intermediate snapshots and separate effect assertions alongside final outcomes.
feedback_basis: The observed difference occurred between pending and ready stages; eventual completion alone missed it.

Note 3
step: Verification
change: State that syntax checks and unavailable dependencies do not verify behavior.
feedback_basis: Visible verification was a syntax check; dependencies were missing, and no behavioral harness output was shown.

Note 4
step: Evidence limits
change: Keep adjacent behavior and scored observations source qualified.
feedback_basis: Adjacent behavior passed on assessed paths, while the exact waiting flag contract and cause remained uncertain.