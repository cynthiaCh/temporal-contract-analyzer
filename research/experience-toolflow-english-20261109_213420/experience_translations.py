"""AI-assisted English translations; derived texts, not new model candidates."""
RULES = {
    'T1': [
        ('applicability', 'Applies when a shared source can be reused across visits, each attempt has an independent subscription, and visible feedback can synchronously reenter navigation. The same data object does not imply the same visit identity.'),
        ('event_relation', 'For a source that may synchronously emit cached events during startup, establish the attempt\'s admission eligibility before starting it. Subsequent streaming events remain subject to that attempt\'s eligibility.'),
        ('preservation', 'Once a visit retires, stop admitting subsequent events even if the cleanup or removal capability has not yet returned. This restriction must not depend on deferred physical cleanup.'),
        ('preservation', 'For an event admitted before retirement, retain its audit exactly once when decoding settles. That settlement must not authorize the retired visit to admit new events or produce visible progress.'),
        ('preservation', 'After synchronous reentry, the new visit retains its own UI and cancellation resources. Subsequent settlement or cleanup of the old visit must not take ownership from the new one. Preserve existing retry, cancellation and entry-bound record semantics.'),
        ('verification', 'Test subsequent events from the same source after synchronous navigation and before the outer startup call returns. Cover hiding, switching and reopening the same source separately. Independently check rejection by the retired visit, delayed audit of previously admitted events, and valid visible progress for the current visit. Cleanup tests performed only after return do not cover this window.'),
        ('exclusion', 'Limit this repair to progress-admission timing and lifecycle boundaries. Do not expand records or public interfaces, or change shared-source reuse, independent workspaces, retry, cancellation, navigation, resource ownership or the audit policy for already-admitted events.'),
    ],
    'T4': [
        ('applicability', 'Applies when shared cache state outlives observers, each attempt has its own cancellation resource, actual access to the cancellation capability is recorded lazily, and paused continuations resume asynchronously.'),
        ('event_relation', 'For fresh online-mode work that has not entered execution while offline, after the last observer leaves, prevent that attempt from entering on a reconnect continuation with a still-live cancellation signal. Coordinate settlement, state restoration and resource termination according to existing cancellation semantics.'),
        ('exclusion', 'Do not retire all work merely because it is paused, has not entered execution or temporarily has no observers. Background refresh backed by an existing successful cache, and work that has entered execution without accessing its cancellation capability, may continue and write back to the cache under existing rules.'),
        ('preservation', 'Keep the shared consumption record and the cancellation resource of an individual attempt under their respective ownership. An attempt-local resource does not justify relocating, resetting or making the shared consumption record attempt-local.'),
        ('preservation', 'Preserve sharing across multiple observers, harmless handling of unknown departures, physical abort and prior-state restoration for consumed work, background completion for entered but unconsumed work, and isolation that prevents late completion of an old attempt from overwriting current data.'),
        ('verification', 'Separately test zero entry or entry with an already-aborted signal after the target offline departure and reconnect; legitimate cached background continuation and later consumption; and continuation eligibility, asynchronous timing, state restoration, observer reuse and late-completion isolation.'),
    ],
}
LABELS = {'applicability':'Applicability','event_relation':'Event relation','preservation':'Preservation','verification':'Verification','exclusion':'Exclusion'}

def render(primary):
    return '\n\n'.join('R%02d [%s]\n%s' % (i,LABELS[category],body) for i,(category,body) in enumerate(RULES[primary],1))+'\n'
