import { createTrailingTask } from "./trailing-task.js";

export function createSearchPreview({ timers, publish }) {
  const task = createTrailingTask(query => publish({ query }), 40, timers);
  return {
    query(value) { task.push(value); },
    hide() { task.cancel(); },
  };
}
