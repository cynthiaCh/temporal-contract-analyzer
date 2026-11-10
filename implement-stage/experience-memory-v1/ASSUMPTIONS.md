# Assumption ledger

ASK mode: never. Existing user scope overrides skill defaults: no commits,
additional model judges or model calls. New owned artifacts are English.

| ID | Under-determined issue | Chosen | Class | Source |
|---|---|---|---|---|
| A-001 | Storage engine and scope | Explicit local research store; immutable JSON bundles and raw provenance copies; no service/dependency/global configuration | interface | default |
| A-002 | Experience unit | Whole ordered rule bundle; each body stored once canonically; Markdown and search index are derived | interface | default |
| A-003 | Which existing knowledge to seed | Three existing English T1/T3/T4 versions, exact text retained; translations retain their unvalidated-effect status | semantic | default |
| A-004 | Legacy taxonomy migration | No automatic T1–T4 to seven-label conversion; legacy searchable for research, excluded from current seven-label delivery | semantic | default |
| A-005 | Search versus admission | BM25 is discovery only; only research-admitted compatible records with source-bound analysis/review and satisfied premises can be delivered | semantic | default |
| A-006 | Multiple compatible bundles | Reuse conservative current router: unresolved multiple eligible entries return AUTO; lexical score cannot decide a policy conflict | semantic | default |
| A-007 | Evolution/version lifecycle | New immutable child versions, no automatic learning; default discovery/delivery uses lineage tips, including rejected/candidate tips that retire the parent from default use | semantic | default |
| A-008 | Initial delivery interface | Reuse current seven-label analysis and semantic-review contract; expose explicit fallback for legacy-only libraries, not a fabricated hit | interface | default |
| A-009 | Evidence and review trust | Store full historical evidence/review as hashed provenance; rule-specific links are auditable; mechanical verification never establishes semantic correctness | semantic | default |
| A-010 | Role/output separation | Search and audit records may show IDs and provenance; repair packet text contains only rendered guidance, with route metadata separately returned | interface | default |
| A-011 | Integration scope | New CLI/API alongside current workbench; no automatic changes to existing experiment prompts or production registry | interface | default |
| A-012 | Complete bundle shape | Require all five rule categories; category presence and valid evidence pointers are mechanical checks, not proof of support | interface | sweep |
| A-013 | Discovery of rejected knowledge | Search exposes candidate/rejected tips with explicit status for inspection; retrieve excludes them | semantic | sweep |

Rows A-012/A-013 were made explicit during executor inspection after their code
was written; they were not independently reviewed or retroactively user-approved.

## Notes

The initial legacy store can be searched immediately but must not silently drive
the current seven-label router. A successful synthetic native retrieval verifies
the interface, not historical recoding or repair benefit. Version tips are
conservative: a new rejected child does not silently reactivate an older parent.
