The workspace draft editor currently writes to the store on every keystroke.
Coalesce edits using the existing trailing-task utility: after a 120 ms quiet
interval, write only the latest text in that editing burst. Subsequent bursts
must continue to save. Preserve the editor's other behavior and public interfaces.
The adjacent search preview is outside this maintenance change.
