// Recent preview currently exposes network observations only. This consumer's
// cache presentation is a separate product migration, not part of detail speedup.
export function createRecentPreview({ repository, publish }) {
  let release = () => {};
  return {
    inspect(id) { release(); release = repository.watchFresh(id, publish); },
    hide() { release(); release = () => {}; },
  };
}
