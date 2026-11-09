R01 [Applicability]
Applies when shared cache state outlives observers, each attempt has its own cancellation resource, actual access to the cancellation capability is recorded lazily, and paused continuations resume asynchronously.

R02 [Event relation]
For fresh online-mode work that has not entered execution while offline, after the last observer leaves, prevent that attempt from entering on a reconnect continuation with a still-live cancellation signal. Coordinate settlement, state restoration and resource termination according to existing cancellation semantics.

R03 [Exclusion]
Do not retire all work merely because it is paused, has not entered execution or temporarily has no observers. Background refresh backed by an existing successful cache, and work that has entered execution without accessing its cancellation capability, may continue and write back to the cache under existing rules.

R04 [Preservation]
Keep the shared consumption record and the cancellation resource of an individual attempt under their respective ownership. An attempt-local resource does not justify relocating, resetting or making the shared consumption record attempt-local.

R05 [Preservation]
Preserve sharing across multiple observers, harmless handling of unknown departures, physical abort and prior-state restoration for consumed work, background completion for entered but unconsumed work, and isolation that prevents late completion of an old attempt from overwriting current data.

R06 [Verification]
Separately test zero entry or entry with an already-aborted signal after the target offline departure and reconnect; legitimate cached background continuation and later consumption; and continuation eligibility, asynchronous timing, state restoration, observer reuse and late-completion isolation.
