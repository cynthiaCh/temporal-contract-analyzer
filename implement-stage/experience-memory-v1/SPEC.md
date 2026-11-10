# Unified research experience memory

Build an offline, local, dependency-free experience library. Base commit:
`ed90be1a98f477b2ad2ea16decbe8d0e0ebbca6c`.

Inputs: versioned structured rule bundles, historical frozen registries and
candidate-visible task/source/analysis/review packets. Outputs: immutable JSON
records, content-addressed provenance copies, deterministic Markdown, lexical
search results and conservative source-bound retrieval packets.

Entry point: `python3 -B -m temporal_contract_analyzer experience-memory`.
Initial research store: `experience-memory/`. Existing production/workbench
libraries and historical experiments remain unchanged. No model calls, commits,
installation, automatic evolution, taxonomy recoding or experiment launches.

Historical T1/T3/T4 entries remain searchable under their original taxonomy.
Automatic repair delivery initially supports the existing seven-obligation
analysis/review interface; legacy entries require explicit evidence-backed
recoding in a new version before that interface can deliver them.

Success: `python3 -B -m unittest discover -s tests -p 'test_experience_memory.py'`.
