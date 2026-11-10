# Expert-gated experience evolution

Base commit: `9d612d2d8f276e55603d959f5712bf9a6a1729ba`.

Implement bounded automatic development: frozen visible inputs, retrieval,
independent repair feedback, one reflection per round, two candidate validations,
and a real operator review checkpoint. Only an explicit named expert decision
activates a version. Adding/rejecting a child never implicitly replaces the active
parent. Evaluation uses an immutable active snapshot and cannot learn.

Reuse existing research isolation, request metering, archival and trusted scoring
adapters. Keep original experiments and library records intact. No paid sessions,
extra model judges, commits, installation, global settings or production updates.

Expose CLI execution and an offline expert review report. Validate the complete
state machine with synthetic adapters, plus the native adapter's command and
preflight paths offline. Live execution requires explicit CLI opt-in and a
prepared, source-reviewed input packet; missing runtime/calibration blocks it.
