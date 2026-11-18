# Harbor clearance review


The workspace edits persistent documents and submits snapshots to a review queue.
The public API is synchronous: open(id), edit(text), close(), submit(), dispose().
Returning to a document creates a fresh editor visit and restores persisted text.
The adjacent search preview publishes after a 40 ms quiet interval; hiding it
cancels unpublished work and later queries remain usable.

The coordinator owns editor visits; the acquired confirmation capability owns a view outlet. The document repository and durable queue are separate services. Component or native source defines the local service contracts.
Their local interface contracts define the behavior to preserve.

The injected store has read/write/subscribe, the queue has enqueue/list/subscribe,
and timers have schedule(callback, delay)/cancel(handle). Render functions are
output sinks and do not call application code. Keep the workspace API and these
injected interfaces. A submission returns the queue receipt, or null when no
editor is selected. Dispose detaches integrations before closing the workspace.

Typed pointer visit and injected function callbacks; acquired capability uses pointer identity, never document-key equality.

An outlet acquires the visit active when binding is called; it cannot infer an earlier action from a receipt. Each opening creates a new identity. Native RPC only adapts timer and passive output/integration resource calls; storage, queue delivery, acquired outlet and command state execute in the target runtime.
