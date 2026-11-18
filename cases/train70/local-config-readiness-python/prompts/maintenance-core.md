# Maintenance task

The remote static-configuration endpoint used by `RecordEditor` has been
retired. Replace that request with the existing `LOCAL_CONFIG` and keep the
editor's existing behavior unchanged.

Do not migrate `AuditEditor`.

