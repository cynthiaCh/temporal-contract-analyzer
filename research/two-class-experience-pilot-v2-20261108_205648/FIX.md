# v2 runtime and archival fixes

New authorized batch; v1 and global/production configuration unchanged.

- archive.collect now handles explicit null or missing usage, missing per-field values, malformed events and missing/malformed ledger. Raw CLI event stream/stderr and raw ledger remain primary; agent-messages and partial-answer are derived without marking an unfinished turn complete. service-errors retains original CLI errors and failed hook records separately from archive-status. Raw provider wire body is not exposed by the CLI and is not fabricated.
- usage.py separates observed per-field token subtotal, full usage (null if incomplete), per-field unknown request counts, wholly missing usage, pending requests, success vs terminated hook counts and accounting errors. Zero is retained only when actually reported.
- runner keeps snapshots/diff/partial response after stream failure, timeout or parsing failure. Valid behavior scoring requires normal complete turn, valid final envelope, source-body reads, valid request accounting, no service failure and successful immutable archive. A partial patch alone is not a completed scored candidate. Original error identity is preserved even when archival succeeds.
- v2 campaign stops after the first infrastructure/invalid-runtime session, without retries or supplementation; tests retain all planned slots. This intentionally differs from v1 continuous-two infrastructure rule and v1 partial resource-limit scoring.
- Python owns all copying, code/source snapshots, diff generation, manifests and cost summaries. Maintenance prompt unchanged in its mechanical-archival instruction; models only repair business source and verify necessary behavior.

Validation before models:

31 offline unit checks passed, including exact v1 failed-event/ledger replay, null/missing/per-field usage, pending request, timeout, malformed event/final answer, complete-score admission, both scorer schemas, success/retained/lost distinction, conflict veto and drift binding. Four actual candidate bwrap namespaces verified JS/Python body reading, readonly extraction, hidden host archive, hook IPC and automatic snapshot. Durable replay in offline/replay-v1-failure preserves the exact observed partial final candidate; original service error remains, archive OK, scorer callback not invoked, known total 34555 with one unknown request. No connection/model probes were used. These checks cannot guarantee future service availability.

Semantic extraction/feedback/veto changes and evidence are in SEMANTIC_AUDIT.md. Veto is an executing-agent visible-input audit, not a new model judge or automated proof of semantics. No v1 learned text seeds a new reflection.
