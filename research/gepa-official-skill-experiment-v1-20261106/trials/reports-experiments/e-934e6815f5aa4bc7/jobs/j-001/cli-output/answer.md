Updated [src/temporal-flow.js](/workspace/src/temporal-flow.js) so direct profile saving emits `ack` only after a successful commit. A failed commit now emits only `error`, which the view displays. The adjacent acknowledgement path was left unchanged.

Verified successful and failed saves, the view’s failure state, and adjacent behavior with a passing Node assertion check.