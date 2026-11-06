Updated [src/progress.js](/workspace/src/progress.js) so the panel subscribes before the feed emits its cached first packet. It also keeps an older, slow-decoding frame from replacing a newer frame on screen, while still recording every decoded frame.

A targeted check passed for the initial update, out-of-order decoding, telemetry, and selecting the same file again.