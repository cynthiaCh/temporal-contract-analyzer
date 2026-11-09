# Museum accession activity viewer

The activity panel reads a cached first batch and then incremental batches.
The host supplies rendering and history adapters. The pinned runtime and host adapter are described in docs/host-api.md.

Public workspace methods are select(feed, mode) and hide(). Selecting the same
feed after leaving creates a new panel visit. Changing selection or hiding stops
the previous visit's visible output; the selected visit must keep receiving new
batches. Reusing an existing feed object is supported.

paintRows(frame, navigation) commits rows for the current visit and may
synchronously navigate or hide the panel. It can return a Promise for layout
completion. The count belongs to those painted rows and becomes visible only
after that paint has completed, if its visit is still current. Ordinary live
counts remain required. A component or feed object can survive several visits.

History records each received batch once its decoding completes. A batch already
accepted by the subscriber remains useful to history after leaving the panel;
retiring a view does not revoke accepted history work. Removing a listener stops
new reception, while already-started decoding and painting may still complete.

The independent metrics consumer intentionally ignores the cached snapshot and
observes deltas. Its policy is outside this panel repair unless separately
authorized. Preserve APIs, payloads, rendering timing and history behavior.

See docs/host-api.md for the native method spellings and injected completion interface.
