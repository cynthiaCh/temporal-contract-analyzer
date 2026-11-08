// Let me analyze the issue more carefully by looking at the exact problem statement
// The issue says: "The archaeological excavation atlas service can now report that a package is still pending before it becomes ready. Update the foreground preparation client so it keeps checking pending preparation and delivers the package only after a ready status."

// Looking at the current implementation, I think the issue might be that:
// 1. The service can return pending multiple times
// 2. The client should keep checking until ready
// 3. But there might be a race condition or logic issue

// Let me examine the code more carefully to see if there's a problem with the current logic

// From session.js:
// In Resource.check():
//   - If ready === true: complete (cancel retry, set loading false, add to completed)
//   - If ready === false: call pending(generation)

// In WorkspaceJob.pending():
//   - Call schedule(generation) to retry later

// In DialogResource.pending():
//   - Just call publish() - no retry scheduling

// The issue might be that the foreground preparation client (WorkspaceJob) should be more robust in handling
// the case where the service reports pending multiple times before becoming ready.

// But actually, looking at the current code, it seems to be working correctly.
// Let me think about what could be wrong...

// Maybe the issue is that the client should not deliver the package until it's ready,
// but there's some scenario where it might deliver prematurely.

// Looking at the code again, I think the issue might be in the timing or the way the client
// handles the state transitions. Let me check if there's a specific case that's not handled properly.

// Actually, let me re-read the issue once more...

// The issue says "Update the foreground preparation client so it keeps checking pending preparation and delivers the package only after a ready status."

// This suggests that the current client might be delivering packages before they're ready.
// But looking at the code, it seems like it should wait until ready.

// Wait, let me check if there's a problem with the DialogResource vs WorkspaceJob behavior.
// The DialogResource (for downloads) just publishes when pending, but WorkspaceJob (foreground) schedules retries.

// Maybe the issue is that the client is not properly waiting for the ready status in all cases.