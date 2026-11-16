# V11: source-grounded semantic experience selection

V11 (`tempoevo-trajectory-v11`) replaces label-only delivery in the structured and
fixed-contract conditions. V10 and earlier roots remain readable but cannot execute.
This is a retrieval protocol change, not a reinterpretation of prior scores or
approvals. Existing reviewed experience files are not edited or reapproved.

## Retrieval and delivery

1. Read the frozen approved snapshot (training-only provisional guidance remains a
   separate, explicitly labeled channel when online learning was selected).
2. Apply the existing source-supported labels, requires and excludes. Audit/version
   or cross-case effectiveness is not a new admission gate. Citation line offsets
   remain hints; exact quoted words may span lines within the same source file.
3. Rank mechanism-eligible candidates by BM25 over original task, source-derived
   analysis and obligation statements. Recall at most 20. Zero lexical overlap alone
   does not establish inapplicability; remaining candidates use stable identity order.
4. A separate `selection` model stage assesses every recalled candidate's complete
   applicability, material scenario prerequisites, exclusions, object/operation mapping,
   concrete contribution and supported obligation coverage. Generic labels such as
   lifecycle/reentry do not establish retained audit, decoding, persistence or query
   cancellation obligations. Unsupported or unknown critical premises exclude delivery.
   Cross-domain guidance is allowed with an explicit source-backed mapping.
5. Python validates the structured assessment, exact candidate identities and public
   citations. Greedy selection prefers additional obligation coverage, direct relevance,
   then BM25. Declared redundant pairs and near-identical texts (token-set Jaccard >=
   0.85) do not consume multiple slots. Deliver at most five entries and 16,000 actual
   text characters. There is no quota to fill; no applicable guidance means plain
   Auto-Contract repair. No effectiveness or behavioral PASS is inferred by this model.

`retrieval/selection-N-recall.json`, `stages/selection-N/input.json`, its result and
`delivery.json` preserve candidates, assessments, evidence, exclusions and selection
reasons. Contract revision may trigger reselection from the same frozen snapshot,
using original public evidence; it never reads other tasks' new candidates in testing.
The baseline, contract-only and BM25 ablations retain their respective retrieval rules.

## Calls and budget

New contract-enabled testing roots use
`contract_review_policy=public_contract_review_3_versions_v1`. Before repair,
the draft is reviewed for source grounding, coverage, overconstraint, consistency
and explicit unknowns. Public-source investigation and cited corrections may
produce at most three Contract versions (the draft and two revisions). Each
version can be reviewed once; the third cannot be revised. Categories may be
multiple or unresolved; they do not mandate all category checks. Experience suggests
checks, while the current request/source establishes requirements. Unsupported
draft obligations may be removed or rewritten with a reason and public evidence
for each affected ID. Original task requirements must remain preserved; schema
and citation validation do not establish semantic correctness.

Reviews stop as `ready` (no supported actionable issue), `unresolved`, or
`budget_exhausted`; none is an execution PASS. Draft, reviews and final Contract
are archived separately. Unknowns and review outcomes accompany the single repair
Action. Changed classification/premises trigger retrieval from the same frozen
snapshot. If the shared selection budget is exhausted, old guidance is withdrawn.
No Gold output or generated patch enters this pre-repair review. Training and the
no-Contract baseline retain their existing flow.

All stages use the frozen model profile (default gpt-6.1-sol / medium). Learning
selection has at most 12 requests and 600 seconds per invocation, including transport
retries. Structured learning reserves up to three selections: initial, plus
one after each possible Contract revision. Fixed-contract learning reserves one. No candidate
means no selection model call, although the maximum budget remains reserved.

For default single-submission structured testing:

- routing: 12 requests;
- selection/reselection: 12 shared requests and 600 seconds;
- Contract draft and up to three reviews: 12 shared requests and 600 seconds;
- Action: 24, including public test execution and any code revisions within the session;
- no outer diagnosis or additional Action;
- total maximum: **60 requests** across routing, shared selection, shared Contract
  construction/review and Action budgets, with a 2,400-second total stage maximum.
  Reviewing does not multiply these budgets. Learning retains up to three Actions,
  two diagnoses and three selections, plus extraction, for **168 requests**.

Unused stages are not called or billed. Gold/public evaluations have separate
budgets. A selection failure is execution-invalid, not a behavioral repair attempt.
Actual requests, tokens, time, stage retries and missing usage remain reported.

## Testing boundary and continuation

Learning diagnosis compares behavioral Contract fields separately from evidence
and unknowns. Changes only to `supporting_evidence` or `unknowns` do not trigger a
Contract delta or experience reselection. Behavioral changes still require a
nonempty delta, preserve retained obligations, and require grounded routing in
structured mode. Implementation-only and fixed-contract runs cannot revise
behavioral requirements. Unused routing proposals from metadata-only diagnoses
are archived as unused and cannot authorize experience delivery.

Diagnostic evidence may cite either the original public inputs or the actual
previous failed candidate. `PREVIOUS_CANDIDATE:<relative path>` explicitly selects
the latter; legacy bare paths are resolved against both supplied source maps and
their matched versions are recorded in `supporting_evidence_bindings`. Those
bindings accompany the next Action's within-task reflections. Contract and
routing evidence remain grounded only in original public inputs. All revision
checks and any necessary reselection finish before the revised Contract or
diagnosis is committed. Invalid revisions leave the prior Contract intact.
These fixes change the frozen implementation binding; earlier trajectories stay
read-only, and any new model execution requires a newly prepared root.

When the behavioral Contract is unchanged but a proposed Contract citation
literally matches only the previous candidate, retain the prior original-source
Contract evidence and record the candidate-only citations separately. The raw
diagnostic output remains archived. Fabricated quotations and candidate-derived
evidence for behavioral revisions are still rejected.
If a diagnostic candidate-version prefix quotes only the original version of
that same file, record the literal source match and an explicit version
correction; do not change the quoted words or silently treat them as repaired
code. A quote absent from both supplied versions remains invalid.

Analysis's closed read grammar also permits exactly `git status --short` and
`git --no-optional-locks status --short`, including sequences with allowed source
readers. Other Git operations/options and paths outside the workspace remain
denied. A hook-denied operation is reported as `tool_policy_denied` with the
actual tool/command, retaining any secondary JSON parse error. Such denials
cannot trigger transport retries. Failed stages are marked invalid rather than
left marked as running. The public workspace need not be a Git repository;
the stage prompt recommends direct source readers.

Training evaluates each patch with its training Oracle, retries on failure and stops
on acceptance, within three Actions. Public checks remain auxiliary. Testing instead
uses `single_submission_then_independent_gold`: one bounded Action submits its final
patch, then Gold scores it once. No Gold result reaches any model call, controls
another attempt or selects between candidates. Testing ends as `scored` regardless
of the score, with `repair_stop_reason=single_submission` and a separate `gold_result`.
The model can run project tests and revise code within its Action budget. There is
no required per-case checker or human intervention. Experience remains frozen and
read-only, with no extraction, expert summary or publication.

Earlier V11 testing roots using `oracle_pass_or_action_budget_exhausted` are historical
and read-only, as are older public-check-controlled retry protocols. The mode-specific
acceptance policy distinguishes them without rewriting their summaries or outcomes.
See [feedback policy](PUBLIC_TEST_ADAPTERS.md).

Testing roots without the current `contract_review_policy` are also read-only.
Their saved summaries and outcomes remain unchanged; new executions require fresh
roots rather than silently adding review to an existing frozen experiment.
Runtime bindings now also cover semantic retrieval, routing, memory conversion and
ranking code, so a changed retriever cannot silently affect an existing frozen root.

The interrupted November 15 queues and their costs remain preserved. Previously
recorded scores are not rerun or relabeled by this correction. Any run that used Gold
feedback during repair must be reported as Gold-assisted, rather than blind testing.
New runs require fresh roots; no paid benchmark run is launched by this correction.

## Verification and limits

Offline synthetic tests cover unsupported domain premises despite label matches,
unknown/weak/contradicted relevance, source-backed transfer, forged citations,
missing/duplicate assessments, duplicate text, character/entry/recall bounds,
unapproved exclusion, model profile/budget, historical read-only boundaries and
single-submission testing, Gold-verdict-independent model inputs, one final scoring
call, training retries and no-learning isolation. No benchmark Gold failure details are used to
tune retrieval. Model applicability judgments remain fallible; Python validates their
structure and citations, not the truth of every semantic inference. Lexical recall
can miss useful cross-domain candidates and token-set deduplication is conservative.
Real repair benefit needs a controlled comparison, not an attractive shortlist.
