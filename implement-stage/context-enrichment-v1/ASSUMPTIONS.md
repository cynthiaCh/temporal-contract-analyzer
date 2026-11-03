# Assumption Ledger — context enrichment
<!-- ASK mode: never -->

| ID | Under-determined | Chosen | Class | Source |
|---|---|---|---|---|
| A-001 | Source of context | Only the verified report snapshot, including overlays; never current working-tree files | semantic | default |
| A-002 | Seed selection | All finding evidence ranges, or one explicit finding ID; merge overlapping/adjacent source ranges; no finding means empty seeds | semantic | default |
| A-003 | Meaning of enrichment | Syntactic candidate definitions, not proven dataflow, executed calls, complete dependencies or bug verdicts; unresolved always accompanies snippets | semantic | default |
| A-004 | First relationship types | Lexical definitions and static local named/default ESM imports in JS/TS/Vue; unsupported Python, namespace imports, reexports, external modules, dynamic dependencies are gaps | semantic | default |
| A-005 | Integration strategy | Reimplement helper's traversal/budget/provenance behavior on installed Babel/Vue ASTs; no vendored helper or absolute-path dependency | interface | default |
| A-006 | Interface and bounds | `reports context REPORT_ID` and `read_context`; finding_id optional; depth 0–5 default 1, code budget 1–100000 default 12000; aliases explicit JSON object; output schema temporal-context-1 | interface | default |
| A-007 | Budget and traversal | Seeds must fit or fail with actionable error; definitions added atomically in deterministic breadth-first order; merge overlaps, count code Unicode characters, record depth/budget omissions | semantic | default |
| A-008 | Experimental compatibility | Separate opt-in material; no changes to frozen B/C/D rendering or restricted MCP tool exposure; MCP context uses delivery receipts/pagination | semantic | default |
| A-009 | UI | Context action on selected report/finding with readable snippets and gaps; no automatic forwarding to agents | interface | default |
| A-010 | Module resolution | Explicit extensions must match snapshot paths exactly; extensionless resolution uses the fixed JS/TS/Vue/index candidate list, rejects multiple candidates, applies longest explicit alias prefix; no TS extension substitution or project resolver emulation | semantic | sweep |
| A-011 | Excerpt granularity and definition usage | Whole lines and whole variable/function/class declarations (including sibling declarators) may include unrelated references which are also traversed; counts merged snippets carrying reasons, including definitions already in seeds; not symbols or retrieval effectiveness | semantic | sweep |
| A-012 | Context seed size | Keep exact evidence line ranges rather than automatically including the enclosing function | semantic | default |
| A-013 | Context export location | JSON stdout by default; optional new-file output refuses overwrite and must be outside both the original candidate root and the report store's immutable runs tree | interface | sweep |
| A-014 | Delivery consistency | MCP caches four parameterized JSON materials per session with FIFO eviction; pagination requires identical generating options | interface | sweep |
| A-015 | Missing parser or unsupported file | Preserve seeds plus explicit gap instead of aborting context generation; retain original scan status; parser timeout 45 seconds; no findings skips parser | interface | sweep |
| A-016 | Unresolved inventory | Unbound names, parameter bindings and type-only references do not request definitions or individual gaps; unresolved covers recognized unsupported/omitted relationships only | semantic | sweep |
| A-017 | Vue boundary | Normal script and setup scopes stay separate; only normal script contributes exports; template/cross-block gap always recorded for selected Vue code; external template, custom blocks, external script or unsupported script language reject enrichment of the whole Vue file | semantic | sweep |
| A-018 | Existing launcher compatibility | Health advertises context_enrichment=snapshot-definitions-v1; Codex launcher upgrades an idle service missing either the experiment UI or context marker, and refuses to restart an active old service | interface | default |
