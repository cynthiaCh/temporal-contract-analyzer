# Unified research experience library

The current categorized library is [`experience-memory/library/`](../experience-memory/README.md).
Testing business selection and construction routing are described in [WORKFLOW.md](WORKFLOW.md);
the bundle/discovery APIs below do not define a separate execution workflow.
This feature stores and retrieves experience without models, network calls,
dependencies, experiment execution or production-library updates.

It has three separate outputs:

1. An immutable structured JSON bundle, with one canonical body per rule.
2. A derived BM25 discovery result, indexed from rule text and mechanism predicates.
3. A source-checked optional repair body, with route/provenance kept separately.

`context.py` retrieves the **current candidate's source** from archived AST
findings and definitions. This library retrieves **cross-case research
experience**. They are separate corpora and APIs.

## Inspect and search the existing library

On macOS, double-click [launch-experience-review.command](../launch-experience-review.command)
in the repository root. It opens the local review queue in your browser and
works regardless of the terminal's starting directory. The queue shows unreviewed
and reviewed counts; inspect each record’s AI state before human content review.
Keep its terminal open while reviewing, then press Ctrl+C to stop the service.
Open the store actually used by the worker. Legacy/unbound candidates from
isolated stores may be submitted as described below; a v3 execution-bound record
remains in its store so that review and worker authorization cannot diverge.

For a local visual review, run from the repository root:

```bash
python3 -B -m temporal_contract_analyzer experience-memory review --store experience-memory
```

The command opens a loopback-only page and keeps its server running until Ctrl+C.
The review interface uses English for demonstration and international use.
Mechanism descriptions are display translations; the versioned taxonomy,
experience bodies, source quotations and operator-authored decisions are not
rewritten or reapproved by this UI language change.
Use `--no-browser` to print the address without opening a browser, or supply an
exact record digest after `review` to open that version. The page lists immutable
records, shows rules and prerequisites, and reads only the selected record's
retained `sources/` evidence. It does not depend on historical research paths.

The list groups records into unreviewed and reviewed entries, with counts and
filters for all/unreviewed/reviewed. Unreviewed includes AI-pending or blocked proposals;
it does not mean eligible for human acceptance. A version is reviewed only when an explicit
operator decision exists for that exact digest; historical AI admission does not
count, and a new child does not become reviewed automatically. An explicit
incremental decision may reference unchanged accepted parent findings. Reviewed entries
show the latest decision, reviewer and time, independently of whether they are
currently active. Opening one displays saved findings; an explicit re-review
button opens a new blank form. Submission refreshes the list and saved findings.

Choose findings for affected rules, optionally write review reasons, enter your
actual name and overall decision, then explicitly confirm the exact changes,
their interactions and any displayed parent findings. Full review remains an
option. Clicking submit records the decision through the existing expert
interface. Choose review-only acceptance or acceptance with authorization to
select the accepted content for preferred retrieval. An authorized v3 worker
continues validation and performs the guarded enable; the page cannot dispatch
models. Legacy immediate activation remains a maintenance option. Reaccepting
an older version does not roll back retrieval. Explicit
rollback has its own action; the page shows the active version separately from
the latest review. Revision/rejection are recorded without accepting it. Opening the page never creates approval or calls
a model. The result displays the decision directory and activation status.

CLI commands with `--output` write to the named new file and now print its saved
path to stderr. They do not submit a review. A generated review template remains
unapproved until the operator completes and explicitly submits it.

## Readable titles and honest candidate states

`STORE/display.json` stores optional display-only titles using one mechanism for
all identities. Its format is `{"schema_version":"experience-display-v1",
"titles":{"EXPERIENCE_ID":"Readable title"}}`. These titles never enter repair
prompts or routing. They change neither immutable records nor their SHA, lineage,
AI findings, human decisions or active pointers. An unregistered identity falls
back to a labeled excerpt of its first rule; no model call is made to name it.
The browser has no hard-coded list of known experience IDs.

List and detail views separate title, stable experience identity, version/digest,
source batch (when recorded) and parent. A parentless model proposal does not
establish novelty. “Latest record” describes lineage recency, not qualification.
AI-pending, running, incomplete and failed states are explicit. New human-only records say “Awaiting human content review · AI check not performed”.
In legacy audit-policy workflows only AI-passed records await human content review; old records with
no AI receipt say “AI check not recorded”. Existing human decisions remain visible.
Rule-by-rule novelty comparisons appear beside the complete AI result, including
old-version/rule references, covered obligations and specific uncovered increments.

## Incremental content review

The page compares a candidate with its direct parent and shows changed text
before/after, parent evidence, and any changed prerequisites. If only R02 changed,
the parent has a current named acceptance, and the other six rules retain their
text/category, linked evidence and shared applicability, only R02 needs a new
finding. The six parent findings appear in a collapsed section with their actual
reviewer, decision and source version. They are not six new approvals by the
current reviewer. Opening the page or generating a template submits nothing.

The backend rechecks eligibility under the existing decision lock. It references
the exact latest parent acceptance, not the parent's activity or AI review flag.
Changed rule evidence requires a new finding for that rule. Changed taxonomy,
labels, requires/excludes, applicability/exclusion rules or their evidence, and
global outcome evidence require full review. Missing/revoked parent acceptance
also prevents inheritance. A stale parent-decision reference is rejected before
writing a decision. Changing the requested review scope requires full review.

Structural equality does not prove semantic independence. The reviewer must
check interactions with retained rules and can choose **Review R03 explicitly**
for an otherwise unchanged rule, or **Review all rules instead**. Switching the
granularity preserves the current draft. Re-reviewing an already reviewed exact
version opens a full form; it does not silently override its existing findings.

CLI `review-template` uses the same incremental plan by default; `--full` emits
all explicit rule findings. Incremental input contains only new findings and
`inherit_from` with the exact parent-version and parent-decision IDs. The backend
resolves every omitted eligible finding itself. A v2 decision stores all resolved
findings with per-rule `inherited_from` references (parent version, decision and
rule), so history and frozen snapshots can verify the actual provenance. Existing
v1 decisions are unchanged. A v2 snapshot requires its retained audited decision
history. New-version acceptance still needs the current operator's explicit
decision, and neither inheritance nor content acceptance bypasses effect-based
activation requirements.

## V4 learning and historical origins

V4 is the only execution protocol. Success candidates and real-human failure
summaries enter a temporary candidate pool. Materialize them with `tempoevo
publish-candidate`, then use the existing named content review and immutable
editing interface. Acceptance makes the exact record eligible for frozen retrieval;
no old worker, AI audit or post-review repair stage runs from the review page.

Historical origin metadata, grants and evidence remain readable, but origin batches
are read-only and cannot be canceled, resumed, recovered or executed by this package.
Use `history status/report --root BATCH` to inspect their retained outputs.
Editing an experience creates a new version and requires its own acceptance.

## Submit a candidate from an isolated development store

A candidate record, a named content-review decision, and an active retrieval
version are separate artifacts. A pending effect screen does not prohibit
record submission or content review. AI-assisted admission is not a named expert
decision. The v3 controller records the candidate before its AI check; neither
record creation nor a passed AI check accepts or enables content.

When a run uses an isolated store, its record is not automatically present in
the repository's review page. Submit that exact version explicitly:

```sh
python3 -B -m temporal_contract_analyzer experience-memory submit CANDIDATE_SHA256 --from-store /path/to/run/memory --store experience-memory
python3 -B -m temporal_contract_analyzer experience-memory review CANDIDATE_SHA256 --store experience-memory
```

Both stores must already exist. Submission retains the immutable candidate and
any needed ancestors, source blobs, original screening (including pending or
blocked findings), and matching development-source exposure. It does not copy
expert decisions or active pointers, activate the candidate, launch models, or
change the originating experiment. Repeated submission is idempotent; conflicting
versions or screening evidence are rejected before publishing records. Evidence
files are published completely before the candidate becomes visible.

This submission path is for legacy/unbound candidates. A v3 execution-bound
record cannot be copied into a different review store with an orphaned job or
grant. Review it in the originating store. To use a legacy/unbound record in a
new authorized v3 batch, set candidate_sha256 to its exact version in that store;
the new batch obtains its own common checks, starts and validation evidence.

The development report's `candidate_handoff` names the actual record store and
provides review/submission arguments. A named reviewer can record a review-only
acceptance while effect evidence is pending. Enable still requires
both content acceptance and qualifying development evidence. Submitting into a
Git-tracked review store creates new Git-visible data; keeping an isolated store
outside the repository does not.

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
child does not replace the active parent. `active.json` explicitly maps each
identity to one accepted current-taxonomy digest; its activation history is
updated atomically with the pointers. Reads do not replay review order to choose
versions. Rejection of the exact active version disables it without
implicitly restoring an older version. Multiple eligible identities are delivered together, capped at five by default. Matching is based on labels and mechanism premises, not a numerical rank.

The library itself does not launch models or evolve ranking, taxonomy or prompts.
The [controller](WORKFLOW.md) reflects on accepted construction trajectories or
stages expert failure summaries as candidates. Named acceptance makes exact
versions eligible for later approved snapshots. Screening is optional evidence,
not a prerequisite for delivery. Testing cannot produce or approve experience.

To inspect or review an exact version without launching models:

```bash
python3 -B -m temporal_contract_analyzer experience-memory active --store experience-memory
python3 -B -m temporal_contract_analyzer experience-memory review-template RECORD_SHA256 --store experience-memory --output review-drafts/review.json
# Complete the generated review-drafts/review.json before submitting it.
python3 -B -m temporal_contract_analyzer experience-memory expert-review RECORD_SHA256 --decision review-drafts/review.json --store experience-memory
```

The template has empty reviewer/reasons, false explicit support findings and a
revision default. It is not approval. The operator supplies the required new
findings and explicitly confirms any eligible referenced parent findings.
Overall and per-rule reasons are optional and may remain empty; the actual
reviewer, explicit decision and a resolved finding for every rule remain required.
The automated controller never calls this approval action on its own.

### Development qualification is separate from historical activity

The default delivery view includes every record whose latest named review is
`accept`, including historical taxonomies, review-only acceptances, and approved
revisions without an active pointer. Protocol versions and cross-source effect
screening no longer gate retrieval or activation. Rejected, revision-requested,
unreviewed, and explicitly withdrawn records stay outside the current pool.
Frozen historical experiments retain their original contents.

Task evidence must satisfy each record's reviewed prerequisites and exclusions.
Historical taxonomy labels remain unchanged; those records match by mechanism
predicates. Within one experience identity, retrieval prefers the most recently
reviewed applicable revision; an inapplicable child cannot hide an approved parent.
`default_eligible` reports approval eligibility independently of the preferred
selection in `active.json`.

Screening records remain optional, immutable evidence for studying effectiveness.
They are visible in the review page and do not control delivery.

V3 screens live under workflow/screens/CANDIDATE_SHA/VALIDATION_JOB.json with
exact candidate/job bindings. Old or parent screens cannot qualify a bound v3
version. The latest named decision, immutable evidence and active pointer remain
separate from these workflow projections.

New v2 bundles allow one or more evidence-backed rules rather than requiring all
five category headings. Applicability remains structured in requires/excludes;
necessary preservation/boundary/verification meaning must remain in the guidance.
A valid shape or category label is not a semantic approval. The single model rule
body is still rendered deterministically; metadata and evidence IDs are not
silently expanded into invented business rules. See the complete
[development and evaluation protocol](WORKFLOW.md).

### Explicit active versions and migration

New stores start with an empty `active.json`. Existing stores without that file
require an explicit mapping migration; reads never create or guess one. Supply
an `id -> exact SHA256` JSON object containing only already accepted native
versions. Migration retains all records, sources and decisions and identifies
the actual technical actor, without inventing a new expert review:

```bash
python3 -B -m temporal_contract_analyzer experience-memory migrate-active selected-versions.json --actor OPERATOR --reason 'Explicit version migration' --store experience-memory
```

The reviewed native versions in this repository have been migrated explicitly;
historical batches and their frozen snapshots were not migrated or rewritten.

`expert-review` defaults to review-only content acceptance. Use `--activate` to
also update the preferred selection after acceptance. `--review-only` is also accepted. Use
`--expected-current DIGEST` (or `none`) to guard a review against a stale view.
Preferred selections retain their recorded history; all approved revisions remain
retrieval candidates regardless of that selection.

Already accepted versions can be selected without repeating expert findings:

```bash
python3 -B -m temporal_contract_analyzer experience-memory activate NEW_SHA256 --expected-current CURRENT_SHA256 --actor OPERATOR --store experience-memory
python3 -B -m temporal_contract_analyzer experience-memory rollback ACCEPTED_ANCESTOR_SHA256 --expected-current CURRENT_SHA256 --actor OPERATOR --reason 'Explicit rollback' --store experience-memory
```

Activation and rollback check exact acceptance, taxonomy compatibility and the
expected current pointer under the same store lock. A normal activation permits
an initial version or a descendant; only explicit rollback may select a compatible
accepted ancestor. Rejected versions, unknown digests and unrelated branches
cannot be selected. A failed pointer write retains any completed review but
does not report activation success. The index is an atomic file containing both
the version mapping and actual selection history; it has no duplicate archived
status to maintain. Existing frozen snapshots remain valid after later changes.

Keep CLI review drafts in the project's `review-drafts/` directory, outside the
canonical memory store. The CLI creates missing parent directories. Drafts are
ignored by Git; submitted decisions are retained in `experience-memory/decisions/`.
Temporary-directory paths are not required for this workflow.

## Source-bound delivery for current seven-label analyses

`retrieve` accepts only an explicit JSON object containing `task`, `sources`,
`analysis` and optional `review`, using the existing seven-label analysis/review
contracts documented in [CONTRACT_TAXONOMY.md](CONTRACT_TAXONOMY.md). `sources` maps
candidate-relative paths to actual text. It does not accept case/cluster identity,
expected labels, historical scores, evaluator data or reference patches.

```bash
python3 -B -m temporal_contract_analyzer experience-memory freeze --store experience-memory --output review-drafts/memory-snapshot.json
python3 -B -m temporal_contract_analyzer experience-memory retrieve visible-input.json --store experience-memory --output review-drafts/experience-delivery.json
```

For a frozen experiment, pass both `--snapshot review-drafts/memory-snapshot.json` and
`--expected-snapshot SHA256`, reading the digest from that snapshot. Later active
updates do not change its selected versions. Without `--snapshot`, retrieval uses
the current active view and the expected digest rejects activation drift. Output
paths must be new files outside the store. These commands never start a model.

The router checks source citations, source-bound semantic review, compatible
labels, known required premises and explicitly contradicted exclusions. Unknown
premises/exclusions fail closed. Up to five eligible bundles are delivered together by default; multiple matches alone do not cause AUTO. Selection is by the chosen
entry digest, not array position. Source-bound review may be AI-assisted; no new
human-approval requirement is introduced.

The result separates `route`, `selected_memory_records`, `memory_snapshot` and
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

The original versions remain in `legacy-toolflow-t1-t4-v1`. Their reviews, source objects, translation
lineage and available evidence/outcomes are preserved as hashed audit copies.
Initial provenance is recorded in
`implement-stage/experience-memory-v1/IMPORT.json` in the [research archive](ARCHIVE.md).

The original legacy versions remain inspectable by digest and `list`; they are
not overwritten. New native candidates carry explicit per-rule source annotations
and parent linkage, preserving all rule text and requires/excludes. These are
AI-assisted executor annotations, not fresh automatic model extraction, expert
approval, classifier ground truth or new behavior evidence.

The candidate labels are O/L/I/A (subscription retirement), R/L/I/A (paused shared
work), and O/B/L/I/A (deferred boundary binding). No F label was forced into the
inventory. Some B grounds are explicitly preserved-behavior inferences, not
literal README deadlines. See the full
[archived recoding audit](ARCHIVE.md) (`research/unified-seven-label-recoding-20261110_112750/REPORT.md`).

The three native child digests have saved acceptance decisions. The historical explicit
active index retains those selections, including exploratory scope for deferred
boundary binding. Their acceptance is sufficient for inclusion in the default snapshot, without
certification under the v2 effect protocol. Previously, a later acceptance of its legacy parent superseded the native
child under review-order selection; the explicit index removes that ambiguity.
No stored decision or old experiment was rewritten. Searching an unaccepted
candidate still does not permit delivery, and activation creates no new replay
or repair-benefit evidence.

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

Multiple matching records are included with unique SHA:rule references, also retained in failure reflection. Singular selected_memory_record / selected_sha256 fields are populated only for a single match; consumers must use the plural fields for multiple matches. Unknown prerequisites and exclusion boundaries still prevent a record from matching.

Delivery defaults to at most five matched experience identities. Matching and latest-applicable revision selection happen before the cap. Eligible identities are ordered by label Jaccard similarity to the current task, then shared-label count, then stable digests; this is a transparent heuristic, not an empirically calibrated effectiveness score. The audit records matched_count, max_experiences, truncated_count and omitted record digests. The retrieve CLI supports --max-experiences; the Python retrieve / route_view APIs accept max_experiences. Truncation never turns successful matches into AUTO, and delivered rule bodies are not cut.

## Updating compact experience instead of appending guidance

Compact libraries retain all reviewed versions as archive entries. Fresh approved
snapshots and `approval.active()` now resolve `revise` / `merge` proposals under
`compact-current-guidance-v2`: an unambiguous accepted revision replaces its target
in retrieval; an accepted merge replaces all targets. Pending/rejected proposals
never supersede accepted guidance. Rejecting a replacement exposes its still-accepted
sources again. Historical frozen snapshots remain valid; no archived acceptance or
text is rewritten.

New proposals bind both target IDs and exact target hashes. Acceptance checks that
the target is still current, so concurrent stale revisions require rebasing rather
than silently creating competing active replacements. Cycles, competing replacements,
missing targets and stale hashes are reported; the affected connected lineage is
retained without choosing a winner by file order or review time. An explicitly
accepted merge covering every competing branch resolves that fork. This conservatively
keeps unresolved historical guidance available. `compact.active_view(path)` exposes
the complete report; the review page labels superseded and unresolved entries, and
new trajectories archive `memory-lifecycle.json`. Acceptance and current retrieval
status are distinct.

Training reflection has a separate update search: up to 16 complete related entries,
including delivered guidance, ranked using the original task and source-grounded
business obligations. It also receives a short discovery catalog of the frozen bank;
previews are incomplete and cannot establish novelty on their own. Action still
receives at most five entries. Exact duplicates become evidence supplements. New
entries compared against existing guidance require an explicit independent increment
and actual attempt evidence; the extraction prompt prefers evidence/revise/merge,
requires explaining why existing guidance cannot cover a proposed new mechanism, and
requires retaining still-applicable business obligations in updates. Language changes
or wording changes alone do not justify new guidance. These are source-grounded model
judgments, not a semantic guarantee that every paraphrase is detected.

This does not automatically synthesize merged guidance for ambiguous historical
branches, remove preservation obligations, learn from test outcomes or rerun models.


## Consolidated guidance and evidence appendices

The six source-preserving consolidations in `library/zz-consolidated.json` use
`evidence_ref` to bind a relative `evidence/*.json` appendix and its SHA-256. Each
appendix retains the complete original entries and their source file/version hashes,
the consolidated guidance, section coverage and preservation checklist. Evidence
quotations and historical observations are archival context, not requirements for a
new repair. Only the five concise guidance sections enter normal solver delivery.
The loader verifies the appendix digest, current guidance, exact target hashes and
complete archived source content; missing, modified or external appendices fail
integrity validation. Appending consolidation records preserves original file hashes
and decision order, so the pre-consolidation snapshot remains verifiable.

A separately accepted, appendix-backed merge bound to exact currently accepted
source versions can supersede those named sources even when their older ancestry
is missing or ambiguous. It does not retire an unrelated branch or infer a winner
among other historical versions. Cyclic or stale merge targets cannot use this
exception; rejecting the merge restores the applicable accepted sources. This
supports reviewed partial consolidation without rewriting older lineage or dropping
unreviewed obligations. Other ambiguous lineages retain the conservative behavior.
