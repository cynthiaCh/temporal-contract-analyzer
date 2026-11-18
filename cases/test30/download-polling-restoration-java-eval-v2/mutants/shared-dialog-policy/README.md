# Customs certificate packaging
The transport asynchronously fulfills false (pending) or true (ready). It can
report pending repeatedly. It does not issue retries itself. Retry callbacks are
scheduled for a later event turn and can be cancelled; no real-time interval is
part of this API. Render consumers never call back into this resource.

The foreground resource serves an opened document package. start, close, reopen
and snapshot are its public commands. The adjacent workspace job has its own
lifetime; its panel is only a display. Final owner disposal releases resources.
See the native resource classes and the workspace close implementation.

Business context: Customs certificate packaging. The package token identifies the prepared artifact;
foreground presentation and workspace preparation have separate owners.

Native embedding ABI: create(host, surface, token) (Go: createResource) returns
a Client exposing start/close/reopen/snapshot/dispose (Go exported counterparts).
The host provides deferred checks, timer registration/cancellation and output.
Resource helper types are implementation details; clients use the interface.
