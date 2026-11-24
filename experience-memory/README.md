# Current experience library

`library/` is the only source for new training and testing runs. It contains
58 active experiences, each with an accepted English Abstract bound to its current
guidance. The 22 replaced entries and the legacy records, sources, workflow,
screening and training archives have been removed from this working tree.
Original historical material remains in Git history and external experiment logs.
Consolidation evidence in `library/evidence/` supports the current entries and is
not a retrieval library.

Open `launch-experience-review.command` to review guidance and Abstracts. Content
and Abstract acceptance are separate. New training candidates remain pending;
missing, rejected or outdated Abstracts cannot be used by a new experience run.
Human proposals without an Abstract remain editable drafts. There is no automatic
first-sentence or truncated-preview fallback.

```bash
python3 -B -m temporal_contract_analyzer experience-memory review --store experience-memory/library
python3 -B -m temporal_contract_analyzer experience-memory freeze --store experience-memory/library
```

New experiments use the current categorized library. Explicit subsets must contain
current accepted guidance and the matching accepted Abstracts. Historical snapshots
remain historical inputs; they cannot prepare a new experiment. Already prepared
protocols are not rewritten by library cleanup.

Local retrieval indexes the reviewed Abstract alone, recalls at most six candidates
with full guidance for applicability verification, and delivers at most three entries
within 8000 characters. Training can publish proposed corrections for review.
Testing and training-set replay use frozen experience and never update the library.

Keep the existing experiment configuration, case list, per-case outcomes and concise
summary. Keep bulky logs in the run directory. Record model, effort, concurrency,
repair budget and library version in those records; do not generate extra manifests.
