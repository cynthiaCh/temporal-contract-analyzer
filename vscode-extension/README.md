# TempoEvo: Temporal Contract Analyzer

Review temporal source clues in Vue, JavaScript, TypeScript and Python from VS Code.

## Installation and daily use

1. In the Extensions panel, choose `…` → **Install from VSIX…** and select `temporal-contract-analyzer-0.2.0.vsix`.
2. **Python 3.9+** is required on the host. The extension discovers it automatically, or search settings for **TempoEvo** and set **Python Path**. The analyzer, Babel and Vue parsers are bundled; no pip, npm or separate Node installation is needed.
3. Open and trust your project. Saving an edited Vue file scans it automatically. **TempoEvo: Scan current file** in the command palette also analyzes unsaved editor contents.
4. View hints in **Problems** or the Explorer's **TempoEvo** sidebar. Expand hints for evidence, click to navigate to source, and hover for conditions and review questions.
5. To include other files, right-click a project directory and select **TempoEvo: Scan folder…**. Directory scans include unsaved contents of open files; single-file scans analyze only the current file.

Each scan replaces the previous editor hints and archives the report and actual source snapshot by default. Editing immediately clears stale locations; save or scan manually to refresh. The sidebar report button opens the latest complete Markdown report as a read-only snapshot, without writing project files. Historical reports are explicitly marked stale.

**TempoEvo: Open shared report archive** opens historical evidence, source snapshots, human reviews and before/after comparisons. **Copy latest report ID** hands the same report to Codex. The CLI, extension and Codex MCP share global configuration; see `docs/ANALYZER.md` in the source repository. Clearing editor results does not delete archives.

Single files and selected directories in multi-root workspaces are supported. Remote development requires Python on the remote extension host. Browser-based VS Code and virtual filesystems are unsupported.

## Settings

| Setting | Default | Description |
|---|---|---|
| `temporalContracts.scanOnSave` | `true` | Scan the current file on save; disable for manual scans only |
| `temporalContracts.pythonPath` | Auto-detect | Python executable path, not a shell command |
| `temporalContracts.archiveEnabled` | `true` | Save each report and source snapshot |
| `temporalContracts.reportStore` | Global configuration | Shared archive directory, outside the scanned project |
| `temporalContracts.timeoutSeconds` | `90` | Analysis timeout |

**TempoEvo: View runtime log** shows status and errors. Automatic scan failures also appear in the sidebar and status bar even without a popup.

## Interpreting results

Hints are **syntax clues requiring human review**, displayed at information level rather than claiming discovered bugs. No hints does not establish safety. Parsing failures display **Analysis incomplete**, rather than implying zero risk.

Vue 2 / Vue 3 inline `<script>` and `<script setup>` support JS / TS / JSX / TSX with original `.vue` line/column locations. Template expressions, reactive dependencies, watcher scheduling, cross-script bindings and component-instance dispatch remain unmodeled. Unsupported external scripts and custom blocks are explicitly reported.

Analysis runs locally on the extension host. It does not call models, upload source, execute project code, install project dependencies or automatically edit code. Directory scans use the analyzer's exclusions and size limits. In `temporal-contract-bench`, select a specific candidate project's `base/` rather than the entire research repository.

## Development and packaging

Install locked parser dependencies from the repository root, then prepare the extension:

```sh
npm ci --prefix temporal_contract_analyzer/javascript --ignore-scripts --no-audit --no-fund
cd vscode-extension
npm ci --ignore-scripts --no-audit --no-fund
npm run stage
npm test
npm run test:host
npm run test:browser
npm run package
```

Node 22+ is recommended for building; end users do not need Node. `runtime/` is copied from this repository's analyzer/parser dependencies during staging and should not be edited manually. The Python analyzer remains the sole rule implementation; VS Code handles invocation, presentation and navigation.

`test:host` defaults to local VS Code on macOS, or uses `VSCODE_EXECUTABLE_PATH`. Elsewhere the testing utility downloads a host. Tests use temporary user-data directories to avoid changing editor settings.

Browser tests use local Chrome, configurable with `CHROME_PATH`, and write reports to temporary directories.

Output: `../dist/temporal-contract-analyzer-0.2.0.vsix`. This is a private extension for local use, not published to Marketplace. No open-source license has been selected for the project. Third-party parser licenses remain with their dependencies.
