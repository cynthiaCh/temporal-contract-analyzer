**`run-05` verdict: WARN, with one remaining combined state-binding case.** All previously reported callback/helper counterexamples are resolved. The known p-debounce evidence remains reproducible. Same-family / provisional review.

| Check | Verdict | Evidence |
|---|---|---|
| A. Provenance | PASS | Verified upstream sources and maintainer regression oracle remain separate from constructed extraction expectations (`run.py:68–88,100–104`). |
| B. Normalization | PASS | Raw counts; no prediction-based normalization (`run.py:51–56,120–128`). |
| C. Results | PASS | All 11 reports reproduce exactly; bundles verify; comparison reproduces; six implementation snapshots match current bytes and protocol hashes. |
| D. Execution | PASS | Full TAP outcome tuples agree with recorded results and runner checks (`run.py:145–152`). Retained logs report **25 focused tests** and **152 full-suite tests** passing. |
| E. Scope | PASS | One known defect and nine constructed variants, with explicit exclusions of accuracy, generalization, safety, and LLM-benefit claims. |
| F. Type | PASS | `real_gt` for upstream behavioral regression; constructed `synthetic_proxy` expectations for extraction statuses. |

The remaining correction is in `temporal_contract_analyzer/publication.py:169–173`: `non_function_writes` requires `owner(...) == binding`. An ambiguous class-scope write has `owner(...) is None`; it is also absent from the function prefix, so neither uncertainty check catches it.

```js
function wrap(deliver) {
  let active;
  return function entry() {
    if (active) return;
    class X {
      static {
        active = true;
        { let active; }
      }
    }
    const value = deliver();
    active = value;
  };
}
```

Current output is **`write_after_call`, with no uncertainty**. Class initialization actually writes the outer `active` before `deliver()`. Under the documented conservative scope, this should be **`not_established`**. Apply the same possible-ancestor-binding test already used by `visible_writes()` to non-function-scope state writes. This is a combination of the two newly handled uncertainty cases, not a request for general control-flow proof.

Independently confirmed resolved: original block/helper shadowing, sibling callback/helper mutation, scalar destructuring, named-function self-binding, object/array destructuring of `.apply`, ambiguous sibling mutation, catch/class shadowing, and class static-block/static-field callback mutation. The positive named helper still resolves.

**Supported:** the known-case ordering distinction; all 11 disclosed development expectations; frozen-source/report correspondence; existing tests 80/80 on both versions and regression tests 0/3→3/3. **Unsupported:** general relation correctness, runtime safety, unseen-project accuracy, or developer/LLM benefit.

Actual follow-up inspection covered the production/test diff against `run-04`, current documentation and retained logs, 14 independent in-memory probes, all `run-05` reports/bundles/sources, implementation snapshots, protocol, summary, comparison, and complete TAP outcome tuples. I did not rerun the behavioral suites or spawn additional agents. No files were modified.

```json
{
  "audit_skill": "experiment-audit",
  "verdict": "WARN",
  "overall_verdict": "warn",
  "integrity_status": "pass",
  "reason_code": "ambiguous_non_function_state_write_not_marked_unknown",
  "audited_run": "run-05",
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
    "independent_in_memory_probes": 14,
    "focused_tests_in_retained_log": 25,
    "full_suite_tests_in_retained_log": 152,
    "behavioral_suites_rerun_by_auditor": false
  },
  "required_corrections_remaining": [
    "Treat ambiguous non-function-scope state writes as unknown when the outer binding remains a possible ancestor target."
  ],
  "audited_input_hashes": {
    "temporal_contract_analyzer/core.py": "sha256:81eef03d8d409a649a4323c0d3a4b05c85a634d0f4e8b9ad0442f276f9f003bb",
    "temporal_contract_analyzer/publication.py": "sha256:8ae1de551e24bfb561c404670e56050c0c8d66be110d3f99d5015f3c1d6eeb11",
    "temporal_contract_analyzer/layers.py": "sha256:2571dd45d15380a9df70459f186b21cab0ff200334f792809c06aac530a1f564",
    "temporal_contract_analyzer/boundary_cards.py": "sha256:1115545eff6d4845d12804eabb6dfce68684f95ef21fef0bca42c3823153acfa",
    "tools/temporal-contract-analyzer/parse.cjs": "sha256:43f1909f7e6c67df30754959e2bb1b1bddd31ac1919ad3868bb210dfd4dcd347",
    "tests/test_state_publication.py": "sha256:ebd14847138e1a307eb09ffbb157e79db8a06bacdfbd6bf30c1140c497c095d2",
    "external-tests/reentry-publication-v1/run.py": "sha256:644fd4840da194e22bd053bc7ad25b9ca5524a6425aeb27b9d32bba875538343",
    "docs/STATE_PUBLICATION_REVIEW.md": "sha256:f75f6db4347df7ebe54270dfc784464d29aa27a8887b071cb36153ccdc38b43f",
    "external-tests/reentry-publication-v1/README.md": "sha256:f495a065af70103db83e954029aecb47676320ba92f86e7402d7c4362eda5ad3",
    "external-tests/reentry-publication-v1/run-05/protocol.json": "sha256:9c689f2b032c7aa49d8ac0d74eea3a8d844e3d3c26f2eb863dd776cc3c067795",
    "external-tests/reentry-publication-v1/run-05/summary.json": "sha256:69a6e2db08098d67a578cde8d794d2a0d54c4bd61ed9e981b9ff9b8179e12868",
    "external-tests/reentry-publication-v1/run-05/comparison.json": "sha256:e7ef7e57f3060ea57edef350acf6ffb9c0b4d5bd42ee066bd38f2d29fc3fb474"
  },
  "repository_files_modified": false,
  "additional_agents_spawned": false,
  "paid_model_calls_dispatched": false
}
```

