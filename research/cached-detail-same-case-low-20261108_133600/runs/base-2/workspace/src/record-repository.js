// Repository snapshots are acceptable for reading, but never attest freshness.
// watchFresh never emits a cached snapshot. The transport emits after subscribe
// returns. watch(..., "prefer-cache", ...) may invoke receive inline, before the
// function returns its release handle, then keeps the live network subscription.
// Every returned handle owns exactly that watch, even if receive navigated away.
export function createRecordRepository({ transport, seed = {} }) {
  const cache = new Map(Object.entries(seed));
  function watch(id, policy, receive) {
    let live = true;
    if (policy === "prefer-cache" && cache.has(id)) {
      receive({ id, value: cache.get(id), source: "cache" });
    }
    const stop = transport.subscribe(id, value => {
      cache.set(id, value);
      if (live) receive({ id, value, source: "network" });
    });
    return () => {
      if (!live) return;
      live = false;
      stop();
    };
  }
  return { watch, watchFresh: (id, receive) => watch(id, "fresh", receive) };
}
