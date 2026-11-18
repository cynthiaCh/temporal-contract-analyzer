# Temporal-risk audit

Before editing, inspect the candidate-visible repository for evidence that code
being removed, replaced, or reordered may incidentally delay, sequence, cancel,
invalidate, or wait for another operation. Consider at least two feasible event
orders and preserve every evidence-supported behavior and authorization
boundary. Do not assume that such a coupling exists, and do not invent a
requirement without repository evidence. Then complete the maintenance task.
