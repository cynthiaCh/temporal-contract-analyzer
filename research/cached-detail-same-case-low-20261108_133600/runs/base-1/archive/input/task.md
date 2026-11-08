# Improve warm record-detail activation

The detail workspace still waits for a network observation when a record already
exists in the shared repository cache. Update detail activation to use the
repository's existing cache-preferred watch mode: when cached data is available,
show it within the opening call and continue receiving fresh network updates.
A cold record should continue to work normally. Preserve the workspace's
existing behavior. This task covers the detail panel; keep compliance review and
recent preview behavior unchanged.
