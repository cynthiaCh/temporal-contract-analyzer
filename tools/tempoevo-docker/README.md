# Selected-case Docker batches

`prepare_selected.py` prepares and freezes inputs; it does not call a model.
`run_selected.py --execute` starts the explicitly authorized experiment. Always
use a new output root. Historical trajectories are not reinterpreted or resumed
under a different protocol.

The default selection remains the historical hardest50 CSV. To use a different
ranked CSV, pass `--selection-file`. To resolve public inputs directly from the
frozen SWE-TempoC roster, also pass `--swe-tempoc-root` (testing only):

```bash
python3 -B tools/tempoevo-docker/prepare_selected.py \
  --root /new/batch/root \
  --selection-file examples/tempoevo-v4/case-selections/swe-tempoc-hard-latent25-20261116/selected_25_cases.csv \
  --swe-tempoc-root /path/to/swe-tempoc \
  --solver-image sha256:SOLVER_IMAGE_ID \
  --grader-image sha256:GRADER_IMAGE_ID \
  --mode testing --condition structured --model-profile sol61-medium --limit 25
python3 -B tools/tempoevo-docker/run_selected.py --root /new/batch/root --execute
```

The image arguments require full immutable locally present IDs. Preparation
archives the actual selected CSV and source digest. It validates unique ranks
and case IDs, existing split restrictions, public source identity and the current
protocol. Failed preparation remains explicit in `progress.json`.

Current V11 testing uses Auto-Contract and, for `structured`, a frozen approved
experience snapshot. It permits one bounded Action, then one independent Gold
evaluation. Gold does not enter model feedback or retry decisions. Testing does
not extract or publish experiences. Historical difficulty-based selection is
diagnostic, not evidence of an unseen independent test set.

For regular roster cases, only the public maintenance core and base are loaded;
provided Contract suffixes, references and scorer contents are not solver inputs.
The RxJS upstream maintenance case additionally uses `upstream_inputs.py`: it
extracts all original `src/**`, named original public tests, and root documents
from the checksum-bound original archive. Full upstream npm dependencies are
not mounted in the solver. `upstream_gold.py`, on the trusted side, restores the
unprojected original files and applies the actual submitted changes (including
deletions in the projection), then invokes the unchanged SWE-TempoC scorer.
Trusted tests and reference patches are never copied to the solver. This public
source projection differs from historical full-repository baselines and must be
reported when comparing that case. Full grading is validated by the eventual
final score, not by preparation or source extraction alone.
