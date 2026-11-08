// A cached record cannot support a compliance decision: even a warm repository
// must wait for a network observation. Closing review releases its subscription.
export function createComplianceReview({ repository, publish }) {
  let release = () => {};
  return {
    inspect(id) { release(); release = repository.watchFresh(id, publish); },
    close() { release(); release = () => {}; },
  };
}
