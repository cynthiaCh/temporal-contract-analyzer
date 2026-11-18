Pending draft text belongs to the document that was edited. Leaving an editor
must commit its latest pending text exactly once before close/open returns, but
must first retire that view's save-status binding. A commit notifies workspace
integrations synchronously: navigation requested inside that callback supersedes
the outer navigation, and must not be overwritten afterward. Reopening the same
document restores its last text without retaining an old batch. A timer-fired
commit may also reenter navigation. Search preview work remains discard-on-hide;
do not change the shared utility's cancel operation into a flush operation.
