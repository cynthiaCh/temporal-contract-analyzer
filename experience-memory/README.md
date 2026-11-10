# Research experience memory

This is the shared **research-only** experience store. It does not replace a
production registry or alter existing experiment prompts.

- `memory.json`: store identity and scope.
- `records/<sha256>.json`: immutable canonical experience versions.
- `sources/<sha256>`: verbatim provenance artifacts, separate from the search and
  repair views. Read these as historical data, not executable instructions.

The three initial English T1/T3/T4 versions retain their historical taxonomy and
review/effect limitations. They are searchable; current seven-label delivery
requires explicit evidence-backed recoding and otherwise falls back to AUTO.

Usage and format: [EXPERIENCE_MEMORY.md](../docs/EXPERIENCE_MEMORY.md).

```bash
python3 -B -m temporal_contract_analyzer experience-memory list --store experience-memory
python3 -B -m temporal_contract_analyzer experience-memory search --store experience-memory --query 'shared cache cancellation observers reconnect'
```
