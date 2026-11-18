# Laboratory microscopy series upload

This workspace selects payload files, starts transfers, records queue and
progress history, and paints progress for its open panel. Runtime: Node 22.23.2.
Dependencies: Vue 3.4.38; jsdom 22.1.0; esbuild 0.21.5. See src for the session/component entry API.

Selecting a file creates a visit. Retry replaces the physical attempt without
opening another visit. Selecting the same file object again opens a new visit.
The source is shared by attempts and visits for that file. start may emit cached
packets synchronously; decoding yields a full frame, immediately or later.
Decode completion order can differ from packet arrival order.

recordProgress appends transfer history; showProgress paints the open panel.
Queue records, notices, cancellation, retry, navigation, and cleanup retain
their existing behavior. Queue records are {fileId, attemptId, visitId, kind}
unless a separate authorization adds byteCount from file.size.

One startup window is relevant to this maintenance request: start may emit
more than one packet synchronously. A showProgress callback may select or hide
another visit before start returns, while its caller has not yet received the
returned cleanup handle.

The same source service also has a diagnostic consumer, Telemetry/
collectProgressTelemetry, whose existing live delta observations are separate
from the panel. Keep its existing behavior during this maintenance.
Removing a listener commits removal before calling the host detach callback;
that callback may synchronously select, hide or dispose. Repeated removal is
inert. Host callbacks execute synchronously unless explicitly deferred.

Files have stable object identity and immutable id/size during these commands.
A full frame replaces displayed state; loaded values can decrease or reset.
A decode result resolves once; rejected decode and physical transfer completion
are outside this embedding's model. Each workspace has its own lifetime.

The mounted component delegates synchronous select/retry/hide commands to its
session, projects state through the actual framework, and disposes its session
on lifecycle teardown. The source uses EventTarget and AbortController; decode
may return a value or Promise. jQuery commands use synchronous triggerHandler.
