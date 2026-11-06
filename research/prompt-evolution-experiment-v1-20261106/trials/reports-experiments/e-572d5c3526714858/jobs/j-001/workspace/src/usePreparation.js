"use strict";

const React = require("react");
const { checkPreparation, schedulePreparationRetry, cancelPreparationRetry } = require("./preparation-api.js");

function usePreparation(initialToken) {
  const state = React.useRef({
    visible: true,
    loading: false,
    retryScheduled: false,
    checkCount: 0,
    completed: [],
    token: initialToken,
  });
  const retry = React.useRef(null);
  const generation = React.useRef(0);
  const active = React.useRef(true);
  const [, render] = React.useReducer((value) => value + 1, 0);

  const publish = () => { if (active.current) render(); };
  const cancelRetry = () => {
    const pending = retry.current;
    retry.current = null;
    if (pending && pending.handle !== null) cancelPreparationRetry(pending.handle);
    state.current.retryScheduled = false;
  };
  const check = (requestToken, requestGeneration) => {
    if (!active.current || requestGeneration !== generation.current) return;
    state.current.loading = true;
    state.current.checkCount += 1;
    publish();
    checkPreparation(requestToken).then((ready) => {
      if (!active.current || requestGeneration !== generation.current) return;
      if (ready) {
        state.current.loading = false;
        state.current.retryScheduled = false;
        if (!state.current.completed.includes(requestToken)) state.current.completed.push(requestToken);
        publish();
        return;
      }

      const pending = { handle: null };
      retry.current = pending;
      state.current.retryScheduled = true;
      publish();
      const handle = schedulePreparationRetry(() => {
        if (retry.current !== pending) return;
        retry.current = null;
        state.current.retryScheduled = false;
        check(requestToken, requestGeneration);
      });
      if (retry.current === pending) pending.handle = handle;
      else cancelPreparationRetry(handle);
    });
  };
  const start = () => {
    cancelRetry();
    const requestGeneration = ++generation.current;
    check(state.current.token, requestGeneration);
  };

  React.useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
      generation.current += 1;
      cancelRetry();
    };
  }, []);

  return {
    start,
    close() {
      state.current.visible = false;
      publish();
    },
    reopen(nextToken) {
      state.current.token = nextToken;
      state.current.visible = true;
      publish();
      start();
    },
    snapshot() {
      return { ...state.current, completed: [...state.current.completed] };
    },
  };
}

module.exports = { usePreparation };
