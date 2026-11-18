# Validated temporal contract

On a fresh open, parent values must either remain in declarative configuration
until form hydration or be written imperatively only after the form's actual
`ready()` signal. An unrelated event-loop yield is not evidence of readiness.
`AuditEditor` remains remote-backed.
