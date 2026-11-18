Validated temporal obligations:
- The panel must observe the first snapshot whether start emits synchronously
  or in a later microtask, followed by each normal delta once.
- A select/hide retires the previous visit. Reusing the identical feed object
  does not revive old decoded or painted continuations.
- Decoding already accepted by the listener continues to record history once,
  even after its view is retired; new frames from a detached listener do not.
- Rows may commit only for their owning current visit. A count must additionally
  wait for its own paint completion and still belong to the current visit then.
  paintRows can synchronously navigate or hide, as well as return a Promise.
- Subscribe/start can synchronously invoke rendering. A nested select/hide wins,
  and an outer subscribe returning afterward must not overwrite newer cleanup
  or leave a retired listener attached.
- Ordinary live rows and counts, including fresh work after reopening, remain
  required. Metrics excludes the cached snapshot unless separately authorized.
