Work only on the candidate-visible files in this workspace. Do not inspect sibling experiment jobs, original repositories or report stores.

Document switching currently bypasses the departure handoff already used by
explicit close. Make `open(id)` perform that same handoff before showing the
target document. Preserve navigation semantics, close/dispose behavior, stored
document text, and all public interfaces.

<candidate-assistance>
# Retrieved candidate context

Raw source, configuration and documentation excerpts selected using the original task only. Retrieval is incomplete; inspect other candidate files when needed.

## README.md:1-12
```
# Document workspace departure handoff

`workspace.js` manages one visible document. Edits write synchronously to the
document store. Explicit close already performs a departure handoff so the host
can commit departure metadata or redirect to a conflict document.

A handoff integration may synchronously call the supplied navigation API. A
navigation call that starts later takes precedence, even if it returns before an
older call. `dispose()` is a silent teardown and does not run business handoff.

The workspace exposes synchronous `open`, `edit`, `close`, and `dispose` methods.
Keep these public interfaces and the document store's `read` and `write` methods.
```

## package.json:1-6
```
{
  "name": "handoff-redirect-reentrancy-fixture",
  "version": "1.0.0",
  "private": true,
  "type": "module"
}
```

## src/document-store.js:1-7
```
export function createDocumentStore(initial = {}) {
  const records = new Map(Object.entries(initial));
  return {
    read(id) { return records.get(id) ?? ""; },
    write(id, text) { records.set(id, text); return { id, text }; },
  };
}
```

## src/workspace.js:1-25
```
export function createWorkspace({ store, renderDocument, onHandoff = () => {} }) {
  let current = null;
  function retire(withHandoff) {
    const leaving = current;
    current = null;
    renderDocument(null);
    if (leaving && withHandoff) {
      onHandoff({ id: leaving.id, text: store.read(leaving.id) }, navigation);
    }
  }
  const navigation = {
    open(id) {
      // Switching currently bypasses the business handoff used by close.
      retire(false);
      current = { id };
      renderDocument({ id, text: store.read(id) });
    },
    edit(text) {
      if (current) store.write(current.id, text);
    },
    close() { retire(true); },
    dispose() { retire(false); },
  };
  return navigation;
}
```


</candidate-assistance>
