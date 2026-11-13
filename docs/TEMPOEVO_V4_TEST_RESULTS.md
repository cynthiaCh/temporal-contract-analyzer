# V4 local verification

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
