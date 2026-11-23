# Fig3: GPT-6.1 library-size update

Reproduce: `python3 figures/gpt61-memory-size/build.py`.

The new 20/40-entry points use the existing index matrix produced by `tools/generate_bootstrap_indices.py`: 1,000 paired bootstrap samples, 30 case draws, Python random seed 20260925, sample SD (ddof=1). Case IDs are joined to the recorded index order. All 30 outcomes in each group are valid. The 40-entry result retains the original 18 valid scores and replaces only the 12 infrastructure-invalid outcomes with their authorized fresh replays.

GPT-6.1 points (bootstrap mean ± SD, %): 0 entries 53.4 ± 9.6 (preserved Table1); 20 entries 80.2 ± 7.1 (24/30); 40 entries 90.2 ± 5.6 (27/30); 61 entries 90.0 ± 5.5 (user-specified, matching Table1). The historical 0/61 summaries are preserved, rather than recalculated under a different case ordering. GPT-5.6 and DeepSeek data are unchanged from published Fig3.

Overleaf project: https://www.overleaf.com/project/6aeb6a27e6c2f33263179d63
Updated `sections/9_usage.tex` and added `sections/Acc-MemorySize-GPT61.pdf`, retaining both original figure assets. Before/after source snapshots are included. No model calls or additional experiments.

Online source readback matched the updated text. Downloaded compiled output `/home/sribd/Downloads/ICPC_2027_Tool-3.pdf` was checked: 6 pages, Fig3 on page 4, all three legend labels visible, new text present, original Table1 cells retained. Vector figure checked at paper scale.
