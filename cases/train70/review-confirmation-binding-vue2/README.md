Synthetic derived variant of review-confirmation-binding-vanilla.

Run: node case-clusters/document-review-binding/arms/review-confirmation-binding-vue2/oracle/probe.cjs case-clusters/document-review-binding/arms/review-confirmation-binding-vue2/reference/bounded ungranted
Install pinned native runtimes: python3 -B runtimes/document-submit-ports/install.py --install
Pinned real frameworks are installed in the ignored shared results runtime and exercised by the framework loader. Both prompt conditions share base and oracle; solver materializes only base and selected prompt.

Actual validation: reference PASS on 26 deterministic schedules; no-op UNDERREACH for unfinished coalescing; nine targeted mutants each produce behavioral violation witnesses. Base PASS under the original immediate-write policy. Registered native-probe and actual HTTP /api/options supported=true. See case-clusters/document-review-binding/expansion/review-confirmation-binding-vanilla/validation-summary.csv and oracle/assertion-obligation-map.json for commands, scope matrix and relation-level witnesses. These are synthetic same-source variants, not independent real issues; no human-reviewed freeze or publication eligibility claimed.
