# Public checks for reserved test ranks 26–50

The built-in public adapter covers six task families and all 25 registered reserved
test IDs. `tools/tempoevo-docker/public_frontend.cjs` imports candidate source and
mounts the actual React/Vue/jQuery entry API using the already pinned grader-image
dependencies. Vanilla JS uses its exported public session/workspace. Native cases
keep the existing trusted language RPC bridge and driver; application behavior
executes in the candidate runtime. No frontend loader imports an oracle module.

The checker uses only task, README, public host API and candidate source obligations:

| Family | Declared public examples |
|---|---|
| Autosave | Quiet burst/latest text, departure persistence, retired subscription status, synchronous navigation, transient preview cancellation/reuse |
| Query | Fresh offline departure/reconnect, remaining shared observer, unconsumed active cache completion |
| Transfer | Cached initial progress, out-of-order full frames with retained audit, unchanged queue record shape |
| Async generator | Early match waits for retained source cleanup, predicate error preserved after cleanup, exhaustion/null result and scan order |
| Review confirmation | Quiet bursts, synchronous submission persistence and entry receipt, queue callback navigation and obsolete confirmation, preview preservation |
| Subscription lifetime | Open delivery and returned completion, closed modal suppresses late writes while returning the operation, independent shell after child disposal |

These examples are intentionally not a claim of exhaustive correctness. They do
not redefine task obligations or replace final Gold. In testing, public PASS ends
repair under the frozen stopping rule; the original Gold runs once afterward, and
its result never triggers another repair.

Preparation mounts `case.json`, `public_checks.cjs` and `public_frontend.cjs` as
trusted evaluator inputs. Their hashes and task-visible check descriptions are
frozen into the trajectory. No reference implementation or hidden schedule/assertion
is opened for adapter development or testing preparation. Gold calibration controls
remain disabled for `--mode testing`.

Verification includes:

- All 25 original public candidates execute in Docker and produce valid observations,
  with no adapter/import/compilation error. Original behavior failures are expected;
  these observations are not model-repair results.
- Six synthetic API models satisfy the suites; six deliberately faulty variants
  fail them. These are independent unit fixtures, not benchmark patches or references.
- The testing-preparation test checks that only `visible` evaluation is invoked,
  and no reference/control branch is opened.
- Final-only Gold, no feedback leakage and no testing-memory writes remain covered
  by the deterministic trajectory tests.

No dependency installation, model invocation, paid experiment, Gold scoring or
reference-based calibration is performed to complete these public adapters.
