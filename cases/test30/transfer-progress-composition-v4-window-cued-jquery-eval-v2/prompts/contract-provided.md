# Provided contract

Apply the complete contract below together with `README.md`: register before warm
start; admit frames only while the attempt is current and not aborted; finish
and audit every admitted decode once; publish UI only for the current visit and
never behind a newer arrival; treat listener cleanup as a synchronous navigation
boundary where later-started commands win; preserve retry ownership and record
shape. The optional authorization alone adds `byteCount`.

Frame arrival order is visit-owned and continues across retry attempts. Accepted
decode always records audit once even after retirement; visible publication also
requires the originating visit and a token newer than its last published frame.
Removing a listener may synchronously navigate, so a later-started cleanup
navigation supersedes the older outer command before its destination starts.
The diagnostic telemetry consumer is delta-only: it intentionally starts before
attaching and must not receive cached bootstrap.

Port environment: single event loop, synchronous host methods except explicitly deferred decode; start and showProgress may reenter before cleanup handle/attempt is returned; listener removal commits before synchronous host detach navigation; repeated removal inert; record, showQueued, recordProgress, transport passive synchronous sinks in parent schedules; onCancel may reenter in preserved boundaries; decode returns value or single-fulfillment deferred result; manually resolved, never forced async; files stable objects with immutable id/size and shared source per file; no decode rejection or concurrent-thread race modeled. Native source services forward callbacks synchronously; deferred completion retains the native bound closure. A native cancellation object corresponds to the physical signal; framework lifecycle teardown disposes its session.

Accepted retry and visible ownership are separate obligations. A retry accepted
at call entry retains exactly one command for that entry visit and file, even
if cancelling its previous attempt synchronously selects, hides, or disposes.
The cancellation precedes enqueueing that captured retry. Later navigation owns
the panel: the captured retired retry cannot replace its owner or emit a queued
notice, and its physical attempt is cancelled. Retirement prevents new frame
admission and decoding; it does not erase accepted queue history or an already
admitted decode's eventual audit. The existing record shape is preserved.
