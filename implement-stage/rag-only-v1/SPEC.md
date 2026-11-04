# Task-driven RAG-only pilot

Extend the existing continued-repair runner with a feedback-free `rag_only` condition. Run the same 11 original D-failure snapshots, keeping explicit model, effort, mode and 600-second timeout. Compare to the already saved, same-parent v2 D and hypothesis runs; controls are historical, not rerun.

RAG input is the original task plus task-ranked candidate source/Markdown chunks and bounded lexical/import definitions. No D report, scan findings, failure names, oracle outcomes, candidate hypotheses or experience memory enter the retrieval query or model material. Evaluation still uses trusted calibrated oracles and parent gain/loss accounting outside the model input.

Success: retrieval leakage and budget tests, existing repair tests; 11 real RAG jobs with frozen inputs/materials and full scored records. Same-family assumption review remains provisional. No claim about embedding RAG, broader corpora, randomized controls or equal actual token consumption.

Base commit: 3a8fd7868128a8c5b7b93bd24666d3f5a92cc62b, with the preceding uncommitted hypothesis-repair implementation preserved.
