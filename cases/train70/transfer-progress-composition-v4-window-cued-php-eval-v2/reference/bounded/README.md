# Insurance damage evidence transfer

This workspace selects payload files, starts transfers, records queue and
progress history, and paints progress for its open panel. Runtime: PHP 7.4.3.
Dependencies: JSON extension 7.4.3. See src for the session/component entry API.

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

Environment.call/bind provides a synchronous source embedding: listen(file
 token, callback token) returns a subscription, start can invoke it before
returning, and unlisten may reenter navigation. decode(file token, packet,
completion token) returns {deferred:false,frame} or {deferred:true}. Deferred
completion invokes the bound native closure on an explicit later host turn.
Transport receives a physical cancellation observer corresponding to the
native attempt state; cancel is idempotent. The wire embedding interns file
objects and forwards source/sink calls. Go uses context cancellation; the other
native ports use object flags. No native DOM/Promise runtime is claimed.
