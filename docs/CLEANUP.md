# Performed cleanup — f195c332aa1d

Historical experiments and results were moved, not discarded. 700,213 files / 8,425,887,097 content bytes have matching before/after hash/mode/link inventories.

- Research archive: [temporal-contract-analyzer-research-archive-20261110_131852](/home/sribd/Downloads/wangshu/temporal-contract-analyzer-research-archive-20261110_131852)
- Full report: [REPORT.md](/home/sribd/Downloads/wangshu/temporal-contract-analyzer-research-archive-20261110_131852/_cleanup/REPORT.md)
- Machine-readable summary: [summary.json](/home/sribd/Downloads/wangshu/temporal-contract-analyzer-research-archive-20261110_131852/_cleanup/summary.json)
- Clean source export: [temporal-contract-analyzer-release-20261110_131852](/home/sribd/Downloads/wangshu/temporal-contract-analyzer-release-20261110_131852) — 223 source files, 1.60 MiB, plus manifest.

The maintained tool now packages its single-session runtime, JS parsers, lockfiles and canonical controller prompt. Version: 0.6.10. The root MASTER_PROMPT.md links to the packaged canonical file. The existing research experience store remains byte-identical; no versions activated, no model calls, no global configuration changes and no Git commit. The index remains unchanged; Git working-tree deletions for historical paths represent the external archive moves.

Independent source/wheel smoke checks passed (4/4), as did eight runner archival/replay checks. The final 430-test suite retained 13 failures and two subtest errors: host Python 3.8.10 does not satisfy Python >=3.9, and host Node v22.23.2 does not satisfy two fixtures requiring v16.20.2. Scoring/version gates remain unchanged. This is not an all-green release certification.

The clean export excludes this machine-local document, historical studies, installed dependencies and exposed research memory. Existing local Node dependencies are retained in the checkout. Historical records still occupy disk space in the archive. License selection and publishing are pending owner actions. See [archive boundaries](ARCHIVE.md) for portable documentation.
