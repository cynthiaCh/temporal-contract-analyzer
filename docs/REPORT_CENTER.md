# Shared report archive (Analyzer 0.6 / VS Code 0.2)

The standalone CLI, VS Code and Codex MCP share one disk-based report archive. Each scan creates a new report ID. The browser reads that ID's results and source snapshot rather than rescanning the current project to display an old report.

## Initial configuration

Run from this repository using Python 3.9+. On macOS, `/usr/bin/python3` may be used:

```sh
/usr/bin/python3 -B -m temporal_contract_analyzer reports init \
  --store "$HOME/.temporal-contract-analyzer/reports" \
  --node /usr/local/bin/node
/usr/bin/python3 -B -m temporal_contract_analyzer reports open
```

Set `--node` to the actual installed Node executable. Global configuration is stored in `~/.temporal-contract-analyzer/config.json`. Report-directory precedence is command arguments / extension settings, `TCA_REPORT_STORE`, global configuration, then `~/.temporal-contract-analyzer/reports`. `TCA_CONFIG` selects a separate configuration file for uses such as test isolation.

The archive must be outside the scanned project; neither may contain the other. It stores source snapshots and should be managed with research material. There is currently no automatic cleanup policy. The service listens only on `127.0.0.1` and requires no account, database or external CDN. Closing the browser does not stop the background service. Reopening reuses it; the port may change after a restart:

```sh
/usr/bin/python3 -B -m temporal_contract_analyzer reports open --no-browser
/usr/bin/python3 -B -m temporal_contract_analyzer reports stop
```

After updating the analyzer, run `stop` then `open` to load the new version. In remote development, the archive and service run on the extension-host machine. The browser needs a forwarded port to that machine; automatic forwarding is not implemented in this version.

## Daily usage

- **VS Code**: saving or manually scanning archives results by default. In the command palette, choose **Temporal Contracts: Open shared report archive** or **Copy latest report ID**. Set `archiveEnabled=false` to disable archiving; leave `reportStore` empty to follow global configuration. Clearing editor hints does not delete historical reports.
- **Browser**: create scans; filter by project/rule/task/origin; inspect four-question boundary review cards and source snapshots; record relation judgments and protection sufficiency separately; add repository evidence and missing evidence; rescan from a baseline and compare hint changes.
- **CLI**: existing `scan` and `freeze` behavior is unchanged; use `reports scan` to write to the shared archive.

```sh
/usr/bin/python3 -B -m temporal_contract_analyzer reports scan /absolute/path/to/vue-project \
  --project my-app --label before-fix --task-id task-001
/usr/bin/python3 -B -m temporal_contract_analyzer reports list --project my-app
/usr/bin/python3 -B -m temporal_contract_analyzer reports show REPORT_ID
/usr/bin/python3 -B -m temporal_contract_analyzer reports verify REPORT_ID
/usr/bin/python3 -B -m temporal_contract_analyzer reports scan /absolute/path/to/vue-project \
  --label after-fix --parent-report-id BEFORE_ID
/usr/bin/python3 -B -m temporal_contract_analyzer reports compare BEFORE_ID AFTER_ID
```

Replace placeholders such as `REPORT_ID` with returned values. Linking and comparison require the same absolute project path and scan scope. Incompatible tool/parser versions prevent hint-change calculation. `reports scan` returns exit code 2 for partial / empty / failed scans while retaining a displayable record where possible. Invalid arguments, an unwritable archive or forced process termination may prevent record creation.

## Using Codex in VS Code

Codex calls the same analyzer through local MCP without manipulating another extension's interface. Register the server using your checkout's actual path:

```sh
codex mcp add temporal_contracts -- /usr/bin/python3 -I -S -B -X utf8 \
  /absolute/path/to/temporal-contract-analyzer/temporal_contract_analyzer/hub_entry.py \
  reports mcp
```

Codex CLI and the IDE extension share MCP configuration. Reload the Codex session after registration, and the VS Code window if necessary. See the [official Codex MCP documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) for configuration.

Example instruction:

> Use temporal_contracts scan_project to scan the current Vue project's absolute path, then read the complete report with read_report, following next_offset. Review evidence before editing and testing. After repair, scan the same scope again with the previous parent_report_id, compare the reports and return their IDs.

Or copy an ID from the extension and ask:

> Read report REPORT_ID with temporal_contracts read_report and inspect its source snapshot with read_source. Check differences between snapshot and current code before suggesting edits.

| MCP tool | Function |
|---|---|
| `scan_project` | Scan an absolute file/directory path on disk, archive it and return its ID |
| `list_reports` | Search historical records |
| `read_report` | Read a complete report or frozen layer by ID in pages |
| `read_source` | Read the corresponding source snapshot by ID in pages |
| `read_context` | Enrich archived hints with candidate definitions; page through separate JSON with provenance and gaps |
| `compare_reports` | Compare two scans of the same project and scope |

The browser provides a **Source context** tab and **Expand related source** on boundary cards. The CLI equivalent is `reports context REPORT_ID`. See [context enrichment](CONTEXT_ENRICHMENT.md) for parameters and scope. Restricted frozen-layer MCP sessions expose only their designated layer, without this tool.

The extension can capture unsaved editor contents; Codex/browser scans read disk. To study identical input, have Codex **read the report ID supplied by the extension**, rather than rescan and assume equality. A shared Node configuration reduces parser-runtime differences across entry points. Archiving and the browser do not call models; material returned through MCP enters the current Codex session.

## Research records and boundaries

Each archive contains `metadata.json`, `snapshot.json`, successfully generated `report.json/md/html`, a verification manifest, and `bundle/` only when parsing is complete. Records retain project path, scope, time, origin, task ID, parent report, tool and input digests. The snapshot contains **source included in analysis**, not the entire Git repository, dependencies or runtime environment.

The default entry is **Boundary review**. Change-scope filtering uses explicit file paths or files changed since a linked baseline, expanding at file level through candidate direct call links. Dynamic calls and complete callback chains are not covered. The old E/T/L/H measurement workbench, single-case experiments and history browser were removed; see [ARCHITECTURE.md](ARCHITECTURE.md). Existing external measurement data is retained, but current report interfaces do not read, verify or append it.

Human annotations are stored separately in `notes/REPORT_ID/`, with confirmed / dismissed / uncertain judgments and notes. The browser also records protection sufficiency, repository requirements and protection evidence, and missing evidence. Older plain-text records remain readable. These are human judgments, not automatic experimental ground truth. Before/after hint counts are not repair success rates.

`deliveries/REPORT_ID/` records the exact paginated MCP response text, layer, digest, session and client identifiers. The browser's **Agent deliveries** view shows:

- `prepared_for_tool_response`: material prepared for return.
- `transport_written`: the server wrote the tool response.

These records do not establish client receipt, model attention or resulting edits, and do not contain the full conversation trace. Formal experiments must separately link tasks, model configuration, complete traces and test results. Annotations and delivery records do not rewrite frozen reports. Digest checks detect content mismatch; they are neither tamper-proof signatures nor correctness proofs.

For a research session restricted to one designated layer, start a restricted MCP server:

```sh
/usr/bin/python3 -I -S -B -X utf8 \
  /absolute/path/to/temporal-contract-analyzer/temporal_contract_analyzer/hub_entry.py \
  reports mcp --report-id REPORT_ID --layer facts
```

This server exposes only the designated report layer. It cannot list other reports, read source or switch layers. It does not restrict the agent's other tools or filesystem permissions, cannot independently guarantee condition isolation, and does not replace the bench's controlled runner. Formal experiments need separate isolation of other material channels; do not simultaneously enable an unrestricted server. Partial / empty / failed reports cannot be delivered as complete frozen material.

Existing `temporal-contract-bench` experiments, frozen inputs, scorers and historical data have not been migrated or rewritten. This archive supports daily tool use and subsequent research records.

## Validation

```sh
/usr/bin/python3 -B -m unittest discover -s tests
cd vscode-extension
npm run stage
npm test
npm run test:host
npm run test:browser
npm run package
```

Browser tests use Playwright with local Chrome; set `CHROME_PATH` on non-macOS systems as needed. Integration tests use temporary archives and synthetic candidate source, without adding test records to the research archive.
