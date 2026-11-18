# Maintenance task

A notification received after the alerts modal is closed still updates the modal's state. Fix the issue. Change only the modal subscription; do not migrate the application-shell subscription.

# Validated temporal contract

Modal close invalidates its notification listener before later delivery. The ungranted shell listener is application-owned and survives child disposal.


Environment: notification transport returns a deferred result. Returned payload must be preserved even when UI writes are suppressed; native result callback corresponds to run completion. A closed modal instance is terminal.
