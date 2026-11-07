Implemented foreground preparation polling in [usePreparation.js](/tmp/ftcb-agent-workspace-qm725qyp/candidate/src/usePreparation.js).

- Pending responses now schedule another check while keeping the dialog loading.
- Completion occurs only for an explicit ready response.
- Closing cancels retries and invalidates in-flight results.
- Reopening creates a new generation, so old timers/responses cannot affect it.
- Background export behavior remains independent.

Self-checks passed with the required runtime: `v18.17.0`:
- pending → retry → ready lifecycle
- close/reopen stale-response isolation
- JavaScript syntax check