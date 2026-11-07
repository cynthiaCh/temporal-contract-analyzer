# Audit log：提交完成与历史身份

Each submit captures doc, actor and text at call entry. A successful commit creates exactly one audit record with that snapshot and the returned revision, only after commit succeeds. Failed commits create no success audit. Accepted submissions survive close or reopen. Saved/error UI belongs only to the current visit and its latest submission; history is not owned by a view.

The search preview remains 40 ms, discards pending queries on hide and is reusable.
