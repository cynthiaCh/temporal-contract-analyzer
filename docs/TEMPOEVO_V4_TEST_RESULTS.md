# Current verification after V1–V3 retirement

- Full remaining offline suite: **485 tests passed**, 89.075 seconds.
  Log: `/tmp/v4-only-release-regressions.log`.
- Shared/V4/history/review targeted suite: **82 tests passed**.
- Browser incremental-review interaction suite: **11 tests passed**.
- V4 offline demo: `/tmp/tempoevo-v4-only-demo-20261113`, visible PASS on
  Action 2, zero real model calls.
- Python AST import audit found no production imports of retired engines.
- Real V3 batch read-only check preserved original bytes and mtimes.
- JavaScript syntax and `git diff --check` passed.

The lower suite count reflects removal of old-controller-specific tests; shared
backend/scoring/isolation/review tests were migrated and retained. See
[retirement boundaries](LEGACY_RETIREMENT.md).

## Earlier pre-retirement verification (historical)


- Full offline suite: **578 tests passed**, 112.251 seconds.
  Log: `/tmp/tempoevo-v4-release-regressions.log`.
- Final V4 targeted suite: **24 tests passed**, 2.619 seconds.
  Log: `/tmp/v4-release-targeted.log`.
- CLI help smoke check passed.
- Review JavaScript `node --check` passed.
- `git diff --check` passed.
- Offline end-to-end demo: `/tmp/tempoevo-v4-delivered-demo-20261113`, visible success
  on Action 2, passing candidate staged, no real model/provider calls.

Coverage includes early stopping, pass on Actions 2/3, expert-only summary after
three valid failures, unchanged Contract for implementation gaps, source-supported
Contract revision and obligation deletion rejection, prior-candidate reuse,
structured rerouting in the same frozen bank, BM25/structured approved-only
retrieval, held-out no-learning and gold feedback separation, baseline and fixed
Contract conditions, independent source repeats, invalid/partial stages, explicit
cancellation and measured cost retention, invalid model/budget identity, completed
stage reuse, evaluator/source binding, publication idempotency, and unapproved
success/failure-summary candidates. Existing legacy tests remain in the full suite.

No paid experiment, deployment, real-model training, 100-case campaign or external
expert action was performed. Synthetic model metadata does not constitute empirical
model execution evidence; the native adapter is verified with a patched offline
transport and the existing isolated runner configuration.
