The workspace draft editor currently writes to the store on every keystroke.
Coalesce edits using the existing trailing-task utility: after a 120 ms quiet
interval, write only the latest text in that editing burst. Subsequent bursts
must continue to save. Preserve the editor's other behavior and public interfaces.
The adjacent search preview is outside this maintenance change.

Pending draft text belongs to the document that was edited. Leaving an editor
must commit its latest pending text exactly once before close/open returns, but
must first retire that view's save-status binding. A commit notifies workspace
integrations synchronously: navigation requested inside that callback supersedes
the outer navigation, and must not be overwritten afterward. Reopening the same
document restores its last text without retaining an old batch. A timer-fired
commit may also reenter navigation. Search preview work remains discard-on-hide;
do not change the shared utility's cancel operation into a flush operation.
