**Current verdict: WARN for `run-04` bytes.** The original counterexamples are fixed and the experiment remains reproducible. Additional binding-invalidity cases require correction. This is a **same-family, provisional** review; the prior WARN remains historical.

| Check | Verdict | Current evidence |
|---|---|---|
| A. Provenance | PASS | Same verified upstream snapshots and maintainer regression tests; constructed extraction expectations remain explicitly labeled (`run.py:68–88,100–104`). |
| B. Normalization | PASS | Raw counts and explicit expected statuses; no prediction-derived normalization (`run.py:51–56,120–128`). |
| C. Existence/numbers | PASS | All 11 `run-04` reports reproduce exactly; all bundles verify; comparison reproduces. Six implementation snapshots match current files and protocol hashes (`run.py:91–104`). |
| D. Execution integrity | PASS | Complete outcome tuples now require exact counts, exit status, and zero cancellation/skips/todos (`run.py:145–152`). Retained TAP agrees. I independently ran all **22 focused tests**, passing; the full retained log reports **149 tests passing**. |
| E. Scope | PASS | One known defect, two upstream versions, nine constructed variants; no accuracy or developer/LLM benefit claims (`docs/STATE_PUBLICATION_REVIEW.md:45–49`; experiment `README.md:16–20`). |
| F. Evaluation type | PASS | `real_gt` for upstream behavioral regression; constructed `synthetic_proxy` expectations for extraction statuses. |

Original sibling reassignment, scalar destructuring, block-local helper, and named-function self-binding probes now suppress the erroneous association. The positive named-function-expression helper still resolves.

Remaining corrections:

1. **Ambiguous writes are silently discarded instead of invalidating a possible outer binding.** At `publication.py:48–60`, `owner()` returns `None` for a block-uncertain name and `visible_writes()` excludes that write. This counterexample still emits an external callback relation:

   ```js
   function wrap(deliver) {
     let active;
     function replace() { deliver = () => 1; { let deliver; } }
     return function entry() {
       if (active) return;
       replace();
       active = deliver();
     };
   }
   ```

   The real assignment replaces the outer parameter. Conservatively invalidate associations when an ambiguous write could target the binding.

   The same issue affects synchronous class initialization because its synthetic scope is absent from `functions` (`parse.cjs:135–142`; `publication.py:43–60`):

   ```js
   class X { static { deliver = () => 1; } }
   active = deliver();
   ```

   A static-field initializer has the same result.

2. **Member targets nested inside destructuring are missing from `write_roots`.** `parse.cjs:75–77` removes top-level member access but does not recursively recover member roots inside patterns:

   ```js
   ({method: deliver.apply} = {method: () => 1});
   active = deliver.apply(this, []);
   ```

   The write records `write_roots: []`, so the overwritten method is still associated with the original callback. Recursively handle pattern leaves, including member targets.

3. **Catch parameters and class declarations remain unrecorded shadowing bindings.** A returned entry inside `catch (deliver)` or a block containing `class deliver {}` is still linked to `wrap(deliver)`. Relevant parser handling is `parse.cjs:135–142,163–164`; binding ownership uses only recorded variables/functions and self-names (`publication.py:27–55`). Record these shadowing boundaries or exclude their unresolved associations.

These are specific false binding/order relations, not unsupported safety verdicts. The documented candidate-review framing is appropriate, but the stronger visible-write/shadowing exclusions in `docs/STATE_PUBLICATION_REVIEW.md:9` are still not fully implemented.

**Supported:** the known p-debounce ordering distinction, all 11 recorded development expectations, exact frozen implementation/report correspondence, and the retained 80/80 versus 0/3→3/3 behavioral outcomes. **Unsupported:** general binding correctness, unseen-project accuracy, runtime safety, or developer/LLM benefit.

Actual follow-up scope: current parser/publication logic and all focused tests; changed layer fields and comparison logic; unchanged core/card files checked by exact hashes; current runner/docs; all 11 `run-04` sources and bundles, comparison, implementation snapshots, protocol, summary and TAP; independent additional analyzer probes. Behavioral TAP suites were inspected rather than rerun. No repository files were modified and no paid model calls were dispatched.

```json
{
  "audit_skill": "experiment-audit",
  "verdict": "WARN",
  "overall_verdict": "warn",
  "integrity_status": "pass",
  "reason_code": "remaining_binding_invalidation_and_shadowing_gaps",
  "audited_run": "run-04",
  "requested_reviewer_model": "gpt-6-astra",
  "requested_reviewer_reasoning": "ultra",
  "reviewer_model": null,
  "reviewer_family": "openai",
  "review_independence": "same-family",
  "acceptance_status": "provisional",
  "checks": {
    "gt_provenance": "PASS",
    "score_normalization": "PASS",
    "result_existence": "PASS",
    "execution_integrity": "PASS",
    "scope": "PASS",
    "eval_type": [
      "real_gt",
      "synthetic_proxy"
    ]
  },
  "verification": {
    "exact_current_reports": 11,
    "verified_current_bundles": 11,
    "matching_implementation_snapshots": 6,
    "focused_tests_independently_passed": 22,
    "full_suite_passes_in_retained_log": 149,
    "behavioral_suites_rerun_by_auditor": false
  },
  "required_corrections_remaining": [
    "Conservatively invalidate possible outer bindings for ambiguous writes, including class static initialization scopes.",
    "Recover member roots recursively inside destructuring assignment targets.",
    "Represent or conservatively exclude catch-parameter and class-declaration shadowing."
  ],
  "audited_input_hashes": {
    "temporal_contract_analyzer/core.py": "sha256:81eef03d8d409a649a4323c0d3a4b05c85a634d0f4e8b9ad0442f276f9f003bb",
    "temporal_contract_analyzer/publication.py": "sha256:d80ce7721c24555cf612530772ddf324e408cd11ba5642dbdad9b02191165473",
    "temporal_contract_analyzer/layers.py": "sha256:7ccb7a0c68f855a901ddc74a7c49eee23cbeed13e4967f6c55dd091d37353e37",
    "temporal_contract_analyzer/boundary_cards.py": "sha256:1115545eff6d4845d12804eabb6dfce68684f95ef21fef0bca42c3823153acfa",
    "tools/temporal-contract-analyzer/parse.cjs": "sha256:a739083ebcbc5d9f3dfde913bcc1fd7db1cad1a33eb6ae82340c2210f2872441",
    "tests/test_state_publication.py": "sha256:72e990c8eec01bb1e7c08e2370664c2e3f923255229fcd9ef58387b61220a8f9",
    "external-tests/reentry-publication-v1/run.py": "sha256:644fd4840da194e22bd053bc7ad25b9ca5524a6425aeb27b9d32bba875538343",
    "docs/STATE_PUBLICATION_REVIEW.md": "sha256:9a48f709989e8377bb7bfea53d5f532d44b57351d72bd0d8b34a85112aa16736",
    "external-tests/reentry-publication-v1/README.md": "sha256:5163f3b30c4bbc57063ba30e18018c19747b4294315bb2bb2fbd31cdb8c99533",
    "external-tests/reentry-publication-v1/run-04/protocol.json": "sha256:85455d293af5cc7043a57b767caa4e19e60cc5fddbeddaaa06a163afc1f942f7",
    "external-tests/reentry-publication-v1/run-04/summary.json": "sha256:be8516260bf466b63085dad33f87960382de3a9e1abfa69c4d0bc4d1e64d6604",
    "external-tests/reentry-publication-v1/run-04/comparison.json": "sha256:7070ab199a890d1d3f4037204e997497a8571eb5cb42822bb4927bb06df769ef"
  },
  "repository_files_modified": false,
  "paid_model_calls_dispatched": false
}
```

