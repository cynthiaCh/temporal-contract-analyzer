# Analyzer, report archive and source context

Use this guide to inspect source evidence in the CLI, browser, editor or MCP.
These operations do not call models. They are separate from experimental
[learning/testing](WORKFLOW.md) and [personal correction memory](PERSONAL_MCP.md).
Install the parser dependencies described in the [README](../README.md) for
JS/TS/Vue; Python analysis does not require Node.

## Scan and inspect reports

```sh
python3 -B -m temporal_contract_analyzer scan /absolute/project --format md
python3 -B -m temporal_contract_analyzer scan /absolute/project --format html --view exploratory
python3 -B -m temporal_contract_analyzer reports init \
  --store /absolute/report-archive --node /absolute/path/to/node
python3 -B -m temporal_contract_analyzer reports open
python3 -B -m temporal_contract_analyzer reports scan /absolute/project \
  --project my-app --label before-fix --task-id task-001
python3 -B -m temporal_contract_analyzer reports list --project my-app
python3 -B -m temporal_contract_analyzer reports show REPORT_ID
python3 -B -m temporal_contract_analyzer reports verify REPORT_ID
```

Use actual returned IDs. `reports scan` archives evidence; ordinary `scan` does not
create a shared report by itself. Archive and scanned project must be separate,
with neither containing the other. Archives contain source snapshots and have no
automatic cleanup policy. Directory precedence is explicit arguments / extension
settings, `TCA_REPORT_STORE`, global config, then
`~/.temporal-contract-analyzer/reports`. `TCA_CONFIG` selects another config file.

The service listens on `127.0.0.1`; closing the browser does not stop it. Use
`reports stop`, then `reports open` after updates. `reports open --no-browser`
prints access information without launching a browser. Remote extension hosts
need manual browser port forwarding.

The browser shows boundary cards, source snapshots, annotations and source-context
expansion. VS Code can archive scans and copy report IDs; editor overlays may
include unsaved content while CLI/browser scans read disk. Pass the same report
ID to an agent when identical input matters. See the
[extension guide](../vscode-extension/README.md).

For before/after comparisons, keep the same absolute project path and scan scope:

```sh
python3 -B -m temporal_contract_analyzer reports scan /absolute/project \
  --label after-fix --parent-report-id BEFORE_ID
python3 -B -m temporal_contract_analyzer reports compare BEFORE_ID AFTER_ID
```

Incompatible parser/tool versions prevent hint-change calculation. Partial/empty/
failed scans return exit code 2 and retain a displayable record where possible;
invalid arguments or process termination may prevent record creation.

## Report interpretation and bounded checks

Markdown/HTML default to a focused view; JSON retains the full original evidence.
`--view exploratory` restores broader hints and syntax events. The focused view
shows evidence-complete `write_after_call` state-publication candidates,
`detach_after_call` listener-removal candidates and `key_before_result` argument-cache
candidates. Each rule has its own relation/evidence checks; equivalent cards are
merged while retaining call locations. `write_before_call` is an ordering fact, and
`not_established` is unknown. Hidden cards, fewer hints or a disappearing card do
not prove safety or a successful repair. Source excerpts may be shortened; the
archived source is retained.

The bounded JS/TS/Vue reentry check locates shared-state reads, callback-capable
calls and state writes on recognized synchronous paths. It expands direct IIFEs
and uniquely bound local functions within depth/event limits (four levels and
2,000 events per entry), not a whole-program call graph. Calls before the first
JS `await` can execute synchronously; this is not Python-coroutine semantics.

| Evidence | Current bounded support | Boundary |
|---|---|---|
| Callback provenance | Parameter calls, call/apply, restricted one-hop copies and captured receiver Reflect calls | Actual function types, runtime replacement and general aliases are unproven |
| Branches and clearing | Recognized positive/nested paths and simple null/undefined cleanup patterns | No complete control-flow, exception or reaching-definitions proof |
| Invocation quotas | Restricted numeric parameter guards and explicit decrement patterns | Not arbitrary arithmetic, coercion, reset or global effect-count proofs |
| Order states | `write_after_call`, `write_before_call`, `not_established` | Neither runtime reentry nor sufficient protection is proven |

Deferred callbacks, imported/dynamic callees, Vue templates and complete framework
scheduling are not expanded. Unsupported or ambiguous paths remain unknown.
Conditional cleanup is described only when its condition holds; cleanup is not
inherently defective. For exact rule predicates see `reentrancy.py`, `lifecycle.py`,
`countdown.py` and `review.py` under `temporal_contract_analyzer/`. Development cases
and artificial regressions are not independent precision or agent-benefit studies.

## Source context

In the browser choose **Expand related source** or **Source context**. CLI:

```sh
python3 -B -m temporal_contract_analyzer reports context REPORT_ID \
  --depth 2 --max-chars 12000 --format md
```

| Option | Meaning |
|---|---|
| `--finding-id ID` | One hint; omitted means all hints |
| `--depth 0..5` | Default 1; zero keeps seed evidence only |
| `--max-chars 1..100000` | Default 12000 source Unicode characters, not tokens |
| `--aliases '{"@":"src"}'` | Explicit snapshot-relative aliases; no build-config guessing |
| `--format json\|md`, `--output PATH` | JSON default; output must be new and outside original project |

Context is separate `temporal-context-1` material from verified archived snapshots,
not current workspace files or a modification of report layers. It includes
snippets with provenance, unresolved dependencies and usage. Seeds over budget
fail explicitly; supplemental definitions are omitted whole with recorded gaps.
No findings means empty context, not repository-wide search.

Definition enrichment supports limited JS/TS/Vue-script lexical bindings and static
local named/default imports within the snapshot. Ambiguous extensionless imports
remain gaps. Namespace imports, re-exports, CommonJS, dynamic imports, runtime
member dispatch and complete data/control flow are unsupported. Other languages
retain seeds with unsupported enrichment. Single-file scans do not read adjacent
modules; scan the dependency directory when needed. An empty unresolved list does
not establish complete dependencies or useful retrieval.

Implementation boundaries are in `publication.py`, `countdown.py`, `reflective.py`,
`protocols.py` and `review.py` under `temporal_contract_analyzer/`.

## Read through MCP

Register the server as in [PERSONAL_MCP.md](PERSONAL_MCP.md). Unrestricted sessions
provide `scan_project`, `list_reports`, `read_report`, `read_source`, `read_context`,
`compare_reports`, plus the personal experience tools. Read paginated results
through `next_offset`; keep IDs/options constant across pages. For `read_context`:

```json
{"report_id":"REPORT_ID","depth":2,"max_chars":12000,"offset":0,"limit":12000}
```

Only `report_id` is required; optional `finding_id` and `aliases` match CLI scope.
Read the archived evidence, check snapshot/workspace differences, then decide edits.

A restricted server uses `reports mcp --report-id REPORT_ID --layer facts` and
exposes only that report layer, without source/context or memory tools. It does
not constrain the agent's other tools or filesystem, and cannot alone establish
experimental condition isolation. Partial/empty/failed reports cannot be delivered
as complete frozen material.

## Archive and human review boundaries

A report stores metadata, the analyzed source snapshot, generated reports and
verification data; it is not a full repository or environment backup. Human notes
live separately under `notes/REPORT_ID/`. Relation judgments, protection evidence
and missing-evidence notes are review records, not automatic ground truth.

`deliveries/REPORT_ID/` records paginated MCP text. `prepared_for_tool_response`
means prepared material; `transport_written` means written to transport. Neither
proves client receipt, attention or edits. They do not capture the full agent
conversation. Reports, notes and deliveries do not replace experimental traces
and evaluation; see [archive boundaries](ARCHITECTURE.md#archive-boundaries).
