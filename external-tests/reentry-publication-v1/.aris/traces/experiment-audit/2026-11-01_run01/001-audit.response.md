**Overall: WARN. The retained experiment is reproducible and appropriately qualified, but the new rule has material binding errors that need correction.** Review route: fresh native Codex, requested `gpt-6-astra / ultra`, **same-family / provisional**.

Paths below are relative to `/Volumes/Extreme/paper+survey/temporal-contract-analyzer`.

| Check | Status | Evidence |
|---|---|---|
| A. Ground-truth provenance | PASS | The live [upstream commit](https://github.com/sindresorhus/p-debounce/commit/e7dfeb6563390ee677ae0d7e402ae88cdafab622) matches the retained patch. All 12 snapshot SHA-256 values match their provenance inventory. The separate three-test regression file exactly reproduces the appended upstream tests plus imports. Analyzer input contains only `index.js` (`external-tests/reentry-publication-v1/run.py:68–100`). |
| B. Score normalization | PASS | Reports retain raw test counts and raw hint counts. No prediction-derived normalization occurs (`run.py:51–56,103–118`). The 11 expected extraction outputs are development expectations, clearly labeled rather than presented as accuracy. |
| C. Result existence/numbers | PASS | All 11 `run-03` reports reproduce exactly; their frozen bundles verify. `comparison.json` also reproduces exactly. Both baseline reports reproduce with the retained implementation and unchanged dependencies, including their historical tool hash. Recorded outcomes are 80/80 existing tests on both versions and 0/3 → 3/3 regression passes (`run-03/summary.json:298–342`), matching TAP. |
| D. Execution integrity | PASS | Analysis, bundle verification, comparison, and behavioral execution are actually called (`run.py:96–136`). Latest retained full-suite log reports **144 tests passing**. There are no phantom model runs or unused metrics presented as results. |
| E. Scope | PASS | Documentation explicitly identifies one known upstream defect and nine constructed variants, with no holdout, precision/recall, developer-benefit, or LLM-benefit claim (`docs/STATE_PUBLICATION_REVIEW.md:45–49`; experiment `README.md:16–20`). |
| F. Evaluation type | PASS | **`real_gt`** for behavior against maintainer-provided regression tests; **`synthetic_proxy` / constructed development expectations** for the 11 extraction-status checks. Upstream provenance does not prove independent human authorship of every test. |

Three material implementation corrections remain:

1. **Lexical shadowing can select the wrong function.** Block declarations are recorded in the containing function’s scope (`tools/temporal-contract-analyzer/parse.cjs:117,124–126`), and lookup uses that flattened scope (`temporal_contract_analyzer/publication.py:40–44,78–90`).

   ```js
   function wrap(deliver) {
     let active;
     function helper() {}
     return function entry() {
       if (active) return;
       { const helper = () => deliver(); }
       active = helper();
     };
   }
   ```

   This emits `write_after_call` for `deliver()`, although the actual call resolves to the empty outer helper. Named function-expression self-bindings can likewise be mistaken for the outer callback parameter. Respect these bindings or conservatively suppress expansion when they cannot be resolved.

2. **An invoked sibling helper can replace a callback or local helper without invalidating its old identity.** Reassignment checks inspect lexical ancestors only (`publication.py:62–68,83–89`).

   ```js
   function wrap(deliver) {
     let active;
     function replace() { deliver = () => 1; }
     return function entry() {
       if (active) return;
       replace();
       active = deliver();
     };
   }
   ```

   The analyzer still emits an external-callback relation. Replacing `helper` in `replace()` similarly leaves the obsolete helper body eligible for expansion. Writes found in the expanded prefix must invalidate the affected binding.

3. **Destructuring assignment bypasses reassignment detection.** Replacing `replace();` above with `({deliver} = {deliver: () => 1});` has the same error. The parser records target text `{deliver}`, while invalidation only recognizes exact scalar or dotted targets (`parse.cjs:175–176`; `publication.py:63–65`). Preserve assigned binding names for assignment patterns.

These findings concern **incorrect specific binding/order evidence**, including relations exported into facts (`layers.py:91–93,217–220`). They are not allegations that the tool claims runtime safety: its safety and completeness disclaimers are explicit. Nevertheless, they contradict the documented shadowing and visible-reassignment exclusions (`docs/STATE_PUBLICATION_REVIEW.md:9–10`).

Other inspected behavior is appropriately limited. Async-IIFE execution before the first `await`, await-operand evaluation, generator exclusion, and deferred-body exclusion match the inspected examples. Depth/event limits are disclosed. Repeated helper calls may lose later invocation distinctions through source-ID deduplication (`publication.py:143–145`); the retained first relation remained valid in the tested case, so this is incomplete coverage rather than another demonstrated false relation. Exact comparison of simple write values preserves the distinction between `"a  b"` and `"a b"` (`core.py:260–262`; `tests/test_state_publication.py:153–157`).

One runner hardening item does **not** invalidate current results: assertions at `run.py:135–136` check selected pass/fail counts without requiring exact test totals, expected exit status, and zero cancellations/skips/todos. Current retained receipts satisfy all of those conditions. Require the complete outcome tuple before using this runner as a future acceptance gate.

**Supported claims:** the new rule presents the key ordering distinction in this known upstream case; all 11 disclosed development expectations match; the upstream behavioral difference is reproduced; baseline/current bundles preserve distinct tool identities.

**Unsupported claims:** general callback/helper binding correctness, unseen-project detection quality, precision/recall, runtime safety, or developer/LLM repair benefit.

Actual inspection included all listed production files and publication tests; the complete runner; current documentation; all 11 `run-03` source/report bundles; both baseline bundles and retained implementation; historical `run-02` protocol/summary/comparison; upstream provenance and regression derivation; and retained test logs. Large reports and duplicated sources were additionally checked through complete structural loading, hashing, deterministic rendering, and exact scanner reproduction. I did not rerun the behavioral TAP suites; I checked their retained outputs and execution code. No repository files were edited and no paid model calls were dispatched.

```json
{
  "audit_skill": "experiment-audit",
  "verdict": "WARN",
  "overall_verdict": "warn",
  "integrity_status": "pass",
  "reason_code": "reproducible_development_evidence_with_material_binding_errors",
  "requested_reviewer_model": "gpt-6-astra",
  "requested_reviewer_reasoning": "ultra",
  "reviewer_model": null,
  "model_identity_source": "requested_route_only_no_separate_returned_identity",
  "reviewer_family": "openai",
  "review_independence": "same-family",
  "acceptance_status": "provisional",
  "reviewer_task": "/root/publication_audit",
  "checks": {
    "gt_provenance": "PASS",
    "score_normalization": "PASS",
    "result_existence": "PASS",
    "execution_integrity": "PASS",
    "scope": "PASS",
    "eval_type": [
      "real_gt: upstream behavioral regression",
      "synthetic_proxy: constructed extraction expectations"
    ]
  },
  "actual_scope": {
    "upstream_incidents": 1,
    "real_source_versions": 2,
    "constructed_variants": 9,
    "current_reports_reproduced": 11,
    "baseline_reports_reproduced": 2,
    "model_runs": 0
  },
  "required_corrections_remaining": [
    "Respect block and named-function-expression bindings, or conservatively suppress ambiguous expansion.",
    "Invalidate callback/helper identities after visible writes in expanded sibling helpers.",
    "Recognize destructuring assignment targets during binding invalidation."
  ],
  "nonblocking_hardening": [
    "Require complete behavioral outcome tuples in runner assertions.",
    "Retain the disclosed bounded and incomplete invocation coverage limitations."
  ],
  "claims": [
    {
      "id": "known_upstream_relation_distinction",
      "impact": "supported"
    },
    {
      "id": "recorded_development_results",
      "impact": "supported"
    },
    {
      "id": "general_lexical_binding_correctness",
      "impact": "unsupported"
    },
    {
      "id": "runtime_safety",
      "impact": "unsupported"
    },
    {
      "id": "unseen_project_accuracy_or_llm_benefit",
      "impact": "unsupported"
    }
  ],
  "audited_input_hashes": {
    "temporal_contract_analyzer/publication.py": "sha256:eb3758a609fe1201918c422c23ce6148e52de2908420b3e75fac6432d6acc881",
    "temporal_contract_analyzer/core.py": "sha256:81eef03d8d409a649a4323c0d3a4b05c85a634d0f4e8b9ad0442f276f9f003bb",
    "temporal_contract_analyzer/layers.py": "sha256:6816cb6503350268763f91b2a58f823beaf62c5458497c717e9d101cefd9f2cf",
    "temporal_contract_analyzer/boundary_cards.py": "sha256:1115545eff6d4845d12804eabb6dfce68684f95ef21fef0bca42c3823153acfa",
    "tools/temporal-contract-analyzer/parse.cjs": "sha256:32a838887c36b546bd40645fb56712827b60555d20b9289302d16b8199096371",
    "tests/test_state_publication.py": "sha256:ee17702955eacbbe2fd2e3902af1fb1abaedced08be56cfe7ff9919e82e6e403",
    "docs/STATE_PUBLICATION_REVIEW.md": "sha256:68cf2a6c156711bb05a1fddd0569bbfd4b1010a79f4f7d88fc06fbbf9e241c5e",
    "external-tests/reentry-publication-v1/run.py": "sha256:abe02e728941e46ccfd939cdf9f5f074ddaa43ace2d6429afe145334b80f70e0",
    "external-tests/reentry-publication-v1/run-03/protocol.json": "sha256:d86628ff8bbddd97edc02cc18474617bdfdf07f637cdd8f63f340f91e4c69cac",
    "external-tests/reentry-publication-v1/run-03/summary.json": "sha256:8ec037bf0370b5fe90fa7b8219b5a71649698700674781cc5ab02b51c926a7d6",
    "external-tests/reentry-publication-v1/run-03/comparison.json": "sha256:8258e4e6da960f7ed36eee12ed5cfa7f41a4a3e50ba98f5299592f43fc5de841",
    "external-tests/reentry-publication-v1/README.md": "sha256:af5b0a6b234badf23108634d92a7b149372ef27ab97a6c95600fe45549abe9ee"
  },
  "behavioral_suites_rerun_by_auditor": false,
  "repository_files_modified": false,
  "paid_model_calls_dispatched": false
}
```

