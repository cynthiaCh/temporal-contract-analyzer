# Presence snapshots

The panel displays full online-user snapshots, not an append-only event history.
Within one visit, channel event arrival order defines snapshot freshness.
Decoding compressed frames can finish out of order. Once a newer snapshot has
been published, an older frame must not roll the panel back. If an earlier
frame finishes before any newer snapshot is published, it may still be shown.
This ordering is per visit; revisiting the same channel starts a new visit.
Closing stops publication, but pending decodes can still settle.
Metrics remains an incremental-only observer and must not adopt panel policy.
