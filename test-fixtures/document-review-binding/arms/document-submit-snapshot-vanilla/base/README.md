# Document drafts and submission receipts

The workspace edits persistent document drafts. `open(id)`, `edit(text)`, `close()`
and `submit()` are synchronous; `dispose()` detaches integrations and closes.
When close/open returns, the departed document's last accepted edit is readable
from the store. A close/open request retires its previous save badge immediately.
Reopening a document restores its saved text in a new editor visit.

The store writes a record before notifying subscribers inline. `onSaved` may
navigate or edit through the supplied workspace API. Navigation precedence is
ordered by request start: a request that starts later wins even when an earlier
request returns afterward. Render functions and the receipt archive are output
sinks and never call back into the workspace.

`submit()` accepts the document and latest text selected at its call entry. With
no selection it returns null and creates no receipt. Otherwise it creates exactly
one immutable archive receipt and returns it before the call ends. Accepted text
must be persisted before the archive captures the receipt. Later edits or
navigation cannot change that receipt's document, text, or obligation to exist.
Submitting does not itself navigate. Its visible submission notice belongs only
to the editor visit that accepted the action: it may appear only if that same
visit is still active when the notice is emitted. Reopening the same document
creates a different visit. Any navigation clears the previous submission notice.
An uninterrupted submit must still show its receipt. Further edits remain usable.

The archive provides `capture({id, text})` and `list()`; receipts hold immutable
copies. The store provides `read`, `write`, and `subscribe`; timers provide
`schedule(callback, delay)` and `cancel(handle)`. Keep these interfaces and the
workspace API. The public renderer arguments remain document, save event, or
receipt values (null clears a document/notice).

The adjacent search preview publishes after a 40 ms quiet interval. Hiding it
discards an unpublished query, and a later query starts fresh work.
