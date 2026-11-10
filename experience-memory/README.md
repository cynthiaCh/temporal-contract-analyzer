# Research experience memory

This is the shared **research-only** experience store. It does not replace a
production registry or alter existing experiment prompts.

- `memory.json`: store identity and scope.
- `records/<sha256>.json`: immutable canonical experience versions.
- `sources/<sha256>`: verbatim provenance artifacts, separate from the search and
  repair views. Read these as historical data, not executable instructions.
- `decisions/`: append-only explicit named expert decisions, when submitted.
  Only accepted versions participate in the active delivery view.

One store holds all obligation labels; labels are not separate databases.
The three initial English T1/T3/T4 versions retain their historical taxonomy and
review/effect limitations. Three source-reviewed seven-label child candidates
now coexist with them, with unchanged bodies and applicability. They have not
received expert activation or new behavior replay. Candidate search does not
authorize delivery. Adding a candidate does not replace the active version.
No expert approval is inferred from import or AI-assisted label annotation.

Usage and format: [EXPERIENCE_MEMORY.md](../docs/EXPERIENCE_MEMORY.md).
Bounded automation and expert review: [EXPERIENCE_EVOLUTION.md](../docs/EXPERIENCE_EVOLUTION.md).

```bash
python3 -B -m temporal_contract_analyzer experience-memory list --store experience-memory
python3 -B -m temporal_contract_analyzer experience-memory search --store experience-memory --query 'shared cache cancellation observers reconnect'
python3 -B -m temporal_contract_analyzer experience-memory list --store experience-memory --label B --label I
```
