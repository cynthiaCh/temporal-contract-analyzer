Updated `src/usePreparation.js` so the dialog:

- completes only when status is `"ready"`;
- schedules another preparation check when status is `"pending"`;
- cancels scheduled retries when closed, reopened, or unmounted;
- ignores responses for replaced tokens.

Self-checks passed with the required runtime: `v18.17.0`, including syntax checks and a pending → retry → ready behavior harness.