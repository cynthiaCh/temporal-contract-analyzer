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
export function createReceiptArchive() {
  const receipts = [],listeners=new Map();let serial=0;
  return {
    capture(value) { const receipt = Object.freeze({id: value.id, text: value.text}); receipts.push(receipt);for(const [token,fn]of [...listeners])if(listeners.has(token))fn(receipt);return receipt; },
    list: () => receipts.map(value => ({...value})),
    subscribe(fn){const token=++serial;listeners.set(token,fn);return ()=>listeners.delete(token);},
  };
}
export function trailing(timers, wait, consume) {
  let ticket = null, value = null;
  const retire = () => { if (ticket !== null) timers.cancel(ticket); ticket = null; value = null; };
  const flush = () => { const saved = value; retire(); if (saved !== null) consume(saved); };
  return {
    push(text) { if (ticket !== null) timers.cancel(ticket); value = text; ticket = timers.schedule(flush, wait); },
    flush, cancel: flush,
  };
}
export function createSearchPreview({timers, publish}) {
  const task = trailing(timers, 40, query => publish({query}));
  return {query: text => task.push(text), hide: () => task.cancel()};
}

// An outlet captures the visit active at acquisition; it has no knowledge of an earlier action.
export function bindConfirmation(current,emit){const owner=current();return {isActive(){return owner!==null&&owner===current();},show(receipt){if(this.isActive())emit(receipt);}};}
