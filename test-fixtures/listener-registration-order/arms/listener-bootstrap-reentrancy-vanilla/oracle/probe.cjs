"use strict";
const path = require("path");
const { pathToFileURL } = require("url");
const { getEventListeners } = require("events");
const root = path.resolve(process.argv[2] || "");
const caseId = "listener-bootstrap-reentrancy-vanilla";
const schedules = {};
const runtimeErrors = [];
const exact = (actual, expected) => JSON.stringify(actual) === JSON.stringify(expected);
async function check(name, run) {
  try { schedules[name] = await run(); }
  catch (error) {
    runtimeErrors.push({ scenario: name, error: String(error.stack || error) });
    schedules[name] = { passed: false, runtimeError: String(error) };
  }
}
async function main() {
  const load = name => import(pathToFileURL(path.join(root, "src", name)).href);
  const { createPresenceChannel } = await load("channel.js");
  const { createWorkspaceNavigation } = await load("workspace-navigation.js");
  const { renderPresence } = await load("presence-panel.js");
  const { collectMetrics } = await load("metrics-consumer.js");
  for (const mode of ["synchronous", "deferred"]) {
    await check(mode, async () => {
      const actual = (await renderPresence("a", mode)).events;
      const expected = ["a:bootstrap", "a:update"];
      return { actual, expected, passed: exact(actual, expected) };
    });
  }
  await check("metrics-policy", async () => {
    const actual = (await collectMetrics("m")).events;
    const expected = ["m:update"];
    return { actual, expected, passed: exact(actual, expected) };
  });
  for (const scenario of ["nested-switch", "nested-close", "ordinary-navigation", "ordinary-reopen", "nested-switch-inline-update", "nested-close-inline-update"]) {
    await check(scenario, async () => {
      const a = createPresenceChannel("a");
      const b = createPresenceChannel("b");
      const actual = [];
      let acted = false;
      const nav = createWorkspaceNavigation((value, controls) => {
        actual.push(value);
        if (!acted && value === "a:bootstrap") {
          acted = true;
          if (scenario === "nested-switch" || scenario === "nested-switch-inline-update") controls.select(b);
          if (scenario === "nested-close" || scenario === "nested-close-inline-update") controls.hide();
          if (scenario.endsWith("inline-update")) a.emitUpdate();
        }
      });
      nav.select(a);
      if (scenario === "ordinary-navigation") nav.select(b);
      if (scenario === "ordinary-reopen") { nav.hide(); nav.select(a); }
      a.emitUpdate(); b.emitUpdate();
      nav.hide(); a.emitUpdate(); b.emitUpdate();
      const activeListeners = [a, b].reduce((n, c) => n + getEventListeners(c.target, "presence").length, 0);
      const expected = scenario.startsWith("nested-close") ? ["a:bootstrap"]
        : scenario === "ordinary-reopen" ? ["a:bootstrap", "a:bootstrap", "a:update"]
        : ["a:bootstrap", "b:bootstrap", "b:update"];
      return { actual, expected, activeListeners, passed: exact(actual, expected) && activeListeners === 0 };
    });
  }
  const missing = Object.entries(schedules).filter(([name, row]) => name !== "metrics-policy" && !row.passed).map(([name]) => name);
  const forbidden = schedules["metrics-policy"].passed ? [] : ["metrics-policy-changed"];
  const verdict = missing.length ? (forbidden.length ? "UNDERREACH_AND_OVERREACH" : "UNDERREACH") : (forbidden.length ? "OVERREACH" : "PASS");
  process.stdout.write(JSON.stringify({ case_id: caseId, verdict, missing_required_effects: missing, observed_forbidden_effects: forbidden, schedules, runtime_errors: runtimeErrors }));
  process.exitCode = verdict === "PASS" && !runtimeErrors.length ? 0 : 1;
}
main().catch(error => { process.stderr.write(String(error.stack || error)); process.exitCode = 2; });
