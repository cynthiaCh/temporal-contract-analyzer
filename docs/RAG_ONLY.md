# Task-only RAG pilot

`rag_only` gives the agent the original task and retrieved excerpts from the current frozen candidate. It does not append D explanations, failed effect identifiers, hypotheses or experience memory. The corpus is candidate source plus visible Markdown/text, including README requirements; the query is the original task verbatim. Historical failure selection and trusted scoring remain researcher-side.

Retrieval uses local BM25 (k1=1.5, b=0.75), 48-line chunks with stride 40, up to eight ranked chunks and 8000 initial characters. Local lexical definitions/imports expand at most two levels within 12000 total code/text characters. Scores, exact selected snippets, parser status and omitted ranges are saved in `rag-context.json`; exact model material is frozen in the job prompt/report. This pilot does not use embeddings, external documents or a complete call graph.

`Workbench.prepare_rag(experiment_id, job_id)` creates a single independent workspace from the immutable candidate snapshot that was actually scored. The original task and explicit model/effort/config route/timeout are inherited. Existing two-arm hypothesis preparation and archived runs keep their meaning. Start/evaluate reuse the normal Workbench implementation and parent gain/loss checks. A regressing candidate is not eligible and never automatically replaces its parent.

The batch entry point prepares by default; `--execute` starts real model calls:

```sh
python3 tools/run_rag_comparison.py \
  --matrix results/ad-model-effort-20261104/results.json \
  --controls results/hypothesis-repair-v2-20261104/campaign/verified-results.json \
  --output /path/to/new-rag-campaign \
  --bench-root /path/to/temporal-contract-bench \
  --node /path/to/node --execute
```

Only the original 11 failed D jobs in that export are selected. The script verifies source snapshot, oracle baseline and model/effort/config/timeout against the historical v2 D and hypothesis controls before any calls. It adds 11 RAG attempts, not another 22 control/treatment attempts. Raw scores and regressions are reported alongside the historical controls, explicitly marked as noncontemporaneous. Actual tokens need not be equal. Single runs on author-exposed tasks are descriptive developer experiments, not evidence of generalization or statistical significance.
