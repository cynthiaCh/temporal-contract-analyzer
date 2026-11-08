# Record detail workspace

The detail panel currently waits for the record transport even when the workspace
repository already holds a useful cached snapshot. Public entry points live in
`src/workspace.js`; the repository is shared with compliance review and recent
preview. The transport supplies updates after subscribe returns.

Each `open(id)` requests a new panel activation, including opening the same id
again. `close()` ends that activation. `selection()` and selection rendering
represent the latest requested destination. A record row is useful only while
its activation is selected. A selected panel continues receiving network updates
until close or another open; after departure it retains no transport subscription.

The renderSelection and renderDetail adapters only paint; navigation integrations
are registered through onDetail. The workspace's detail-delivered integration is
synchronous and may request navigation. The repository documents the separate delivery modes and release
contract. Compliance must continue making fresh observations. Recent preview's
network-only presentation is a separately owned feature; changing it requires
its own maintenance authorization.

This is native JavaScript, with an injected record transport for deterministic
network scheduling. There is no frontend framework lifecycle to emulate.
