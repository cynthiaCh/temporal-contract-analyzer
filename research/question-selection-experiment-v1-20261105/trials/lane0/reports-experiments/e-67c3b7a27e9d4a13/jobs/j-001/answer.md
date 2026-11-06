Fixed the presence panel so it attaches its listener before connecting, allowing it to receive the initial online-user state. It also discards delayed values after the panel closes or switches rooms.

Verified synchronous and deferred bootstrap, later updates, workspace navigation, and cleanup. The metrics consumer was unchanged.