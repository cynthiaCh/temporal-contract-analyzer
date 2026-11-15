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

For default three-Action structured testing:

- routing: 12 requests;
- selection: 3 x 12;
- initial Contract: 12;
- Actions: 3 x 24;
- diagnoses: 2 x 12;
- total maximum: **156 requests**; learning optionally adds 12 extraction requests
  for **168**. Each invocation has its own 600-second maximum. At most 10 testing
  LLM invocations are budgeted (routing + three selections + Contract + three Actions
  + two diagnoses = 10 invocations, with 6,000 seconds total stage maximum).

Unused stages are not called or billed. Gold/public evaluations have separate
budgets. A selection failure is execution-invalid, not a behavioral repair attempt.
Actual requests, tokens, time, stage retries and missing usage remain reported.

## Testing boundary and continuation

Training and testing share `oracle_retry`: each generated patch is evaluated by
the Oracle, FAIL triggers another Action and PASS stops, within three total Actions.
Public checks are auxiliary and cannot override the Oracle. Only its pass/fail
boolean enters repair feedback; reference patches and hidden assertion details do
not. This is Oracle-assisted testing, not a final-only blind score. Testing still
uses frozen memory and never learns or publishes experience. The former one-Gold,
public-feedback-only protocol is historical and read-only; its results are not
relabeled and new configurations cannot select it. See [feedback policy](PUBLIC_TEST_ADAPTERS.md).
Runtime bindings now also cover semantic retrieval, routing, memory conversion and
ranking code, so a changed retriever cannot silently affect an existing frozen root.

The interrupted November 15 V10 queue is preserved. Its completed ranks 26–46 are
not rerun. Rank 47 was explicitly cancelled mid-Action and starts a new V11 trajectory
from original public code; its interrupted cost remains in the old archive. Unstarted
ranks 48–50 also use new V11 roots. These four executions are a continuation, not a
homogeneous 25-case V11 efficacy experiment. Earlier invalid executions are not silently
retried. A clean paired comparison needs separately authorized runs.

## Verification and limits

Offline synthetic tests cover unsupported domain premises despite label matches,
unknown/weak/contradicted relevance, source-backed transfer, forged citations,
missing/duplicate assessments, duplicate text, character/entry/recall bounds,
unapproved exclusion, model profile/budget, historical read-only boundaries and
shared Oracle retry/no-learning isolation. No benchmark Gold failure details are used to
tune retrieval. Model applicability judgments remain fallible; Python validates their
structure and citations, not the truth of every semantic inference. Lexical recall
can miss useful cross-domain candidates and token-set deduplication is conservative.
Real repair benefit needs a controlled comparison, not an attractive shortlist.
