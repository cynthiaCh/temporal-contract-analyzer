"use strict";

// This fixture's public service contract is deliberately explicit: the
// transport resolves false while preparation is pending and true when ready.
const PREPARATION_STATUS = Object.freeze({
  PENDING: false,
  READY: true,
});

function checkPreparation(token) {
  if (typeof globalThis.__preparationTransport !== "function") {
    throw new Error("preparation transport is not installed");
  }
  return globalThis.__preparationTransport(token);
}

function schedulePreparationRetry(callback) {
  if (typeof globalThis.__schedulePreparationRetry !== "function") {
    throw new Error("retry scheduler is not installed");
  }
  return globalThis.__schedulePreparationRetry(callback);
}

function cancelPreparationRetry(handle) {
  if (typeof globalThis.__cancelPreparationRetry === "function") {
    globalThis.__cancelPreparationRetry(handle);
  }
}

module.exports = {
  PREPARATION_STATUS,
  checkPreparation,
  schedulePreparationRetry,
  cancelPreparationRetry,
};
