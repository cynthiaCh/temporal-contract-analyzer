export function createDocumentStore(initial = {}) {
  const records = new Map(Object.entries(initial));
  return {
    read(id) { return records.get(id) ?? ""; },
    write(id, text) { records.set(id, text); return { id, text }; },
  };
}
