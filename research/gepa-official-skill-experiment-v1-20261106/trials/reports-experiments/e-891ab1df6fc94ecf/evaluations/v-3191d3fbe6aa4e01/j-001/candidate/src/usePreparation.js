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
  const [, render] = React.useReducer((value) => value + 1, 0);
  const retry = React.useRef(null);
  const generation = React.useRef(0);
  const active = React.useRef(true);

  React.useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
      generation.current += 1;
      if (retry.current !== null) cancelPreparationRetry(retry.current);
      retry.current = null;
    };
  }, []);

  const publish = () => render();
  const cancelRetry = () => {
    if (retry.current !== null) cancelPreparationRetry(retry.current);
    retry.current = null;
    state.current.retryScheduled = false;
  };
  const check = () => {
    cancelRetry();
    const attempt = ++generation.current;
    const requestToken = state.current.token;
    state.current.loading = true;
    state.current.checkCount += 1;
    publish();
    checkPreparation(requestToken).then((status) => {
      if (!active.current || attempt !== generation.current || !state.current.visible) return;
      if (status) {
        state.current.loading = false;
        if (!state.current.completed.includes(requestToken)) state.current.completed.push(requestToken);
      } else {
        state.current.retryScheduled = true;
        const handle = schedulePreparationRetry(() => {
          if (!active.current || attempt !== generation.current || !state.current.visible) return;
          retry.current = null;
          check();
        });
        if (active.current && attempt === generation.current && state.current.visible) retry.current = handle;
        else cancelPreparationRetry(handle);
      }
      if (active.current && attempt === generation.current) publish();
    });
  };

  return {
    start: check,
    close() {
      generation.current += 1;
      cancelRetry();
      state.current.visible = false;
      state.current.loading = false;
      publish();
    },
    reopen(nextToken) {
      generation.current += 1;
      cancelRetry();
      state.current.token = nextToken;
      state.current.visible = true;
      publish();
      check();
    },
    snapshot() {
      return { ...state.current, completed: [...state.current.completed] };
    },
  };
}

module.exports = { usePreparation };
