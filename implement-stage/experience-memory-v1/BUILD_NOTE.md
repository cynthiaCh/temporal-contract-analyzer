# Build note

| Rung | Feature | Acceptance command | Tier | Status |
|---|---|---|---|---|
| F0 | CLI initialize/list spine | `python3 -B -m temporal_contract_analyzer experience-memory list --store experience-memory` | MUST | passed |
| F1 | Structured immutable storage, provenance, deterministic rendering | `python3 -B -m unittest discover -s tests -p 'test_experience_memory.py'` | MUST | passed |
| F2 | Lexical discovery and current source-bound delivery | `python3 -B -m unittest discover -s tests -p 'test_experience_memory.py'` | MUST | passed |
| F3 | Exact historical import, docs and regression checks | `python3 -B -m unittest discover -s tests -p 'test_experience_memory.py'` | MUST | passed |

## Run record

F0 ran first: init exited 0 and created `experience-memory/memory.json`; list
exited 0 with an empty list before storage/retrieval features were implemented.
F1's initial five storage tests passed. F2 expanded the accumulated suite to 13,
all passing. F3 expanded it to 17, all passing. Existing taxonomy/routing tests:
14/14 passing. First acceptance runs for each rung passed; no live stubs remain.

Historical seed import: 3 exact bodies, 19 rules, original applicability and
source bytes unchanged. `IMPORT.json` records the source hashes and conversions.
Three English discovery queries produced plausible lexical rankings; this is a
smoke check, not a labeled retrieval or repair-effect evaluation.

The optional existing workbench suite ran 13 tests with 6 failures. Extracting
the unmodified HEAD package and test into a temporary directory reproduced the
same six failures. Original scoring cannot find a Python meeting its minimum
version; both default Python paths report 3.8.10. No evaluator/runtime changes
were made. Raw current/baseline logs and comparison are retained in this folder.

A one-off validation-log collector initially used `str.removesuffix`, unavailable
under Python 3.8. It was corrected to slicing before logs were collected. This
was preparation tooling, not a model session or behavior score.

## Deferred

Evidence-backed legacy recoding, learned ranking, embeddings/vector service,
automatic prompt evolution, workbench integration and paid repair evaluation.

## Blockers

No blocker for the completed offline library. Legacy experience is not directly
deliverable through the current seven-label interface without explicit new
recoding. The existing workbench's runtime requirement remains a separate blocker
to its full regression suite; the same failure is present at the base commit.

## Review assurance

No additional model judge will be called. The skill's fresh-model assumption
sweep is not executed under the session's no-extra-model scope. An executor-only
inspection and deterministic checks are labeled accordingly, not independent
approval. The executor inspection identified two interface/semantic choices not
previously explicit in the ledger (A-012/A-013); both are now recorded. This does
not substitute for a fresh independent sweep or establish method effectiveness.
