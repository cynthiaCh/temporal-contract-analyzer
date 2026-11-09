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
Applies when a shared source can be reused across visits, each attempt has an independent subscription, and visible feedback can synchronously reenter navigation. The same data object does not imply the same visit identity.

R02 [Event relation]
For a source that may synchronously emit cached events during startup, establish the attempt's admission eligibility before starting it. Subsequent streaming events remain subject to that attempt's eligibility.

R03 [Preservation]
Once a visit retires, stop admitting subsequent events even if the cleanup or removal capability has not yet returned. This restriction must not depend on deferred physical cleanup.

R04 [Preservation]
For an event admitted before retirement, retain its audit exactly once when decoding settles. That settlement must not authorize the retired visit to admit new events or produce visible progress.

R05 [Preservation]
After synchronous reentry, the new visit retains its own UI and cancellation resources. Subsequent settlement or cleanup of the old visit must not take ownership from the new one. Preserve existing retry, cancellation and entry-bound record semantics.

R06 [Verification]
Test subsequent events from the same source after synchronous navigation and before the outer startup call returns. Cover hiding, switching and reopening the same source separately. Independently check rejection by the retired visit, delayed audit of previously admitted events, and valid visible progress for the current visit. Cleanup tests performed only after return do not cover this window.

R07 [Exclusion]
Limit this repair to progress-admission timing and lifecycle boundaries. Do not expand records or public interfaces, or change shared-source reuse, independent workspaces, retry, cancellation, navigation, resource ownership or the audit policy for already-admitted events.
