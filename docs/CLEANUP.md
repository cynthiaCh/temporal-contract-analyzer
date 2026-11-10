# Performed cleanup — f195c332aa1d

Historical experiments and results were moved, not discarded. 700,213 files / 8,425,887,097 content bytes have matching before/after hash/mode/link inventories.

- Research archive: [temporal-contract-analyzer-research-archive-20261110_131852](/home/sribd/Downloads/wangshu/temporal-contract-analyzer-research-archive-20261110_131852)
- Full report: [REPORT.md](/home/sribd/Downloads/wangshu/temporal-contract-analyzer-research-archive-20261110_131852/_cleanup/REPORT.md)
- Machine-readable summary: [summary.json](/home/sribd/Downloads/wangshu/temporal-contract-analyzer-research-archive-20261110_131852/_cleanup/summary.json)
- Clean source export: [temporal-contract-analyzer-release-20261110_131852](/home/sribd/Downloads/wangshu/temporal-contract-analyzer-release-20261110_131852) — 223 source files, 1.60 MiB, plus manifest.

The maintained tool now packages its single-session runtime, JS parsers, lockfiles and canonical controller prompt. Version: 0.6.10. The root MASTER_PROMPT.md links to the packaged canonical file. The existing research experience store remains byte-identical; no versions activated, no model calls, no global configuration changes and no Git commit. The index remains unchanged; Git working-tree deletions for historical paths represent the external archive moves.

Independent source/wheel smoke checks passed (4/4), as did eight runner archival/replay checks. The final 430-test suite retained 13 failures and two subtest errors: host Python 3.8.10 does not satisfy Python >=3.9, and host Node v22.23.2 does not satisfy two fixtures requiring v16.20.2. Scoring/version gates remain unchanged. This is not an all-green release certification.

The clean export excludes this machine-local document, historical studies, installed dependencies and exposed research memory. Existing local Node dependencies are retained in the checkout. Historical records still occupy disk space in the archive. License selection and publishing are pending owner actions. See [archive boundaries](ARCHIVE.md) for portable documentation.

## Local residual cleanup — 2026-11-10, Asia/Shanghai

The previous archive paths above refer to another host and could not be verified
on this checkout. This follow-up preserves local remnants independently; it does
not certify that the full historical archive is available on this machine.

- Local archive: `/Volumes/Extreme/paper+survey/temporal-contract-analyzer-local-archive-20261110_142455/`.
- `manifest.json` records every original/destination path, file SHA256,
  permission mode and symlink target; `summary.json` records verified totals.
- Moved the remaining `external-tests/`, `paper/` and `refine-logs/` trees into
  `residuals/`: 316 files, 32,448,555 bytes, including 311 Git-untracked files
  and five ignored Finder metadata files. All inventories match after moving.
- Relocated installed parser dependencies from the obsolete
  `tools/temporal-contract-analyzer/node_modules/` to the maintained
  `temporal_contract_analyzer/javascript/node_modules/`. All 475 installed
  file/link entries retain their hashes, modes and link targets; 439 had been
  visible as untracked files. Package versions and integrity values match the
  maintained lockfile. No installation or dependency upgrade was needed.
- Added narrow ignore rules for the legacy dependency location and local paper
  build products. No tracked source, experience record or expert decision was
  removed. No Git commit, history rewrite or public upload was performed.

Retain `tests/`, `case-clusters/`, `templates/` and parser/runtime package assets:
they are used by the tool or its offline checks. Installed editor dependencies,
old VSIX/screenshot output and private `.aris/` work remain ignored locally and
are excluded by the clean exporter. The local experience library remains intact;
the public exporter deliberately starts without exposed research candidates.

For publication, generate a new source-only tree with `tools/export-release.py`.
Keep research evidence and this machine-local cleanup record outside that tree.
License selection, access to the full historical archive, and a separately
curated paper-reproduction artifact remain distinct release tasks.

Follow-up validation: 107 selected offline tests ran; 106 passed and one native
backend calibration check could not complete because this macOS host lacks the
required Linux `bwrap` isolation tool. No gate was bypassed. The source-only
export contains 223 files (about 1.60 MiB); its CLI, Python/TypeScript/Vue parsing,
source-context parser, native-backend import and packaged controller prompt
passed smoke checks. JavaScript checks used the relocated, lockfile-matched
dependencies through `NODE_PATH`; dependencies are not bundled in the export.
The six local experience records and all source evidence match Git HEAD exactly;
the active view remains empty. Validation details are in the local archive.

The generated tree is
`/Volumes/Extreme/paper+survey/temporal-contract-analyzer-release-local-20261110_142455/`.
Portable documentation examples now use configurable or placeholder paths instead
of the original author's volume layout. No open-source license was selected.
