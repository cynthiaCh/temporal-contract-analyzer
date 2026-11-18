Repair the insurance tariff lookup cache: a fresh online-mode query mounted and unmounted entirely offline later calls its signal-consuming query function with a live signal after reconnect. This occurs independently of refetchOnReconnect. Preserve supported query behavior, interfaces, dependencies and build/test configuration. Change product source only.

Additional contract:
- Last observer of a pending+paused fetch leaves before queryFn entry; reconnect must not invoke it with a live signal
- Signal getter marks query-level consumption lazily; reset occurs only at actual queryFn entry. Paused attempts retain prior consumption and last-observer cancellation policy.
- Removing one of multiple observers must not cancel active observed work; removal of unknown observer is inert
- Previously successful cached paused fetch or unconsumed in-flight request remains allowed to finish; cancelRetry differs from cancel
- Consumed in-flight cancellation reverts previous query state, idles fetch and aborts physical signal; late completion cannot commit
- Network mode controls initial start; focus/online eligibility controls paused continuation; refetchOnReconnect does not suppress retryer continuation
- Actual promise settlement and retryer rejection gate prevent canceled or old attempt from accepting late completion
The signal-consumption flag belongs to the query; a retained context getter still marks that query while returning its own attempt controller. Eligible paused continuation release is not revoked by a later offline event. Each physical controller and settlement remains bound to its original attempt.
Environment: single event loop, lazy reads, synchronous queryFn entry, actual async completions and deterministic scheduler. No invocation or aborted-at-entry invocation are both valid for the reported fresh-query schedule.
