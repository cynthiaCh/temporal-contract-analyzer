Note 1
step: Observation
change: Require tracing registration, startup, cleanup, and each effect consumer.
feedback_basis: Reads covered these components, but the tested switch during startup still produced the wrong combination of history and current effects.

Note 2
step: Contract
change: State effect-specific ownership and ordering rules from source evidence.
feedback_basis: The patch guarded current display and retained history differently; feedback identifies their combination as the remaining behavior gap, without establishing a universal rule.

Note 3
step: Implementation
change: Check whether reentry lets an old call resume after ownership changes.
feedback_basis: Modified locations changed startup and handle publication; the visible checks did not drive the reported switch during startup.

Note 4
step: Validation
change: Assert separate effects across supported adversarial orders through the real entry point.
feedback_basis: Self-written checks passed, yet whole behavior scored 0.0. The supplied feedback does not isolate the exact cause.