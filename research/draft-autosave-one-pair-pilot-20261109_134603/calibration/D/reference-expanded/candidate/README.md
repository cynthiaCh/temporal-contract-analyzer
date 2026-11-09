# Workspace draft editor

`createWorkspace` drives a document editor and its save badge. The workspace store
holds draft text across navigation and closed editor views. Returning to a document
restores the user's last edit. Save integrations receive committed records and may
select another document synchronously. Later navigation means the navigation request that starts later takes precedence, even if an earlier request returns afterward. For example, if open(B) starts and saving the departed A invokes a callback that calls open(C), C remains selected after the callback and the outer open(B) return. If that callback calls close() instead, the editor remains closed after the outer open(B) returns. These are navigation results, independent of when the departed document's save occurs.
When close/open returns, the departed document's last accepted edit is available
through the store, even if the next view selects a different document.

`createSearchPreview` is an adjacent transient search panel. It publishes after a
40 ms quiet interval; hiding it discards an unpublished query. It can be reused.

The public methods are synchronous. Output render functions observe state; navigation
comes through the workspace API, including its `onSaved` integration. `store` provides
`read`, `write` and `subscribe`; `timers` provides `schedule(callback, delay)` and
`cancel(handle)`. Production timers use the browser's timers. Keep these interfaces.
