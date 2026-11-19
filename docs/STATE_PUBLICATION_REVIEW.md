# Synchronous reentry and state-write ordering: 0.6.1 development checks

This implementation adds one bounded check: an entry reads a shared closure variable and may subsequently enter a caller-supplied function. The analyzer locates whether the variable is written before the call, afterward, or cannot be related on the current path. Results are review evidence, not bug verdicts or risk scores.

Tool code and subsequent development validation are maintained in `temporal-contract-analyzer`. Bench material is retained for historical research only. The fixed source, tests, provenance and licenses needed here are included in this repository, without reading from bench.

## Input and execution scope

- Reads syntax events from JS/TS and Vue inline scripts only. Candidate programs are not executed; tests, patches, historical conclusions and model outputs are not read to generate findings.
- A candidate entry must read a closure variable declared outside the current invocation. Invocation-local variables and entry parameters are not shared state.
- Recognizes direct parameter-function calls and `.call`/`.apply` candidates. Parameter reassignment, shadowing or visible direct method writes block the association, including writes in sibling functions, class initialization and destructured members. Named-function-expression internal names are handled separately; catch parameters and class declarations participate in shadowing checks. When precise block-declaration visibility is unavailable, same-name associations are conservatively excluded. Visible child scopes are checked for rewriting even when execution cannot be established, potentially causing false negatives. Runtime replacement, dynamic aliases and actual function types remain unproven.
- Expands direct immediately invoked functions and uniquely bound local functions without visible rewriting, up to four levels and 2,000 events per entry. No whole-program call graph is built. Remaining calls are not expanded after the limit; no match does not establish safety. Repeated calls can reuse source event IDs rather than distinguish runtime instances.
- Expressions before the first await in a JS async function may call external code. In `await cb()`, cb is called before suspension. This JS rule does not apply to Python coroutines or generators.
- Does not expand timer/Promise callbacks, uncalled bodies, generator bodies, imported functions or dynamic member targets. Actual arguments are not propagated to callee parameters.
- Calls in conditional branches are not expanded; potential await points truncate the current function's synchronous prefix. Conditional writes, destructured state writes, ambiguous bindings and unexpanded class-scope writes remain unknown rather than established guards. Return, throw, catch/finally and other complex control flow do not receive complete path proofs.

## Output states

| state_publication.status | Meaning | Does not establish |
|---|---|---|
| write_after_call | On the selected bounded evaluation path, the user call precedes a later state write | Runtime reentry or a definite bug |
| write_before_call | A write to the same binding is located before the call | A busy-state value or sufficient protection |
| not_established | No corresponding prefix write is found, or the write has unresolved conditions | Missing protection or program safety |

Structured evidence records the state binding, entry guard, user call, write and immediately executed call chain. Complex assignment values remain in original source events rather than being quoted again. New relations enter both facts/review; interpretive states enter review only. Boundary cards cite user calls and entry guards separately. Comparison checks relation states and extractable simple write values; hint counts alone cannot establish a repair.

## Why the old p-debounce implementation matches

In the real repair's parent commit, line 103 reads currentPromise and line 118 begins:

```js
currentPromise = (async () => {
    // ...
    result = await function_.apply(this, arguments_);
    // ...
})();
```

The user call at line 124 happens before the right-hand side returns. Although the assignment text starts at line 118, assignment completion follows that call. This is an evaluation relation rather than line-number sorting. The maintainer's repair sets currentPromise at line 121 before calling the user function at line 129.

## Development validation

Entry point: `python3 -B external-tests/reentry-publication-v1/run.py --output external-tests/reentry-publication-v1/run-new`.

Requires the fixed historical snapshots/tests in `external-tests/reentry-publication-v1/fixtures/p-debounce/` and an existing local Node >=22. No new dependencies are installed and no models called. Historical inputs, scans and reports are not overwritten. New output includes per-item source, frozen bundles, HTML, comparison reports and TAP.

There is one real parent commit and one repair commit. Renaming, formatting, deferred execution, variable shadowing, conditional writes and undefined writes are known development controls, not additional independent defects. Matching expectations is neither precision/recall nor unseen-project validation.

The old extractor produced three coarse hints for both versions without explicitly locating this relation. The new extractor adds one state relation to each: write_after_call for the faulty version, write_before_call for the repaired version. The original 80 tests pass for both; the maintainer's three additional reentry regressions all fail before repair and pass afterward. Actual files in the external experiment directory are the authoritative logs.

This establishes that the development check can present the key relation in this known issue. Developer review benefits and LLM repair benefits have not been measured. Further rule extensions require validation from independent sources.

## Delivery boundaries

This change affects the Python core, JS parser and card projection used by frozen reports and source pages. The VS Code VSIX was not repackaged, nor the old embedded bench analyzer synchronized. Existing frozen bundles retain their original bytes; old reports do not adopt a new tool identity. Actual scan versions and tool hashes are recorded in generated report.json.

## 0.6.3: One-shot callback clearing in conditional branches

Adds restricted recognition of `if (fn) { fn(...); fn = undefined/null; }`, independent of function/project names. The hypothesis is that `fn` serves as both entry state and an outer parameter binding; on the selected normal path, synchronous invocation precedes clearing, warranting an immediate-reentry check. This is not a general conditional-path reachability proof.

- For simple identifier guards, the parser records actual branch-block identity and whether the branch consists of supported sequential statements. Equal condition text does not merge separate branches.
- The entry guard must be a direct function-body statement. Call and clear must occur in its same positive branch within the bounded initial synchronous prefix. Clearing after a direct return/throw is excluded.
- The binding must be an outer parameter rather than a current-invocation local/parameter. Its only visible write in the entire file must be this simple null/undefined clear after the call. The old callback-reassignment checks are not generally relaxed.
- Shadowed undefined is not inferred as an empty value. Property writes, destructured writes and sibling-function writes still exclude associations. `.call`/`.apply` remain candidates; runtime replacement is unproven.
- Nested if, loops, try/finally, additional blocks and local-helper expansion inside this branch are unsupported; suspension still truncates analysis. Negated guards, compound conditions and calls through saved aliases are not inferred. Strict limits leave false negatives; no match is not safety.
- Uses existing `reentrant-state-publication` / `write_after_call` and ordering relations, without relaxing default low-noise filters. Additional structure records `path_conditions` and `callback_binding_basis`.

The same-source onetime recheck is in `external-tests/onetime-v8-independent-v1/run-02/`: zero hints in 0.6.2 become one in 0.6.3, citing index.js L17/L18/L19. Upstream code is unchanged; five controls still pass and two reentry expectations still fail. This case participated in rule development and cannot estimate general precision or LLM benefit. New tests cover renaming, formatting, null, call/apply, TS/Vue, cross-branch cases, early clearing, reassignment, shadowing, suspension, deferred calls and unreachable writes.

## 0.6.4: Nested if paths and a separate reentry flag

Adds a restricted path under the existing publication rule: a linear block inside an outer if/else executes `if (flag) return`, calls an outer-supplied function, and writes true to the same shared flag. Evaluation order distinguishes write-before-call from write-after-call. Flag and callback are independent variables; the callback need not itself be state.

Assumptions and boundaries:

- Guard keys include scope and source offset, recording branch identities, then/else blocks and paths up to four levels. Identical condition text does not combine separate if statements or mutually exclusive branches.
- Parent conditions support simple identifiers, this, restricted equality and negation, excluding calls, property accesses and compound logic. Pure constants and detected simple identifier truth-value contradictions are excluded. There is no complete reachability, SAT or type proof.
- Target blocks allow sequential statements and one simple identifier early-return guard. Logical/conditional expressions, suspension, extra control and nested functions/classes are outside this check. Initial synchronous-prefix and 2,000-event limits remain. Events after return/throw do not establish subsequent writes.
- Flags must be outer shared bindings rather than current-entry locals/parameters. Outer declarations may be uninitialized or false; the target block permits one simple `flag = true`. Other visible resets, class/sibling/destructured writes and uncertain bindings are conservatively excluded. Callbacks retain existing unreassigned-parameter checks.
- Findings cite all parent guards, the flag guard, call and write, with `path_conditions`. Layer C retains new path syntax fields. Historical frozen reports lacking these fields keep their original rendering bytes; the old p-debounce bundle still verifies.
- Direct receiver-property state such as `this[key]` remains unanalyzed. Write-before-call is a fact, not proof of receiver or all-path safety. Exceptions, indirect writes and runtime replacement need human review.

Fixed component/once source and a clearly labeled artificial variant were rechecked in `external-tests/component-once-v001-v1/run-03/`: zero default cards for the original, one for the variant. Source digests and runtime observations match 0.6.3 run-01; execution checks remain seven passes for the original and six passes/one failure for the variant. Candidate code, expectations and probes were not changed to produce the difference. The variant is not a real upstream defect; this case is now development regression material.

## 0.6.5: Local callback snapshots and clearing order

Adds one-hop provenance for `if (fn === null) return; const copy = fn; fn = null; copy(...);` and forms moving clearing after invocation. JavaScript value-copy semantics mean clearing the original binding does not alter a previously saved local copy. Only clear-after-call produces default issue cards; clear-before-call remains an ordering fact without claiming all-path safety.

Assumptions and boundaries:

- The direct entry body has one strict-null early-return guard, supporting `fn === null` and `null === fn`. The original binding must be an outer parameter, not a current-entry parameter or shadowed name.
- The copy must be a simple var/let/const declaration in the same sequential block, initialized from that parameter after the guard and before the sole visible null clear. The copy may be called before or after clearing. Clearing the original before copying does not establish a function candidate.
- Additional copy/source reassignment, method writes, destructured writes or ambiguous bindings remain excluded. Only direct calls and `.call`/`.apply` candidates are recognized, without multi-hop tracking, conditional assignments, property aliases, bind results or cross-function argument propagation.
- Handles bounded initial synchronous prefixes and linear bodies, retaining the 2,000-event limit. Branches, suspension, deferred callbacks and unreachable clears are not linked. `== null`, other guard/clear values and aliases declared before later assignment are unsupported. Runtime types, indirect writes and dynamic method replacement need review.
- Findings attach `callback_alias` (original name, copy name, copy event, scope) and provenance. Copy locations enter default card evidence. Layer C adds `local_alias_snapshot_before_call` and null-guard syntax fields, without establishing a complete dynamic call graph. Historical frozen reports lacking the fields retain their original bytes.

`external-tests/async-once-v326-v1/run-02/` stores the same-source recheck: the original changes from zero raw hints to one clear-before-call fact, still with zero default issue cards; the artificial variant changes from zero to one issue card. Original inputs, runners, witnesses and outcomes remain unchanged: original 7/7, artificial variant 6/7. This case participated in rule development; its artificial variant is neither a real upstream defect nor generalization evidence.

## 0.6.6: Receiver functions and Reflect call candidates

New `reflective.py` reuses lexical binding, visible-write and synchronous-prefix checks for a restricted pattern: a factory captures this as a function value; a closure limits execution with a positive boolean flag; Reflect.apply/construct performs the call. No project/variable names or Function.prototype.once text are required.

Assumptions and boundaries:

- The function value must come from a unique direct factory-body declaration `let/const/var target = this`, without other visible writes. The flag belongs to the same factory, initialized true and uniquely written false in the selected positive branch. Only simple positive identifier guards directly in the entry are selected. The limit is 2,000 events; arbitrary nested flows are not expanded.
- Supports direct Reflect.apply/construct or simple destructuring from unshadowed Reflect, with renaming. Apply takes three arguments, construct two, with the captured function binding first. Extraction declarations must be in the visible prefix; same-entry extraction must precede the call.
- Visible Reflect parameters, function/variable/class/catch/import shadowing and direct/property/destructured writes block association. Additional local API-alias writes also exclude it. Known property-mutating APIs for Reflect/globalThis are conservatively excluded, potentially excluding harmless writes. Cross-file/indirect mutation and actual native identity remain unproven.
- Supports sequential calls or separate conditional arms of `this instanceof currentNamedWrapper ? construct(...) : apply(...)`. The parser retains each arm's identity, test text and parent block, without claiming simultaneous execution. Other conditional expressions, suspension, extra branches, deferred execution and unreachable writes do not establish relations.
- Each call emits its state ordering and `receiver_capture_before_reflective_call`, with capture, flag initialization and API-destructuring evidence. The default low-noise view merges two candidates sharing flag/guard/write into one card, retaining both locations; raw reports retain arm details. Write-before-call does not prove all-path safety, actual function type or correct caching semantics.

The latest recheck is `external-tests/ungap-once-v012-v1/run-03/`: the original has two write-before-call facts and zero issue cards; an artificial delayed-flag variant has two write-after-call candidates merged into one card. Fixed source, original runner, seven checks and ten upstream assertions match run-01; outcomes remain original 7/7, variant 6/7. A separate constructor-reentry probe is stored in constructor_verification.json: the same variant increases constructions from one to two, not a second independent defect.

This case was used for rule development and cannot subsequently count as an unseen validation project. It demonstrates distinction of a known artificial regression, not overall precision or LLM assistance. Historical run-01 and intermediate run-02 are preserved; old frozen bundles still verify.

## 0.6.7: Simple post-call clearing preserves call-site provenance

Parameter-call association no longer abandons every binding with a visible write. If the parameter's sole visible write is a simple null/undefined clear after the call in the same direct entry block's normal synchronous prefix, the call-site parameter provenance candidate is retained. This detects ordering between just-once's separate called flag and user call without requiring cleanup deletion.

Assumptions and boundaries:

- Call and clear must share a direct linear block in the same function frame, without additional conditions or conditional expressions. Clearing must be within the bounded initial synchronous prefix. Existing expansion/event budgets remain; suspension, return/throw and uncertain branches are not crossed.
- Only the binding's sole visible write is accepted: simple `callback = null`, or `callback = undefined` with unshadowed undefined. Pre-call writes, arbitrary replacements, method overwrites, destructuring, multiple writes and clears in class/sibling/helper frames remain conservative exclusions.
- Decisions are per call site: calls before clearing may retain provenance; later calls cannot reuse the original parameter candidate. This is not complete reaching-definitions, alias or whole-program control-flow analysis.
- Adds `external_call_before_callback_clear` and `callback_cleanup` provenance. Existing guard/state writes still determine write_before_call / write_after_call. The default view requires complete clearing relations and citations. Clearing is neutral ordering evidence; cards explicitly do not classify the cleanup statement itself as defective.
- If the original callback binding is itself entry state, post-call clearing can still be a meaningful reentry candidate. Calling a statement cleanup does not generally make its ordering irrelevant.

`external-tests/just-once-v220-v1/run-02/` stores the recheck: the original retains fn = undefined and identifies called as written first, with zero default cards. An artificial delayed-called variant has one card. Inputs, original runner and witnesses match run-01; outcomes remain original 7/7, variant 6/7. The run-01 false negative and static cleanup-deletion diagnosis are retained. This round changed the tool rather than candidates or cleanup. All old development cases/bundles were separately checked; this is not independent generalization or LLM-benefit evidence.

## 0.6.8: Numeric invocation-budget decrement and conditional calls

New countdown.py analyzes a restricted shared parameter representing a numeric quota: a positive numeric condition gates a call to another factory parameter, and the entire file has one explicit -- update. It distinguishes pre-decrement in the condition from post-call budget updates rather than labeling every decrement a temporal risk.

Assumptions and boundaries:

- Supports `if (--budget > k) { callback(...) }` or a standalone -- update after `if (budget > b) { ... }`. The latter update may occur inside the positive branch before/after the call, or after that branch; its prefix/postfix result is unused. Thresholds must be nonnegative safe-integer literals. Post-decrement condition values, increments, compound arithmetic, dynamic thresholds and other comparison operators are unsupported.
- Budget and callback must be parameters of the same outer function. Current-invocation locals, resets/reassignments, extra visible writes and shadowing are excluded. The positive branch permits sequential statements and one direct parameter callback call, including call/apply candidates. Extra control, termination, suspension, deferred callbacks and multiple calls are conservatively excluded. Existing synchronous-prefix and 2,000-event budgets remain.
- For subsequent `if (budget <= bound) callback = null`, validates the cleanup variable, block identity, thresholds and decrement/call ordering. The cleanup threshold is k+1 for the pre-decrement condition, b for ordinary comparison. Parameter candidates are retained only after checking this monotone-budget pattern; arbitrary conditional writes do not establish a known callback.
- Cleanup may not execute. New `external_call_before_conditional_callback_clear` describes ordering only when its condition holds. Default reports show that condition and retain cleanup guard/write evidence, without declaring cleanup defective.
- New syntax fields countdown_guard/countdown_cleanup/update_prefix/update_standalone distinguish tested values from update side effects. Layer C retains bounded relations such as numeric_budget_guard_before_call; layer D adds numeric_budget and write_operator. Existing default write_before_call / write_after_call filtering is reused.
- Numeric-budget meaning, finite safe-integer inputs and runtime function type remain review premises. Numeric coercion, budget after exceptions, indirect alias writes and a complete upper bound are not proven. If the condition is not an invocation budget, the user should reject the candidate rather than treat it as a definite defect or basis for automatic reordering.

`external-tests/underscore-before-v1/run-02` stores the same-source recheck: the original records decrement-before-call with zero default issue cards; an artificial delayed-decrement variant has one card. Candidates, original runner and seven witnesses are unchanged. Outcomes remain original 7/7, variant 6/7; ordering controls for finite integers 0/1/2/3 pass. This artificial variant is not a real upstream defect, and the case is now development regression material.
