# Project instructions

## Keep experiment work simple

- Prefer the existing experiment runner and configuration. Do not create a new
  framework or a collection of per-run helper scripts for routine experiments.
- By default, retain only the experiment configuration, selected case list,
  concise progress, per-case outcomes, and final summary. Record the model,
  reasoning effort, concurrency, repair budget, and experience-library version
  in those existing records.
- Do not generate SHA256 manifests, checksum inventories, hash receipts,
  environment-spec hashes, or extra integrity/attestation reports unless the user
  explicitly requests them. Do not add file hashing or repeated calibration as
  a prerequisite for launching an ordinary experiment.
- Reuse an established working environment. Do not introduce extra validation
  agents, environment ledgers, approval gates, or repeated environment checks
  for routine runs unless the user requests them or a concrete failure requires
  investigation. These project preferences override optional skill workflows.
- Commit concise experiment records. Keep bulky raw logs, repeated protocol
  snapshots, and calibration attachments in the run directory rather than
  duplicating them in Git. Do not copy the same evidence into multiple places.
- Existing internal experience IDs and execution bindings are implementation
  details, not a reason to generate additional hash records. Do not delete or
  rewrite bindings required by a running experiment. Changes to such mechanisms
  belong in a separate, targeted code change with relevant tests.
- Preserve the declared training/test split. Label evaluation on training cases
  as training-set replay; do not relabel them as independent test cases.
- Testing uses frozen experience and does not update the library unless the
  user explicitly asks for training or experience updates.
