# Release scope and archive boundaries

Inspected HEAD: `f195c332aa1d7d00e1c41d6cef9820c6da691a95`. No files were deleted or moved.

The intended core is source/AST evidence, the versioned obligation vocabulary, source context retrieval, unified experience memory, expert activation, and bounded development/evaluation interfaces. A fixed experience schema does not by itself make the current repository a portable release.

## Measured tracked content

Sizes below are current tracked working-file bytes, not Git history, ignored caches or an installed package.

| Directory | Tracked files | MiB | Share |
|---|---:|---:|---:|
| research | 30047 | 608.90 | 94.3% |
| external-tests | 3027 | 27.92 | 4.3% |
| refine-logs | 87 | 2.30 | 0.4% |
| paper | 56 | 2.14 | 0.3% |
| experience-memory | 37 | 1.55 | 0.2% |
| implement-stage | 153 | 0.88 | 0.1% |
| temporal_contract_analyzer | 59 | 0.68 | 0.1% |
| tests | 40 | 0.37 | 0.1% |
| experiments | 6 | 0.31 | 0.0% |
| idea-stage | 25 | 0.21 | 0.0% |
| vscode-extension | 17 | 0.18 | 0.0% |
| figures | 3 | 0.14 | 0.0% |
| docs | 15 | 0.11 | 0.0% |
| tools | 12 | 0.11 | 0.0% |
| [root files] | 11 | 0.07 | 0.0% |
| case-clusters | 52 | 0.04 | 0.0% |
| examples | 2 | 0.00 | 0.0% |
| templates | 1 | 0.00 | 0.0% |

Total tracked content: 645.91 MiB across 33650 files.

## Proposed disposition

| Content | Public tool tree | Preservation action |
|---|---|---|
| Core package, required JS parsers, CLI and selected UI | Keep | Include only advertised features, with their runtime assets |
| Canonical taxonomy, experience schema, master/role prompt specifications | Keep | Version and document what the runtime actually loads |
| Tests and minimal examples/fixtures | Keep | Existing tests use case-clusters and templates; move fixtures only with matching path/test updates |
| Reviewed reusable guidance | Keep a curated view | Pending candidates are examples, not expert-approved defaults; preserve evidence/lineage separately |
| research/, refine-logs/, implement-stage/, idea-stage/ | Exclude from normal tool release after decoupling | Preserve full originals in a separately versioned research archive |
| external-tests/, paper/, paper plans, publication figures and result sets | Select a minimal reproducibility artifact | Archive full inputs/results/commands supporting every reported claim, including failures |
| __pycache__/, *.pyc, .DS_Store, reproducible temporary build output | Exclude; removable after checking regeneration | They are not research evidence; many are already ignored |
| Logs, traces, patches, scores and usage files | Do not delete by suffix | Failed/interrupted runs and unknown usage are provenance, not disposable caches |

## Actual dependencies that block blanket deletion

1. Shared runtime dependencies are now packaged under `_session_runtime/` and loaded by `execution_backend.py`. The V1–V3 schedulers are removed; historical outputs are inspected only through `history status/report`.

2. Tests still read `case-clusters/` and `templates/case/prompts/temporal-audit.md`. These are small fixture dependencies, not merely old experiments. Preserve them or relocate them with the tests.

3. `core.py` and `context.py` load JavaScript assets under repository-level `tools/temporal-contract-analyzer/`. The package configuration lists Python modules, Web assets and taxonomy/reminder JSON, so an installed-artifact test must check these external assets rather than assuming checkout execution proves packaging works. Keep dependency lockfiles.

4. Case discovery/evaluation still supports the sibling `temporal-contract-bench`; the history browser defaults to `research/`; the evolution controller loads the root master prompt. Separate optional benchmark/history adapters from normal tool startup and ship every required prompt/asset explicitly.

5. Documentation, experience provenance and reused runtime material include repository-local or machine-specific paths. Keep the originals, and create an explicit portable/public projection with provenance and its own digests rather than silently editing frozen records or claiming old approvals bind new content.

6. Experience loading validates content-addressed provenance and parent-version chains. A curated export must include the selected records' required source/parent closure, or use an explicitly derived runtime format. Do not delete `experience-memory/sources/` or parent records and assume the unchanged canonical records will still validate.

7. Release version metadata currently differs: `setup.cfg` declares 0.6.0 while `core.py` declares 0.6.9. Reconcile release metadata and test the built artifact; no version was changed in this inspection.

## Recommended release process

1. Define the advertised feature boundary and promote required runtime assets out of historical batches.
2. Export a new whitelist-based public source tree; retain this development checkout and immutable research evidence.
3. Test CLI, AST parsing, retrieval, expert gates and synthetic lifecycle from the export/installed artifact without the original research directories or sibling checkout. Paid experiments are not needed for these checks.
4. Prepare a separate reproducibility artifact with the exact frozen code, commands, prompts, full results and limitations supporting paper claims. Do not replace missing evidence with only favorable summaries.
5. Add an owner-selected LICENSE and third-party provenance/notices. Prepare any anonymous submission projection against the applicable venue requirements; no venue-specific acceptance claim is made here.

Removing working-tree files does not remove them from Git history. This inspection does not authorize history rewriting, publication, uploading artifacts or deletion of original experiments.

Current scope: a concrete inventory and dependency/disposition proposal only. No cleanup, runtime extraction, license selection, release build or public publishing was performed.

## Subsequent execution

The authorized cleanup is recorded separately in [CLEANUP.md](CLEANUP.md). The observations above describe the pre-cleanup tree.
