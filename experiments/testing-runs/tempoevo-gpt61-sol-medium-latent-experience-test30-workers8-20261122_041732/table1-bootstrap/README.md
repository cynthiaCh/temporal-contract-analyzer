# Table 1: GPT-6.1-sol medium, Latent + Experience only

Raw:23/30=76.7%, no unscored cases. Bootstrap mean ± sample SD: 77.0067 ± 7.7165%; displayed cell: 77.0 ± 7.7%.

Generated with tools/generate_bootstrap_indices.py, 1000 paired draws of30 fixed cases, seed20260925, sample SD(ddof=1). The index matrix exactly matches the preceding GPT-5.6 Latent+Experience bootstrap. The coverage column is not ground truth. Historical Auto-Contract+Experience is recomputed for reference only; its existing Table1 cell is preserved. Frozen61 bank, no new selector/Contract calls or experience updates. Runtime differences from historical parent are disclosed in the experiment README.

Overleaf verification and exact one-cell patch are in overleaf-sync/. Reproduce with python3 -B experiments/testing-runs/tempoevo-gpt61-sol-medium-latent-experience-test30-workers8-20261122_041732/table1-bootstrap/build.py
