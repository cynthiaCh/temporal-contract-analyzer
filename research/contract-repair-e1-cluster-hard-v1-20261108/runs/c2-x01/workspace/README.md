# Observatory exposure package
The transport asynchronously fulfills false (pending) or true (ready). It can
report pending repeatedly. It does not issue retries itself. Retry callbacks are
scheduled for a later event turn and can be cancelled; no real-time interval is
part of this API. Render consumers never call back into this resource.

The foreground resource serves an opened document package. start, close, reopen
and snapshot are its public commands. The adjacent workspace job has its own
lifetime; its panel is only a display. Final owner disposal releases resources.
See the native resource classes and the workspace close implementation.

Business context: Observatory exposure package.
