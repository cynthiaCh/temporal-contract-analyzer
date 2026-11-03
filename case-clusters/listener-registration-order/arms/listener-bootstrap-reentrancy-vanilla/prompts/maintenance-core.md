# Maintenance task

Immediately after opening the presence panel, the initial online-user state is
sometimes missing even though later presence updates appear. Fix the presence
panel while preserving workspace navigation and the public APIs.

This case uses synchronous decoding only. Preserve the behavior documented in
README.md. Do not change the metrics consumer.
