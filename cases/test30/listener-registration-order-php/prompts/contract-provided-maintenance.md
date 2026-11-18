# Maintenance task

Immediately after opening the presence panel, the initial online-user state is
sometimes missing even though later presence updates appear. Fix the presence
panel while preserving its existing behavior, including workspace navigation.

Do not change the metrics consumer.

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

Environment: one event loop, connect emits a bootstrap inline or queues a microtask; decode returns an immutable scalar value or once-fulfilled deferred result, with no rejection in this task. Immediate completions/publications remain synchronous. Publication may select/hide/reopen before connection/setup returns. Listener detachment is passive and skips removed not-yet-called listeners during dispatch. A transport may be reused and independent workspaces may share it. Accepted decode completions may finish in either order; there is no arrival-order latest-wins requirement. Framework unmount/native disposal maps to hide and invalidates output; no public methods are invoked after terminal disposal except harmless final hide.
