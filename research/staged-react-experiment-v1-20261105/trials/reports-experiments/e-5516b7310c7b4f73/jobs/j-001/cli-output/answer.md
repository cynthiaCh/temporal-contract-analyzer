Fixed the first-click issue in [temporal-flow.js](/workspace/src/temporal-flow.js:3). The premium action now checks entitlement after readiness, so an early click works for an entitled user. The emergency control is unchanged.

Verification passed for both click timings, both entitlement states, and the emergency behavior. Syntax checking passed.