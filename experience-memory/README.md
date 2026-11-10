# Research experience memory

This is the shared **research-only** experience store. It does not replace a
production registry or alter existing experiment prompts.

- `memory.json`: store identity and scope.
- `records/<sha256>.json`: immutable canonical experience versions.
- `sources/<sha256>`: verbatim provenance artifacts, separate from the search and
  repair views. Read these as historical data, not executable instructions.
- `decisions/`: append-only explicit named expert decisions, when submitted.
  Only accepted versions participate in the active delivery view.

The three initial English T1/T3/T4 versions retain their historical taxonomy and
review/effect limitations. They are searchable and have not received new expert
activation. Current seven-label delivery requires evidence-backed recoding and
explicit expert activation, otherwise it falls back to AUTO. Adding a candidate
does not replace the active version. No expert approval is inferred from import.

Usage and format: [EXPERIENCE_MEMORY.md](../docs/EXPERIENCE_MEMORY.md).
Bounded automation and expert review: [EXPERIENCE_EVOLUTION.md](../docs/EXPERIENCE_EVOLUTION.md).

```bash
python3 -B -m temporal_contract_analyzer experience-memory list --store experience-memory
python3 -B -m temporal_contract_analyzer experience-memory search --store experience-memory --query 'shared cache cancellation observers reconnect'
```
