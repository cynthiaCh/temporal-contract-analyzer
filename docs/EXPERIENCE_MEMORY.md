# Unified research experience library

The local store is [`experience-memory/`](../experience-memory/README.md).
This feature stores and retrieves experience without models, network calls,
dependencies, experiment execution or production-library updates.

It has three separate outputs:

1. An immutable structured JSON bundle, with one canonical body per rule.
2. A derived BM25 discovery result, indexed from rule text and mechanism predicates.
3. A source-checked optional repair body, with route/provenance kept separately.

The existing `rag.py` retrieves the **current candidate's source**. This library
retrieves **cross-case research experience**. They are separate corpora and APIs.

## Inspect and search the existing library

Run from the repository root:

```bash
python3 -B -m temporal_contract_analyzer experience-memory list --store experience-memory
python3 -B -m temporal_contract_analyzer experience-memory verify --store experience-memory
python3 -B -m temporal_contract_analyzer experience-memory search --store experience-memory --query 'shared cache observers cancellation signal reconnect'
python3 -B -m temporal_contract_analyzer experience-memory search --store experience-memory --query 'deferred edits submission entry snapshot' --taxonomy legacy-toolflow-t1-t4-v1
```

`list` returns record digests. Use one of those digests to inspect the canonical
record or reproduce its guidance:

```bash
python3 -B -m temporal_contract_analyzer experience-memory show RECORD_SHA256 --store experience-memory
python3 -B -m temporal_contract_analyzer experience-memory show RECORD_SHA256 --store experience-memory --format md
```

Search is **discovery**, not admission or automatic delivery. Results include
their taxonomy and review status. Candidate/rejected records may be inspected;
they cannot be delivered by `retrieve`. Search does not index IDs, provenance,
historical scores, outcome records or source directory names. Rankings are lexical
scores, not predicted repair benefit. The whole bundle is returned to preserve
conditions, verification actions and counterexamples.

## Canonical format

Schema version: `experience-bundle-v1`. Exact fields:

| Field | Meaning |
|---|---|
| `id`, `version`, `parent_sha256` | Stable experience identity, immutable version, explicit parent |
| `taxonomy_version`, `labels` | Compatible taxonomy and labels; no silent conversion |
| `requires`, `excludes` | Mechanism predicate keys, never evidence IDs or explanatory prose |
| `rules` | Ordered `{id, category, body}` objects; R01 onward, one body each |
| `review` | `{status, kind, source_sha256, limitations}`; explicit research admission or candidate/rejection |
| `audit.sources` | Original paths and hashes; exact bytes copied into `sources/` |
| `audit.rule_links` | `{rule_id, source_sha256, pointer}` links into raw evidence/model/review objects |
| `audit.notes`, `audit.outcome_refs` | Lineage/unknowns and outcome pointers, outside runtime search and repair views |
| `body_sha256`, `sha256` | Derived body and record digests |

Rule categories are `applicability`, `event_relation`, `preservation`, `exclusion`
and `verification`; a complete v1 bundle retains all five categories. Category
presence and pointer existence do not establish semantic support.

Review status is `candidate`, `research_admitted` or `rejected`. Review kind records
`ai_assisted_historical`, `ai_assisted`, `human` or `synthetic`. The software does
not turn any of these into independent human approval. Synthetic test records are
not seed experiences or effectiveness evidence.

Evidence pointers use JSON Pointer syntax. The empty pointer references the
whole original artifact, including a non-JSON document. Rule-specific evidence
links can point to original rule objects that preserve support, condition,
counterevidence and causal-status fields. Evidence management IDs stay in audit
records. Semantically important runtime caveats must also be present in rule text;
storing a caveat only in an audit note does not deliver it to the repair agent.

## Add and version knowledge

`add` accepts the exact canonical fields without the two derived digests, or an
already sealed record whose digests must match. Supply original source files with
`--source`; their contents must match the declared hashes. Original sources are
preserved verbatim, not converted into a second canonical rule body.

```bash
python3 -B -m temporal_contract_analyzer experience-memory init --store /tmp/new-research-memory
python3 -B -m temporal_contract_analyzer experience-memory add new-bundle.json --source evidence.json --source review.json --store /tmp/new-research-memory
```

Existing `(id, version)` records cannot be overwritten. A new version of an
existing identity must reference its parent record digest. Default discovery and
delivery use lineage tips. A candidate or rejected child conservatively retires
its parent from default use; it does not silently reactivate the parent. Branches
are retained; multiple eligible tips remain a delivery conflict.

There is no automatic reflection, learning, ranking update, taxonomy recoding or
class-prompt evolution. New knowledge is prepared and reviewed under a separate
bounded development protocol, then explicitly added as a version. Research
admission may be exploratory and is not production admission or proof of benefit.

## Source-bound delivery for current seven-label analyses

`retrieve` accepts only an explicit JSON object containing `task`, `sources`,
`analysis` and optional `review`, using the existing seven-label analysis/review
contracts documented in [CONTRACT_TAXONOMY.md](CONTRACT_TAXONOMY.md). `sources` maps
candidate-relative paths to actual text. It does not accept case/cluster identity,
expected labels, historical scores, evaluator data or reference patches.

```bash
python3 -B -m temporal_contract_analyzer experience-memory freeze --store experience-memory --output /tmp/memory-snapshot.json
python3 -B -m temporal_contract_analyzer experience-memory retrieve visible-input.json --store experience-memory --output /tmp/experience-delivery.json
```

For a frozen experiment, read `sha256` from the snapshot and pass it as
`--expected-snapshot SHA256`. Store changes then reject retrieval. Output paths
must be new files outside the store. No command starts a model or repairs code.

The router checks source citations, source-bound semantic review, compatible
labels, known required premises and explicitly contradicted exclusions. Unknown
premises/exclusions fail closed. Multiple eligible bundles fall back to AUTO;
the lexical score does not resolve a policy conflict. Selection is by the chosen
entry digest, not array position. Source-bound review may be AI-assisted; no new
human-approval requirement is introduced.

The result separates `route`, `selected_memory_record`, `memory_snapshot` and
`experience_text`. Pass **only `experience_text`** as optional repair guidance.
If it is null, retain AUTO; do not append the audit result. A/B common material
must remain identical except for the selected text. Existing runners do not
automatically consume this new library; integration is a separate intervention.

## Initial inventory and explicit limitation

The store contains three exact historical English bodies:

- `subscription-retirement`: T1 translation, seven rules; English wording not
  directly effect-validated.
- `paused-shared-work`: T4 translation, six rules; English wording not directly
  effect-validated.
- `deferred-boundary-binding`: T3, six rules, from the recent development batch;
  its original stop and missing test maintenance remain unchanged.

All remain in `legacy-toolflow-t1-t4-v1`. Their reviews, source objects, translation
lineage and available evidence/outcomes are preserved as hashed audit copies.
Initial provenance is recorded in
[`IMPORT.json`](../implement-stage/experience-memory-v1/IMPORT.json).

They are searchable now. **They are not relabeled into the current seven-class
taxonomy and are not automatically delivered by its router.** A valid current
query with only these entries returns an explicit recoding-needed fallback.
Evidence-backed recoding must create reviewed new versions; it is not a class-name
lookup or an extra hidden classification call. No such recoding is performed here.

## Verification scope

`verify` checks record shape, lineage, digests, preserved source bytes and evidence
pointer resolution. It does not judge business policy or repair effectiveness.
The offline suite uses explicitly synthetic native records to exercise successful
delivery and rejection cases. That validates an interface, not empirical benefit.
