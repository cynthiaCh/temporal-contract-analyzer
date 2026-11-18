# Source-pattern record

This case is a clean-room vanilla JavaScript
reconstruction of the `listener-registration-order` causal pattern in
SemanticScopeBench. It retains only the abstract distinction between a presence
consumer that needs a channel bootstrap event and a metrics consumer that
intentionally counts incremental events only.

The implementation uses neutral synthetic tokens, standard `EventTarget`, and
no private source code, company identifier, endpoint, payload, or dependency.

## Source classification

Source kind: `clean_room_reconstruction`. The direct source is the named SemanticScopeBench causal pattern. This label records the reconstruction lineage; representation variants and authored extensions retain their existing independent-unit assignments.
