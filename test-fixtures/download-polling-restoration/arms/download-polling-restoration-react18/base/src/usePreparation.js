"use strict";

const React = require("react");
const { PREPARATION_STATUS, checkPreparation } = require("./preparation-api.js");

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

  const publish = () => render();
  const check = () => {
    const requestToken = state.current.token;
    state.current.loading = true;
    state.current.checkCount += 1;
    publish();
    checkPreparation(requestToken).then((status) => {
      state.current.loading = false;
      if (status === PREPARATION_STATUS.READY) state.current.completed.push(requestToken);
      publish();
    });
  };

  return {
    start: check,
    close() {
      state.current.visible = false;
      publish();
    },
    reopen(nextToken) {
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
