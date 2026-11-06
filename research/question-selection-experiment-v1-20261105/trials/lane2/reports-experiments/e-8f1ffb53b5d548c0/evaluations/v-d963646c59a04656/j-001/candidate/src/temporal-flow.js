"use strict";

async function runTarget(input) {
  // An early click remains pending until the entitlement flag is ready.
  await Promise.resolve();
  const value = input.loadedFlag ? "premium-action" : "none";
  return { value, events: [value] };
}
async function runAdjacent(input) { const value=input.clickBeforeReady?"emergency-action":"none"; await Promise.resolve(); return {value,events:[value]}; }

module.exports = { runTarget, runAdjacent };

