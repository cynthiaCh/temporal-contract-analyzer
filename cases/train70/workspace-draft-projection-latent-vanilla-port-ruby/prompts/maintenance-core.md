# Coalesce draft saves in the workspace

The editor currently writes to the workspace store on every edit. Change editor
autosave to coalesce a burst of input: after 120 ms without another edit, save
only its latest text. Reuse the existing trailing-task utility where appropriate.
Preserve the workspace's existing navigation and persistence behavior. Keep
search preview behavior unchanged; its timing is outside this maintenance task.
