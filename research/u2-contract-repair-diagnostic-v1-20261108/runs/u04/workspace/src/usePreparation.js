"use strict";

const React = require("react");
const {
  checkPreparation,
  schedulePreparationRetry,
  cancelPreparationRetry,
} = require("./preparation-api.js");

function isReady(status) {
  if (status === true || status === "ready") return true;
  return Boolean(status && (status.ready === true || status.status === "ready"));
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
  });
  const [, render] = React.useReducer((value) => value + 1, 0);

  const publish = () => render();
  const clearRetry = () => {
    const current = state.current;
    if (current.retry !== null) cancelPreparationRetry(current.retry);
    current.retry = null;
    current.retryScheduled = false;
  };
  const invalidate = () => {
    state.current.generation += 1;
    clearRetry();
  };
  const check = (generation) => {
    const current = state.current;
    if (!current.visible || generation !== current.generation) return;

    const requestToken = current.token;
    current.loading = true;
    current.retryScheduled = false;
    current.retry = null;
    current.checkCount += 1;
    publish();

    let request;
    try {
      request = checkPreparation(requestToken);
    } catch (error) {
      if (generation === state.current.generation && state.current.visible) {
        state.current.loading = false;
        publish();
      }
      return;
    }

    Promise.resolve(request).then(
      (status) => {
        const latest = state.current;
        if (generation !== latest.generation || !latest.visible) return;

        if (isReady(status)) {
          latest.loading = false;
          latest.retryScheduled = false;
          latest.retry = null;
          if (!latest.completed.includes(requestToken)) latest.completed.push(requestToken);
          publish();
          return;
        }

        // Pending work remains loading while the next check is queued.
        try {
          const retry = schedulePreparationRetry(() => {
            const active = state.current;
            if (generation !== active.generation || !active.visible) return;
            active.retry = null;
            active.retryScheduled = false;
            check(generation);
          });
          if (generation !== latest.generation || !latest.visible) {
            cancelPreparationRetry(retry);
            return;
          }
          latest.retry = retry;
          latest.retryScheduled = true;
          latest.loading = true;
          publish();
        } catch (error) {
          if (generation === latest.generation && latest.visible) {
            latest.loading = false;
            latest.retryScheduled = false;
            latest.retry = null;
            publish();
          }
        }
      },
      () => {
        const latest = state.current;
        if (generation !== latest.generation || !latest.visible) return;
        latest.loading = false;
        latest.retryScheduled = false;
        latest.retry = null;
        publish();
      },
    );
  };

  React.useEffect(() => () => invalidate(), []);

  return {
    start() {
      invalidate();
      state.current.visible = true;
      const generation = state.current.generation;
      check(generation);
    },
    close() {
      invalidate();
      state.current.visible = false;
      state.current.loading = false;
      publish();
    },
    reopen(nextToken) {
      invalidate();
      state.current.token = nextToken;
      state.current.visible = true;
      state.current.loading = false;
      const generation = state.current.generation;
      check(generation);
    },
    snapshot() {
      const { retry, generation, ...snapshot } = state.current;
      return { ...snapshot, completed: [...snapshot.completed] };
    },
  };
}

module.exports = { usePreparation };
