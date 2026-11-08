# Host API

Store read/write/subscribe are synchronous. Records are written before inline
delivery; removed subscriptions are skipped. onSaved may call navigation or edit.
Rendering a save event is tied to the mounted subscription; close/open retires
that subscription immediately. Departed text is readable when navigation returns.
Each opening is a fresh visit, even when its record key is the same.

Archive capture/list copy document and text values; these sinks never navigate.
A submit accepts its selected record and text at entry, returns one immutable
receipt, and the store already contains that text when capture is called. No
selection returns null. Later navigation does not undo acceptance. Visible
feedback belongs to its original visit; navigation clears it, and uninterrupted
acceptance displays it. This API is also used after edits continue.

Timers schedule(callback, delay) and cancel(handle) are injected by the host.
Cancellation discards a pending preview query. Preview publishes at a 40 ms
quiet interval; hide discards unpublished work and subsequent reuse is supported.
