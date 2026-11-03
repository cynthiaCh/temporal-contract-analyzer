# Presence panel contract — asynchronous decoding

A channel frame may decode immediately or return a Promise. The active panel must
receive its initial snapshot and later decoded updates. Retiring a panel visit by
closing it or selecting another room ends that visit's publication rights. A frame
whose decoding began in a retired visit must not update any panel, even if decoding
finishes later. Opening the same channel object again creates a new visit; that
visit must receive its own messages normally, without accepting the old visit's
pending results.

Listener registration and synchronous bootstrap-triggered navigation are already
handled, including old-channel updates emitted by the host before the outer
selection returns. Preserve them. The subscription helper accepts an optional
fourth `isCurrent` predicate; omitted predicates preserve its three-argument API. Decoding services need not support cancellation; stopping
a visit's display must not require changing those services. Final close detaches
its listeners. The metrics consumer intentionally ignores the synchronous initial
snapshot and counts later updates only; its behavior and public APIs are unchanged.

No new dependency is needed; the candidate is a Node ES module.
