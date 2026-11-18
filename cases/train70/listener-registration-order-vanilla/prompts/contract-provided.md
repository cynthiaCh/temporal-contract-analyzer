# Temporal contract

Presence must subscribe before connection, including synchronous bootstrap.
Publication can synchronously hide the panel or select another channel. Publish
the current visit's ownership and cleanup before invoking connection; an outer
show must not overwrite a nested show's ownership or resurrect a hidden visit.
Only the current visit may publish a decoded frame. A pending decoder can settle
after listener removal; switching, hiding, and reopening the same transport
invalidate the prior visit. Each current event is published exactly once.
Retire subscriptions when their visit ends, including a visit ended during
bootstrap publication. Metrics remains incremental-only unless migration is
explicitly authorized; do not globally reorder its connection and subscription.
