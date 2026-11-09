# Museum accession notes

This desk edits persistent records and accepts archive receipts. The host injects
store, timers, archive and rendering services. Public calls open(id), edit(text),
close(), submit() and dispose() are synchronous. Renderers are output sinks and
never reenter. Store delivery may call workspace integrations inline; the latest
navigation request by start order is the host's selection. Adjacent preview uses
its own trailing utility and can be hidden or reused. See docs/host-api.md and
the source implementations for the service APIs.
