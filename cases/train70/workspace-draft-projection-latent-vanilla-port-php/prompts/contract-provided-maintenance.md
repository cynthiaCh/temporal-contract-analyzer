# Coalesce draft saves in the workspace

The editor currently writes to the workspace store on every edit. Change editor
autosave to coalesce a burst of input: after 120 ms without another edit, save
only its latest text. Reuse the existing trailing-task utility where appropriate.
Preserve the workspace's existing navigation and persistence behavior. Keep
search preview behavior unchanged; its timing is outside this maintenance task.


Recovered contract: close or select must commit the departed document's latest
accepted text before returning, under that document's identity, after retiring
its save badge. Flush may synchronously invoke navigation from a store listener.
Both the editor's post-flush state installation and the workspace's subsequent
outline/breadcrumb commit must honor a newer navigation. A correct guard inside
the editor does not cover the caller's later projection write. Every select is a
distinct visit even for the same document; a superseded visit must not enter
history. A consumed batch saves once, and a callback-created new batch survives.
Preview hide discards work; only the granted suffix changes its quiet interval.
