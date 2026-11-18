# Workspace draft editor

`editor.js` drives one visible document editor. The workspace store retains draft
text across navigation and closed editor views. Returning to a document restores
its last accepted edit. Save-status listeners belong to the visible editor view;
they stop when that view begins closing.

`search-preview.js` is an adjacent transient search panel. It publishes after a
40 ms quiet interval. Hiding it discards an unpublished query, and the panel can
be reused afterward.

The editor exposes synchronous `open`, `edit`, and `close` methods. `store`
provides `read`, `write`, and `subscribe`; `timers` provides
`schedule(callback, delay)` and `cancel(handle)`. Keep these public interfaces.
