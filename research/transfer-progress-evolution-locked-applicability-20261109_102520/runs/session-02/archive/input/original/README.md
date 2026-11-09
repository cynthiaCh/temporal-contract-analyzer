# Transfer retry panel

This frontend workspace selects files, starts transfers, and shows queued status.
Run with Node v16.20.2; there are no dependencies. `src/workspace.js` exports
`createTransferWorkspace({ transport, onCancel, record, showQueued })`. Each
workspace has independent visit and attempt counters. A `select(file)` call
opens a new visit, including when the exact same file object is selected again.
`retry()` accepts one retry for the current visit; `hide()` closes its panel;
`dispose()` ends the workspace. `snapshot()` exposes current ownership.

Retry already cancels the previous transfer before enqueueing an accepted retry. Preserve that behavior during progress maintenance.
An accepted retry always belongs to the file and visit present at entry, creates
exactly one new attempt, and remains in the queue record even if cancellation
causes navigation. Attempt IDs increase once per enqueued command within each
workspace; navigation must not retarget an accepted retry to the newly selected
file or drop its command. Queueing and recording are synchronous.

Cancellation uses a native `AbortController`: `abort()` synchronously calls the
host's `onCancel` observer before returning. That observer may select another
file, hide the panel, or hide and reopen the identical file object. New selection
immediately starts its own transfer. The newer visit must retain its view and
handle when the older retry resumes. Queued notices are visible output: a notice
from a retired visit must not be sent, including after reopening the same file.
Normal retries in a current visit still issue one queued notice each.

The accepted old retry must still enqueue and record once after such navigation.
Its newly created transfer is canceled immediately if its visit has ended; this
does not remove its retained queue record. There must be no remaining active
transfer from that old visit. The new visit remains able to retry and hide;
hiding cancels its owned handle and repeated cancellation is idempotent.
Selection and hiding may themselves cancel an old handle and synchronously
receive newer navigation; the newer navigation keeps ownership. A hidden panel
accepts no retry. Workspace disposal cancels every remaining transfer and is
idempotent. Disposing one workspace cannot affect another.

`transport({file, attemptId, signal})` starts a pending physical transfer and
observes the native signal. `record` and `showQueued` are passive synchronous
sinks. Every queue record remains exactly `{fileId, attemptId, visitId, kind}`;
`kind` is `select` or `retry`. Adding `byteCount` from `file.size` is an adjacent
record-format extension requiring separate authorization. Notices remain
`{fileId, attemptId, visitId, status: "queued"}`. Preserve these public interfaces.

## Transfer progress

A file may supply a shared `progressFeed` with a native EventTarget `target`,
`start()`, and `decode(packet)`. Starting a view of the stream may synchronously
emit its cached progress event; further progress events arrive on the same target.
Events are named `progress` and their detail is decoded to `{seq, loaded}`.
Decoding may return a value or a Promise. The same file and source can be reused
by multiple panel visits. Each selected or retried attempt starts one subscription.

The workspace accepts `recordProgress({fileId, attemptId, frame})` and
`showProgress({fileId, attemptId, frame})`. The former is a passive retained audit
sink. Every accepted progress event is recorded exactly once when decoding
finishes, including work accepted before the visit closes. A retired visit
accepts no new progress events. Removing a listener does not retract a decode
that already started. Closing or replacing the visit stops visible progress;
new visits remain live. `showProgress` may synchronously select or hide through
the workspace, and normal current progress must remain visible. Progress does
not change queue records, native transfer cancellation, or accepted retry policy.
Disposal removes subscriptions and cancels transfers; work already accepted
for audit remains retained. Preserve these adapter interfaces.
