Pending draft text belongs to the document that was edited. Leaving an editor
must commit its latest pending text exactly once before close/open returns, after
retiring that view's save-status binding. Reopening a document restores its last
text without retaining an old batch. Search preview work remains discard-on-hide;
do not change the shared utility's cancel operation into a flush operation.
