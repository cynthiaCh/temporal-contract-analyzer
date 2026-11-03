# Presence panel contract — synchronous decoding

The presence panel must display the initial online-user snapshot and later updates,
for both synchronous and deferred bootstrap delivery. Decoding in this case always
returns a value immediately; asynchronous decoding is outside this task.

Publishing a snapshot calls the host inline. That callback may synchronously select
another room or hide the panel before the outer selection returns. The most recent
navigation request owns the panel. Departed subscriptions must stop publishing and
must be detached; a later hide must also detach the surviving subscription. Normal
switching, closing and reopening remain supported.

The metrics consumer intentionally excludes the synchronous initial snapshot and
counts later updates only. Its policy and the channel/navigation public APIs must
remain unchanged. No new dependency is needed; the candidate is a Node ES module.
