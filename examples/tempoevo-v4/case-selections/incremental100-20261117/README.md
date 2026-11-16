# Incremental100 construction and testing

Authorized execution:70 training cases (26 historical V8-equivalent accepted runs reused,
44 new/repeated runs),20 new tests,10 retained development regression results (8/10).
The fixed100 forces inclusion of those10 and replaces4 cases from the earlier relative
hardest100 draft. Exact source core is parent_case_id. IDs are disjoint across train/test;
each tested core has a training counterpart. Per-core ratios are approximate.

All solver roles use gpt-6.1-sol/medium. Four training workers run the public CLI;
44 new runs retain V8 three-Action construction semantics. Newly executed cases use
explicit public syntax/build smoke checks and unchanged independent training Oracle.
These public checks cover less business behavior than some historical reused V8 examples;
reused results are historical training evidence, not reruns under identical seed/checks.
Initial39 approved experiences remain historical guidance. Older37 merged entries do
not have complete per-entry case lineage; initial lineage audit is linked in plan.json.

After every new training case reaches a valid terminal result, archive all candidate
pools/provisional entries, publish successful content candidates, then accept this run's
new entries as Silas under explicit user authorization. automatic-review.json records
that this is automatic authorized acceptance, not an independent human review. Failed
or exhausted training is never reported as an accepted repair. Invalid/infrastructure
jobs hold test launch for investigation; existing successful jobs are retained.

Freeze the resulting approved bank and execute only the new20 tests with4 workers.
Testing is business-source-v1, selection12+Contract12+Action24 requests,one Action,
one final-only Gold; no diagnosis, extraction, A/B or extra Contract review. Retain
old10 scores and their original39 bank unchanged. Report new20 separately, then optional
combined(old8 + new passes)/30. The combined value is explicitly mixed-time/mixed-bank
and includes a development cohort; it does not establish unseen generalization.

Preflight uses immutable images, selected source identity, three Gold controls per new
training/test case and public smoke controls per training case. No models before
independent agent-follows-doc validation. Runtime bytes must not change while jobs run.
For a confirmed tool bug, preserve failed roots, drain active workers, fix/verify and
prepare replacement trajectories for affected jobs; never overwrite old scores or
replay a partially started stage. Behavioral failure uses only its original3 Actions.

Compatibility preflight corrections: legacy Python-pilot manifests and unchanged Python scorer are supported; only the disposable RxJS execution-log directory is writable. Large derived RxJS repositories use declared public source projection with all product src and named original public tests, while the trusted grader restores the remaining immutable originals and applies actual submitted modifications/deletions. This input projection differs from historical full-repository baselines.
