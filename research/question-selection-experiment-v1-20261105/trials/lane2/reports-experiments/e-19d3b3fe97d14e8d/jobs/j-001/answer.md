Fixed the presence panel so its listener is active before the channel emits the initial state. The panel also ignores delayed decode results from a visit that has closed or been replaced. Workspace navigation still works, and the metrics consumer is unchanged.

Verified synchronous and deferred bootstrap, updates, navigation, cleanup, stale results, and metrics behavior.