import { createTrailingTask } from "./trailing-task.js";

export function createSearchPreview({ timers, publish }) {
  const task = createTrailingTask(query => publish({ query }), 120, timers);
  return {
    query(text) { task.push(text); },
    // A hidden preview has no use for a pending query; reopen starts fresh.
    hide() { task.cancel(); },
  };
}
