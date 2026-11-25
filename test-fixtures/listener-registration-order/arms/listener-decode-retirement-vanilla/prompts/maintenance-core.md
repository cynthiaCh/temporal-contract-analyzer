# Maintenance task

After quickly switching rooms or closing the presence panel, an old online-user
update can still appear. Fix the presence panel's subscription lifecycle while
preserving normal delivery, workspace navigation and public APIs.

Bootstrap registration and synchronous navigation are already repaired in this
case. Preserve the behavior documented in README.md. Do not change the metrics
consumer.
