# Experiment Audit Report

Date: 2026-11-01. Reviewer route: native Codex, requested gpt-6-astra / ultra. Same-family / provisional; actual returned model identity unavailable.

**Final scoped verdict: PASS for `run-06`.** All reported counterexamples are resolved, and no material correction remains within this follow-up’s scope. Earlier WARNs apply to their historical bytes. Review assurance remains **same-family / provisional**.

The last combined case now produces `not_established`, includes `non_function_scope_state_write`, and emits no concrete publication-order relation. `possible_owner()` consistently handles possible ancestor bindings in both callback invalidation and class-scope state uncertainty (`temporal_contract_analyzer/publication.py:61–68,172–175`). The exact regression is retained at `tests/test_state_publication.py:197–209`.

| Check | Verdict | Evidence |
|---|---|---|
| A. Provenance | PASS | Previously verified upstream snapshots and maintainer regression tests remain separate from constructed development expectations (`run.py:68–88,100–104`). |
| B. Normalization | PASS | Raw outcomes and explicit expected statuses; no prediction-derived normalization (`run.py:51–56,120–128`). |
| C. Results | PASS | All **11 current reports reproduce exactly**; all bundles verify; comparison reproduces; six implementation snapshots match current files and protocol hashes. |
| D. Execution integrity | PASS | TAP agrees with complete outcome checks (`run.py:145–152`). Current retained logs report **25 focused tests** and **152 full-suite tests passing**. |
| E. Scope | PASS | One known defect and nine constructed variants. Conservative exclusions, repeated-source-ID limitations, and absence of safety/generalization claims are explicit (`docs/STATE_PUBLICATION_REVIEW.md:9–13,45–49`). |
| F. Evaluation type | PASS | `real_gt` for upstream behavioral regression; constructed `synthetic_proxy` expectations for extraction statuses. |

I independently reran 14 in-memory probes: all 12 prior callback/helper counterexamples suppress the incorrect association; the combined class/state case becomes unknown; the positive named-helper example still resolves.

**Supported claims:** the rule presents the known p-debounce ordering distinction; all 11 disclosed development expectations match; frozen implementations and reports correspond; retained behavioral outcomes are 80/80 existing tests on both versions and 0/3→3/3 regression passes.

**Not established:** general relation correctness, runtime safety, unseen-project accuracy, or developer/LLM benefit. A bounded candidate-review result remains a review lead.

Actual final scope: affected code/test changes, current documentation, the retained counterexamples, all `run-06` source/report bundles and implementation snapshots, protocol/summary/comparison, TAP outcome tuples, and current test logs. Behavioral suites were inspected rather than rerun. No files were edited, additional agents spawned, or paid model calls dispatched.

