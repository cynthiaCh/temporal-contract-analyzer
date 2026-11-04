# Assumption Ledger

ASK mode: never

| ID | Under-determined by request | Chosen | Class | Source |
|---|---|---|---|---|
| R-001 | Meaning of standalone RAG | Original task + retrieved candidate code/Markdown only; no D explanations, oracle feedback, hypothesis templates or memory in model inputs. | semantic | default |
| R-002 | Retrieval mechanism and corpus | Local BM25 over 48-line overlapping chunks of the frozen scored candidate; query is verbatim original task. Reuse parsed lexical/local-import definition expansion up to depth 2. No embeddings or external knowledge base. | semantic | default |
| R-003 | Which runs and controls | Same 11 original D failures as v2, one RAG attempt each; reuse historical v2 D/hypothesis controls, verify identical parent snapshot and settings. Not a fresh randomized paired campaign. | semantic | default |
| R-004 | Retrieval budget | Up to eight ranked chunks and 8000 seed code/text characters, then expand within 12000 total source characters; record omissions and incomplete parsing. Same model/effort/timeout caps, actual tokens measured separately. | interface | default |
| R-005 | Researcher-side oracle use | Scored source selection, calibration and regression checks remain oracle-informed outside model inputs. Retrieval accepts only task, public candidate bytes and lexical parser information. | semantic | default |
| R-006 | Integration | Add an opt-in single-job RAG preparation method; preserve the existing two-arm hypothesis-repair API and archived manifests. No UI redesign or automatic patch promotion. | interface | default |
