# Research archive boundary

The tool source and the research record have separate distribution scopes. Full research directories, results (including failed and interrupted sessions), publication files, old output inventories and build ledgers are preserved in a sibling archive. They are not required to import or run the analyzer.

The local checkout's `docs/CLEANUP.md` records the actual archive location and verified counts. It is excluded from the clean public export because it contains machine-local paths. The archive's `_cleanup/` contains the move inventory, raw hashes, source-promotion provenance, commands, validation logs and report.

Historical relative references are interpreted relative to that archive's root. Original absolute paths and code/input hashes inside frozen records remain unchanged; they describe the original execution environment. Moving a record does not make an old frozen campaign resumable. Reproduction requires explicitly restoring its layout and exact dependencies or preparing a new batch with declared differences.

The optional history browser accepts `TCA_DEVELOPMENT_ROOT=/absolute/path/to/archive/research`. No archive path is embedded in the public tool. The research experience store remains unchanged in the development checkout and is also snapshotted with its source/parent closure in the archive. It is excluded from the public source export; initialize a new store explicitly. AI-assisted annotations do not imply expert activation.

The original import ledger is `implement-stage/experience-memory-v1/IMPORT.json`; the seven-label annotation audit is `research/unified-seven-label-recoding-20261110_112750/REPORT.md`; older methods remain under `refine-logs/`. These are archive-relative provenance locators, not required runtime imports.

No failed result is discarded, no unknown usage is replaced with zero, and no old experimental claim is upgraded by this file cleanup. Git history is retained. License selection, privacy/anonymity review, and public distribution are separate owner actions.
