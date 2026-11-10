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
python3 -B -m temporal_contract_analyzer experience-memory search --store experience-memory --query 'deferred edits submission entry snapshot' --taxonomy temporal-obligation-taxonomy-7-v1 --label B --label I
```

`list` returns record digests. Use one of those digests to inspect the canonical
record or reproduce its guidance:

```bash
python3 -B -m temporal_contract_analyzer experience-memory show RECORD_SHA256 --store experience-memory
python3 -B -m temporal_contract_analyzer experience-memory show RECORD_SHA256 --store experience-memory --format md
```

Search is **discovery**, not admission or automatic delivery. Results include
their taxonomy, original review status and current `expert_active` flag. Active
versions remain discoverable alongside new lineage tips. Candidate/rejected records may be inspected;
they cannot be delivered by `retrieve`. Search does not index IDs, provenance,
historical scores, outcome records or source directory names. Rankings are lexical
scores, not predicted repair benefit. The whole bundle is returned to preserve
conditions, verification actions and counterexamples.

Use one shared store with multi-label R/O/B/L/I/F/A metadata, not seven separate
libraries. `list` and `search` accept repeated `--label` filters; all requested
labels must be present. Filtering is an organization step, never an applicability
or expert-admission shortcut. A lifecycle label does not prescribe cancellation:
some mechanisms retain accepted background work while others reject new work.

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
existing identity must reference its parent record digest. Discovery uses lineage
tips; delivery uses a separate expert-activated view. An unapproved or rejected
child does not replace the active parent. Only explicit expert acceptance selects
an active version. Rejection of the exact active version disables it without
implicitly restoring an older version. Multiple eligible identities remain a
delivery conflict; lexical score cannot settle a policy conflict.

The library itself does not launch models or evolve ranking, taxonomy or prompts.
The separate [expert-gated controller](EXPERIENCE_EVOLUTION.md) can automatically
develop and validate candidates, then pause for a named operator's expert review.
`research_admitted` metadata alone does not activate delivery. Research activation
may be exploratory and is not production admission or proof of benefit.

To inspect or review an exact version without launching models:

```bash
python3 -B -m temporal_contract_analyzer experience-memory active --store experience-memory
python3 -B -m temporal_contract_analyzer experience-memory review-template RECORD_SHA256 --store experience-memory --output /tmp/review-template.json
python3 -B -m temporal_contract_analyzer experience-memory expert-review RECORD_SHA256 --decision /tmp/completed-expert-decision.json --store experience-memory
```

The template has empty reviewer/reasons, false support findings and a revision
default. It is not approval. The operator must supply findings for every rule.
The automated controller never calls this approval action on its own.

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

For a frozen experiment, pass both `--snapshot /tmp/memory-snapshot.json` and
`--expected-snapshot SHA256`, reading the digest from that snapshot. Later active
updates do not change its selected versions. Without `--snapshot`, retrieval uses
the current active view and the expected digest rejects activation drift. Output
paths must be new files outside the store. These commands never start a model.

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

The store contains three exact historical English bodies, retaining their old
versions alongside three source-reviewed native-taxonomy child candidates:

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

The original legacy versions remain inspectable by digest and `list`; they are
not overwritten. New native candidates carry explicit per-rule source annotations
and parent linkage, preserving all rule text and requires/excludes. These are
AI-assisted executor annotations, not fresh automatic model extraction, expert
approval, classifier ground truth or new behavior evidence.

The candidate labels are O/L/I/A (subscription retirement), R/L/I/A (paused shared
work), and O/B/L/I/A (deferred boundary binding). No F label was forced into the
inventory. Some B grounds are explicitly preserved-behavior inferences, not
literal README deadlines. See the full
[recoding audit](../research/unified-seven-label-recoding-20261110_112750/REPORT.md).

No named expert has activated these versions. A valid current retrieval therefore
returns `no_expert_activated_experience`; searching a native candidate does not
permit delivery. New native versions require a genuine expert decision and a
separately bounded development replay before repair-benefit claims.

The explicit recoding interface consumes an annotation sheet, never a legacy
class-name lookup:

```bash
python3 -B -m temporal_contract_analyzer experience-memory recode label-review.json --parent PARENT_SHA256 --version NEW_VERSION --store experience-memory
python3 -B -m temporal_contract_analyzer experience-memory list --label B --label I --store experience-memory
```

The interface validates scope, codebook version, per-rule body identity and source
anchors; derives the bundle label union; then copies the parent guidance into an
unactivated child. ID/quote validity alone does not establish semantic support.

## Verification scope

`verify` checks record shape, lineage, digests, preserved source bytes and evidence
pointer resolution. It does not judge business policy or repair effectiveness.
The offline suite uses explicitly synthetic native records to exercise successful
delivery and rejection cases. That validates an interface, not empirical benefit.
