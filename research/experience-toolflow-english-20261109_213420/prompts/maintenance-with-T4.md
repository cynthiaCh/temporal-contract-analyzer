Fix the museum accession activity viewer's startup and navigation lifecycle.

Opening a feed backed by a warm cache sometimes leaves the first batch missing,
although later activity appears. During quick feed changes or closing and
reopening the panel, rows or the count can also appear for a previous visit.

Correct these timing problems while preserving normal live updates, history
recording, public APIs and the existing rendering adapters. The independent
metrics consumer is outside this repair.


The following automatic Contract is auxiliary material. Check it against the current task and source; do not follow unsupported policies blindly:
For each panel visit, receive the cached first batch when its feed starts, including when start emits synchronously, and continue receiving live deltas while that visit is selected. After selection changes or the panel hides, prevent rows or counts from a previous visit from becoming visible, including when the same feed object is reused and decode or paint completes later. A count may become visible only after its corresponding rows have finished painting and only if that visit is still current. Preserve history for every batch already received by the panel subscriber once decoding completes, even if the visit has ended; detachment stops new reception but does not revoke accepted work. Preserve public APIs, payloads, host rendering behavior, and the independent metrics consumer’s policy. Account for callbacks that run inline and painting that synchronously navigates or hides; no particular repair strategy is required.

Locate, repair and validate autonomously within /workspace. Modify product source only; preserve interfaces, dependencies, and build/test configuration. Do not install dependencies or access the network or research materials. For JavaScript use /runtime/node; for Python use /usr/bin/python3 -B. Write your final report in English.
Original snapshots, final source, diffs, logs and scores are archived automatically by external Python code. Only repair business code and perform necessary validation. Do not create experiment backups, archived patches or result-summary files. Return a JSON object whose only field is report. In English, briefly describe the actual changes, validation and uncovered scope, using no more than 6000 Unicode characters.

The following is the frozen English experience translation. Check its applicability against current evidence:
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
