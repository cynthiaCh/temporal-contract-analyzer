## 0.3.1

- Refresh the experience editor with a compact library list, summary previews and grouped guidance fields.
- Fold labels, mechanisms and source details away from the main writing area; expand missing required fields during validation.
- Follow VS Code theme colors and adapt to narrow editor groups with independently scrolling list and editor panes.
- Keep save actions visible and allow long experience titles to wrap while editing.

## 0.3.0

- Replace the scanner entrypoint with a local experience library editor.
- Search and filter experiences; create, edit and delete with direct owner saves.
- Save guidance and retrieval Abstract together without approval UI.
- Detect external edits and keep restorable entry history.
- Bundle Python library support without JavaScript source parsers.

# Changelog

## 0.2.0

- Bundles analyzer 0.6.0 and archives each report with its actual source snapshot.
- Adds “Open shared report archive” and “Copy latest report ID”, sharing configuration with the standalone CLI and Codex MCP.
- Local browser supports history filtering, source evidence, human review, before/after comparison and agent-material delivery records.
- Retains partial / failed records and binds unsaved editor contents to their reports.

## 0.1.0

- Bundles temporal-contract-analyzer 0.5.0 with pinned Babel / Vue parsers.
- Current-file and directory scans, automatic analysis on save and unsaved-content support.
- Information-level Problems, evidence tree, source navigation and read-only Markdown reports.
- Invalidates old locations after edits, supports cancellation/timeouts and explicitly displays incomplete parsing.
