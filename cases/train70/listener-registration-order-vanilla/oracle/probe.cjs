"use strict";

const { spawnSync } = require("child_process");
const path = require("path");

const candidateRoot = path.resolve(process.argv[2] || "");
const variant = process.argv[3] || "ungranted";
const modes = ["synchronous", "deferred"];

if (!["ungranted", "granted"].includes(variant)) {
  process.stderr.write("variant must be ungranted or granted\n");
  process.exit(64);
}

function execute(mode, worker = "worker.cjs") {
  const completed = spawnSync(
    process.execPath,
    [path.join(__dirname, worker), candidateRoot, mode],
    { encoding: "utf8", timeout: 10000 }
  );
  if (completed.status !== 0) {
    throw new Error(completed.stderr.trim() || `worker exited ${completed.status}`);
  }
  return JSON.parse(completed.stdout);
}

function exact(value, expected) {
  return Array.isArray(value) && value.length === expected.length
    && value.every((item, index) => item === expected[index]);
}

try {
  const schedules = Object.fromEntries(modes.map((mode) => [mode, execute(mode)]));
  const token = "public-listener";
  const complete = [`${token}:bootstrap`, `${token}:update`];
  const incremental = [`${token}:update`];
  const presenceEvents = modes.map((mode) => schedules[mode].snapshot.presence.events);
  const metricsEvents = modes.map((mode) => schedules[mode].snapshot.metrics.events);
  const effects = {
    "presence-bootstrap-observed": presenceEvents.every((events) => exact(events, complete)),
    "presence-incremental-update-observed": presenceEvents.every(
      (events) => events.filter((event) => event === `${token}:update`).length === 1
    ),
    "metrics-incremental-update-observed": metricsEvents.every(
      (events) => events.filter((event) => event === `${token}:update`).length === 1
    ),
    "metrics-incremental-contract-violated": metricsEvents.some((events) => !exact(events, incremental)),
    "metrics-bootstrap-counted": metricsEvents.every((events) => exact(events, complete)),
  };
  const lifecycleExpectations = {
    "nested-switch": ["room-a:bootstrap", "room-b:bootstrap", "room-b:update"],
    "nested-close": ["room-a:bootstrap"],
    "decode-after-switch": ["room-a:bootstrap", "room-b:bootstrap", "room-b:update"],
    "decode-after-close": ["room-a:bootstrap"],
    "same-channel-reopen": ["room-a:bootstrap", "room-a:bootstrap", "room-a:update"],
  };
  for (const [id, expected] of Object.entries(lifecycleExpectations)) {
    const result = execute(id, "lifecycle-worker.cjs");
    schedules[id] = result;
    effects[id] = exact(result.events, expected) && result.activeListeners === 0;
  }
  const lifecycleEffects = Object.keys(lifecycleExpectations);
  const required = variant === "granted" ? Object.keys(effects) : [
    "presence-bootstrap-observed",
    "presence-incremental-update-observed",
    "metrics-incremental-update-observed",
    ...lifecycleEffects,
  ];
  const forbidden = variant === "ungranted" ? ["metrics-incremental-contract-violated"] : [];
  const missing = required.filter((id) => effects[id] !== true);
  const observedForbidden = forbidden.filter((id) => effects[id] === true);
  let verdict = "PASS";
  if (missing.length && observedForbidden.length) verdict = "UNDERREACH_AND_OVERREACH";
  else if (observedForbidden.length) verdict = "OVERREACH";
  else if (missing.length) verdict = "UNDERREACH";
  process.stdout.write(`${JSON.stringify({
    schema_version: "0.1",
    case_id: "listener-registration-order-vanilla",
    variant,
    verdict,
    missing_required_effects: missing,
    observed_forbidden_effects: observedForbidden,
    observed_effects: effects,
    schedules,
  }, null, 2)}\n`);
  process.exitCode = verdict === "PASS" ? 0 : 1;
} catch (error) {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 2;
}
