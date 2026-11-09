Do hard cases imply hard cluster siblings?

Answer: often for the query cluster, but not uniformly across other clusters. This analysis retains the previous receipt admission and exact-copy folding. No model or grader is run.

Historical manifest paths identify 239 of 249 case IDs in 13 clusters. Unassigned cases stay unassigned; cluster identity is not inferred from names. A source unit may contain several clusters.

|Cluster|Cases|Failures / valid|Pooled failure rate|Case failure range|Cases with >=50% failures|
|---|---:|---:|---:|---:|---:|
|query-paused-initial-fetch-10266|9|253/318|79.56%|76.32% to 86.21%|9/9|
|document-review-binding|20|416/788|52.79%|33.33% to 86.49%|9/20|
|draft-autosave-handoff|40|832/1583|52.56%|10.14% to 74.42%|27/40|
|workspace-draft-projection-cues|10|206/392|52.55%|45.45% to 64.52%|8/10|
|transfer-retry-handoff|20|402/784|51.28%|29.73% to 75.86%|10/20|
|async-generator-close-python-expansion|9|156/438|35.62%|13.16% to 55.77%|3/9|
|download-polling-restoration-low-cue-react18-expansion|9|84/318|26.42%|21.05% to 37.50%|0/9|
|listener-registration-order|32|306/1243|24.62%|11.11% to 48.05%|0/32|
|download-polling-restoration|21|124/886|14.00%|0.00% to 51.47%|1/21|
|local-config-readiness|30|148/1192|12.42%|0.00% to 42.86%|0/30|
|rxjs-asyncsubject-reentrant-6520|10|45/422|10.66%|4.65% to 22.22%|0/10|
|subscription-lifetime-scope-vanilla-expansion|9|31/339|9.14%|0.00% to 19.44%|0/9|
|draft-handoff-decomposition|20|58/818|7.09%|0.00% to 31.65%|0/20|

Comparisons that leave the selected hard case out:

|Selected hard case|Cluster|Own failure rate|Sibling failures / valid|Sibling failure rate|Sibling range|
|---|---|---:|---:|---:|---:|
|query-paused-initial-fetch-10266-java|query-paused-initial-fetch-10266|86.21%|228/289|78.89%|76.32% to 83.33%|
|review-confirmation-binding-react|document-review-binding|86.49%|384/751|51.13%|33.33% to 81.58%|
|draft-autosave-handoff-precise-rule-vanilla-port-jquery|draft-autosave-handoff|74.42%|800/1540|51.95%|10.14% to 72.73%|
|workspace-draft-projection-latent-vanilla-port-ruby|workspace-draft-projection-cues|64.52%|186/361|51.52%|45.45% to 58.62%|
|transfer-progress-composition-v4-window-cued-java-eval-v2|transfer-retry-handoff|75.86%|380/755|50.33%|29.73% to 70.27%|
|async-generator-close-python-port-vue2|async-generator-close-python-expansion|55.77%|127/386|32.90%|13.16% to 52.73%|
|download-polling-restoration-low-cue-react18|download-polling-restoration|51.47%|89/818|10.88%|0.00% to 41.77%|

Main observations:

1. All nine formally mapped query variants have failure rates above 76%. Even after omitting the hardest Java variant, the other eight retain a high pooled failure rate. This is the clearest within-cluster difficulty pattern in this archive.
2. document-review-binding ranges from about one third to over 86% failures. The non-vanilla review-confirmation variants are much harder than several submit-snapshot variants; the vanilla review-confirmation arm itself is easier. Cluster membership alone does not guarantee equally hard training and test cases.
3. transfer-retry-handoff also has wide variation. The composition/window-cued Java arm is hard, while several maintenance variants have failure rates around 30%–40%. The shared source mechanism does not establish equal difficulty.
4. The debounced-submit-flush source unit spans multiple clusters, including hard draft-autosave-handoff and much easier draft-handoff-decomposition. Treating this entire source unit as one cluster would obscure important differences.
5. A legacy case named query-paused-initial-fetch-10266 has 11/11 passes under the same source-unit label, but its recorded manifest is cases/... rather than membership in the nine current cluster arms. It is separately reported, not silently merged into those arms or relabeled as the same task version.

Matched configuration checks:

configuration-matched-peers.csv contains 2155 leave-one-case-out comparisons within the same recorded model, effort, prompt condition, variant, workflow profile and time budget. Only 27 rows have at least three anchor scores. These repeats remain correlated and may use distinct case/evaluator versions; no significance or causal cluster-effect claim is made.

Illustrative prompt-condition contrast:

For the 8 common query arms under recorded gpt-6-sol/low and 600 seconds, latent-maintenance fails 8/8, while provided-Contract fails 0/8. Each arm has only one score per condition. The recorded manifest/input hashes agree for all eight pairs; evaluator versions and all other execution details are not independently verified. This posthoc illustration shows why pooled cluster difficulty cannot predict a new AUTO protocol by itself. It is not a causal effect estimate.

Implication for selecting the next pair: use cluster membership to shortlist, then check each exact case under the intended model/effort/Contract/budget and score version. The query cluster offers stronger historical difficulty evidence than the wider document or transfer clusters. Do not assume that an arbitrary sibling must avoid a ceiling. No new experiment is started by this report.

Files:

- cluster-ranking.csv: all recorded cluster summaries.
- cluster-case-rates.csv: every member and its rate.
- leave-one-case-out-peers.csv: all hard anchors with the anchor removed from sibling statistics.
- configuration-matched-peers.csv: configuration-matched sibling comparisons; no score-version equivalence claim.
- membership-evidence.json and case-membership.csv: exact historical membership evidence and unknowns.
- illustrative-condition-contrast.csv: eight common query cases demonstrating condition dependence.
- source-unit-summary.csv: the broader source grouping kept separate.
- summary.json and source-manifest.json: conclusions and unchanged input hashes.
