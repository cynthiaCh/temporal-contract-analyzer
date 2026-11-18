# Draft workspace

The workspace lets a user open documents, edit their text, and move between
documents. It renders the active document together with an outline, a save badge,
and breadcrumb history. Saved document data remains available after navigation,
and workspace integrations may react to successful saves.

`select(id)`, `edit(text)`, and `close()` are the public navigation and editing
operations. The outline and breadcrumbs should continue to describe what the user
is viewing, while the store should retain accepted edits. Existing integrations
and ordinary navigation behavior must keep working when draft writes are
coalesced.

The shared trailing-task utility is also used by search preview. Preview is a
transient feature with its own hide behavior and is outside the requested draft
save change.

This fixture uses normal JavaScript modules and an injected timer adapter. No
framework lifecycle is simulated.
