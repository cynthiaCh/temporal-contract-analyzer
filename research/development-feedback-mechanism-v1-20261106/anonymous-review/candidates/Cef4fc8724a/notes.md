Note 1
step: Admission
change: Added an explicit boundary between new input after retirement and earlier accepted work settling later.
feedback_basis: The scored difference was an extra history entry from a newly emitted input after navigation; accepted late work remained valid on observed paths.

Note 2
step: Ordering
change: Require transition-before-input and input-before-transition comparisons, including reentrant callbacks.
feedback_basis: The local harness covered stale completion and several lifecycle paths but did not establish the reported input-admission boundary.

Note 3
step: Validation
change: Limit conclusions from local checks and distinguish whole-task behavior from selected passes.
feedback_basis: Local checks passed while the whole behavior score was 0.0; the trace did not uniquely establish a cause.