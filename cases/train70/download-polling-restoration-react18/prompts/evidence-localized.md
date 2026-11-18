# Evidence locations

Before editing, inspect the following candidate-visible locations together:

- `src/DownloadDialog.jsx`: how the foreground surface uses its preparation
  hook;
- `src/usePreparation.js`: `start`, `close`, `reopen`, and request-completion
  handling;
- `src/BackgroundExportPanel.jsx`: how the adjacent surface uses its hook;
- `src/useBackgroundPreparation.js`: retry, close, and cleanup handling;
- `src/preparation-api.js`: the preparation status and scheduling interfaces.

Use these locations to determine which existing observable behaviors the
maintenance change must preserve. The locations are navigation evidence, not
a prescribed contract or repair. Then complete the maintenance task.
