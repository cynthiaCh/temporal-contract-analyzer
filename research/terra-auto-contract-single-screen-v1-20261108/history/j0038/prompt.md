The museum scan bundle preparation service can now report that a package is still pending before it becomes ready. Update the foreground preparation client so it keeps checking pending preparation and delivers the package only after a ready status.


Temporal contract: pending preparation must be polled until ready. While the
foreground preparation remains pending or a retry is scheduled, the dialog
must remain loading and must not report completion. Closing the foreground
dialog invalidates its timer and every in-flight response; reopening starts a
new generation and old responses must remain inert. The adjacent background
export is workspace-owned and continues after its panel closes unless the
authorization suffix explicitly migrates it to dialog ownership.

Environment: service completion is asynchronous, even when resolved before close
in the same event turn. Each request captures its token and resource generation.
The retry scheduler invokes callbacks on a later controlled turn and supports
cancellation. Tokens are scalar values; reopening the same token is still a new
generation. There is no rejection/thread race in this environment. Output sinks
never reenter. Final owner/framework disposal invalidates responses and timers
for both consumers. Active ready work still completes once; cancelled or stale
continuations cannot publish, schedule, clear current loading, or deliver.

Workspace-owned export and foreground dialog have different start policies.
An ungranted background start performs another check without invalidating an
earlier workspace-owned response or making a closed panel visible again. Ready
responses for the same artifact token do not duplicate its completed delivery.
Closing the background display preserves both queued retries and in-flight work.
Final owner disposal for either consumer cancels its retry timer and makes all
responses inert: they cannot deliver, publish, or schedule another request.
The public snapshot retains the candidate's existing disposal-state policy.

Work only from the provided candidate workspace. Do not inspect repository history, benchmark materials or the network. Run relevant native self-checks with: python3.
