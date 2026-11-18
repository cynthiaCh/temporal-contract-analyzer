# Listener snapshot ordering extension

Adds out-of-order decoding of complete state frames within one visit. Visit-identity guards alone cannot prevent state rollback within that visit.

The original task prompt is unchanged; the candidate README specifies snapshot semantics. Registration order, reentrancy, cleanup, and metrics controls from the parent case are retained.
This is an author-designed extension, not a new real-world incident; it shares its parent's independent research unit.
Additional temporal structure does not establish a lower model success rate.

Run oracle/demo.cjs to check the reference and mutants. The parent's correct visit-only repair should fail the added schedules.
