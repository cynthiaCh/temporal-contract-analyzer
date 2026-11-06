The study-local `.venv` contains the complete official GEPA wheel built from `../official-src`, commit `8e9ae9ed063f6a0259c93db595b96953fdab0e6d` (package metadata 0.1.4). See `official.json`, `pip-freeze.txt`, the saved wheel and its SHA256. No project production dependencies were changed.

Recreate with Python 3.11 venv and install the saved wheel into that venv. The executor/scorer remain the repository's existing implementations and external runtime installations; their paths, inputs, and versions are recorded in protocol and calibration.

Formal runs are intentionally not auto-resumable: the adapter refuses an existing task ledger/checkpoint rather than silently spending another budget. Offline tests use a synthetic callable, never the provider. Actual startup and each completed evaluation are separately archived; an incomplete startup consumes its budget slot.
