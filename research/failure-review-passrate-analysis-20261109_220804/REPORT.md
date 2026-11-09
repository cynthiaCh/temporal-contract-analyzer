Historical case pass-rate analysis

Source: `/home/sribd/Downloads/wangshu/failure-review-export-20261029.zip`. Complete discovery ledger: 49,212 entries; 11,886 model-bearing receipts including two explicitly named stubs. This is the October 29 export, not the November experience experiments.

The failure index alone is not a valid denominator: index.csv excludes PASS. The complete discovery-inventory.json was streamed from the ZIP without extracting 3.65 GB of archive material or executing any archived script. Its 11,886 run receipts and 7,565 PASS labels reconcile with the exporter summary.

Primary descriptive result: 6,603/9,694 = 68.11%. The denominator includes only matched, mutually consistent saved run/score receipts with clear final status and no contamination or other explicit final validity failure. There are 3,091 admitted behavioral failures and 1,267 excluded/unverified real-model execution groups. No score has been rerun or independently re-certified.

Cases: 249; 248 have valid-score evidence. 24 have observed 100%, 3 observed 0%, and 221 fall between. All three zero-rate cases have only two valid scores. Six cases have fewer than ten valid scores. One case has no valid-score denominator.

Case-balanced mean rate (each of the 248 scored case IDs has equal weight): 67.20%; median case rate: 73.10%. These are descriptive distributions, not estimates over independently sampled cases. 36 case IDs have multiple recorded manifest/input hashes; 1788 valid groups lack these version fields.

Counting rules:

- Model-bearing run.json receipts define the observation inventory. Standalone scores, controls and posthoc rescoring do not create new model attempts. Two explicit stub identities are excluded.
- Final status must be SCORED or COMPLETED, verdict recognized, explicit validity not false, no contamination finding, outer validity status clear, and a matching associated score must exist with no case/variant/verdict disagreement or a contradictory PASS/runtime-error label. Completed candidate runtime failures retain their original non-PASS verdict and are separately flagged. These are historical receipt admission rules, not independent validation of grader semantics.
- Missing score evidence, errors, contamination and unscored outcomes are excluded from the behavioral denominator. A zero denominator is N/A, never 0%. Candidate export incompleteness is not silently converted into a behavioral failure.
- 887 exact full-receipt copy groups were identified using a recorded execution identity and identical canonical receipt content. 923 redundant copies were folded; all original paths remain in duplicate_groups.csv and execution_groups.csv. Different model attempts/retries are retained. Modified copies may remain, so no independence claim is made.
- Case IDs remain separate; language/framework variants are not collapsed into independent source incidents. Model, effort, condition, variant, workflow profile, time budget and available version hashes are exposed in strata files.
- A case can occur under different source/evaluator versions or mixed prompt conditions. Pooled rank is observational, not intrinsic difficulty or a controlled comparison. Equal exact pass fractions share a dense rank; sample size only breaks display ties. No significance or IID confidence-interval claims are made.

Raw-copy sensitivity:

Before copy folding: 7,227/10,521 = 68.69%, excluding 1,363 unverified/error real-model receipts. After exact-copy folding: 68.11%; change -0.58 percentage points. Both tables are retained. In particular, 306 PASS labels with CONTAMINATED status are not counted as valid passes.

Lowest pass rates with at least ten valid scores:

|Case|Pass / valid|Pass rate|Excluded / unverified groups|
|---|---:|---:|---:|
|`review-confirmation-binding-react`|5/37|13.51%|4|
|`query-paused-initial-fetch-10266-java`|4/29|13.79%|10|
|`query-paused-initial-fetch-10266-go`|5/30|16.67%|9|
|`review-confirmation-binding-vue2`|7/38|18.42%|2|
|`query-paused-initial-fetch-10266-php`|6/32|18.75%|8|
|`query-paused-initial-fetch-10266-vue3`|8/39|20.51%|3|
|`query-paused-initial-fetch-10266-ruby`|7/34|20.59%|8|
|`query-paused-initial-fetch-10266-python3`|9/42|21.43%|8|
|`query-paused-initial-fetch-10266-vue2`|8/35|22.86%|5|
|`query-paused-initial-fetch-10266-vanilla`|9/39|23.08%|3|
|`review-confirmation-binding-vue3`|9/39|23.08%|2|
|`query-paused-initial-fetch-10266-jquery`|9/38|23.68%|5|
|`transfer-progress-composition-v4-window-cued-java-eval-v2`|7/29|24.14%|11|
|`review-confirmation-binding-jquery`|9/36|25.00%|5|
|`draft-autosave-handoff-precise-rule-vanilla-port-jquery`|11/43|25.58%|5|

Highest pass rates with at least ten valid scores:

|Case|Pass / valid|Pass rate|Excluded / unverified groups|
|---|---:|---:|---:|
|`draft-async-save-handoff-ruby`|42/42|100.00%|4|
|`local-config-readiness-latent-vue2-port-jquery`|40/40|100.00%|3|
|`draft-async-save-handoff-jquery`|39/39|100.00%|3|
|`draft-autosave-handoff-v2-ruby`|38/38|100.00%|5|
|`local-config-readiness-latent-vue2-port-go`|38/38|100.00%|4|
|`local-config-readiness-latent-vue2-port-php`|38/38|100.00%|6|
|`draft-async-save-handoff-go`|37/37|100.00%|5|
|`draft-autosave-handoff-v2-php`|37/37|100.00%|5|
|`local-config-readiness-latent-vue2-port-python3`|37/37|100.00%|4|
|`draft-autosave-handoff-v2-go`|36/36|100.00%|5|
|`download-polling-restoration-explicit-java-eval-v2`|35/35|100.00%|7|
|`draft-async-save-handoff-java`|35/35|100.00%|6|
|`draft-async-save-handoff-python3`|35/35|100.00%|6|
|`draft-autosave-handoff-v2-java`|35/35|100.00%|7|
|`draft-autosave-handoff-v2-python3`|35/35|100.00%|7|

Cases used in the recent research discussion, where present in this older export:

|Case|Pass / valid|Pass rate|Excluded / unverified groups|
|---|---:|---:|---:|
|`query-paused-initial-fetch-10266-python3`|9/42|21.43%|8|
|`query-paused-initial-fetch-10266-vanilla`|9/39|23.08%|3|
|`transfer-progress-maintenance-v2-vanilla`|28/77|36.36%|3|
|`document-submit-snapshot-vanilla`|42/78|53.85%|9|
|`document-submit-snapshot-python3-eval-v2`|19/34|55.88%|8|
|`transfer-progress-maintenance-v2-python3`|23/37|62.16%|6|
|`cached-feed-lifecycle-repair-python3`|29/33|87.88%|8|
|`draft-autosave-handoff-order-example-vanilla`|62/69|89.86%|3|

These older pooled rates do not describe the recent AUTO+automatic-Contract protocol. For example, current preferred gpt-5.6-terra/low has sparse per-case observations in this archive. The whole archive mixes six models and latent, provided-Contract and Generic conditions. Use the filters or case_model_condition.csv before choosing a comparable case.

Complete ranking (all case IDs; lowest pass rate first):

|Case|Pass / valid|Pass rate|Excluded / unverified groups|
|---|---:|---:|---:|
|`document-submit-snapshot-python3`|0/2|0.00%|0|
|`transfer-progress-composition-v4-window-cued-php`|0/2|0.00%|0|
|`transfer-progress-composition-v4-window-cued-vue2`|0/2|0.00%|0|
|`review-confirmation-binding-react`|5/37|13.51%|4|
|`query-paused-initial-fetch-10266-java`|4/29|13.79%|10|
|`query-paused-initial-fetch-10266-go`|5/30|16.67%|9|
|`review-confirmation-binding-vue2`|7/38|18.42%|2|
|`query-paused-initial-fetch-10266-php`|6/32|18.75%|8|
|`query-paused-initial-fetch-10266-vue3`|8/39|20.51%|3|
|`query-paused-initial-fetch-10266-ruby`|7/34|20.59%|8|
|`query-paused-initial-fetch-10266-python3`|9/42|21.43%|8|
|`query-paused-initial-fetch-10266-vue2`|8/35|22.86%|5|
|`query-paused-initial-fetch-10266-vanilla`|9/39|23.08%|3|
|`review-confirmation-binding-vue3`|9/39|23.08%|2|
|`query-paused-initial-fetch-10266-jquery`|9/38|23.68%|5|
|`transfer-progress-composition-v4-window-cued-java-eval-v2`|7/29|24.14%|11|
|`review-confirmation-binding-jquery`|9/36|25.00%|5|
|`draft-autosave-handoff-precise-rule-vanilla-port-jquery`|11/43|25.58%|5|
|`review-confirmation-binding-python3`|9/35|25.71%|7|
|`draft-autosave-handoff-vue3-port-python3`|9/33|27.27%|7|
|`draft-autosave-handoff-vanilla-port-jquery`|11/39|28.21%|3|
|`draft-autosave-handoff-precise-rule-vanilla-port-ruby`|11/37|29.73%|5|
|`draft-autosave-handoff-vue3-port-jquery`|11/37|29.73%|4|
|`transfer-progress-composition-v4-window-cued-go-eval-v2`|11/37|29.73%|8|
|`draft-autosave-handoff-vanilla-port-vue3`|11/36|30.56%|2|
|`draft-autosave-handoff-vue3-port-ruby`|11/36|30.56%|4|
|`draft-autosave-handoff-precise-rule-vanilla-port-vue3`|12/39|30.77%|2|
|`draft-autosave-handoff-vanilla-port-java`|10/32|31.25%|10|
|`draft-autosave-handoff-vue3-port-go`|11/35|31.43%|5|
|`draft-autosave-handoff-vanilla-port-react`|12/38|31.58%|2|
|`draft-autosave-handoff-vue3-port-vue3`|12/38|31.58%|2|
|`draft-autosave-handoff-vue3-port-php`|10/31|32.26%|8|
|`transfer-progress-composition-v4-window-cued-python3-eval-v2`|10/31|32.26%|11|
|`draft-autosave-handoff-precise-rule-vanilla-port-go`|11/34|32.35%|8|
|`draft-autosave-handoff-precise-rule-vanilla-port-php`|12/37|32.43%|4|
|`draft-autosave-handoff-vanilla-port-php`|12/37|32.43%|5|
|`draft-autosave-handoff-vue3-port-react`|12/37|32.43%|2|
|`draft-autosave-handoff-vue3-port-vue2`|12/37|32.43%|3|
|`draft-autosave-handoff-precise-rule-vanilla-port-react`|13/40|32.50%|2|
|`draft-autosave-handoff-vanilla-port-vue2`|13/40|32.50%|2|
|`draft-autosave-handoff-precise-rule-vanilla-port-vue2`|13/39|33.33%|4|
|`draft-autosave-handoff-precise-rule-vanilla-port-python3`|12/36|33.33%|5|
|`transfer-progress-composition-v4-window-cued-ruby-eval-v2`|11/33|33.33%|9|
|`draft-autosave-handoff-vue3-port-java`|11/32|34.38%|7|
|`draft-autosave-handoff-vanilla-port-go`|13/37|35.14%|5|
|`draft-autosave-handoff-vanilla-port-python3`|13/37|35.14%|5|
|`review-confirmation-binding-go`|13/37|35.14%|5|
|`workspace-draft-projection-latent-vanilla-port-ruby`|11/31|35.48%|8|
|`transfer-progress-composition-v4-window-cued-php-eval-v2`|13/36|36.11%|6|
|`transfer-progress-maintenance-v2-vanilla`|28/77|36.36%|3|
|`draft-autosave-handoff-precise-rule-vanilla-port-java`|12/33|36.36%|7|
|`review-confirmation-binding-php`|12/33|36.36%|8|
|`draft-autosave-handoff-vanilla-port-ruby`|13/35|37.14%|5|
|`transfer-progress-composition-v4-window-cued`|25/67|37.31%|3|
|`review-confirmation-binding-ruby`|13/34|38.24%|6|
|`review-confirmation-binding-java`|14/36|38.89%|5|
|`transfer-progress-composition-v4-window-cued-vue2-eval-v2`|14/36|38.89%|5|
|`workspace-draft-projection-latent-vanilla-port-java`|12/29|41.38%|10|
|`workspace-draft-projection-latent-vanilla-port-go`|15/35|42.86%|5|
|`workspace-draft-projection-latent-vanilla-port-php`|15/35|42.86%|5|
|`async-generator-close-python-port-vue2`|23/52|44.23%|4|
|`transfer-progress-composition-v4-window-cued-jquery-eval-v2`|16/35|45.71%|8|
|`workspace-draft-projection-latent-vanilla-port-python3`|16/35|45.71%|4|
|`async-generator-close-python-port-react`|26/55|47.27%|6|
|`download-polling-restoration-low-cue-react18`|33/68|48.53%|3|
|`transfer-progress-composition-v4-window-cued-react-eval-v2`|17/35|48.57%|6|
|`workspace-draft-projection-latent-vanilla-port-vue3`|18/37|48.65%|2|
|`async-generator-close-python-port-vue3`|22/45|48.89%|4|
|`workspace-draft-projection-latent-vanilla-port-react`|19/38|50.00%|2|
|`workspace-draft-projection-latent-vanilla-port-jquery`|18/36|50.00%|4|
|`download-polling-restoration-explicit-vanilla`|1/2|50.00%|0|
|`download-polling-restoration-python3`|1/2|50.00%|0|
|`transfer-progress-composition-v4-window-cued-vue3-eval-v2`|20/39|51.28%|3|
|`workspace-draft-projection-latent-vanilla-port-vue2`|20/39|51.28%|4|
|`listener-registration-order-vanilla`|40/77|51.95%|4|
|`async-generator-close-python-port-jquery`|26/49|53.06%|6|
|`document-submit-snapshot-vanilla`|42/78|53.85%|9|
|`workspace-draft-projection-latent-vanilla`|42/77|54.55%|3|
|`transfer-progress-maintenance-v2-jquery`|18/33|54.55%|6|
|`document-submit-snapshot-python3-eval-v2`|19/34|55.88%|8|
|`document-submit-snapshot-react-eval-v2`|19/34|55.88%|5|
|`local-config-readiness-python`|40/70|57.14%|10|
|`cached-feed-lifecycle-repair-vanilla`|39/68|57.35%|4|
|`download-polling-restoration-react18`|46/79|58.23%|7|
|`document-submit-snapshot-vue2-eval-v2`|20/34|58.82%|4|
|`transfer-progress-maintenance-v2-react`|22/37|59.46%|4|
|`listener-registration-order-ruby`|24/40|60.00%|4|
|`draft-autosave-handoff-order-example-python3`|23/38|60.53%|4|
|`listener-registration-order-java`|22/36|61.11%|8|
|`document-submit-snapshot-vue3-eval-v2`|21/34|61.76%|4|
|`transfer-progress-maintenance-v2-python3`|23/37|62.16%|6|
|`download-polling-restoration-low-cue-react18-port-jquery`|20/32|62.50%|5|
|`document-submit-snapshot-go-eval-v2`|22/35|62.86%|7|
|`document-submit-snapshot-java-eval-v2`|22/35|62.86%|7|
|`transfer-progress-maintenance-v2-java`|22/35|62.86%|10|
|`review-confirmation-binding-vanilla`|45/71|63.38%|10|
|`draft-autosave-handoff-vue3`|44/69|63.77%|3|
|`document-submit-snapshot-ruby-eval-v2`|24/37|64.86%|6|
|`draft-autosave-handoff-order-example-ruby`|24/37|64.86%|5|
|`listener-registration-order-python3`|24/37|64.86%|3|
|`transfer-progress-maintenance-v2-go`|24/37|64.86%|5|
|`transfer-progress-maintenance-v2-vue3`|26/40|65.00%|2|
|`document-submit-snapshot-php-eval-v2`|23/35|65.71%|7|
|`draft-autosave-handoff-order-example-vue2`|25/38|65.79%|3|
|`draft-autosave-handoff-order-example-vue3`|26/39|66.67%|4|
|`document-submit-snapshot-jquery-eval-v2`|24/36|66.67%|5|
|`transfer-progress-maintenance-v2-vue2`|24/36|66.67%|6|
|`draft-autosave-handoff-order-example-jquery`|20/30|66.67%|9|
|`download-polling-restoration-low-cue-react18-port-python3`|25/37|67.57%|6|
|`transfer-progress-maintenance-v2-php`|25/37|67.57%|5|
|`draft-autosave-handoff-v2-vanilla`|54/79|68.35%|2|
|`draft-autosave-handoff-order-example-react`|22/32|68.75%|6|
|`listener-registration-order-vanilla-module`|27/39|69.23%|3|
|`listener-registration-order-go`|25/36|69.44%|4|
|`local-config-readiness-latent-vue2`|54/77|70.13%|3|
|`download-polling-restoration-low-cue-react18-port-vue3`|26/37|70.27%|4|
|`local-config-readiness-low-cue-go`|26/37|70.27%|6|
|`transfer-progress-maintenance-v2-ruby`|26/37|70.27%|4|
|`listener-registration-order-react`|24/34|70.59%|4|
|`listener-registration-order-jquery`|22/31|70.97%|4|
|`draft-autosave-handoff-vanilla`|48/67|71.64%|4|
|`download-polling-restoration-low-cue-react18-port-vue2`|26/36|72.22%|3|
|`draft-autosave-handoff-order-example-java`|26/36|72.22%|6|
|`listener-registration-order-vue2`|24/33|72.73%|5|
|`async-generator-close-python-port-php`|36/49|73.47%|11|
|`async-generator-close-python-port-go`|37/50|74.00%|8|
|`listener-registration-order-php`|26/35|74.29%|4|
|`download-polling-restoration-low-cue-react18-port-react`|27/36|75.00%|2|
|`listener-snapshot-order-vanilla-port-python3`|28/37|75.68%|2|
|`listener-registration-order-vue3`|29/38|76.32%|3|
|`local-config-readiness-low-cue-vanilla`|29/38|76.32%|3|
|`local-config-readiness-low-cue-jquery`|30/39|76.92%|3|
|`local-config-readiness-low-cue-vue2`|52/67|77.61%|3|
|`download-polling-restoration-low-cue-react18-port-php`|28/36|77.78%|4|
|`listener-snapshot-order-vanilla-port-vue3`|28/36|77.78%|4|
|`rxjs-asyncsubject-clear-latent-maintenance`|14/18|77.78%|2|
|`listener-snapshot-order-vanilla-port-ruby`|25/32|78.12%|8|
|`async-generator-close-python-port-java`|40/51|78.43%|9|
|`cached-feed-lifecycle-repair-java`|26/33|78.79%|13|
|`download-polling-restoration-low-cue-react18-port-go`|26/33|78.79%|10|
|`download-polling-restoration-low-cue-react18-port-java`|26/33|78.79%|9|
|`listener-snapshot-order-vanilla-port-react`|26/33|78.79%|6|
|`download-polling-restoration-low-cue-react18-port-ruby`|30/38|78.95%|5|
|`draft-autosave-handoff-order-example-php`|30/38|78.95%|5|
|`listener-snapshot-order-vanilla-port-jquery`|27/34|79.41%|4|
|`local-config-readiness-low-cue-vue3`|31/39|79.49%|7|
|`async-generator-close-python-port-ruby`|39/49|79.59%|11|
|`cached-feed-lifecycle-repair-vue3`|28/35|80.00%|8|
|`draft-autosave-handoff-order-example-go`|29/36|80.56%|5|
|`subscription-lifetime-scope-vanilla-port-vue2`|29/36|80.56%|5|
|`download-polling-restoration-jquery-eval-v2`|30/37|81.08%|4|
|`download-polling-restoration-python3-eval-v2`|30/37|81.08%|5|
|`local-config-readiness-low-cue-react`|30/37|81.08%|4|
|`async-generator-close-python`|66/81|81.48%|4|
|`cached-feed-lifecycle-repair-vue2`|31/38|81.58%|6|
|`local-config-readiness-low-cue-python3`|31/38|81.58%|4|
|`local-config-readiness-low-cue-java`|27/33|81.82%|9|
|`cached-feed-lifecycle-repair-jquery`|28/34|82.35%|6|
|`listener-snapshot-order-vanilla-port-java`|28/34|82.35%|6|
|`listener-snapshot-order-vanilla-port-php`|29/35|82.86%|6|
|`cached-feed-lifecycle-repair-react`|30/36|83.33%|4|
|`listener-snapshot-order-vanilla-port-vue2`|31/37|83.78%|2|
|`draft-autosave-handoff-precise-rule-vanilla`|58/69|84.06%|2|
|`cached-feed-lifecycle-repair-vanilla-module`|32/38|84.21%|4|
|`listener-snapshot-order-vanilla`|59/70|84.29%|2|
|`cached-feed-lifecycle-repair-go`|31/36|86.11%|6|
|`download-polling-restoration-vue3-eval-v2`|32/37|86.49%|4|
|`listener-snapshot-order-vanilla-port-go`|32/37|86.49%|5|
|`async-generator-close-python-port-python3`|33/38|86.84%|7|
|`rxjs-asyncsubject-clear-latent-maintenance-port-jquery`|40/46|86.96%|9|
|`rxjs-asyncsubject-clear-latent-maintenance-port-php`|40/46|86.96%|8|
|`draft-autosave-handoff-v2-jquery`|34/39|87.18%|4|
|`draft-autosave-handoff-v2-vue3`|34/39|87.18%|3|
|`subscription-lifetime-scope-vanilla-port-react`|34/39|87.18%|5|
|`rxjs-asyncsubject-clear-latent-maintenance-port-python3`|42/48|87.50%|4|
|`subscription-lifetime-scope-vanilla-port-python3`|35/40|87.50%|2|
|`cached-feed-lifecycle-repair-python3`|29/33|87.88%|8|
|`download-polling-restoration-go-eval-v2`|30/34|88.24%|5|
|`subscription-lifetime-scope-vanilla-port-java`|30/34|88.24%|7|
|`cached-feed-lifecycle-repair-php`|31/35|88.57%|8|
|`download-polling-restoration-ruby-eval-v2`|31/35|88.57%|5|
|`local-config-readiness-low-cue-ruby`|31/35|88.57%|6|
|`rxjs-asyncsubject-clear-latent-maintenance-port-react`|39/44|88.64%|7|
|`rxjs-asyncsubject-clear-latent-maintenance-port-vue3`|40/45|88.89%|4|
|`cached-feed-lifecycle-repair-ruby`|32/36|88.89%|6|
|`download-polling-restoration-java-eval-v2`|32/36|88.89%|9|
|`rxjs-asyncsubject-clear-latent-maintenance-port-go`|41/46|89.13%|7|
|`local-config-readiness-low-cue-php`|33/37|89.19%|5|
|`draft-async-save-handoff-vue3`|34/38|89.47%|3|
|`draft-autosave-handoff-v2-react`|34/38|89.47%|3|
|`draft-async-save-handoff-vanilla`|62/69|89.86%|2|
|`draft-autosave-handoff-order-example-vanilla`|62/69|89.86%|3|
|`subscription-lifetime-scope-vanilla`|62/69|89.86%|2|
|`download-polling-restoration-explicit-vue2-eval-v2`|36/40|90.00%|3|
|`subscription-lifetime-scope-vanilla-port-jquery`|43/47|91.49%|4|
|`draft-async-save-handoff-vue2`|35/38|92.11%|3|
|`download-polling-restoration-explicit-python3-eval-v2`|36/39|92.31%|6|
|`download-polling-restoration-explicit-vue3-eval-v2`|36/39|92.31%|4|
|`download-polling-restoration-vue2-eval-v2`|36/39|92.31%|2|
|`draft-autosave-handoff-v2-vue2`|36/39|92.31%|2|
|`rxjs-asyncsubject-clear-latent-maintenance-port-ruby`|40/43|93.02%|8|
|`rxjs-asyncsubject-clear-latent-maintenance-port-vue2`|40/43|93.02%|8|
|`local-config-readiness-python-port-ruby`|28/30|93.33%|10|
|`subscription-lifetime-scope-vanilla-port-php`|32/34|94.12%|7|
|`download-polling-restoration-react-eval-v2`|34/36|94.44%|3|
|`local-config-readiness-latent-vue2-port-vue2`|34/36|94.44%|5|
|`local-config-readiness-python-port-jquery`|34/36|94.44%|3|
|`subscription-lifetime-scope-vanilla-port-ruby`|35/37|94.59%|4|
|`subscription-lifetime-scope-vanilla-port-vue3`|35/37|94.59%|3|
|`download-polling-restoration-explicit-go-eval-v2`|36/38|94.74%|4|
|`download-polling-restoration-explicit-ruby-eval-v2`|36/38|94.74%|4|
|`draft-async-save-handoff-react`|36/38|94.74%|3|
|`local-config-readiness-python-port-vue2`|36/38|94.74%|2|
|`local-config-readiness-python-port-vue3`|36/38|94.74%|3|
|`local-config-readiness-python-port-python3`|40/42|95.24%|4|
|`rxjs-asyncsubject-clear-latent-maintenance-port-java`|41/43|95.35%|9|
|`local-config-readiness-python-port-php`|29/30|96.67%|7|
|`download-polling-restoration-explicit-react18`|65/67|97.01%|5|
|`download-polling-restoration-explicit-php-eval-v2`|34/35|97.14%|5|
|`local-config-readiness-latent-vue2-port-react`|34/35|97.14%|4|
|`local-config-readiness-python-port-react`|35/36|97.22%|4|
|`download-polling-restoration-php-eval-v2`|37/38|97.37%|4|
|`download-polling-restoration-explicit-vanilla-eval-v2`|38/39|97.44%|4|
|`download-polling-restoration-explicit-jquery-eval-v2`|39/40|97.50%|2|
|`draft-async-save-handoff-ruby`|42/42|100.00%|4|
|`local-config-readiness-latent-vue2-port-jquery`|40/40|100.00%|3|
|`draft-async-save-handoff-jquery`|39/39|100.00%|3|
|`draft-autosave-handoff-v2-ruby`|38/38|100.00%|5|
|`local-config-readiness-latent-vue2-port-go`|38/38|100.00%|4|
|`local-config-readiness-latent-vue2-port-php`|38/38|100.00%|6|
|`draft-async-save-handoff-go`|37/37|100.00%|5|
|`draft-autosave-handoff-v2-php`|37/37|100.00%|5|
|`local-config-readiness-latent-vue2-port-python3`|37/37|100.00%|4|
|`draft-autosave-handoff-v2-go`|36/36|100.00%|5|
|`download-polling-restoration-explicit-java-eval-v2`|35/35|100.00%|7|
|`draft-async-save-handoff-java`|35/35|100.00%|6|
|`draft-async-save-handoff-python3`|35/35|100.00%|6|
|`draft-autosave-handoff-v2-java`|35/35|100.00%|7|
|`draft-autosave-handoff-v2-python3`|35/35|100.00%|7|
|`local-config-readiness-latent-vue2-port-ruby`|35/35|100.00%|7|
|`local-config-readiness-python-port-java`|35/35|100.00%|4|
|`subscription-lifetime-scope-vanilla-port-go`|35/35|100.00%|6|
|`local-config-readiness-latent-vue2-port-java`|34/34|100.00%|7|
|`local-config-readiness-python-port-go`|34/34|100.00%|7|
|`local-config-readiness-latent-vue2-port-vue3`|33/33|100.00%|6|
|`draft-async-save-handoff-php`|32/32|100.00%|6|
|`query-paused-initial-fetch-10266`|11/11|100.00%|11|
|`download-polling-restoration-react`|2/2|100.00%|0|
|`publish-validity-preview-request-latent-vanilla`|0/0|N/A|6|

Downloads and audit trail:

- ranking.html: standalone sortable/filterable table with model, effort, condition, variant and minimum sample size controls, plus filtered CSV download.
- case_ranking.csv and case-ranking.json: primary exact-copy-folded ranking.
- case_ranking_raw_receipts.csv: raw-receipt ranking and per-case copy sensitivity.
- case_model_condition.csv and case_model_condition_version.csv: configuration and available-version strata.
- model_effort_condition.csv: configuration aggregates; condition_deltas_descriptive.csv: within-recorded-stratum latent-baseline differences, descriptive only; absent baseline means no fabricated delta.
- execution_groups.csv/json, duplicate_groups.csv and excluded_records.csv: every included/excluded group and all original source paths.
- raw-run-receipts.jsonl and run-receipts.json: full original inventory run objects and reduced metadata; score/outer projections are kept separately.
- inventory-audit.json, export-summary.json, source-provenance.json, offline-tests.log, integrity.json and ARTIFACTS.sha256: reconciliation, source identity and analysis integrity.

Candidate runtime-error sensitivity:

Six completed behavioral-failure groups contain candidate runtime errors: source syntax errors, invalid decode arguments, or DEBUG output breaking the host protocol. Their original failures remain in the main denominator. Excluding all runtime-labelled groups as a sensitivity gives 6,603/9,688 = 68.16%. This does not relabel explicit CANDIDATE_RUNTIME_ERROR/SCORER_ERROR final statuses as completed scores. Evidence is in runtime-result-review.json.

Findings and implications:

1. Query-paused variants repeatedly appear among the lowest pooled pass rates. This supports considering them as historical difficulty signals, subject to matched model/condition and existing exposure; it does not prove a mechanism-specific cause.
2. The new direct-routing cached-feed case and draft-autosave order example have high historical pooled rates, consistent with ceiling risk. Their sparse matched Terra/low evidence does not establish that every future attempt must pass.
3. More than one thousand execution groups are unverified or invalid. Counting these as behavioral failures, or using the failure-only CSV as the complete dataset, would distort ranking.
4. Use configuration-specific historical rows to shortlist candidates, fix a protocol before any new run, and record outcome-informed selection. No new experiment, model call, grading run, production update or Git commit is performed here.
