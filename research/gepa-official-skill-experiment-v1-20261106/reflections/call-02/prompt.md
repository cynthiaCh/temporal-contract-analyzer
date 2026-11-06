Optimize only a reusable temporal-contract checking skill supplied to a code-maintenance agent. The original task, execution system, tools, retrieval, scoring and ending protocol are fixed and cannot be changed. This is reflection and instruction proposal, not a maintenance run: do not call tools, read files, run commands or ask questions. Everything needed for this proposal is in this message.

Current skill:
```
# Temporal contract skill: result ownership and effect validity

Purpose: help complete the original maintenance task. This skill is an aid, not a second task, a request for a prose-only answer, or a new business specification. Apply only what the original task and visible project evidence support.

S1 Applicability. Look for work that can finish after the initiating access, operation, or consumer changes, or a callback that can change ownership while another call is still running. Look for multiple effects such as a stored record and a current display. If these conditions are absent, record why this skill does not apply and continue the maintenance task.

S2 Source evidence. Read the entry, actual producer/decoder or dependency, completion callback, ownership transition/cancel path, and each effect consumer relevant to the change. Cite file:line. Separate task requirements, source facts, hypotheses, and unavailable evidence. Do not infer a dependency guarantee from a function name or add input formats/behaviors because they seem plausible.

S3 Check relations. Identify the resource, access/visit, physical operation/attempt, and accepted value or work when the visible code distinguishes them. Follow when those identities are captured, retired, and compared. Determine from this project whether cancellation removes future inputs, cancels already-started work, or only hides a consumer. For each effect, ask independently what identity and validity it needs; do not assume one guard suits every effect.

S4 Compare concrete orders. Using controllable visible APIs, compare ordinary completion; completion after close/switch; same-resource reuse; and replacement/retry if present. Include synchronous callback reentry when supported by the source. Observe stored effects and visible effects separately. For ordered full results, compare normal completion order and reversed completion order without inventing a frame schema.

S5 Non-applicability and unknowns. Background obligations, rollback, permission withdrawal, or dependencies that truly suppress completion can change the answer. Find visible evidence or keep the question unresolved. Do not impose persistence after cancellation or access-based cancellation on every project. Preserve other consumers of shared helpers and original public interfaces.

S6 Repair and verify. Implement the smallest supported maintenance change, or explain with evidence why no change is needed or why the task remains incomplete. Run relevant candidate-visible checks, inspect their real output and revise if warranted. Verify ordinary use, lifecycle boundaries, distinct effects, reuse, and adjacent behavior only where applicable. Keep failed/unrun checks explicit. A contract discussion or successful self-written smoke check alone is not completion of the original repair.

```

Actual train executions and grounded feedback:
```
# Example 1
## Inputs
### original_maintenance_task
A transfer with a warm progress source shows no initial progress until a later
packet arrives. Restore the initial progress update without changing the public
transfer, retry, navigation, cleanup, audit, or queue-record behavior. Full
progress frames may decode out of order; do not allow an older frame to roll the
current display backward. Preserve ordinary streaming, diagnostic telemetry,
and subsequent uses.

### visible_context
# Retrieved candidate context

Raw source, configuration and documentation excerpts selected using the original task only. Retrieval is incomplete; inspect other candidate files when needed.

## README.md:1-26
```
# Transfer retry panel with decoded progress

This workspace selects files, starts transfers, records queue and progress
history, and paints progress for the open panel. Run it with Node v16.20.2; it
has no dependencies. `src/workspace.js` exports the workspace and the source
helpers used by the host application.

Selecting a file creates a visit. Retry replaces the physical attempt without
opening another visit. Selecting the same file again does open another visit.
The feed object is shared by attempts and visits for that file. Its `start()`
method may synchronously emit cached data, and `decode(packet)` may return a
value or a Promise.

`recordProgress` appends transfer history. `showProgress` paints the panel.
The queue adapter in `src/queue.js` shows how those two outputs currently relate
to a visit. Queue records, notices, cancellation, retry, navigation, and cleanup
retain their existing behavior. Queue records remain
`{fileId, attemptId, visitId, kind}` unless a separate authorization adds
`byteCount` from `file.size`.

The same feed API also has a diagnostic consumer in `src/telemetry.js`.
It is not the panel and must keep its existing behavior while the panel defect
is repaired. `src/progress-source.js` is the host-visible feed implementation;
the navigation and transfer modules show how ownership is handed off when a
listener is released. Host callbacks are synchronous unless their code returns
a Promise.
```

## src/panel.js:1-41
```
import { enqueueTransfer } from "./queue.js";
import { publishQueued } from "./notice.js";

export function releaseVisit(visit) {
  const handle = visit.handle;
  visit.handle = null;
  if (handle) handle.cancel();
}

export function selectFile(state, file) {
  if (state.disposed) return null;
  const requestId = ++state.nextVisit;
  const previous = state.current;
  state.current = null;
  if (previous) releaseVisit(previous);
  if (state.disposed || state.nextVisit !== requestId) return null;
  const visit = { id: requestId, file, handle: null };
  state.current = visit;
  const handle = enqueueTransfer(state, visit, "select");
  if (state.current === visit) {
    visit.handle = handle;
    publishQueued(state, visit, handle);
  } else {
    handle.cancel();
  }
  return handle;
}

export function hidePanel(state) {
  state.nextVisit++;
  const previous = state.current;
  state.current = null;
  if (previous) releaseVisit(previous);
}

export function disposeWorkspace(state) {
  if (state.disposed) return;
  state.disposed = true;
  hidePanel(state);
  for (const handle of state.tasks.values()) handle.cancel();
}
```

## src/progress-source.js:1-32
```
class ProgressEvent extends Event {
  constructor(packet) {
    super("progress");
    this.detail = packet;
  }
}

// Removal commits before notifying the host. The host callback is synchronous
// and may call workspace.select(...) or workspace.hide(). Repeated removal is inert.
export function createProgressFeed({ initialPacket, decode = value => value, onDetach = () => {} }) {
  const target = new EventTarget();
  const listeners = new Set();
  const add = target.addEventListener.bind(target);
  const remove = target.removeEventListener.bind(target);
  target.addEventListener = (type, listener, options) => {
    add(type, listener, options);
    if (type === "progress") listeners.add(listener);
  };
  target.removeEventListener = (type, listener, options) => {
    remove(type, listener, options);
    if (type === "progress" && listeners.delete(listener)) onDetach();
  };
  return {
    target,
    decode,
    start() {
      const packet = typeof initialPacket === "function" ? initialPacket() : initialPacket;
      if (packet !== undefined) target.dispatchEvent(new ProgressEvent(packet));
    },
    emit(packet) { target.dispatchEvent(new ProgressEvent(packet)); },
  };
}
```

## src/progress.js:1-12
```
// The source is shared by visits of the same file. Decoding may settle later.
export function watchTransferProgress(feed, receive, record) {
  const listener = event => {
    const deliver = frame => { record(frame); receive(frame); };
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver);
    else deliver(decoded);
  };
  feed.start();
  feed.target.addEventListener("progress", listener);
  return () => feed.target.removeEventListener("progress", listener);
}
```

## src/queue.js:1-20
```
import { createTransfer } from "./transfer.js";

// Queue records are retained even when their originating panel visit ends.
export function makeQueueRecord(file, attemptId, visitId, kind) {
  return { fileId: file.id, attemptId, visitId, kind };
}

export function enqueueTransfer(state, visit, kind) {
  const attemptId = ++state.nextAttempt;
  state.record(makeQueueRecord(visit.file, attemptId, visit.id, kind));
  const progress = {
    record(frame) { state.recordProgress({ fileId: visit.file.id, attemptId, frame }); },
    receive(frame) {
      if (state.current === visit) state.showProgress({ fileId: visit.file.id, attemptId, frame });
    },
  };
  const handle = createTransfer(visit.file, attemptId, state.transport, state.onCancel, progress);
  state.tasks.set(attemptId, handle);
  return handle;
}
```

## src/retry.js:1-15
```
import { enqueueTransfer } from "./queue.js";
import { publishQueued } from "./notice.js";

// A retry click accepts exactly one command for the current visit and file.
export function retryTransfer(state) {
  const visit = state.current;
  if (!visit || !visit.handle || state.disposed) return null;
  const previous = visit.handle;
  previous.cancel();
  const handle = enqueueTransfer(state, visit, "retry");
  if (state.current === visit) visit.handle = handle;
  else handle.cancel();
  if (state.current === visit) publishQueued(state, visit, handle);
  return handle;
}
```

## src/telemetry.js:1-12
```
// Diagnostics count live deltas only. A cached bootstrap is panel state, not a delta.
export function collectProgressTelemetry(feed, recordDelta) {
  const listener = event => {
    const deliver = frame => recordDelta(frame);
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver);
    else deliver(decoded);
  };
  feed.start();
  feed.target.addEventListener("progress", listener);
  return () => feed.target.removeEventListener("progress", listener);
}
```

## src/workspace.js:1-27
```
import { selectFile, hidePanel, disposeWorkspace } from "./panel.js";
import { retryTransfer } from "./retry.js";

export function createTransferWorkspace({ transport, onCancel, record, showQueued, recordProgress = () => {}, showProgress = () => {} }) {
  const state = { transport, onCancel, record, showQueued, recordProgress, showProgress, current: null,
    nextVisit: 0, nextAttempt: 0, tasks: new Map(), disposed: false };
  return {
    select(file) { return selectFile(state, file); },
    retry() { return retryTransfer(state); },
    hide() { hidePanel(state); },
    dispose() { disposeWorkspace(state); },
    snapshot() {
      const visit = state.current;
      return { visitId: visit ? visit.id : null, fileId: visit ? visit.file.id : null,
        attemptId: visit && visit.handle ? visit.handle.attemptId : null,
        disposed: state.disposed, attempts: state.nextAttempt };
    },
  };
}

export { createTransfer } from "./transfer.js";
export { makeQueueRecord, enqueueTransfer } from "./queue.js";
export { publishQueued } from "./notice.js";
export { releaseVisit, selectFile, hidePanel, disposeWorkspace } from "./panel.js";
export { retryTransfer } from "./retry.js";
export { collectProgressTelemetry } from "./telemetry.js";
export { createProgressFeed } from "./progress-source.js";
```

## Generated_Outputs
### actual_reads
#### Item 1
##### event_line
11

##### command
/usr/bin/bash -lc 'cat src/telemetry.js'

##### candidate_paths
###### Item 1
src/telemetry.js

#### Item 2
##### event_line
13

##### command
/usr/bin/bash -lc 'cat src/queue.js'

##### candidate_paths
###### Item 1
src/queue.js

#### Item 3
##### event_line
15

##### command
/usr/bin/bash -lc 'cat package.json'

##### candidate_paths
###### Item 1
package.json

#### Item 4
##### event_line
17

##### command
/usr/bin/bash -lc 'cat src/transfer.js'

##### candidate_paths
###### Item 1
src/transfer.js

#### Item 5
##### event_line
19

##### command
/usr/bin/bash -lc 'cat src/progress.js'

##### candidate_paths
###### Item 1
src/progress.js

#### Item 6
##### event_line
22

##### command
/usr/bin/bash -lc 'cat README.md'

##### candidate_paths
###### Item 1
README.md

#### Item 7
##### event_line
23

##### command
/usr/bin/bash -lc 'cat src/progress-source.js'

##### candidate_paths
###### Item 1
src/progress-source.js

### modified_locations
#### Item 1
##### path
src/progress.js

##### diff
--- before/src/progress.js
+++ after/src/progress.js
@@ -1,12 +1,21 @@
 // The source is shared by visits of the same file. Decoding may settle later.
 export function watchTransferProgress(feed, receive, record) {
+  let nextPacket = 0;
+  let lastShown = 0;
   const listener = event => {
-    const deliver = frame => { record(frame); receive(frame); };
+    const packet = ++nextPacket;
+    const deliver = frame => {
+      record(frame);
+      if (packet > lastShown) {
+        lastShown = packet;
+        receive(frame);
+      }
+    };
     const decoded = feed.decode(event.detail);
     if (decoded && typeof decoded.then === "function") decoded.then(deliver);
     else deliver(decoded);
   };
+  feed.target.addEventListener("progress", listener);
   feed.start();
-  feed.target.addEventListener("progress", listener);
   return () => feed.target.removeEventListener("progress", listener);
 }

##### truncated
False

#### Item 2
##### path
src/queue.js

##### diff
--- before/src/queue.js
+++ after/src/queue.js
@@ -9,12 +9,17 @@
   const attemptId = ++state.nextAttempt;
   state.record(makeQueueRecord(visit.file, attemptId, visit.id, kind));
   const progress = {
+    ready(handle) {
+      state.tasks.set(attemptId, handle);
+      if (state.current === visit) visit.handle = handle;
+    },
     record(frame) { state.recordProgress({ fileId: visit.file.id, attemptId, frame }); },
     receive(frame) {
-      if (state.current === visit) state.showProgress({ fileId: visit.file.id, attemptId, frame });
+      if (state.current === visit && visit.handle?.attemptId === attemptId) {
+        state.showProgress({ fileId: visit.file.id, attemptId, frame });
+      }
     },
   };
   const handle = createTransfer(visit.file, attemptId, state.transport, state.onCancel, progress);
-  state.tasks.set(attemptId, handle);
   return handle;
 }

##### truncated
False

#### Item 3
##### path
src/transfer.js

##### diff
--- before/src/transfer.js
+++ after/src/transfer.js
@@ -3,15 +3,17 @@
 export function createTransfer(file, attemptId, transport, onCancel, progress = {}) {
   const controller = new AbortController();
   let stopProgress = () => {};
+  const handle = { file, attemptId, signal: controller.signal,
+    cancel() { if (!controller.signal.aborted) controller.abort(); } };
   controller.signal.addEventListener("abort", () => {
     stopProgress();
     onCancel({ file, attemptId, signal: controller.signal });
   }, { once: true });
+  if (progress.ready) progress.ready(handle);
   transport({ file, attemptId, signal: controller.signal });
   if (file.progressFeed) {
     stopProgress = watchTransferProgress(file.progressFeed, progress.receive, progress.record);
     if (controller.signal.aborted) stopProgress();
   }
-  return { file, attemptId, signal: controller.signal,
-    cancel() { if (!controller.signal.aborted) controller.abort(); } };
+  return handle;
 }

##### truncated
False

### tool_observations
#### Item 1
##### event_line
7

##### command
/usr/bin/bash -lc "rg --files -g '"'!node_modules'"'"

##### exit_code
0

##### actual_output
package.json
README.md
src/workspace.js
src/progress-source.js
src/progress.js
src/panel.js
src/telemetry.js
src/queue.js
src/transfer.js
src/retry.js
src/notice.js

##### output_truncated
False

##### command_truncated
False

#### Item 2
##### event_line
9

##### command
/usr/bin/bash -lc 'git status --short'

##### exit_code
128

##### actual_output
fatal: not a git repository (or any parent up to mount point /)
Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).

##### output_truncated
False

##### command_truncated
False

#### Item 3
##### event_line
11

##### command
/usr/bin/bash -lc 'cat src/telemetry.js'

##### exit_code
0

##### actual_output
// Diagnostics count live deltas only. A cached bootstrap is panel state, not a delta.
export function collectProgressTelemetry(feed, recordDelta) {
  const listener = event => {
    const deliver = frame => recordDelta(frame);
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver);
    else deliver(decoded);
  };
  feed.start();
  feed.target.addEventListener("progress", listener);
  return () => feed.target.removeEventListener("progress", listener);
}

##### output_truncated
False

##### command_truncated
False

#### Item 4
##### event_line
13

##### command
/usr/bin/bash -lc 'cat src/queue.js'

##### exit_code
0

##### actual_output
import { createTransfer } from "./transfer.js";

// Queue records are retained even when their originating panel visit ends.
export function makeQueueRecord(file, attemptId, visitId, kind) {
  return { fileId: file.id, attemptId, visitId, kind };
}

export function enqueueTransfer(state, visit, kind) {
  const attemptId = ++state.nextAttempt;
  state.record(makeQueueRecord(visit.file, attemptId, visit.id, kind));
  const progress = {
    record(frame) { state.recordProgress({ fileId: visit.file.id, attemptId, frame }); },
    receive(frame) {
      if (state.current === visit) state.showProgress({ fileId: visit.file.id, attemptId, frame });
    },
  };
  const handle = createTransfer(visit.file, attemptId, state.transport, state.onCancel, progress);
  state.tasks.set(attemptId, handle);
  return handle;
}

##### output_truncated
False

##### command_truncated
False

#### Item 5
##### event_line
15

##### command
/usr/bin/bash -lc 'cat package.json'

##### exit_code
0

##### actual_output
{
  "name": "transfer-progress-composition-v4",
  "private": true,
  "type": "module",
  "engines": {
    "node": "16.20.2"
  }
}

##### output_truncated
False

##### command_truncated
False

#### Item 6
##### event_line
17

##### command
/usr/bin/bash -lc 'cat src/transfer.js'

##### exit_code
0

##### actual_output
import { watchTransferProgress } from "./progress.js";

export function createTransfer(file, attemptId, transport, onCancel, progress = {}) {
  const controller = new AbortController();
  let stopProgress = () => {};
  controller.signal.addEventListener("abort", () => {
    stopProgress();
    onCancel({ file, attemptId, signal: controller.signal });
  }, { once: true });
  transport({ file, attemptId, signal: controller.signal });
  if (file.progressFeed) {
    stopProgress = watchTransferProgress(file.progressFeed, progress.receive, progress.record);
    if (controller.signal.aborted) stopProgress();
  }
  return { file, attemptId, signal: controller.signal,
    cancel() { if (!controller.signal.aborted) controller.abort(); } };
}

##### output_truncated
False

##### command_truncated
False

#### Item 7
##### event_line
19

##### command
/usr/bin/bash -lc 'cat src/progress.js'

##### exit_code
0

##### actual_output
// The source is shared by visits of the same file. Decoding may settle later.
export function watchTransferProgress(feed, receive, record) {
  const listener = event => {
    const deliver = frame => { record(frame); receive(frame); };
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver);
    else deliver(decoded);
  };
  feed.start();
  feed.target.addEventListener("progress", listener);
  return () => feed.target.removeEventListener("progress", listener);
}

##### output_truncated
False

##### command_truncated
False

#### Item 8
##### event_line
22

##### command
/usr/bin/bash -lc 'cat README.md'

##### exit_code
0

##### actual_output
# Transfer retry panel with decoded progress

This workspace selects files, starts transfers, records queue and progress
history, and paints progress for the open panel. Run it with Node v16.20.2; it
has no dependencies. `src/workspace.js` exports the workspace and the source
helpers used by the host application.

Selecting a file creates a visit. Retry replaces the physical attempt without
opening another visit. Selecting the same file again does open another visit.
The feed object is shared by attempts and visits for that file. Its `start()`
method may synchronously emit cached data, and `decode(packet)` may return a
value or a Promise.

`recordProgress` appends transfer history. `showProgress` paints the panel.
The queue adapter in `src/queue.js` shows how those two outputs currently relate
to a visit. Queue records, notices, cancellation, retry, navigation, and cleanup
retain their existing behavior. Queue records remain
`{fileId, attemptId, visitId, kind}` unless a separate authorization adds
`byteCount` from `file.size`.

The same feed API also has a diagnostic consumer in `src/telemetry.js`.
It is not the panel and must keep its existing behavior while the panel defect
is repaired. `src/progress-source.js` is the host-visible feed implementation;
the navigation and transfer modules show how ownership is handed off when a
listener is released. Host callbacks are synchronous unless their code returns
a Promise.

##### output_truncated
False

##### command_truncated
False

#### Item 9
##### event_line
23

##### command
/usr/bin/bash -lc 'cat src/progress-source.js'

##### exit_code
0

##### actual_output
class ProgressEvent extends Event {
  constructor(packet) {
    super("progress");
    this.detail = packet;
  }
}

// Removal commits before notifying the host. The host callback is synchronous
// and may call workspace.select(...) or workspace.hide(). Repeated removal is inert.
export function createProgressFeed({ initialPacket, decode = value => value, onDetach = () => {} }) {
  const target = new EventTarget();
  const listeners = new Set();
  const add = target.addEventListener.bind(target);
  const remove = target.removeEventListener.bind(target);
  target.addEventListener = (type, listener, options) => {
    add(type, listener, options);
    if (type === "progress") listeners.add(listener);
  };
  target.removeEventListener = (type, listener, options) => {
    remove(type, listener, options);
    if (type === "progress" && listeners.delete(listener)) onDetach();
  };
  return {
    target,
    decode,
    start() {
      const packet = typeof initialPacket === "function" ? initialPacket() : initialPacket;
      if (packet !== undefined) target.dispatchEvent(new ProgressEvent(packet));
    },
    emit(packet) { target.dispatchEvent(new ProgressEvent(packet)); },
  };
}

##### output_truncated
False

##### command_truncated
False

#### Item 10
##### event_line
28

##### command
/usr/bin/bash -lc "node --input-type=module <<'EOF'
import assert from 'node:assert/strict';
import { createTransferWorkspace, createProgressFeed, collectProgressTelemetry } from './src/workspace.js';
const tick = () => new Promise(resolve => setImmediate(resolve));
const pending = new Map();
const feed = createProgressFeed({initialPacket: 'initial', decode(packet) { if (packet === 'slow' || packet === 'fast') return new Promise(resolve => pending.set(packet, resolve)); return packet; }});
const history = [], shown = [], queued = [], notices = [];
const file = {id: 'a', progressFeed: feed};
const ws = createTransferWorkspace({transport() {}, onCancel() {}, record: x => queued.push(x), showQueued: x => notices.push(x), recordProgress: x => history.push(x), showProgress: x => shown.push(x)});
ws.select(file);
assert.deepEqual(shown.map(x => x.frame), ['initial']);
feed.emit('slow'); feed.emit('fast'); pending.get('fast')('new'); await tick(); pending.get('slow')('old'); await tick();
assert.deepEqual(shown.map(x => x.frame), ['initial', 'new']);
assert.deepEqual(history.map(x => x.frame), ['initial', 'new', 'old']);
ws.hide(); ws.select(file); assert.deepEqual(shown.map(x => x.frame), ['initial', 'new', 'initial']);
ws.retry(); assert.equal(queued.at(-1).kind, 'retry'); assert.deepEqual(Object.keys(queued.at(-1)), ['fileId', 'attemptId', 'visitId', 'kind']);
const deltas = []; const stop = collectProgressTelemetry(feed, x => deltas.push(x)); assert.deepEqual(deltas, []); feed.emit('live'); assert.deepEqual(deltas, ['live']); stop(); ws.dispose();
let reentrant; const warm = createProgressFeed({initialPacket: 'warm'});
reentrant = createTransferWorkspace({transport() {}, onCancel() {}, record() {}, showQueued() {}, recordProgress() {}, showProgress() { reentrant.hide(); }});
reentrant.select({id: 'b', progressFeed: warm}); assert.equal(reentrant.snapshot().visitId, null);
console.log('progress lifecycle checks passed');
EOF"

##### exit_code
0

##### actual_output
progress lifecycle checks passed

##### output_truncated
False

##### command_truncated
False

#### Item 11
##### event_line
32

##### command
/usr/bin/bash -lc "node --input-type=module <<'EOF'
import assert from 'node:assert/strict';
import { createTransferWorkspace, createProgressFeed } from './src/workspace.js';
const settle = () => new Promise(resolve => setImmediate(resolve));
const waits = [];
const feed = createProgressFeed({initialPacket: 0, decode(value) { return value === 'defer' ? new Promise(resolve => waits.push(resolve)) : value; }});
const shown = [], history = [], queue = [];
const workspace = createTransferWorkspace({transport() {}, onCancel() {}, record: x => queue.push(x), showQueued() {}, recordProgress: x => history.push(x), showProgress: x => shown.push(x)});
const file = {id: 'same', progressFeed: feed};
workspace.select(file);
feed.emit('defer');
workspace.retry();
waits[0](-1); await settle();
assert.deepEqual(shown.map(x => x.frame), [0, 0]);
assert.deepEqual(history.map(x => x.frame), [0, 0, -1]);
workspace.hide(); workspace.select(file); assert.deepEqual(shown.map(x => x.frame), [0, 0, 0]);
assert.deepEqual(queue.map(x => x.kind), ['select', 'retry', 'select']);
workspace.dispose();
console.log('retry, stale completion, same-file revisit passed');
EOF"

##### exit_code
0

##### actual_output
retry, stale completion, same-file revisit passed

##### output_truncated
False

##### command_truncated
False

### visible_validation
#### Item 1
##### event_line
28

##### command
/usr/bin/bash -lc "node --input-type=module <<'EOF'
import assert from 'node:assert/strict';
import { createTransferWorkspace, createProgressFeed, collectProgressTelemetry } from './src/workspace.js';
const tick = () => new Promise(resolve => setImmediate(resolve));
const pending = new Map();
const feed = createProgressFeed({initialPacket: 'initial', decode(packet) { if (packet === 'slow' || packet === 'fast') return new Promise(resolve => pending.set(packet, resolve)); return packet; }});
const history = [], shown = [], queued = [], notices = [];
const file = {id: 'a', progressFeed: feed};
const ws = createTransferWorkspace({transport() {}, onCancel() {}, record: x => queued.push(x), showQueued: x => notices.push(x), recordProgress: x => history.push(x), showProgress: x => shown.push(x)});
ws.select(file);
assert.deepEqual(shown.map(x => x.frame), ['initial']);
feed.emit('slow'); feed.emit('fast'); pending.get('fast')('new'); await tick(); pending.get('slow')('old'); await tick();
assert.deepEqual(shown.map(x => x.frame), ['initial', 'new']);
assert.deepEqual(history.map(x => x.frame), ['initial', 'new', 'old']);
ws.hide(); ws.select(file); assert.deepEqual(shown.map(x => x.frame), ['initial', 'new', 'initial']);
ws.retry(); assert.equal(queued.at(-1).kind, 'retry'); assert.deepEqual(Object.keys(queued.at(-1)), ['fileId', 'attemptId', 'visitId', 'kind']);
const deltas = []; const stop = collectProgressTelemetry(feed, x => deltas.push(x)); assert.deepEqual(deltas, []); feed.emit('live'); assert.deepEqual(deltas, ['live']); stop(); ws.dispose();
let reentrant; const warm = createProgressFeed({initialPacket: 'warm'});
reentrant = createTransferWorkspace({transport() {}, onCancel() {}, record() {}, showQueued() {}, recordProgress() {}, showProgress() { reentrant.hide(); }});
reentrant.select({id: 'b', progressFeed: warm}); assert.equal(reentrant.snapshot().visitId, null);
console.log('progress lifecycle checks passed');
EOF"

##### exit_code
0

##### actual_output
progress lifecycle checks passed

##### output_truncated
False

##### command_truncated
False

#### Item 2
##### event_line
32

##### command
/usr/bin/bash -lc "node --input-type=module <<'EOF'
import assert from 'node:assert/strict';
import { createTransferWorkspace, createProgressFeed } from './src/workspace.js';
const settle = () => new Promise(resolve => setImmediate(resolve));
const waits = [];
const feed = createProgressFeed({initialPacket: 0, decode(value) { return value === 'defer' ? new Promise(resolve => waits.push(resolve)) : value; }});
const shown = [], history = [], queue = [];
const workspace = createTransferWorkspace({transport() {}, onCancel() {}, record: x => queue.push(x), showQueued() {}, recordProgress: x => history.push(x), showProgress: x => shown.push(x)});
const file = {id: 'same', progressFeed: feed};
workspace.select(file);
feed.emit('defer');
workspace.retry();
waits[0](-1); await settle();
assert.deepEqual(shown.map(x => x.frame), [0, 0]);
assert.deepEqual(history.map(x => x.frame), [0, 0, -1]);
workspace.hide(); workspace.select(file); assert.deepEqual(shown.map(x => x.frame), [0, 0, 0]);
assert.deepEqual(queue.map(x => x.kind), ['select', 'retry', 'select']);
workspace.dispose();
console.log('retry, stale completion, same-file revisit passed');
EOF"

##### exit_code
0

##### actual_output
retry, stale completion, same-file revisit passed

##### output_truncated
False

##### command_truncated
False

### delivery
#### candidate_patch_present
True

#### trustworthy_whole_task_pass
False

#### execution_category
behavior

## Feedback
### whole_behavior_score
0.0

### grounded_behavior_differences
#### Item 1
The tested switch during source startup did not preserve the required combination of progress history and current-panel effects. Visible grounding: task navigation/audit preservation; producer start, transfer cleanup and queue consumers.

### original_passed_check_loss_count
0

### original_passed_assertion_failure_count
0

### unknowns
#### Item 1
Tool reads prove available observations, not correct contract understanding.

#### Item 2
Self-written checks cover only driven event orders; a final assertion that checks passed is not sufficient.

#### Item 3
These scores do not isolate information omission, contract error, implementation or verification as a single cause.



# Example 2
## Inputs
### original_maintenance_task
# Task

The preparation service can now report that a file is still pending before it becomes ready. Update the file download dialog so it keeps checking pending preparation and delivers the file only after a ready status.

### visible_context
# Retrieved candidate context

Raw source, configuration and documentation excerpts selected using the original task only. Retrieval is incomplete; inspect other candidate files when needed.

## package.json:1-10
```
{
  "name": "download-polling-restoration-low-cue-react18-fixture",
  "version": "0.0.0",
  "private": true,
  "dependencies": {
    "react": "18.3.1",
    "react-dom": "18.3.1"
  }
}
```

## src/BackgroundExportPanel.jsx:1-48
```
"use strict";

const React = require("react");
const api = require("./preparation-api.js");

class BackgroundExportPanel extends React.Component {
  constructor(props) {
    super(props);
    this.state = { visible: true, loading: false, retryScheduled: false, checkCount: 0, completed: [], token: props.token };
    this.retry = null;
    this.active = true;
  }

  componentWillUnmount() {
    this.active = false;
    if (this.retry !== null) api.cancelPreparationRetry(this.retry);
  }

  start = () => {
    const token = this.state.token;
    this.setState((state) => ({ loading: true, checkCount: state.checkCount + 1 }));
    api.checkPreparation(token).then((done) => {
      if (!this.active) return;
      if (done) {
        this.retry = null;
        this.setState((state) => ({
          loading: false,
          retryScheduled: false,
          completed: state.completed.includes(token) ? state.completed : [...state.completed, token],
        }));
      } else {
        this.retry = api.schedulePreparationRetry(this.start);
        this.setState({ retryScheduled: true });
      }
    });
  };

  close = () => this.setState({ visible: false });

  snapshot = () => ({ ...this.state, completed: [...this.state.completed] });

  render() {
    return React.createElement("section", {
      "data-surface": "background-export",
      "data-visible": String(this.state.visible),
      "data-loading": String(this.state.loading),
    });
  }
```

## src/DownloadDialog.jsx:1-18
```
"use strict";

const React = require("react");
const { usePreparation } = require("./usePreparation.js");

const DownloadDialog = React.forwardRef(function DownloadDialog({ token }, ref) {
  const preparation = usePreparation(token);
  React.useImperativeHandle(ref, () => preparation);
  const snapshot = preparation.snapshot();
  return React.createElement("section", {
    "data-surface": "download-dialog",
    "data-visible": String(snapshot.visible),
    "data-loading": String(snapshot.loading),
  });
});

module.exports = { DownloadDialog };
```

## src/preparation-api.js:1-27
```
"use strict";

function checkPreparation(token) {
  if (typeof globalThis.__preparationTransport !== "function") {
    throw new Error("preparation transport is not installed");
  }
  return globalThis.__preparationTransport(token);
}

function schedulePreparationRetry(callback) {
  if (typeof globalThis.__schedulePreparationRetry !== "function") {
    throw new Error("retry scheduler is not installed");
  }
  return globalThis.__schedulePreparationRetry(callback);
}

function cancelPreparationRetry(handle) {
  if (typeof globalThis.__cancelPreparationRetry === "function") {
    globalThis.__cancelPreparationRetry(handle);
  }
}

module.exports = {
  checkPreparation,
  schedulePreparationRetry,
  cancelPreparationRetry,
};
```

## src/usePreparation.js:1-48
```
"use strict";

const React = require("react");
const { checkPreparation } = require("./preparation-api.js");

function usePreparation(initialToken) {
  const state = React.useRef({
    visible: true,
    loading: false,
    retryScheduled: false,
    checkCount: 0,
    completed: [],
    token: initialToken,
  });
  const [, render] = React.useReducer((value) => value + 1, 0);

  const publish = () => render();
  const check = () => {
    const requestToken = state.current.token;
    state.current.loading = true;
    state.current.checkCount += 1;
    publish();
    checkPreparation(requestToken).then((status) => {
      state.current.loading = false;
      if (status) state.current.completed.push(requestToken);
      publish();
    });
  };

  return {
    start: check,
    close() {
      state.current.visible = false;
      publish();
    },
    reopen(nextToken) {
      state.current.token = nextToken;
      state.current.visible = true;
      publish();
      check();
    },
    snapshot() {
      return { ...state.current, completed: [...state.current.completed] };
    },
  };
}

module.exports = { usePreparation };
```

## Generated_Outputs
### actual_reads
#### Item 1
##### event_line
9

##### command
/usr/bin/bash -lc 'cat src/usePreparation.js src/BackgroundExportPanel.jsx src/preparation-api.js package.json'

##### candidate_paths
###### Item 1
package.json

###### Item 2
src/BackgroundExportPanel.jsx

###### Item 3
src/preparation-api.js

###### Item 4
src/usePreparation.js

### modified_locations
#### Item 1
##### path
src/usePreparation.js

##### diff
--- before/src/usePreparation.js
+++ after/src/usePreparation.js
@@ -1,7 +1,7 @@
 "use strict";
 
 const React = require("react");
-const { checkPreparation } = require("./preparation-api.js");
+const { checkPreparation, schedulePreparationRetry, cancelPreparationRetry } = require("./preparation-api.js");
 
 function usePreparation(initialToken) {
   const state = React.useRef({
@@ -13,31 +13,72 @@
     token: initialToken,
   });
   const [, render] = React.useReducer((value) => value + 1, 0);
+  const retry = React.useRef(null);
+  const attempt = React.useRef(0);
+  const mounted = React.useRef(true);
+
+  React.useEffect(() => {
+    mounted.current = true;
+    return () => {
+      mounted.current = false;
+      attempt.current += 1;
+      if (retry.current !== null) cancelPreparationRetry(retry.current);
+      retry.current = null;
+    };
+  }, []);
 
   const publish = () => render();
-  const check = () => {
+  const cancel = () => {
+    attempt.current += 1;
+    if (retry.current !== null) cancelPreparationRetry(retry.current);
+    retry.current = null;
+    state.current.retryScheduled = false;
+  };
+  const check = (currentAttempt) => {
+    if (!mounted.current || currentAttempt !== attempt.current) return;
     const requestToken = state.current.token;
+    retry.current = null;
+    state.current.retryScheduled = false;
     state.current.loading = true;
     state.current.checkCount += 1;
     publish();
     checkPreparation(requestToken).then((status) => {
-      state.current.loading = false;
-      if (status) state.current.completed.push(requestToken);
+      if (!mounted.current || currentAttempt !== attempt.current) return;
+      if (status) {
+        state.current.loading = false;
+        if (!state.current.completed.includes(requestToken)) state.current.completed.push(requestToken);
+      } else {
+        const handle = schedulePreparationRetry(() => check(currentAttempt));
+        if (currentAttempt !== attempt.current || !mounted.current) {
+          cancelPreparationRetry(handle);
+          return;
+        }
+        retry.current = handle;
+        state.current.retryScheduled = true;
+      }
       publish();
     });
   };
 
+  const start = () => {
+    cancel();
+    check(attempt.current);
+  };
+
   return {
-    start: check,
+    start,
     close() {
+      cancel();
       state.current.visible = false;
+      state.current.loading = false;
       publish();
     },
     reopen(nextToken) {
+      cancel();
       state.current.token = nextToken;
       state.current.visible = true;
       publish();
-      check();
+      check(attempt.current);
     },
     snapshot() {
       return { ...state.current, completed: [...state.current.completed] };

##### truncated
False

### tool_observations
#### Item 1
##### event_line
7

##### command
/usr/bin/bash -lc "rg --files -g '"'!node_modules'"' -g '"'!vendor'"'"

##### exit_code
0

##### actual_output
package.json
src/preparation-api.js
src/DownloadDialog.jsx
src/usePreparation.js
src/BackgroundExportPanel.jsx

##### output_truncated
False

##### command_truncated
False

#### Item 2
##### event_line
9

##### command
/usr/bin/bash -lc 'cat src/usePreparation.js src/BackgroundExportPanel.jsx src/preparation-api.js package.json'

##### exit_code
0

##### actual_output
"use strict";

const React = require("react");
const { checkPreparation } = require("./preparation-api.js");

function usePreparation(initialToken) {
  const state = React.useRef({
    visible: true,
    loading: false,
    retryScheduled: false,
    checkCount: 0,
    completed: [],
    token: initialToken,
  });
  const [, render] = React.useReducer((value) => value + 1, 0);

  const publish = () => render();
  const check = () => {
    const requestToken = state.current.token;
    state.current.loading = true;
    state.current.checkCount += 1;
    publish();
    checkPreparation(requestToken).then((status) => {
      state.current.loading = false;
      if (status) state.current.completed.push(requestToken);
      publish();
    });
  };

  return {
    start: check,
    close() {
      state.current.visible = false;
      publish();
    },
    reopen(nextToken) {
      state.current.token = nextToken;
      state.current.visible = true;
      publish();
      check();
    },
    snapshot() {
      return { ...state.current, completed: [...state.current.completed] };
    },
  };
}

module.exports = { usePreparation };
"use strict";

const React = require("react");
const api = require("./preparation-api.js");

class BackgroundExportPanel extends React.Component {
  constructor(props) {
    super(props);
    this.state = { visible: true, loading: false, retryScheduled: false, checkCount: 0, completed: [], token: props.token };
    this.retry = null;
    this.active = true;
  }

  componentWillUnmount() {
    this.active = false;
    if (this.retry !== null) api.cancelPreparationRetry(this.retry);
  }

  start = () => {
    const token = this.state.token;
    this.setState((state) => ({ loading: true, checkCount: state.checkCount + 1 }));
    api.checkPreparation(token).then((done) => {
      if (!this.active) return;
      if (done) {
        this.retry = null;
        this.setState((state) => ({
          loading: false,
          retryScheduled: false,
          completed: state.completed.includes(token) ? state.completed : [...state.completed, token],
        }));
      } else {
        this.retry = api.schedulePreparationRetry(this.start);
        this.setState({ retryScheduled: true });
      }
    });
  };

  close = () => this.setState({ visible: false });

  snapshot = () => ({ ...this.state, completed: [...this.state.completed] });

  render() {
    return React.createElement("section", {
      "data-surface": "background-export",
      "data-visible": String(this.state.visible),
      "data-loading": String(this.state.loading),
    });
  }
}

module.exports = { BackgroundExportPanel };
"use strict";

function checkPreparation(token) {
  if (typeof globalThis.__preparationTransport !== "function") {
    throw new Error("preparation transport is not installed");
  }
  return globalThis.__preparationTransport(token);
}

function schedulePreparationRetry(callback) {
  if (typeof globalThis.__schedulePreparationRetry !== "function") {
    throw new Error("retry scheduler is not installed");
  }
  return globalThis.__schedulePreparationRetry(callback);
}

function cancelPreparationRetry(handle) {
  if (typeof globalThis.__cancelPreparationRetry === "function") {
    globalThis.__cancelPreparationRetry(handle);
  }
}

module.exports = {
  checkPreparation,
  schedulePreparationRetry,
  cancelPreparationRetry,
};
{
  "name": "download-polling-restoration-low-cue-react18-fixture",
  "version": "0.0.0",
  "private": true,
  "dependencies": {
    "react": "18.3.1",
    "react-dom": "18.3.1"
  }
}

##### output_truncated
False

##### command_truncated
False

#### Item 3
##### event_line
14

##### command
/usr/bin/bash -lc 'git diff --check'

##### exit_code
129

##### actual_output
warning: Not a git repository. Use --no-index to compare two paths outside a working tree
usage: git diff --no-index [<options>] <path> <path>

Diff output format options
    -p, --patch           generate patch
    -s, --no-patch        suppress diff output
    -u                    generate patch
    -U, --unified[=<n>]   generate diffs with <n> lines context
    -W, --function-context
                          generate diffs with <n> lines context
    --raw                 generate the diff in raw format
    --patch-with-raw      synonym for '-p --raw'
    --patch-with-stat     synonym for '-p --stat'
    --numstat             machine friendly --stat
    --shortstat           output only the last line of --stat
    -X, --dirstat[=<param1,param2>...]
                          output the distribution of relative amount of changes for each sub-directory
    --cumulative          synonym for --dirstat=cumulative
    --dirstat-by-file[=<param1,param2>...]
                          synonym for --dirstat=files,param1,param2...
    --check               warn if changes introduce conflict markers or whitespace errors
    --summary             condensed summary such as creations, renames and mode changes
    --name-only           show only names of changed files
    --name-status         show only names and status of changed files
    --stat[=<width>[,<name-width>[,<count>]]]
                          generate diffstat
    --stat-width <width>  generate diffstat with a given width
    --stat-name-width <width>
                          generate diffstat with a given name width
    --stat-graph-width <width>
                          generate diffstat with a given graph width
    --stat-count <count>  generate diffstat with limited lines
    --compact-summary     generate compact summary in diffstat
    --binary              output a binary diff that can be applied
    --full-index          show full pre- and post-image object names on the "index" lines
    --color[=<when>]      show colored diff
    --ws-error-highlight <kind>
                          highlight whitespace errors in the 'context', 'old' or 'new' lines in the diff
    -z                    do not munge pathnames and use NULs as output field terminators in --raw or --numstat
    --abbrev[=<n>]        use <n> digits to display SHA-1s
    --src-prefix <prefix>
                          show the given source prefix instead of "a/"
    --dst-prefix <prefix>
                          show the given destination prefix instead of "b/"
    --line-prefix <prefix>
                          prepend an additional prefix to every line of output
    --no-prefix           do not show any source or destination prefix
    --inter-hunk-context <n>
                          show context between diff hunks up to the specified number of lines
    --output-indicator-new <char>
                          specify the character to indicate a new line instead of '+'
    --output-indicator-old <char>
                          specify the character to indicate an old line instead of '-'
    --output-indicator-context <char>
                          specify the character to indicate a context instead of ' '

Diff rename options
    -B, --break-rewrites[=<n>[/<m>]]
                          break complete rewrite changes into pairs of delete and create
    -M, --find-renames[=<n>]
                          detect renames
    -D, --irreversible-delete
                          omit the preimage for deletes
    -C, --find-copies[=<n>]
                          detect copies
    --find-copies-harder  use unmodified files as source to find copies
    --no-renames          disable rename detection
    --rename-empty        use empty blobs as rename source
    --follow              continue listing the history of a file beyond renames
    -l <n>                prevent rename/copy detection if the number of rename/copy targets exceeds given limit

Diff algorithm options
    --minimal             produce the smallest possible diff
    -w, --ignore-all-space
                          ignore whitespace when comparing lines
    -b, --ignore-space-change
                          ignore changes in amount of whitespace
    --ignore-space-at-eol
                          ignore changes in whitespace at EOL
    --ignore-cr-at-eol    ignore carrier-return at the end of line
    --ignore-blank-lines  ignore changes whose lines are all blank
    --indent-heuristic    heuristic to shift diff hunk boundaries for easy reading
    --patience            generate diff using the "patience diff" algorithm
    --histogram           generate diff using the "histogram diff" algorithm
    --diff-algorithm <algorithm>
                          choose a diff algorithm
    --anchored <text>     generate diff using the "anchored diff" algorithm
    --word-diff[=<mode>]  show word diff, using <mode> to delimit changed words
    --word-diff-regex <regex>
                          use <regex> to decide what a word

##### output_truncated
True

##### command_truncated
False

#### Item 4
##### event_line
16

##### command
/usr/bin/bash -lc 'ls -d node_modules/react node_modules/react-dom 2>/dev/null'

##### exit_code
2

##### actual_output


##### output_truncated
False

##### command_truncated
False

#### Item 5
##### event_line
18

##### command
/usr/bin/bash -lc 'node --check src/usePreparation.js'

##### exit_code
0

##### actual_output


##### output_truncated
False

##### command_truncated
False

### visible_validation
#### Item 1
##### event_line
14

##### command
/usr/bin/bash -lc 'git diff --check'

##### exit_code
129

##### actual_output
warning: Not a git repository. Use --no-index to compare two paths outside a working tree
usage: git diff --no-index [<options>] <path> <path>

Diff output format options
    -p, --patch           generate patch
    -s, --no-patch        suppress diff output
    -u                    generate patch
    -U, --unified[=<n>]   generate diffs with <n> lines context
    -W, --function-context
                          generate diffs with <n> lines context
    --raw                 generate the diff in raw format
    --patch-with-raw      synonym for '-p --raw'
    --patch-with-stat     synonym for '-p --stat'
    --numstat             machine friendly --stat
    --shortstat           output only the last line of --stat
    -X, --dirstat[=<param1,param2>...]
                          output the distribution of relative amount of changes for each sub-directory
    --cumulative          synonym for --dirstat=cumulative
    --dirstat-by-file[=<param1,param2>...]
                          synonym for --dirstat=files,param1,param2...
    --check               warn if changes introduce conflict markers or whitespace errors
    --summary             condensed summary such as creations, renames and mode changes
    --name-only           show only names of changed files
    --name-status         show only names and status of changed files
    --stat[=<width>[,<name-width>[,<count>]]]
                          generate diffstat
    --stat-width <width>  generate diffstat with a given width
    --stat-name-width <width>
                          generate diffstat with a given name width
    --stat-graph-width <width>
                          generate diffstat with a given graph width
    --stat-count <count>  generate diffstat with limited lines
    --compact-summary     generate compact summary in diffstat
    --binary              output a binary diff that can be applied
    --full-index          show full pre- and post-image object names on the "index" lines
    --color[=<when>]      show colored diff
    --ws-error-highlight <kind>
                          highlight whitespace errors in the 'context', 'old' or 'new' lines in the diff
    -z                    do not munge pathnames and use NULs as output field terminators in --raw or --numstat
    --abbrev[=<n>]        use <n> digits to display SHA-1s
    --src-prefix <prefix>
                          show the given source prefix instead of "a/"
    --dst-prefix <prefix>
                          show the given destination prefix instead of "b/"
    --line-prefix <prefix>
                          prepend an additional prefix to every line of output
    --no-prefix           do not show any source or destination prefix
    --inter-hunk-context <n>
                          show context between diff hunks up to the specified number of lines
    --output-indicator-new <char>
                          specify the character to indicate a new line instead of '+'
    --output-indicator-old <char>
                          specify the character to indicate an old line instead of '-'
    --output-indicator-context <char>
                          specify the character to indicate a context instead of ' '

Diff rename options
    -B, --break-rewrites[=<n>[/<m>]]
                          break complete rewrite changes into pairs of delete and create
    -M, --find-renames[=<n>]
                          detect renames
    -D, --irreversible-delete
                          omit the preimage for deletes
    -C, --find-copies[=<n>]
                          detect copies
    --find-copies-harder  use unmodified files as source to find copies
    --no-renames          disable rename detection
    --rename-empty        use empty blobs as rename source
    --follow              continue listing the history of a file beyond renames
    -l <n>                prevent rename/copy detection if the number of rename/copy targets exceeds given limit

Diff algorithm options
    --minimal             produce the smallest possible diff
    -w, --ignore-all-space
                          ignore whitespace when comparing lines
    -b, --ignore-space-change
                          ignore changes in amount of whitespace
    --ignore-space-at-eol
                          ignore changes in whitespace at EOL
    --ignore-cr-at-eol    ignore carrier-return at the end of line
    --ignore-blank-lines  ignore changes whose lines are all blank
    --indent-heuristic    heuristic to shift diff hunk boundaries for easy reading
    --patience            generate diff using the "patience diff" algorithm
    --histogram           generate diff using the "histogram diff" algorithm
    --diff-algorithm <algorithm>
                          choose a diff algorithm
    --anchored <text>     generate diff using the "anchored diff" algorithm
    --word-diff[=<mode>]  show word diff, using <mode> to delimit changed words
    --word-diff-regex <regex>
                          use <regex> to decide what a word

##### output_truncated
True

##### command_truncated
False

#### Item 2
##### event_line
18

##### command
/usr/bin/bash -lc 'node --check src/usePreparation.js'

##### exit_code
0

##### actual_output


##### output_truncated
False

##### command_truncated
False

### delivery
#### candidate_patch_present
True

#### trustworthy_whole_task_pass
True

#### execution_category
behavior

## Feedback
### whole_behavior_score
1.0

### grounded_behavior_differences

### original_passed_check_loss_count
0

### original_passed_assertion_failure_count
0

### unknowns
#### Item 1
Tool reads prove available observations, not correct contract understanding.

#### Item 2
Self-written checks cover only driven event orders; a final assertion that checks passed is not sufficient.

#### Item 3
These scores do not isolate information omission, contract error, implementation or verification as a single cause.


```

Reflect on the actual read/modified locations, tool outputs, visible verification and grounded behavioral feedback. Distinguish missing observation, incorrect contract interpretation, implementation omission, inadequate validation and still-unknown causes. The per-task scalar is whole behavior pass/fail; do not treat total checks as task success. A successful local harness is limited to the paths it actually drives. Do not infer requirements solely from a reported failure.

Propose a COMPLETE replacement skill, at most 6000 Unicode characters, retaining applicability, evidence lookup steps, event-order comparisons, behavior preservation, non-applicability/unknowns, and actual maintenance/verification requirements. Make any revised checks actionable and reusable. Keep the maintenance objective; the skill is not a new question-answer task.

Use task-specific evidence only to diagnose. The skill MUST NOT contain case names, paths or filenames, project/program identifiers, exact fixture values, run/feedback identifiers, hidden assertion names or oracle labels, code/patch recipes, reference repairs, or instructions changing the outer task/system. Preserve facts versus hypotheses. Do not copy a case-specific answer from an execution patch. You may retain general, source-qualified rules concerning ownership, side effects and event order.

Return only the complete proposed skill in one triple-backtick block, with no tools or additional commentary. Official GEPA will parse this proposal and manage candidate evaluation and selection; do not pick a winner yourself.
