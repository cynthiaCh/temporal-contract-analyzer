# Workspace drafts with asynchronous acknowledgements

open/edit/close are synchronous. The editor currently submits every edit.
A visit's latest pending text must be submitted exactly once before close or
navigation returns; submission must not wait for network acknowledgement.
Accepted writes belong to the document, survive navigation, and all settle.
Store read exposes the latest accepted draft for immediate reopen; readPersisted
exposes acknowledged data, protected by write revision against late old writes.
The provided transport accepts a write synchronously and returns a Promise.
Its start callback may synchronously open another document, reopen the same
one, hide the editor, or edit that new visit. Acceptance occurs before that hook.
Navigation priority follows call start order: a newer open/close supersedes an
outer navigation that resumes after a save-start callback. Obsolete destinations
must not render. A newly accepted edit must not be erased by old flush cleanup.

A save-status notification may appear only for the current visit's latest edit.
A pending newer edit invalidates an older acknowledgement even before its own
write is submitted. store.write(id,text,owner) round-trips an opaque owner token;
attachSaveStatus supports an owner predicate. Reopening the same document does
not give its new visit ownership of the old visit's acknowledgement.
Do not cancel accepted saves to suppress UI messages. No network failures or
retry policy are included in this fixture; each transport Promise settles once.

The search preview is transient: 40 ms quiet interval, discard pending query
on hide, reusable afterward. It is outside the editor maintenance request.
