# DeepSeek latent + experience, fixed30, workers8

User authorized this paired ablation on2026-11-22. DeepSeek-Flash/low via Qoder Credits; identical frozen58-entry bank,case order,original sources and Action24model-turn/600second limit as Auto-Contract+Experience. One Action followed by independent final Gold; no Contract,no learning,no new selection calls.

`frozen-selections.json` holds the actual historical selector outputs,including successful bounded validation corrections where applicable. Each is revalidated against original public sources and the approved bank; the recomputed delivery must exactly match its frozen digest. The4original invalid selections remain empty. In total23cases retain nonempty guidance and7retain no guidance(including3valid selections with no applicable experience). No new applicability choices based on test outcomes are made.

`retrieval-provenance.json` identifies every parent run,delivery,selector correction stage,model turns and Credits. Historical retrieval costs are reused and reported separately,not silently treated as newly executed or omitted when interpreting end-to-end cost.

`prepare.py` prepares30fresh trajectories and verifies task/source/model/image/budget/bank/retrieval identity before any model execution. `paired-input-validation.json` is the zero-model launch check. The only intended Action input change is a null Contract; experience text and existing Action instruction remain unchanged. The new runtime condition and deterministic replay are documented infrastructure differences; the Qoder adapter and grader are unchanged.

Run progress is visible at http://127.0.0.1:8765/. `monitor.py` writes live `monitor-status.json`,per-case results,and the four-arm paired comparison after all30cases have valid scores. Infrastructure errors remain separate for inspection; valid behavioral failures are not automatically replayed. No paper or figure is changed by this run.

Relevant validation:52business-retrieval/trajectory tests passed,including Action-only execution with exact guidance,final-onlyGold,and rejection of changed delivery/evidence or unsupported training mode.
