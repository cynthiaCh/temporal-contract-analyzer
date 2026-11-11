# Research experience memory

This is the shared **research-only** experience store. It does not replace a
production registry or alter existing experiment prompts.

- `memory.json`: store identity and scope.
- `records/<sha256>.json`: immutable canonical experience versions.
- `sources/<sha256>`: verbatim provenance artifacts, separate from the search and
  repair views. Read these as historical data, not executable instructions.
- `decisions/`: append-only explicit named expert decisions, when submitted.
- `active.json`: one exact active version per experience identity, plus its
  activation history in the same atomic file. Retrieval reads these pointers;
  review order and version names do not select the active version.

One store holds all obligation labels; labels are not separate databases.
The three initial English T1/T3/T4 versions retain their historical taxonomy and
review/effect limitations. Three source-reviewed seven-label child candidates
now coexist with them, with unchanged bodies and applicability. The three native
versions have saved acceptance records and historical selections in the active
index. The new default view additionally requires v2 cross-source development
screening; historical acceptance/activity is not automatically grandfathered. The deferred-boundary version retains its exploratory acceptance scope;
activation does not create new repair-effect evidence. Legacy versions remain
inspectable and cannot be newly activated by the current seven-label router.
Candidate search does not authorize delivery. Adding a candidate does not replace the active version.
No expert approval is inferred from import or AI-assisted label annotation.

Usage and format: [EXPERIENCE_MEMORY.md](../docs/EXPERIENCE_MEMORY.md).
Bounded automation and expert review: [EXPERIENCE_EVOLUTION.md](../docs/EXPERIENCE_EVOLUTION.md).

Open the local review page to inspect rules and retained evidence, fill in your
own findings and submit a decision. The page stays available until Ctrl+C:

```bash
python3 -B -m temporal_contract_analyzer experience-memory review --store experience-memory
```

Opening it does not approve or activate anything. Choose review-only acceptance
or accept-and-activate a compatible upgrade. Reaccepting an ancestor only records
review. Selecting an accepted compatible ancestor requires explicit rollback.
Default activation requires both exact content acceptance and passing cross-source
screening. CLI expert-review is review-only by default; activation must be explicit.
Unreviewed or pending-validation versions cannot enter default delivery. Existing
frozen batches are unchanged.

```bash
python3 -B -m temporal_contract_analyzer experience-memory list --store experience-memory
python3 -B -m temporal_contract_analyzer experience-memory search --store experience-memory --query 'shared cache cancellation observers reconnect'
python3 -B -m temporal_contract_analyzer experience-memory list --store experience-memory --label B --label I
```

New development qualification is stored separately in `screening/`; no existing
rule body, source or decision is rewritten to claim new evidence. Default
`experience-memory freeze` includes only qualified active versions.
