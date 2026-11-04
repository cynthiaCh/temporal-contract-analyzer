# Build Note

| Rung | Feature | Acceptance | Status |
|---|---|---|---|
| F0 | Original paired results → descriptive mechanism table | replay script, no model calls | completed |
| F1 | Task/source gate with A abstention and no feedback inputs | selective gate tests | passed 10 tests |
| F2 | Opt-in preparation, frozen routing, exact A/D prompt equivalence | CLI/integration tests | passed |
| F3 | Replay and fresh assumption sweep | artifact checks/reviewer JSON | completed; same-family provisional |

## Run record

- New selective-routing tests 9/9 passed: unknown/composite abstention without parser, concrete source evidence, no case/model/outcome inputs, lexical dependency relevance, exact original A prompt, exact D layer, frozen decisions and one-job fake-CLI execution. No new real A/D model calls.
- Discovery replay: fixed A 6/24, fixed D 13/24, candidate selector13/24. D deliveries24→18; report characters410778→324576. Missing required effects remain29 overall, but individual task/effort outcomes can differ.
- Observed replay tokens: fixed D input5889755/output83963; selected input5827266/output82226. This is only ~1–2% reduction, not25% compute saving.
- Source groups:3 (two download variants share one source family); this replay is not held-out validation.
- Actual selector model prompt never contains routing reasons; decisions are stored outside the agent workspace. Workbench still archives/scans normal eligible inputs.

## Deferred and limits

No classifier fitting on 24 correlated rows, case-ID allowlist, post-run oracle selector, causal confidence score, default UI migration, deployment efficacy claim or new model campaign. The policy is an opt-in discovery candidate.

- Affected prior suites: workbench16/16, hypothesis-repair7/7, RAG3/3 passed; new gate10/10 passed after scope correction. No broad rerun of unchanged platform-specific suites.
- Review round1 found a real disjoint-consumer false match and count-only partial-effect reporting. Fixed function/declaration-scoped reachability, added the protected-consumer AST regression, and retained all per-check gains/losses against both A and D.
- Final scoped replay: 13/24 successes and18 D deliveries; versus fixedD,7 check gains and7 losses, with3 configurations losing at least one check. The gate is not per-configuration nonregressing.
- Round2 independently rechecked all24 scoped routes and raw required/forbidden identities. No unresolved material/semantic finding. Same-family provisional assurance, not held-out efficacy validation.
- Final artifacts: results/selective-assistance-v1-20261104/scoped-replay/{REPORT.md,summary.json,replay.json,replay.csv,decisions.json}. Earlier replay directories preserve pre-sweep development records; scoped-replay is the final one.
- No live stubs or new real A/D model trials. Prototype policy remains opt-in; original manual A/D behavior unchanged.

## Final semantic/interface choices (full ledger)

# Assumption Ledger

ASK mode: never

| ID | Underdetermined decision | Chosen | Class | Source |
|---|---|---|---|---|
| G-001 | Meaning of effective | Primary metric: whole-task oracle success; report partial required/forbidden checks and regressions separately. Do not select the better A/D result per task at deployment. | semantic | default |
| G-002 | What evidence can justify a policy now? | Four discovery cases (two same-family download variants), six model/effort configurations each; propose transparent candidate rules only, with no calibrated probability or validated generalization claim. | semantic | default |
| G-003 | Which tool mode gets selected? | D only for task-matched polling-state or initial-subscription symptoms with concrete findings inside matched function/declaration ranges or their resolvable identifier-call ranges; otherwise A. No automatic RAG/hypothesis retries. | semantic | default |
| G-004 | How to treat complex effects | Explicit audit/history retention + retry/cancellation + reordered/reentrant publication compositions abstain to A; this is a candidate applicability restriction, not proof D cannot help. | semantic | default |
| G-005 | What can the gate read? | Original task, report parsing status, rule IDs, candidate-visible evidence paths/scopes/locations and lexical local-import dependencies. No case/model identifiers, scores, failure feedback, manifests' mechanism labels or lesson memory. | semantic | default |
| G-006 | How is A protected? | Agent gets the exact existing A task prompt when routing chooses A; decision and reasons are researcher-side only. D receives the exact current D layer with the existing wrapper. | semantic | default |
| G-007 | What does saved cost mean? | Count D material deliveries, report characters and actual observed token usage in replay separately. One agent job either way; no claim of 25% total compute/model-call saving. | semantic | default |
| G-008 | Scan cost and unsupported inputs | Task prefilter can abstain without a scan. Potential matches require a cheap static scan. Workbench still performs its normal eligibility scan/archive for every prepared input; do not claim it avoids all analyzer calls. Existing fully-parsed-input requirement remains. | interface | default |
| G-009 | Interface/default behavior | Add opt-in `prepare_selective_case` and reports `route`/`selective` commands; keep default/manual A/D unchanged. Freeze decision bytes and selected role before model execution. | interface | default |
| G-010 | Validation protocol | Discovery replay only, no new model calls in this task. Future evaluation must freeze rules and split by source task/family, not by model/effort rows. Current evidence is insufficient for out-of-family validation. | semantic | default |
| G-011 | What qualifies as task/source alignment? | Roots use lexical task-token/function-name matching, not proof of the intended entry. A filename alone can select only a single top-level function, never every function in a multi-consumer file. Strip explicit protected/preservation clauses from focal matching. Follow parsed identifier calls within those ranges up to depth2; collocated unrelated callers do not qualify. Runtime/member dispatch remains unproven. | semantic | sweep |
| G-012 | How are partial gains/losses compared? | Retain required-missing and forbidden-observed IDs for A, D and selected outputs; compute per-check gains/losses versus fixed D and separately versus fixed A. Do not hide simultaneous loss behind net counts. | semantic | sweep |
