Fixed the presence panel so it subscribes before connecting, allowing it to receive the initial synchronous bootstrap. The panel also discards a subscription if bootstrap delivery triggers workspace navigation or closes the panel.

I verified synchronous and deferred presence, navigation, pending decodes, and metrics behavior. The metrics consumer was unchanged.