export function createDraftStore(initial = {}) {
  const records = new Map(Object.entries(initial)), subscriptions = new Map();
  let serial = 0, revision = 0;
  return {
    read: key => records.get(key) ?? '',
    write(id, text) {
      records.set(id, text);
      const event = {id, text, revision: ++revision};
      for (const [key, callback] of [...subscriptions]) if (subscriptions.has(key)) callback(event);
      return event;
    },
    subscribe(callback) { const key = ++serial; subscriptions.set(key, callback); return () => subscriptions.delete(key); },
  };
}
export function trailing(timers, wait, consume) {
  let ticket = null, value = null;
  const retire = () => { if (ticket !== null) timers.cancel(ticket); ticket = null; value = null; };
  const flush = () => { const saved = value; retire(); if (saved !== null) consume(saved); };
  return {
    push(text) { if (ticket !== null) timers.cancel(ticket); value = text; ticket = timers.schedule(flush, wait); },
    flush, cancel: retire,
  };
}
export function createSearchPreview({timers, publish}) {
  const task = trailing(timers, 120, query => publish({query}));
  return {query: text => task.push(text), hide: () => task.cancel()};
}
