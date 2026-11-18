# Host integration

open(id), edit(text), close() and dispose() are synchronous entry points.
The store owns persisted document records independently of any mounted view.
Store delivery writes first, snapshots subscriptions, and skips removed listeners.
onSaved is called inline and can navigate or edit; rendering is an output sink.
Every open creates a fresh visit and subscription, including same-key reopen.
Injected timers provide schedule(callback,delay) and cancel(handle).
The preview is transient and independent of the editor's persistence policy.
