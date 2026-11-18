The podcast production notes currently writes on every edit. Coalesce edits using the existing trailing utility: after a 120 ms quiet interval, write only the latest text in that editing burst. Subsequent bursts must continue to save. Preserve other behavior and public interfaces. The adjacent search preview is outside this maintenance change.

Pending draft text belongs to the document that was edited. Leaving an editor
must commit its latest pending text exactly once before close/open returns, but
must first retire that view's save-status binding. A commit notifies workspace
integrations synchronously: navigation requested inside that callback supersedes
the outer navigation, and must not be overwritten afterward. Reopening the same
document restores its last text without retaining an old batch. A timer-fired
commit may also reenter navigation. Search preview work remains discard-on-hide;
do not change the shared utility's cancel operation into a flush operation.

Environment: public entry calls are synchronous on one event thread. Store writes
the record before inline notifications; delivery skips subscriptions removed
during that delivery. onSaved may navigate or edit synchronously. Renderers are
observation-only sinks. Timers are cancellable; persistence belongs to the
document store independently of view lifetime. Empty text is a legal edit.
