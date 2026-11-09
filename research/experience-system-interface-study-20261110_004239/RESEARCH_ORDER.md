# Four separate research questions

## 1. Understand and stabilize outputs

Start with the observed inventory in `OUTPUTS.md`. For each boundary specify the
producer, schema/version, original versus derived status, consumer, admission
checks and incomplete/error states. Keep requirements, observed behavior,
preservation duties, hypotheses and unknowns distinct. Reuse archived failures for
offline tests; do not use model calls to discover basic serialization defects.

Acceptance before moving on: representative successful, rejected, incomplete,
unknown-premise and conflicting cases round-trip without changing meaning; no
schema migration silently changes classification or policy. This inventory is a
first pass, not completion of that acceptance suite.

## 2. Compare experience representations before choosing storage

Study three representations: full Markdown bundles; structured rule bundles with
derived Markdown; and rule-level search records linked to their parent bundle.
Use the same existing evidence to compare preservation of conditions and
counterexamples, auditability, deterministic rendering, duplication, retrieval
granularity and delivered context size. A vector database is an implementation
choice, not evidence that the representation works.

Proposed starting hypothesis: one canonical structured bundle, with each rule body
stored once. Keep versioned applicability predicates, exclusions, evidence links,
preservation constraints, counterexamples, semantic-review status and lineage.
Generate display text and search indexes from that source. Keep empirical outcome
records separate from normative rules. A rule-level index must retrieve its
preservation and boundary dependencies; an isolated slogan is unsafe evidence.

Use separate views: runtime experience text; search metadata; and audit-only
provenance. Case identity, source cluster, scores, reference patches and evaluator
details must not enter the runtime retrieval query or repair prompt. Audit links
may retain them for honest exposure and version tracking.

## 3. Evaluate retrieval for a new case

Runtime pipeline:

1. Build a source-bound query from the task, source/docs, mechanism analysis and
   fixed automatic Contract. Record taxonomy version and unknown premises.
2. Retrieve candidates from the compatible, admitted frozen experience snapshot.
3. Check support for required premises, exclusions, conflicts and preservation
   obligations. Unknown is not satisfied. Do not remove conditions to force hits.
4. Rank eligible candidates by relevant relation coverage, evidence fit,
   redundancy and context budget. Begin with zero or one complete bundle.
5. Return selected identity/version/hash, checks, gaps, fallback reason and exact
   delivered bytes. Resolve the selected entry by identity/hash, not list position.

Study candidate recall, evidence-supported applicability, unsafe selections,
fallbacks, boundary retention and context cost separately. An AI-assisted review
must be labeled as such. Only downstream controlled repair evaluation can show
whether the retrieved material was useful; lexical similarity and hit rate cannot.

Keep source-context retrieval, learned experience retrieval and quarantined audit
records separate even if they share storage infrastructure. No new retrieval
method or performance result has been implemented in this inventory.

## 4. Optimize a shared class prompt as a separate intervention

Assemble repair input from four explicit parts:

`fixed global execution policy + versioned class module + per-case data + retrieved experience packet`

The class module should encode reusable inspection and verification procedures,
not a case-specific patch or answer. Multi-label mechanisms may need composable
modules rather than one exclusive class. Existing static reminders are not learned
class prompts. Do not treat T1–T4 and the seven obligation labels as interchangeable.

Train a proposed module on multiple development cases with full success/loss
feedback. Preserve the prior version. Do not evolve it from frozen evaluation
feedback. If the fixed test cohort has already been inspected, record that exposure.

For later authorized evaluation, a fixed 2x2 separates the mechanisms:

| Class module | No retrieved experience | Frozen retrieved experience |
|---|---|---|
| Existing module | Baseline | Retrieval effect under existing module |
| Revised module | Class-prompt effect | Combined condition and interaction |

Hold models, budgets, tools, candidate starts and evaluators fixed; retain full
behavior vectors, regressions, invalid slots and unknown costs. Same-case
development and same-cluster transfer have different evidential scope. Class-wide
claims need held-out source units, not merely a sibling language variant.

## Sequence and current status

Phase 1 has a concrete initial inventory with historical samples. Phases 2–4 are
proposed studies, not executed validations. Next do representation fixtures and a
versioned interface agreement, then offline retrieval tests, then an explicitly
authorized controlled repair experiment. Do not keep adding experience text or
cases while changing all these components at once.
