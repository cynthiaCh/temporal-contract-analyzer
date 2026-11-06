Fixed the presence panel so it receives the initial synchronous online-user state. The panel also ignores stale callbacks when navigation switches rooms or hides it during a presence update.

Verified synchronous and deferred bootstrap, workspace navigation, pending decodes, and the existing metrics behavior. The metrics consumer was unchanged.