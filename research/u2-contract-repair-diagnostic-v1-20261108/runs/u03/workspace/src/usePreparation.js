"use strict";

const React = require("react");
const {
  checkPreparation,
  schedulePreparationRetry,
  cancelPreparationRetry,
} = require("./preparation-api.js");

// The transport used to return a boolean, but newer transports can return an
// explicit status.  In particular, the string "pending" must not be treated
// as a successful (truthy) result.
function isReady(status) {
  return status === true || status === "ready" ||
    Boolean(status && (status.ready === true || status.status === "ready"));
}

function usePreparation(initialToken) {
  const state = React.useRef({
    visible: true,
    loading: false,
    retryScheduled: false,
    checkCount: 0,
    completed: [],
    token: initialToken,
    generation: 0,
    retry: null,
    mounted: true,
  });
  const [, render] = React.useReducer((value) => value + 1, 0);

  const publish = () => render();

  const cancelRetry = () => {
    const current = state.current;
    if (current.retry !== null) {
      cancelPreparationRetry(current.retry);
      current.retry = null;
    }
    current.retryScheduled = false;
  };

  // A generation belongs to one visible dialog session.  Both scheduled
  // callbacks and request completions check it before changing state.
  const check = (generation) => {
    const current = state.current;
    if (!current.mounted || !current.visible || current.generation !== generation) return;

    const requestToken = current.token;
    current.retry = null;
    current.retryScheduled = false;
    current.loading = true;
    current.checkCount += 1;
    publish();

    Promise.resolve()
      .then(() => checkPreparation(requestToken))
      .then((status) => {
        const latest = state.current;
        if (!latest.mounted || !latest.visible || latest.generation !== generation) return;

        if (isReady(status)) {
          latest.loading = false;
          latest.retryScheduled = false;
          latest.retry = null;
          if (!latest.completed.includes(requestToken)) latest.completed.push(requestToken);
          publish();
          return;
        }

        // Pending remains loading while waiting for the next poll.
        latest.loading = true;
        latest.retryScheduled = true;
        const retry = schedulePreparationRetry(() => {
          const active = state.current;
          if (!active.mounted || !active.visible || active.generation !== generation || active.retry !== retry) return;
          active.retry = null;
          active.retryScheduled = false;
          check(generation);
        });
        latest.retry = retry;
        publish();
      })
      .catch(() => {
        // A failed request follows the same retry contract as a pending one.
        const latest = state.current;
        if (!latest.mounted || !latest.visible || latest.generation !== generation) return;
        latest.loading = true;
        latest.retryScheduled = true;
        const retry = schedulePreparationRetry(() => {
          const active = state.current;
          if (!active.mounted || !active.visible || active.generation !== generation || active.retry !== retry) return;
          active.retry = null;
          active.retryScheduled = false;
          check(generation);
        });
        latest.retry = retry;
        publish();
      });
  };

  React.useEffect(() => () => {
    const current = state.current;
    current.mounted = false;
    current.generation += 1;
    cancelRetry();
  }, []);

  return {
    start() {
      const current = state.current;
      current.generation += 1;
      cancelRetry();
      check(current.generation);
    },
    close() {
      const current = state.current;
      current.generation += 1;
      cancelRetry();
      current.visible = false;
      current.loading = false;
      publish();
    },
    reopen(nextToken) {
      const current = state.current;
      current.generation += 1;
      cancelRetry();
      current.token = nextToken;
      current.visible = true;
      publish();
      check(current.generation);
    },
    snapshot() {
      return { ...state.current, completed: [...state.current.completed] };
    },
  };
}

module.exports = { usePreparation };
