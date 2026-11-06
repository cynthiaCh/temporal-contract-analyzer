# Document workspace departure handoff

`workspace.js` manages one visible document. Edits write synchronously to the
document store. Explicit close already performs a departure handoff so the host
can commit departure metadata or redirect to a conflict document.

A handoff integration may synchronously call the supplied navigation API. A
navigation call that starts later takes precedence, even if it returns before an
older call. `dispose()` is a silent teardown and does not run business handoff.

The workspace exposes synchronous `open`, `edit`, `close`, and `dispose` methods.
Keep these public interfaces and the document store's `read` and `write` methods.
