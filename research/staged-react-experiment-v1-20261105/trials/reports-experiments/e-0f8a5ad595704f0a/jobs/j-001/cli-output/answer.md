Fixed the first-click issue in [temporal-flow.js](/workspace/src/temporal-flow.js:3). The premium action now checks entitlement after readiness, so an entitled user’s early click succeeds. The emergency action is unchanged.

All six behavior checks passed, and `node --check` passed. The Git diff check was unavailable because this workspace is not a Git repository.