Fix the museum accession activity viewer's startup and navigation lifecycle.

Opening a feed backed by a warm cache sometimes leaves the first batch missing,
although later activity appears. During quick feed changes or closing and
reopening the panel, rows or the count can also appear for a previous visit.

Correct these timing problems while preserving normal live updates, history
recording, public APIs and the existing rendering adapters. The independent
metrics consumer is outside this repair.
