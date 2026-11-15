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

All stages use the frozen model profile (default gpt-6.1-sol / medium). Selection
has at most 12 requests and 600 seconds per invocation, with transport retries sharing
those caps. Structured trajectories reserve up to three selections: initial, plus
one after each possible Contract revision. Fixed-contract reserves one. No candidate
means no selection model call, although the maximum budget remains reserved.

For default single-submission structured testing:

- routing: 12 requests;
- selection: 12;
- initial Contract: 12;
- Action: 24, including public test execution and any code revisions within the session;
- no outer diagnosis or additional Action;
- total maximum: **60 requests** across four LLM invocations (routing, selection,
  initial Contract and Action). Each invocation has its own 600-second maximum,
  for a 2,400-second total stage maximum. Learning retains up to three Actions,
  two diagnoses and three selections, plus extraction, for **168 requests**.

Unused stages are not called or billed. Gold/public evaluations have separate
budgets. A selection failure is execution-invalid, not a behavioral repair attempt.
Actual requests, tokens, time, stage retries and missing usage remain reported.

## Testing boundary and continuation

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
