# Analysis-driven context enrichment

Target: connect archived temporal findings to deterministic source-definition enrichment and expose it through CLI, MCP and the report center.

Inputs: a verified archived report and its source snapshot; optional finding ID, explicit aliases, depth and code-character budget.

Outputs: separate `temporal-context-1` JSON/Markdown containing seeds, definitions, reasons, unresolved items, usage, source binding and generator identity. Existing scan reports and frozen layers remain unchanged.

Base commit: dc77e779ab9bc96dd28754e71ad30886ba9ee359.

Success command: `/usr/bin/python3 -m unittest discover -s tests -p 'test_context_enrichment.py'` plus existing suite.

Scope: JS/TS and inline Vue script ASTs using installed Babel/Vue parsers. Resolve local lexical definitions and static local named/default imports; record unsupported or unavailable relationships. No external helper runtime dependency, candidate execution, build-config loading, embeddings, natural-language retrieval, automated repair or self-evolution. Python seeds remain readable with an explicit enrichment gap.
