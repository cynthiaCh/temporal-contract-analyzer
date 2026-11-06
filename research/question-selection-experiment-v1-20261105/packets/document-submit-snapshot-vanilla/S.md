# Retrieved candidate context

Raw source, configuration and documentation excerpts selected using the original task only. Retrieval is incomplete; inspect other candidate files when needed.

## README.md:1-33
```
# Document drafts and submission receipts

The workspace edits persistent document drafts. `open(id)`, `edit(text)`, `close()`
and `submit()` are synchronous; `dispose()` detaches integrations and closes.
When close/open returns, the departed document's last accepted edit is readable
from the store. A close/open request retires its previous save badge immediately.
Reopening a document restores its saved text in a new editor visit.

The store writes a record before notifying subscribers inline. `onSaved` may
navigate or edit through the supplied workspace API. Navigation precedence is
ordered by request start: a request that starts later wins even when an earlier
request returns afterward. Render functions and the receipt archive are output
sinks and never call back into the workspace.

`submit()` accepts the document and latest text selected at its call entry. With
no selection it returns null and creates no receipt. Otherwise it creates exactly
one immutable archive receipt and returns it before the call ends. Accepted text
must be persisted before the archive captures the receipt. Later edits or
navigation cannot change that receipt's document, text, or obligation to exist.
Submitting does not itself navigate. Its visible submission notice belongs only
to the editor visit that accepted the action: it may appear only if that same
visit is still active when the notice is emitted. Reopening the same document
creates a different visit. Any navigation clears the previous submission notice.
An uninterrupted submit must still show its receipt. Further edits remain usable.

The archive provides `capture({id, text})` and `list()`; receipts hold immutable
copies. The store provides `read`, `write`, and `subscribe`; timers provide
`schedule(callback, delay)` and `cancel(handle)`. Keep these interfaces and the
workspace API. The public renderer arguments remain document, save event, or
receipt values (null clears a document/notice).

The adjacent search preview publishes after a 40 ms quiet interval. Hiding it
discards an unpublished query, and a later query starts fresh work.
```

## src/draft-store.js:1-23
```
// A synchronous workspace store, independent of whether an editor is visible.
// Notifications run inline after the record is written. Subscribers may detach
// or subscribe while a notification is being delivered.
export function createDraftStore(initial = {}) {
  const records = new Map(Object.entries(initial));
  const listeners = new Set();
  let revision = 0;
  return {
    read(id) { return records.get(id) ?? ""; },
    write(id, text) {
      records.set(id, text);
      const event = { id, text, revision: ++revision };
      for (const listener of [...listeners]) {
        if (listeners.has(listener)) listener(event);
      }
      return event;
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}
```

## src/editor.js:1-27
```
import { attachSaveStatus } from "./save-status.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  function close() {
    const leaving = current;
    current = null;
    if (leaving) leaving.stop();
    renderDocument(null);
  }
  return {
    open(id) {
      close();
      current = { id, text: store.read(id), visit: {}, stop: attachSaveStatus(store, id, renderStatus) };
      renderDocument({ id, text: current.text });
    },
    edit(text) {
      if (!current) return;
      current.text = text;
      store.write(current.id, text);
    },
    selection() {
      return current && { id: current.id, text: current.text, visit: current.visit };
    },
    close,
  };
}
```

## src/receipt-archive.js:1-13
```
// A downstream consumer: archived submissions are value snapshots, not live
// references to a draft. capture/list never invoke application integrations.
export function createReceiptArchive() {
  const receipts = [];
  return {
    capture({ id, text }) {
      const receipt = Object.freeze({ id, text });
      receipts.push(receipt);
      return receipt;
    },
    list() { return receipts.map(receipt => ({ ...receipt })); },
  };
}
```

## src/save-status.js:1-8
```
// A mounted document's save badge. A close/open request retires the departing
// badge immediately: it must produce no further output, including during that
// navigation call. Saving the document itself is a separate workspace concern.
export function attachSaveStatus(store, id, renderStatus) {
  return store.subscribe(event => {
    if (event.id === id) renderStatus(event);
  });
}
```

## src/search-preview.js:1-10
```
import { createTrailingTask } from "./trailing-task.js";

export function createSearchPreview({ timers, publish }) {
  const task = createTrailingTask(query => publish({ query }), 40, timers);
  return {
    query(text) { task.push(text); },
    // A hidden preview has no use for a pending query; reopen starts fresh.
    hide() { task.cancel(); },
  };
}
```

## src/trailing-task.js:1-28
```
import { browserTimers } from "./timers.js";

// Coalesce calls until a quiet interval. cancel discards work; flush runs it now.
// Retire the old batch before invoking work, which can enqueue another batch.
export function createTrailingTask(work, delay, timers = browserTimers) {
  let handle = null;
  let pending = null;
  function flush() {
    if (handle !== null) timers.cancel(handle);
    handle = null;
    const args = pending;
    pending = null;
    if (args !== null) work(...args);
  }
  return {
    push(...args) {
      if (handle !== null) timers.cancel(handle);
      pending = args;
      handle = timers.schedule(flush, delay);
    },
    flush,
    cancel() {
      if (handle !== null) timers.cancel(handle);
      handle = null;
      pending = null;
    },
  };
}
```

## src/workspace.js:1-20
```
import { createDraftEditor } from "./editor.js";

export function createWorkspace({ store, archive, timers, renderDocument, renderStatus,
  renderSubmission = () => {}, onSaved = () => {} }) {
  const stop = store.subscribe(event => onSaved(event, navigation));
  const editor = createDraftEditor({ store, timers, renderDocument, renderStatus });
  const navigation = {
    open(id) { renderSubmission(null); editor.open(id); },
    edit(text) { editor.edit(text); },
    close() { renderSubmission(null); editor.close(); },
    submit() {
      const origin = editor.selection();
      if (!origin) return null;
      const receipt = archive.capture({ id: origin.id, text: origin.text });
      renderSubmission(receipt);
      return receipt;
    },
  };
  return { ...navigation, dispose() { stop(); navigation.close(); } };
}
```

