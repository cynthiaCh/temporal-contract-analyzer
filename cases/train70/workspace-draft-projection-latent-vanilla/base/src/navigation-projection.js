// The outline and breadcrumb trail serve document navigation. A committed visit
// is distinct even when its document id matches the previous one. The controller
// decides whether a requested visit was retained before committing it here.
export function createNavigationProjection({ renderProjection }) {
  let selected = null;
  const trail = [];
  function publish() {
    renderProjection({ selected: selected && { ...selected }, trail: trail.map(item => ({ ...item })) });
  }
  return {
    commit(visit) { selected = { ...visit }; trail.push({ ...visit }); publish(); },
    clear() { selected = null; publish(); },
  };
}
