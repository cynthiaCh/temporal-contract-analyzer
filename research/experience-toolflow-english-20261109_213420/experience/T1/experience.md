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
