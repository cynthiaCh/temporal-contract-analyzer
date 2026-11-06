Updated [src/progress.js](/workspace/src/progress.js:2) so the panel subscribes before `start()` emits a cached packet. Each decoded frame still enters progress history; a frame from an older packet can no longer repaint over a newer one.

Checks passed for the initial update, out of order decoding, telemetry, retry, hide, cleanup, and subsequent use.