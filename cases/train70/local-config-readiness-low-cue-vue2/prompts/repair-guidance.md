# Repair guidance

A valid implementation may encode the parent identity in the declarative form
rules or defer an imperative write until the form API's actual readiness
signal. Do not treat an arbitrary Promise microtask or timer delay as evidence
that the form API is ready.
