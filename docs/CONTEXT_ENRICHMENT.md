# Source context enrichment driven by analysis hints

The first implementation connects **archived analysis hints → definition enrichment → agent review material**.

It adopts the input locations, dependency expansion, depth/budget limits and provenance ideas of `rag-context-helper`. Definition lookup is implemented using the Babel/Vue parsers already installed in this repository, without depending on an external tool installation. Context is separate material: it does not change scan reports or frozen experimental layers such as B/C/D.

## Browser usage

Restart the local report center after updating:

The following commands run from this source checkout. The existing VSIX has not been rebuilt; its runtime staging script includes the new parser entry point, so a subsequent package build will include context enrichment.

```sh
/usr/bin/python3 -B -m temporal_contract_analyzer reports stop
/usr/bin/python3 -B -m temporal_contract_analyzer reports open
```

Create a project scan and select the report. Click **Expand related source** on a boundary review card, or open the **Source context** tab. Select one or all hints, expansion depth, source-character budget and optional path aliases. The page lists original evidence, supplemental definitions, provenance reasons and unresolved items. You can navigate to archived source or copy the complete material for an agent.

Generating browser material does not call a model or send it to an agent. MCP deliveries have separate delivery records.

## CLI

First scan and archive the same source:

```sh
/usr/bin/python3 -B -m temporal_contract_analyzer reports scan \
  examples/context-enrichment --project context-demo
```

Replace `REPORT_ID` with the returned report ID:

```sh
/usr/bin/python3 -B -m temporal_contract_analyzer reports context REPORT_ID \
  --depth 2 --max-chars 12000 --format md
```

Optional arguments:

- `--finding-id FINDING_ID`: use only evidence locations from this hint; defaults to all hints.
- `--aliases '{"@":"src","Constants":"src/constants"}'`: explicit path aliases relative to the snapshot root, using longest-prefix matching. No tsconfig, Webpack or Vite configuration is loaded.
- `--depth 0..5`: defaults to 1. Zero retains original evidence and records depth gaps for identifiable dependencies that are not expanded.
- `--max-chars 1..100000`: defaults to 12000. Counts Unicode characters in source text only, excluding explanatory text; this is not a token budget.
- `--format json|md`: defaults to JSON.
- `--output /outside/project/context.md`: write a new file; overwriting and writing inside the original candidate project are rejected.
- `--store PATH`, `--node PATH`: use the existing configuration mechanism.

Seed code exceeding the budget causes an explicit failure; select one hint or increase the budget. Supplemental definitions that exceed the budget are omitted in full and recorded as unresolved. Adjacent or overlapping ranges are merged, without counting source twice. A report without findings returns empty context rather than triggering a repository-wide search.

## MCP

Normal MCP sessions provide `read_context`:

```json
{
  "report_id": "REPORT_ID",
  "finding_id": "FINDING_ID",
  "depth": 2,
  "max_chars": 12000,
  "aliases": {"@": "src"},
  "offset": 0,
  "limit": 12000
}
```

Only `report_id` is required. `text` contains one page of context JSON. Follow `next_offset` to read every page before parsing the complete JSON. Keep the report, hint, depth, budget and aliases identical across pages. Responses use the same delivery records and transport receipts as reports/source; records do not establish that a model noticed or used the material. A session caches the four most recent parameter sets to avoid reparsing on every page.

Example agent instruction:

> After scanning the project, read the report with read_report, then retrieve supplemental source for relevant hints with read_context, following next_offset to completion. Review relations and guards using reasons and unresolved items, check differences between snapshot and workspace, then consider edits and tests.

Restricted experimental sessions using `reports mcp --report-id ... --layer ...` still expose only `read_report` for the selected layer, without context or additional source.

## Implementation and scope

- Locate report events through each finding's evidence IDs; seed context with original source lines rather than automatically expanding to the entire enclosing function.
- A separate `context.cjs` uses `@babel/parser` for JS/TS and `@vue/compiler-sfc` for inline scripts, emitting lexical bindings, reference locations and limited export definitions. The original scanner's AST output is unchanged.
- Recognizable function/block/loop/catch scopes account for parameter and declaration shadowing, ignoring ordinary property names, comments, strings and type references. This is not a complete JS/TS semantic parser.
- Supports same-file lexical definitions, static local named/default imports, function/variable/class declarations and limited export lists. Modules are resolved only within the archive manifest.
- Expansion uses deterministic breadth-first order. Multiple candidates for an extensionless import produce `ambiguous-module`; the project's actual resolution configuration is not guessed.
- Python and other unsupported languages retain original evidence and record unsupported definition enrichment. If the parser cannot start, seeds and parser gaps are still returned.
- Namespace imports, re-exports, CommonJS and dynamic imports are not expanded; identifiable gaps are recorded. Vue templates, cross-script bindings and framework scheduling are not modeled.
- Object-member dispatch, runtime reassignment, complete callers, control flow, data flow and state-write sets are not inferred. Unrecognized global names are not individually flagged; an empty `unresolved` list does not establish complete dependencies.

## Output and interpretation

`temporal-context-1` contains `report_id`, `input_sha256`, `scan_status`, `finding_ids`, `aliases`, `parser`, `generator`, `limits`, `snippets`, `unresolved`, `usage`, `qualification` and `limitations`.

`snippets` provides `file/start_line/end_line/code/kind/reasons`. `kind=seed` means the merged range contains original evidence; the same snippet may also contain supplemental definitions. `usage.seeds` counts merged snippets containing seeds. `usage.definitions` counts snippets with definition-relation evidence, including definitions already inside seeds; it is neither a symbol count nor a retrieval success rate.

Context comes only from verified scan snapshots, including archived editor overlays, without reading current project files. Dependencies outside the snapshot remain gaps. Single-file scans do not automatically read adjacent modules; create a report covering the dependency directory. The generator version and digest are recorded separately; changing the generator or options creates a new context condition.

Tests validate functional paths, snapshot isolation, lexical shadowing, budgets and delivery behavior. Retrieval quality and agent repair benefit have not been established.
