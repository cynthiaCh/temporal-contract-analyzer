Note 1
step: Admission boundary
change: Separate fresh input after handoff from delayed completion of accepted work.
feedback_basis: The behavioral difference was an extra history entry from a newly emitted old-source input; accepted work across hiding passed.

Note 2
step: Reentry
change: Inspect release, startup, and callback handoff as distinct event orders.
feedback_basis: The source permits synchronous emission and reentrant host callbacks; the reported trace lacks call-return markers, so the exact cause remains unknown.

Note 3
step: Effects and ownership
change: Check durable and current effects independently across attempts and accesses.
feedback_basis: The patch and local checks covered ordering and current display; feedback preserved those paths while the whole behavior score was 0.0.

Note 4
step: Validation
change: Require a targeted fresh-after-release check and limit conclusions to observed paths.
feedback_basis: Both visible harnesses passed but did not establish the failing event order.